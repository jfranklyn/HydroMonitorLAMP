################################################################################################
#   John Franklyn 06/18/2020
#   BME280 python 3.7 code
#   output written to mysql database pihydropdata
#   changed code to use SPI instead of i2c for BME280
#   ph, rpo, ec, water level sensors will be added
#################################################################################################
from PythonCode.python_mysql_dbconfig import *
from signal import signal, SIGINT
from sys import exit

import time
import board
import busio
import digitalio
import adafruit_bme280
import adafruit_ads1x15.ads1115 as ADS
import io
import os
import sys
import fcntl
#import mysql.connector as mariadb
from time import sleep
from collections import OrderedDict

# initialize all objects
def init():
# Load Raspberry Pi Drivers for AdaFruit 1-Wire Temperature Sensor
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

# Setup objects for ADS1115 board
    i2c = busio.I2C(board.SCL, board.SDA)

    ads = ADS.ADS1115(i2c)

# Create library object using SPI port
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.D5)
    bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, cs)

    sleep_timer = 600  # 10 minutes

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
        "name": "ds18b20_temp",
        "is_connected": True,
        "is_ref": False,
        "ds18b20_file":
            "/sys/bus/w1/devices/28-01157127dfff/w1_slave",
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

def check_for_only_one_reference_temperature():
    ref_check = 0

    for key, value in list(sensors.items()):
        if (value["is_connected"]) is True:
            if value["sensor_type"] == "1_wire_temp":
                if value["is_ref"] is True:
                    ref_check += 1
            if value["sensor_type"] == "atlas_temp":
                if value["is_ref"] is True:
                    ref_check += 1
    if ref_check > 1:
        os.system('clear')
        print("\n\n                     !!!! WARNING !!!!\n\n"
              "You can only have one Primary Temperature sensor, Please set the\n"
              "Temperature sensor that is in the liquid you are testing to True\n"
              "and the other to False\n\n                     !!!! WARNING !!!!\n\n")
        sys.exit()  # Stop program
    return

def remove_unused_sensors():
    conn, curs = open_database_connection()

    for key, value in list(sensors.items()):
        if value["is_connected"] is False:
            try:
                curs.execute("ALTER TABLE sensors DROP {};"
                             .format(value["name"]))
            except mariadb.Error as error:
                print("Error: {}".format(error))
                pass

    close_database_connection(conn, curs)

    return


# Read in the data from the Submerged Temp Sensor file

def read_1_wire_temp_raw(temp_num):
    f = open(sensors[temp_num]["ds18b20_file"], 'r')
    lines = f.readlines()
    f.close()

    return lines


# Process the Temp Sensor file for errors and convert to degrees C

def read_1_wire_temp(temp_num):
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


# read and log each sensor if it is set to True in the sensors list

def log_sensor_readings(all_curr_readings):
    # Create a timestamp and store all readings on the MySQL database

    conn, curs = open_database_connection()
    try:
        curs.execute("INSERT INTO sensors (timestamp) VALUES(now());")
        curs.execute("SELECT MAX(timestamp) FROM sensors")
    except mariadb.Error as error:
        print("Error: {}".format(error))
        pass
    last_timestamp = curs.fetchone()
    last_timestamp = last_timestamp[0].strftime('%Y-%m-%d %H:%M:%S')

    for readings in all_curr_readings:
        try:
            curs.execute(("UPDATE sensors SET {} = {} WHERE timestamp = '{}'")
                         .format(readings[0], readings[1], last_timestamp))
        except mariadb.Error as error:
            print("Error: {}".format(error))
            pass

    close_database_connection(conn, curs)

    return


def read_sensors():
    all_curr_readings = []
    ref_temp = 25

    # Get the readings from any 1-Wire temperature sensors. This sensor is submerged in the tank

    for key, value in sensors.items():
        if value["is_connected"] is True:
            if value["sensor_type"] == "1_wire_temp":
                try:
                    sensor_reading = (round(float(read_1_wire_temp(key)),
                                            value["accuracy"]))
                except:
                    sensor_reading = 50

                all_curr_readings.append([value["name"], sensor_reading])

                if value["is_ref"] is True:
                    ref_temp = sensor_reading

            # Get the readings from any Gravity temperature sensors

            if value["sensor_type"] == "atlas_scientific_temp":
                device = atlas_i2c(value["i2c"])
                try:
                    sensor_reading = round(float(device.query("R")),
                                           value["accuracy"])
                except:
                    sensor_reading = 50

                all_curr_readings.append([value["name"], sensor_reading])

                if value["is_ref"] is True:
                    ref_temp = sensor_reading

            # Get the readings from any Gravity Elec Conductivity sensors

            if value["sensor_type"] == "gravity_ec":
                device = atlas_i2c(value["i2c"])
                # Set reference temperature value on the sensor
                device.query("T," + str(ref_temp))
                try:
                    sensor_reading = (round(((float(device.query("R"))) *
                                             value["ppm_multiplier"]), value["accuracy"]))
                except:
                    sensor_reading = 10000

                all_curr_readings.append([value["name"], sensor_reading])

            # Get the readings from any other Gravity sensors

            if value["sensor_type"] == "atlas_scientific":
                device = atlas_i2c(value["i2c"])
                # Set reference temperature value on the sensor
                device.query("T," + str(ref_temp))
                try:
                    sensor_reading = round(float(device.query("R")),
                                           value["accuracy"])
                except:
                    if value["name"] == "ph":
                        sensor_reading = 2
                    elif value["name"] == "orp":
                        sensor_reading = 1000

                all_curr_readings.append([value["name"], sensor_reading])

    log_sensor_readings(all_curr_readings)

    return

def handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)


def main():
    # change this to match the location's pressure (hPa) at sea level
    bme280.sea_level_pressure = 1013.25
# initialize all objects
    init()
    while True:
        signal(SIGINT, handler)
        print('Running. Press CTRL-C to exit.')

        #   insert data from right closet into MySQL
        SensorDataRowsRight = [('temperature', 'right closet', bme280.temperature, ''),
                               ('humidity', 'right Closet', bme280.humidity, ''),
                               ('pressure', 'right closet', bme280.pressure, ''),
                               ('ph', 'right closet', 0.0, ''),
                               ('rpo', 'right closet', 0.0, ''),
                               ('ec', 'right closet', 0.0, '')]
        # print (SensorDataRowsRight)
        #   query = "INSERT INTO SensorData(sensor, location, dblvalue_raw, value2) " \
        #           "VALUES(%s, %s, %d, %s)"

        insert_SensorDataRows(SensorDataRowsRight)

        #   insert data from left closet into MySQL
        SensorDataRowsLeft = [('temperature', 'left closet', bme280.temperature, ''),
                              ('humidity', 'left closet', bme280.humidity, ''),
                              ('pressure', 'left closet', bme280.pressure, ''),
                              ('ph', 'left closet', 0.0, ''),
                              ('rpo', 'left closet', 0.0, ''),
                              ('ec', 'left closet', 0.0, '')]

        insert_SensorDataRows(SensorDataRowsLeft)

# Read all sensors connected to the ADS1115. Gravity sensors
        read_sensors()

        time.sleep(sleep_timer)  # sleep for 10 minutes

if __name__ == '__main__':
    main()
