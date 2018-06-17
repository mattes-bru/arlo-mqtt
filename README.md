# Netgear ARLO MQTT Gateway

this is an early version of the app and does not do anything useful right now! You have been warned. The tasks planned so far are:

* Publish the ARLO environmental sensors to MQTT
* Write to an MQTT topic when an ARLO ALARM happend
* Publish the battery data to MQTT

## Setup

```arlo-mqtt.py``` is configured through environment variables, this should make a (later) systemd installation easy. You need to set:

* ```MQTT_SERVER```: the address of the MQTT server used
* ```ARLO_USER```: the user of the Netgear ARLO account used
* ```ARLO_PASSWORD```: the password of the Netgear ARLO account used

## Dependencies

```arlo-mqtt.py```  uses [paho-mqtt](https://pypi.org/project/paho-mqtt/) and [arlo](https://pypi.org/project/arlo/)