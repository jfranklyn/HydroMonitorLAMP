from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import *

from signal import signal, SIGINT
from sys import exit

import time
import board
import busio
import adafruit_bme280

# Create library object using Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

sleep_timer = 600 # 10 minutes 

def handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)
 
def main():
# change this to match the location's pressure (hPa) at sea level
    bme280.sea_level_pressure = 1013.25
    
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
        #print (SensorDataRowsRight)
     #   query = "INSERT INTO SensorData(sensor, location, dblvalue_raw, value2) " \
     #           "VALUES(%s, %s, %d, %s)"
         
        insert_SensorDataRows(SensorDataRowsRight)
    #   insert data from left closet into MySQL 
        SensorDataRowsLeft = [('temperature', 'left closet', bme280.temperature, ''),
                 ('humidity', 'left closet', bme280.humidity, '' ),
                 ('pressure', 'left closet', bme280.pressure, ''),
                 ('ph', 'left closet', 0.0, ''),
                 ('rpo', 'left closet', 0.0, ''),
                 ('ec', 'left closet', 0.0, '')]
        
        insert_SensorDataRows(SensorDataRowsLeft)

        time.sleep(sleep_timer) # sleep for 10 minutes

if __name__ == '__main__':
    main()            
