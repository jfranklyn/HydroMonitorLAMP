#!/usr/bin/env python3
"""
list example
[('temperature', 'right closet', 26.6744140625, ''), ('humidity', 'right Closet', 60.60658228232342, ''), ('pressure', 'right closet', 1010.6666028051263, '')]

influxdb point example as a dictionary
write_api.write("my-bucket", "my-org", [{"measurement": "h2o_feet", "tags": {"location": "coyote_creek"}, "fields": {"water_level": 1}, "time": 1}])
"""

import time

import influxdb_client
from influxdb_client import WritePrecision, InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

SensorList = []
SensorList = ['temperature', 'right closet', 26.6744140625,
              'humidity', 'right Closet', 60.60658228232342,
              'pressure', 'right closet', 1010.6666028051263]

DictStr = ""
#DictStr = "[{"measurement": "HydroSensorData", "tags": {"location": "right_closet"}, {"sensor": "ph"}, "fields": {"value": 39.9876}, "time": time.time_ns()}]"
DictStr = "[{"+'"measurement"'+": " '"HydroSensorData"'+"}]"

"""
convert strings to a dictionary string to be used as an influxdb input point
inputs
    lstrow = list of values
    strmeasurement = measurement string
"""
def StringToDictString(lstrow, strmeasurement):
    DictStr = ""
    startStr = "[{"
    endStr = "}]"

    DictStr = startStr + '"measurement"'+": "+'"'+strmeasurement+'"'+"," '"tags"'+': {"'+'sensor" : "'+SensorList[0]+'"}, {"location" : "'+SensorList[1]+'"}, "fields": {"value":'+str(SensorList[2])+"}, "+'"time": 1'+endStr
    
    return DictStr

#dict = StringToDictString(SensorList, "HydroSensorData")
dict = '"[{"measurement": "HydroSensorData", "tags": {"location": "right_closet"}, {"sensor": "ph"}, "fields": {"value": 39.9876}, "time": 1}]'


client = influxdb_client.InfluxDBClient(
url="http://localhost:8086",
token="my-token",
org="Hydropi Org"
)
bucket = "HydroSensorData"
org="Hydropi Org"

if client is None:
    print('Connection failed.')
else:
    print('Connection established.')

write_api = client.write_api(write_options=SYNCHRONOUS)
# write a point or row to influxdb
# p = influxdb_client.Point("SendorData").tag("location", location).tag("sensor", sensor).field("value", dblvalueraw).time(datetime.now(), WritePrecision.MS)
write_api.write(bucket=bucket, org=org, record=dict)
