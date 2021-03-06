#!/usr/bin/env python3
"""
   John Franklyn 06/18/2020
   BME280 python 3.7 code
   output written to mysql database SensorData
   changed code to use SPI instead of i2c for BME280
   Gravity ph, rpo, ec, water level sensors added
   AdaFruit DS18B20 waterproof, temperature sensor added
   Optomax digital liquid sensor added
   Adding logic for multiple ads1115, bme280 boards
   Added logging to mysql and file for errors
:return:
"""

import os
import sys
import time
import glob
import logging
from collections import OrderedDict
from signal import signal, SIGINT

import adafruit_ads1x15.ads1115 as ADS
import adafruit_bme280
import board
import busio
import digitalio
import RPi.GPIO as GPIO
from adafruit_ads1x15.analog_in import AnalogIn

from DFRobot_ADS1115 import ADS1115
from DFRobot_EC import DFRobot_EC
from DFRobot_PH import DFRobot_PH

# Added mysql connection components into main code for logging
from configparser import ConfigParser
from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import *

# Configures pin numbering to Board reference
#GPIO.setmode(GPIO.BOARD)

# Logger class definition
class LogDBHandler(logging.Handler):
    '''
    Customized logging handler that puts logs to the database.
    modified for mysql - 10.3.25-MariaDB
    '''
    def __init__(self, sql_conn, sql_cursor, db_tbl_log):
        logging.Handler.__init__(self)
        self.sql_cursor = sql_cursor
        self.sql_conn = sql_conn
        self.db_tbl_log = db_tbl_log

    def emit(self, record):
        # Set current time
        tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        # Clear the log message so it can be put to db via sql (escape quotes)
        self.log_msg = record.msg
        self.log_msg = self.log_msg.strip()
        self.log_msg = self.log_msg.replace('\'', '\'\'')
        # Make the SQL insert
        sql = 'INSERT INTO ' + self.db_tbl_log + ' (log_level, ' + \
            'log_levelname, log, created_at, created_by) ' + \
            'VALUES (' + \
            ''   + str(record.levelno) + ', ' + \
            '\'' + str(record.levelname) + '\', ' + \
            '\'' + str(self.log_msg) + '\', ' + \
            '\''+tm + '\', ' +  '\'' + str(record.name) + '\');'
        print(sql)
        try:
            self.sql_cursor.execute(sql)
            self.sql_conn.commit()
        # If error - print it out on screen. Since DB is not working - there's
        # no point making a log about it to the database :)
        except Error as e:
            print ('sql')
            print ('CRITICAL DB ERROR! Logging to database not possible!'    )

# initialize the log settings
#logging.basicConfig(filename='HydroMonitorApp'+time.time_ns()+'.log',level=logging.ERROR)
log_file_path = 'HydroMonitorApp'+str(time.time_ns())+'.log'
log_error_level     = 'DEBUG'       # LOG error level (file)
log_to_db = True                    # LOG to database?
db_tbl_log = 'Logger'
# Setup error logging for log to database and log to file
if (log_to_db):
# Make the connection to database for the logger
    try:
        dbconfig = read_db_config()
        log_conn = MySQLConnection(**dbconfig)
        log_cursor = log_conn.cursor()
        logdb = LogDBHandler(log_conn, log_cursor, db_tbl_log)

    except Error as e:
        print(e)
    else:
        print ('MySQL Logger Connection Successful')
    logging.getLogger('').addHandler(logdb)
    
# Register MY_LOGGER
log = logging.getLogger('HydroMonitorApp Logger')
log.setLevel(log_error_level)
logging.basicConfig(filename=log_file_path)

# initialize all objects. 
ads1115_l = ADS1115()
ads1115_r = ADS1115()

ph = DFRobot_PH()
ec = DFRobot_EC()
# Set GPIO pin to input and activate pull_down walter level sensor to reference pin to ground
gpio_pin = 15 
GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Load Raspberry Pi Drivers for AdaFruit 1-Wire Temperature Sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Setup objects for ADS1115 board
i2c = busio.I2C(board.SCL, board.SDA)

# Each ads1115 must have a unique address
try:
    ads_l = ADS.ADS1115(i2c)
    ads1115_l.setAddr_ADS1115(0x48)
except RuntimeError as e:
    log.error('ADS1115(0x48) Not Found'+str(e))
    exit(0)

try:
    ads_r = ADS.ADS1115(i2c)
    ads1115_r.setAddr_ADS1115(0x49)
except RuntimeError as e:
    log.error('ADS1115(0x49) Not Found'+str(e))
    exit(0)

# Create library object using SPI port for BME280
# Add logic for right and left IO boards. Exit program if the boards don't exist
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Each BME280 has a unique GPIO input pin    
try:
    cs_l = digitalio.DigitalInOut(board.D12) # Pin BCM12
    bme280_l = adafruit_bme280.Adafruit_BME280_SPI(spi, cs_l)
except RuntimeError as e:
    log.error('BME280 Left Not Found'+str(e))
    exit(0)

try:
    cs_r = digitalio.DigitalInOut(board.D7) # Pin BCM7
    bme280_r = adafruit_bme280.Adafruit_BME280_SPI(spi, cs_r)
except RuntimeError as e:
    log.error('BME280 Right Not Found'+str(e))
    exit(0)


sleep_timer = 600  # sensors are read every 30 minutes

"""
Verify that there is at least one ds18b20, temperature sensor configured
1 wire sensors should be defined in this folder: /sys/bus/w1/devices
:return: count of sensors found
"""
def check_for_one_wire_temperature_sensors():
    cnt_1wiredevs = 0
    #path name variable .
    myPath="/sys/bus/w1/devices/28-*"
    cnt_1wiredevs = glob.glob(myPath)

    return len(cnt_1wiredevs)

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
    try:
        lines = read_1_wire_temp_raw(temp_num)

        while lines[0].strip()[-3:] != 'YES':
            # noinspection PyUnresolvedReferences
            time.sleep(0.2)
            lines = read_1_wire_temp_raw(temp_num)
        equals_pos = lines[1].find('t=')

        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            # Use line below for Celsius
            #temp_curr = float(temp_string) / 1000.0
            # Uncomment line below for Fahrenheit
            temp_curr = ((float(temp_string) / 1000.0) * (9.0 / 5.0)) + 32
            
    except IndexError:
        log.error('read_1_wire_temp: No 1 Wire sensors found')
        temp_curr = 72 # set this to a default value
    return temp_curr

def log_sensor_readings(all_curr_readings):
    """
    read and log each sensor if it is set to True in the sensors list
    :param all_curr_readings:
    :return:
    """
    # Create a timestamp and store all readings on the MySQL database

    try:
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)
        curs = conn.cursor()
    except conn.Error as error:
        log.error("Error: {}".format(error))
    else:
        print('Connection established.')

        curs = conn.cursor()

    try:
        # get latest timestamp value
        curs.execute("SELECT MAX(reading_time) FROM SensorData")
    except conn.Error as error:
        log.error("Error: {}".format(error))
    
    last_timestamp = curs.fetchone()
    last_timestamp = last_timestamp[0].strftime('%Y-%m-%d %H:%M:%S')

    for readings in all_curr_readings:
        try:
            curs.execute("INSERT INTO SensorData (sensor, location, valueraw, reading_time) "
                         "values ('{}', '{}', {}, '{}' )".format(readings[0], readings[2], readings[1], last_timestamp))
            # debug     print ("row values for insert".format(readings[0], readings[1], readings[2], last_timestamp))
            # insert into SensorData (sensor, location, valueraw, notes, reading_time)
            #       values ('rpo', 'right closet', 28.97, 'A Note', '2020-07-24 12:00:00' )

            conn.commit()

        except conn.Error as error:
            log.error("Error: {}".format(error))

    curs.close()
    conn.close()
    log.setLevel('INFO')
    log.error('log_sensor_readings - Successful. Connection Closed.')

def read_sensors(all_curr_readings, location, ADS1115):
    """
    Generic version to work with any number of locations
    Read data from all sensors
    :param all_curr_readings: dictionary to hold all readings
    :param location: supports any number of unique hydro tanks
    :param ADS1115: AdaFruit ads1115 16 bit. Supports any number of sensors
    """
    # Get the readings from any 1-Wire temperature sensors. This sensor is submerged in the tank
    
    for key, value in sensors.items():
        if value["is_connected"] is True:
            if value["sensor_type"] == "1_wire_temp":
                try:
                    sensor_reading = (round(float(read_1_wire_temp(key)),
                                            value["accuracy"]))
                except (sensor_reading == 0):
                    sensor_reading = 0
                    ref_temp = 25

                all_curr_readings.append([value["name"], sensor_reading, location])

                if value["is_ref"] is True:
                    ref_temp = sensor_reading

            # Get the readings from any Gravity pH sensors
            # ADS channel P0

            if value["sensor_type"] == "gravity_ph":
                # Create single-ended input on channel 0
                try:
                    # chan = AnalogIn(ads, ADS.P0)
                    # set the gain value and then read the sensor voltage
                    ads1115_r.setGain(ADS1115_REG_CONFIG_PGA_6_144V)
                    adc0 = ads1115_r.readVoltage(0)
                    # Create differential input between channel 0 and 1
                    # chan = AnalogIn(ads, ADS.P0, ADS.P1)
                    # debug
                    #                print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
                    # get ph compensated value based on submerged temperature value
                    ph_comp = ph.readPH(adc0['r'], ref_temp)
                    all_curr_readings.append([value["name"], ph_comp, location])

                except(ph_comp == 0):
                    sensor_reading = 0.0

            # Get the readings from any Gravity Electrical Conductivity sensors
            # ADS channel P1

            if value["sensor_type"] == "gravity_ec":
                # Create single-ended input on channel 0
                try:
                    # chan = AnalogIn(ads, ADS.P1)
                    ads1115_r.setGain(ADS1115_REG_CONFIG_PGA_6_144V)
                    adc1 = ads1115_r.readVoltage(1)
                    ec_comp = ec.readEC(adc1['r'], ref_temp)
                    all_curr_readings.append([value["name"], ec_comp, location])

                except (ec_comp == 0):
                    sensor_reading = 0.0

            # Get the readings from any Gravity ORP sensors
            # ADS channel P2. Measured in milli-volts

            if value["sensor_type"] == "gravity_orp":
                # Create single-ended input on channel 0
                try:
                    chan = AnalogIn(ads_r, ADS.P2)
                    # debug
                    #                print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
                    all_curr_readings.append([value["name"], chan.value, location])

                except (chan == []):
                    sensor_reading = 0.0

            # Get the readings from Optomax water level sensor

            if value["sensor_type"] == "optomax_digital_liquid_sensor":
                try:
                    if GPIO.input(gpio_pin) == 0:  
                        # debug
                        #   print("GPIO pin 12 is: ", GPIO.input(gpio_pin))
                        
                        all_curr_readings.append([value["name"], 0, location])
                    if GPIO.input(gpio_pin) == 1:
                        all_curr_readings.append([value["name"], 1, location])                        

                except (GPIO.UNKNOWN()):
                        log.error ("GPIO.UNKNOWN this should never happen")

 
def handler(signal_received, frame):
    """
    Handle keyboard interrupts
    :type signal_received: object
    :param signal_received:
    :param frame:
    """
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)

"""
Configuration Settings

Define the sensor names, what sensors are connected, the sensor type, the
Gravity I2C addresses and define a primary temperature sensor.
In the case shown below that would be either "temp_1" or "atlas_sensor_1".
This is the sensor that is in the liquid that is being sampled and is used
as a reference by the other sensors. If there are no temperature sensors
connected a default value of 25C will be applied.

Note: The temperature sensors cannot both be set to "is_ref: True", also
"temp_1" must always be a DS18B20 type sensor and "temp_1_sub" must
always be type temperature sensor so that the reference
Add this line to /boot/config.txt
    dtoverlay=w1-gpio,gpiopin=4,pullup=on
Add this line to /etc/modules
    w1-therm strong_pullup=1
temperature is always set before the other Gravity sensors are read.

AdaFruit ADS1115 ADC+PGA controller used as the i2c interface for the pH, ORP, EC sensors
This code was updated to support multiple hydroponic tanks
AdaFruit BME288 temperature, pressure, humidity sensor added. This sensor uses SPI
AdaFruit, Optomax digital liquid level gauges added. These gauges are connected directly through GPIO
Added dictionary entry for 2nd temperature sensor
"""

sensors = OrderedDict([
    ("temp_1_sub", {  # DS18B20 AdaFruit Submerged Temperature Sensor
        "sensor_type": "1_wire_temp",
        "name": "subm_temp",
        "is_connected": True,
        "is_ref": True,
        "ds18b20_file":
        # Hard coded for this device. This will change if another 1-wire device is added
            "/sys/bus/w1/devices/28-00000bdeccb7/w1_slave",
        "accuracy": 1}),

    ("temp_2_sub", {  # DS18B20 AdaFruit Submerged Temperature Sensor
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

    ("optomax_level_sensor", {  # Optomax Digital Liquid Sensor
        "sensor_type": "optomax_digital_liquid_sensor",
        "name": "optomax_SPI",
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

"""
read data from all sensors and write to to the mysql database
"""
def main():
    
    # change this to match the location's pressure (hPa) at sea level
    bme280_l.sea_level_pressure = 1013.25
    bme280_r.sea_level_pressure = 1013.25
    
    while True:
        signal(SIGINT, handler)
        print('Running. Press CTRL-C to exit.')

        #   insert data from right closet into MySQL
        sensor_data_rows_right = [('temperature', 'right_closet', bme280_r.temperature, ''),
                                  ('humidity', 'right_closet', bme280_r.humidity, ''),
                                  ('pressure', 'right_closet', bme280_r.pressure, '')]
        # debug
        # print (SensorDataRowsRight)
        #   query = "INSERT INTO SensorData(sensor, location, valueraw, notes) " \
        #           "VALUES(%s, %s, %d, %s)"

        insert_sensordatarows(sensor_data_rows_right)

        #   insert data from left closet into MySQL
        sensor_data_rows_left = [('temperature', 'left_closet', bme280_l.temperature, ''),
                                 ('humidity', 'left_closet', bme280_l.humidity, ''),
                                 ('pressure', 'left_closet', bme280_l.pressure, '')]

        insert_sensordatarows(sensor_data_rows_left)

        # Read sensors for 2 locations connected to the ADS1115. Gravity sensors . 6 sensors attached
        all_curr_readings = []        
        # Verify that the 1 wire temperature probes have been configured
        Count1WireDevices = check_for_one_wire_temperature_sensors()
        if (Count1WireDevices == 0):
            log.error('No ds18b20 1 wire devices found')
            sys.exit(0)
        else:
            pass
            
        # read_sensors_right(all_curr_readings_right). 
        read_sensors(all_curr_readings, 'right_closet', ads1115_r)

        #   update the database will all sensor readings
        log_sensor_readings(all_curr_readings)

        # initalize the list
        all_curr_readings = []

        # read_sensors(all_curr_readings_left)
        #   update the database will all sensor readings
        read_sensors(all_curr_readings, 'left_closet', ads1115_l)
        # read_sensors_left(all_curr_readings_left)
        log_sensor_readings(all_curr_readings)

        time.sleep(sleep_timer)  # sleep for 30 minutes

  
if __name__ == '__main__':
    main()

# Close the logging connection
    log_cursor.close()
    log_conn.close()    

