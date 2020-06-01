from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import read_db_config

import time
import board
import busio
import adafruit_bme280

# Create library object using Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

sleep_timer = 600 # 10 minutes

def connect():
    """ Connect to MySQL database pihydropdata"""
    db_config = read_db_config()
    conn = None
    try:
        print('Connecting to MySQL database:pihydropdata')
        conn = MySQLConnection(**db_config)

        if conn.is_connected():
            print('Connection established.')
        else:
            print('Connection failed.')

    except Error as error:
        print(error)

    finally:
        if conn is not None and conn.is_connected():
            conn.close()
            print('Connection closed.')

def main():
    books = [('Harry Potter And The Order Of The Phoenix', '9780439358071'),
             ('Gone with the Wind', '9780446675536'),
             ('Pride and Prejudice (Modern Library Classics)', '9780679783268')]
    insert_SensorDataRow(SensorData)


if __name__ == '__main__':
    main()            


# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25

while True:
    #print("\nTemperature: %0.1f C" % bme280.temperature)
    #print("Humidity: %0.1f %%" % bme280.humidity)
    #print("Pressure: %0.1f hPa" % bme280.pressure)
    #print("Altitude = %0.2f meters" % bme280.altitude)
    dblTemp = bme280.temperature
    dblHumidity = bme280.humidity
    dblPressure = bme280.pressure
    dblAltitude = bme280.altitude
    
    
    time.sleep(sleep_timer)
