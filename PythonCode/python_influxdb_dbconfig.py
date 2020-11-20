#!/usr/bin/env python3
"""
 11/17/20 changed code to use influxdb instead of mysql
 #   API key for Influxdb
# curl -H "Authorization: Bearer eyJrIjoiN2M2UkVJcmJrR3IwcENKbEt3VkE3cEZjS0NjUkZjS2IiLCJuIjoicGloeWRyb3AiLCJpZCI6MX0=" http://localhost:3000/api/dashboards/home
# insert example for Influxdb: insert SensorData,sensor=sensor,location=location sensor="rpo",location="left",value=88.88
# bucket = database = HydroSensorData
# table = measure = SensorData
# key value pairs = sensor, location
# field value pairs = value
# timestamp is included with every point = row
""" 

from configparser import ConfigParser
from influxdb_client import WritePrecision, InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

def read_db_config(filename='../pihydropdata.ini', section='influxdb'):
    """ Read database configuration file and return a dictionary object
    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """
    # create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))

    return db

#   Insert a single row
def insert_sensordatarow(sensor, location, dblvalueraw, value2):
    """
    Insert statment for sensor row data - One row
    :param sensor:
    :param location:
    :param dblvalue_raw:
    :param value2:
    """
#    query = "INSERT INTO SensorData(sensor, location, dblvalueraw, value2) " \
#            "VALUES(%s, %s, %d, %s)"
#    args = (sensor, location, dblvalue_raw, value2)

    try:
            # connect to influxdb and insert a point = row
            db_config = read_db_config()
            client = influxdb_client.InfluxDBClient(
            url=url,
            token=token,
            org=org
            )
    if client is None:
        print('Connection failed.')
    else:
        print('Connection established.')

    write_api = client.write_api(write_options=SYNCHRONOUS)
# write a point or row to influxdb
    p = influxdb_client.Point("SendorData").tag("location", location).tag("sensor", sensor).field("value", dblvalueraw).time(datetime.now(), WritePrecision.MS)
    write_api.write(bucket=bucket, org=org, record=p)

    except client is None:
        print("Connection Failed with error: " StandardError)

    finally:
        """
        Close client
        """
        client.__del__()

#   Insert multiple rows for all sensors
def insert_sensordatarows(rows: object) -> object:
    """
    Insert statment for sensor row data - One row
    :param sensor:
    :param location:
    :param dblvalue_raw:
    :param value2:
    """
#    query = "INSERT INTO SensorData(sensor, location, dblvalueraw, value2) " \
#            "VALUES(%s, %s, %d, %s)"
#    args = (sensor, location, dblvalue_raw, value2)

    try:
            # connect to influxdb and insert a point = row
            db_config = read_db_config()
            client = influxdb_client.InfluxDBClient(
            url=url,
            token=token,
            org=org
            )
    if client is None:
        print('Connection failed.')
    else:
        print('Connection established.')

    write_api = client.write_api(write_options=SYNCHRONOUS)
# write a point or row to influxdb
    p = influxdb_client.Point("SendorData").tag("location", location).tag("sensor", sensor).field("value", dblvalueraw).time(datetime.now(), WritePrecision.MS)
    write_api.write(bucket=bucket, org=org, record=p)

    except client is None:
        print("Connection Failed with error: " StandardError)

    finally:
        """
        Close client
        """
        client.__del__()


def update_sensordatarows(id, sensor, location, dblvalueraw, value2):
    """
    update for multiple rows
    :param id:
    :param sensor:
    :param location:
    :param dblvalue_raw:
    :param value2:
    """
    # read database configuration
    db_config = read_db_config()

    # prepare query and data
    query = """ UPDATE SensorData
                SET location = %s
                WHERE id = %s """

    data = (location, id)

    try:
        conn = MySQLConnection(**db_config)

        # update location
        cursor = conn.cursor()
        cursor.execute(query, data)

        # accept the changes
        conn.commit()

    except Error as error:
        print(error)

    finally:
        cursor.close()
        conn.close()
        print('update_sensordatarows - Connection Closed.')
