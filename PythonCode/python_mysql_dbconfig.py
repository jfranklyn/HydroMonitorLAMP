#!/usr/bin/env python3
from mysql.connector import MySQLConnection, Error
from configparser import ConfigParser

def read_db_config(filename='pihydropdata.ini', section='mysql'):
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

def query_with_fetchone():
    try:
        dbconfig = read_db_config()
        conn = MySQLConnection(**dbconfig)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SensorData")

        row = cursor.fetchone()

        while row is not None:
            print(row)
            row = cursor.fetchone()

    except Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()

def query_with_fetchall():
    try:
        dbconfig = read_db_config()
        conn = MySQLConnection(**dbconfig)
        cursor = conn.cursor()
        cursor.execute("SELECT sensor, location, dblvalue_raw, value2, reading_time FROM SensorData")
        rows = cursor.fetchall()

        print('Total Row(s):', cursor.rowcount)
        for row in rows:
            print(row)

    except Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()

# itierator to fetch a small number of rows
def iter_row(cursor, size=10):
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

#   use the iterator to fetch the rows in chunks
def query_with_fetchmany():
    try:
        dbconfig = read_db_config()
        conn = MySQLConnection(**dbconfig)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM SensorData")

        for row in iter_row(cursor, 10):
            print(row)

    except Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()

#   Insert a single row
def insert_SensorDataRow(sensor, location, dblvalue_raw, value2):
    query = "INSERT INTO SensorData(sensor, location, dblvalue_raw, value2) " \
            "VALUES(%s, %s, %d, %s)"
    args = (sensor, location, dblvalue_raw, value2)

    try:
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)

        cursor = conn.cursor()
        cursor.execute(query, args)

        if cursor.lastrowid:
            print('last insert id', cursor.lastrowid)
        else:
            print('last insert id not found')

        conn.commit()
    except Error as error:
        print(error)

    finally:
        cursor.close()
        conn.close()

#   Insert multiple rows for all sensors
def insert_SensorDataRows(rows):
    query = "INSERT INTO SensorData(sensor, location, dblvalue_raw, value2) " \
            "VALUES(%s, %s, %s, %s)"

    try:
        print('Connecting to MySQL database:pihydropdata')        
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)
        if conn.is_connected():
            print('Connection established.')
        else:
            print('Connection failed.')
            
        cursor = conn.cursor()
        cursor.executemany(query, rows)

        conn.commit()
    except Error as e:
        print('Error:', e)

    finally:
        cursor.close()
        conn.close()
        print('Connection Closed.')

def update_SensorDataRows(id, sensor, location, dblvalue_raw, value2):
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
