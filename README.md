# HydroMonitorLAMP
Hydroponic Monitoring based on LAMP. Based on RaspberryPi 4B, 4Gb. 
Includes support for sensors: 
BME280
DFRobot:Ph, EC, ORP

Adfruit ads1115 adc's used to interface the DFRobot analog sensors to the Pi. Any number of these can be used for unlimited number of sensors.
Added AdaFruit 1-wire, digital temperature probes. Any number of these can be wired together to make wiring easier
Added Optomax digital liquid sensors to check for low water conditions.

Most of the sensors purchased from dfrobot.com or AdaFruit.com. These are the least expensive I found.
DIY Cloud Weather Station code used for the PhP and apache2 code. PhP code not used.
mysql-connector-python module used for interface between MySQL and Python3.7
Added Grafana for a monitoring UI. Grafana JSON model files includes with this git.
Added fritzing model. This is the complete wiring diagram. Fritzing diagram included in this git
