#!/usr/bin/env python3
"""
   John Franklyn 06/18/2020
   BME280 python 3.7 code
   output written to mysql database pihydropdata
   changed code to use SPI instead of i2c for BME280
   Gravity ph, rpo, ec, water level sensors added
   AdaFruit DS18B20 waterproof, temperature sensor added
:return:
"""

import os
# import sys
# import time
from collections import OrderedDict
from signal import signal, SIGINT
from sys import exit
from time import sleep

import adafruit_ads1x15.ads1115 as ADS
import adafruit_bme280
import board
import busio
import digitalio
from DFRobot_ADS1115 import ADS1115
from DFRobot_EC import DFRobot_EC
from DFRobot_PH import DFRobot_PH
from adafruit_ads1x15.analog_in import AnalogIn

from PythonCode.python_mysql_dbconfig import *

ads1115 = ADS1115()
ph = DFRobot_PH()
ec = DFRobot_EC()
# initialize all objects

# Load Raspberry Pi Drivers for AdaFruit 1-Wire Temperature Sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Setup objects for ADS1115 board
i2c = busio.I2C(board.SCL, board.SDA)

ads = ADS.ADS1115(i2c)

# Create library object using SPI port for BME280
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, cs)

sleep_timer = 200  # sensors are read every 10 minutes


def check_for_only_one_reference_temperature():
    """
    Verify that ony one temperature sensor is used for reference be the other sensors
    NOT USED
    :return:
    """
    ref_check = 0

    for key, value in list(sensors.items()):
        if (value["is_connected"]) is True:
            if value["sensor_type"] == "1_wire_temp":
                if value["is_ref"] is True:
                    ref_check += 1
                else:
                    pass
            else:
                pass
        else:
            pass
        if ref_check > 1:
            os.system('clear')
            print("\n\n                     !!!! WARNING !!!!\n\n"
                  "You can only have one Primary Temperature sensor, Please set the\n"
                  "Temperature sensor that is in the liquid you are testing to True\n"
                  "and the other to False\n\n                     !!!! WARNING !!!!\n\n")
            sys.exit()  # Stop program
        else:
            pass
    return


# not used
# def remove_unused_sensors():
#     """
#     Used to remove unused sensors from the database
#     :return:
#     """
#     conn, curs = open_database_connection()
#
#     for key, value in list(sensors.items()):
#         if value["is_connected"] is False:
#             try:
#                 curs.execute("ALTER TABLE sensors DROP {};"
#                              .format(value["name"]))
#             except mariadb.Error as error:
#                 print("Error: {}".format(error))
#                 pass
#
#     close_database_connection(conn, curs)
#
#     return


# Read in the data from the Submerged Temp Sensor file

def read_1_wire_temp_raw(temp_num):
    """
    read the un-calculated value from the submerged temperature sensor
    :param temp_num:
    :return:
    """
    f = open(sensors[temp_num]["ds18b20_file"], 'r')
    lines = f.readlines()
    f.close()

    return lines


# Process the Temp Sensor file for errors and convert to degrees C

def read_1_wire_temp(temp_num):
    """
    Read the calculated value from the temperature sensor
    :param temp_num:
    :return:
    """
    lines = read_1_wire_temp_raw(temp_num)

    while lines[0].strip()[-3:] != 'YES':
        sleep(0.2)
        lines = read_1_wire_temp_raw(temp_num)
    equals_pos = lines[1].find('t=')

    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        # Use line below for Celsius
        temp_curr = float(temp_string) / 1000.0
        # Uncomment line below for Fahrenheit
        # temp_curr = ((float(temp_string) / 1000.0) * (9.0 / 5.0)) + 32

        return temp_curr


def log_sensor_readings(all_curr_readings):
    """
    read and log each sensor if it is set to True in the sensors list
    :param all_curr_readings:
    :return:
    """
    # Create a timestamp and store all readings on the MySQL database

    db_config = read_db_config()
    conn = MySQLConnection(**db_config)
    curs = conn.cursor()
    if conn.is_connected():
        print('Connection established.')
    else:
        print('Connection failed.')

        curs = conn.cursor()

    try:
        # get latest timestamp value
        curs.execute("SELECT MAX(reading_time) FROM SensorData")
    except conn.Error as error:
        print("Error: {}".format(error))
        pass
    last_timestamp = curs.fetchone()
    last_timestamp = last_timestamp[0].strftime('%Y-%m-%d %H:%M:%S')

    for readings in all_curr_readings:
        try:
            curs.execute("INSERT INTO SensorData (sensor, location, dblvalueraw, reading_time) "
                         "values ('{}', '{}', {}, '{}' )".format(readings[0], readings[2], readings[1], last_timestamp))
            # debug     print ("row values for insert".format(readings[0], readings[1], readings[2], last_timestamp))
            # insert into SensorData (sensor, location, dblvalueraw, reading_time)
            #       values ('rpo', 'right closet', 28.97, '2020-07-24 12:00:00' )

            conn.commit()

        except Error as e:
            print('Error:', e)

    curs.close()
    conn.close()
    print('log_sensor_readings - Connection Closed.')


def read_sensors(all_curr_readings, location):
    """
    Read data from all sensors
    :param all_curr_readings:
    :param location:
    """
    # Get the readings from any 1-Wire temperature sensors. This sensor is submerged in the tank

    for key, value in sensors.items():
        if value["is_connected"] is True:
            if value["sensor_type"] == "1_wire_temp":
                try:
                    sensor_reading = (round(float(read_1_wire_temp(key)),
                                            value["accuracy"]))
                except:
                    sensor_reading = 0

                all_curr_readings.append([value["name"], sensor_reading, location])

                if value["is_ref"] is True:
                    ref_temp = sensor_reading

            # Get the readings from any Gravity pH sensors
            # ADS channel P0

            if value["sensor_type"] == "gravity_ph":
                # Create single-ended input on channel 0
                try:
                    chan = AnalogIn(ads, ADS.P0)

                    # Create differential input between channel 0 and 1
                    # chan = AnalogIn(ads, ADS.P0, ADS.P1)
                    # debug
                    #                print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
                    all_curr_readings.append([value["name"], chan.value, location])
                except(chan == []):
                    if value["name"] == "ph":
                        sensor_reading = 0.0

            # Get the readings from any Gravity Electrical Conductivity sensors
            # ADS channel P1

            if value["sensor_type"] == "gravity_ec":
                # Create single-ended input on channel 0
                try:
                    chan = AnalogIn(ads, ADS.P1)

                    # Create differential input between channel 0 and 1
                    # chan = AnalogIn(ads, ADS.P0, ADS.P1)
                    # debug
                    #                print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
                    all_curr_readings.append([value["name"], chan.value, location])
                except (chan == []):
                    if value["name"] == "ec":
                        sensor_reading = 0.0

            # Get the readings from any Gravity ORP sensors
            # ADS channel P2. Measured in milli-volts

            if value["sensor_type"] == "gravity_orp":
                # Create single-ended input on channel 0
                try:
                    chan = AnalogIn(ads, ADS.P2)

                    # Create differential input between channel 0 and 1
                    # chan = AnalogIn(ads, ADS.P0, ADS.P1)
                    # debug
                    #                print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
                    all_curr_readings.append([value["name"], chan.value, location])

                except (chan == []):
                    if value["name"] == "orp":
                        sensor_reading = 0.0
                    else:
                        pass


def handler(signal_received, frame):
    """
    Handle keyboard interrupts
    :param signal_received:
    :param frame:
    """
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)


# Configuration Settings

# Define the sensor names, what sensors are connected, the sensor type, the
# Gravity I2C addresses and define a primary temperature sensor.
# In the case shown below that would be either "temp_1" or "atlas_sensor_1".
# This is the sensor that is in the liquid that is being sampled and is used
# as a reference by the other sensors. If there are no temperature sensors
# connected a default value of 25C will be applied.
#
# Note: The temperature sensors cannot both be set to "is_ref: True", also
# "temp_1" must always be a DS18B20 type sensor and "temp_1_sub" must
# always be type temperature sensor so that the reference
# temperature is always set before the other Gravity sensors are read.
# AdaFruit ADS1115 ADC+PGA controller used as the i2c interface for the pH, ORP, EC sensors
# This code was updated to support multiple hydroponic tanks
# AdaFruit BME288 temperature, pressure, humidity sensor added. This sensor uses SPI
# AdaFruit, Optomax digital liquid level gauges added. These gauges are connected directly through GPIO


sensors = OrderedDict([
    ("temp_1_sub", {  # DS18B20 AdaFruit Submerged Temperature Sensor
        "sensor_type": "1_wire_temp",
        "name": "subm_temp",
        "is_connected": True,
        "is_ref": True,
        "ds18b20_file":
        # Hard coded for this device. This will change if another 1-wire device is added
            "/sys/bus/w1/devices/28-1b202933bcff/w1_slave",
        "accuracy": 1}),

    ("bme288_sensor_1", {  # BME288 Temp/Humidity/Pressure Sensor
        "sensor_type": "bme288_spi_temp_humid_press",
        "name": "bme288_SPI",
        "is_connected": True,
        "is_ref": True,
        "i2c": 0,
        "accuracy": 1}),

    ("gravity_sensor_2", {  # ORP Gravity Sensor
        "sensor_type": "gravity_orp",
        "name": "orp",
        "is_connected": True,
        "is_ref": False,
        "i2c": 48,
        "accuracy": 2}),

    ("gravity_sensor_3", {  # pH Gravity Sensor
        "sensor_type": "gravity_ph",
        "name": "ph",
        "is_connected": True,
        "is_ref": False,
        "i2c": 48,
        "accuracy": 0}),

    ("gravity_sensor_4", {  # Gravity EC Sensor
        "sensor_type": "gravity_ec",
        "name": "ec",
        "is_connected": True,
        "is_ref": False,
        "i2c": 48,
        "accuracy": 0,
        "ppm_multiplier": 0.67}),  # Convert EC to PPM

    ("optomax_sensor_1", {  # Optomax Digital Liquid Sensor
        "sensor_type": "optomax_liquid_level",
        "name": "liquid_lev",
        "is_connected": True,
        "is_ref": False,
        "i2c": 0,
        "accuracy": 0})])

# Sets the gain and input voltage range for the ph and ec sensors.
# example: ads1115.setGain(ADS1115_REG_CONFIG_PGA_6_144V)
ADS1115_REG_CONFIG_PGA_6_144V = 0x00 # 6.144V range = Gain 2/3
ADS1115_REG_CONFIG_PGA_4_096V = 0x02 # 4.096V range = Gain 1
ADS1115_REG_CONFIG_PGA_2_048V = 0x04 # 2.048V range = Gain 2 (default)
ADS1115_REG_CONFIG_PGA_1_024V = 0x06 # 1.024V range = Gain 4
ADS1115_REG_CONFIG_PGA_0_512V = 0x08 # 0.512V range = Gain 8
ADS1115_REG_CONFIG_PGA_0_256V = 0x0A # 0.256V range = Gain 16


def main():
    """
    read data from all sensors and write to to the mysql database
    """
    # change this to match the location's pressure (hPa) at sea level
    bme280.sea_level_pressure = 1013.25
    # initialize all objects
    #    init()
    while True:
        signal(SIGINT, handler)
        print('Running. Press CTRL-C to exit.')

        #   insert data from right closet into MySQL
        sensor_data_rows_right = [('temperature', 'right closet', bme280.temperature, ''),
                                  ('humidity', 'right Closet', bme280.humidity, ''),
                                  ('pressure', 'right closet', bme280.pressure, '')]
        # print (SensorDataRowsRight)
        #   query = "INSERT INTO SensorData(sensor, location, dblvalue_raw, value2) " \
        #           "VALUES(%s, %s, %d, %s)"

        insert_sensordatarows(sensor_data_rows_right)

        #   insert data from left closet into MySQL
        sensor_data_rows_left = [('temperature', 'left closet', bme280.temperature, ''),
                                 ('humidity', 'left closet', bme280.humidity, ''),
                                 ('pressure', 'left closet', bme280.pressure, '')]

        insert_sensordatarows(sensor_data_rows_left)

        # Read sensors for 2 locations connected to the ADS1115. Gravity sensors . 6 sensors attached
        all_curr_readings_right = []
        all_curr_readings_left = []
        read_sensors(all_curr_readings_right, "right closet")
        #   update the database will all sensor readings
        log_sensor_readings(all_curr_readings_right)

        # read_sensors(all_curr_readings_left)
        #   update the database will all sensor readings
        read_sensors(all_curr_readings_left, "left closet")
        log_sensor_readings(all_curr_readings_left)

        time.sleep(sleep_timer)  # sleep for 10 minutes


if __name__ == '__main__':
    main()
