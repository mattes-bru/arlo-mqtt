import paho.mqtt.client as mqtt
from Arlo import Arlo
from threading import Thread, Event
import os
import queue
import json




class ArloSensors:
    def __init__(self, mqttClient):
        self.mqttClient = mqttClient
        self.airquality = 0.0
        self.temperature = 0.0
        self.humidity = 0.0
    
    def readSensors(self, arlo, cam):
        try:
            print("reading sensors...", end=' ')
            sensor_config = arlo.GetSensorConfig(cam)
            data = sensor_config['properties']
            temperature = data['temperature']['value'] / data['temperature']['scalingFactor']
            humidity = data['humidity']['value'] / data['humidity']['scalingFactor']
            airquality = data['airQuality']['value'] / data['airQuality']['scalingFactor']

            print('done (T: {}, H: {}, A: {})'.format(temperature,humidity,airquality))

            # if abs(self.temperature - temperature) > 0.1:
            #     self.mqttClient.publish("arlo/" + cam["uniqueId"] + "/sensors/temperature" , temperature, retain=True)
            # if abs(self.humidity - humidity) > 0.1:
            #     self.mqttClient.publish("arlo/" + cam["uniqueId"] + "/sensors/humidity" , humidity, retain=True)
            # if abs(self.airquality - airquality) > 0.1:
            #     self.mqttClient.publish("arlo/" + cam["uniqueId"] + "/sensors/airquality" , airquality, retain=True)

            if abs(self.airquality - airquality) > 0.1 or abs(self.humidity - humidity) > 0.1 or abs(self.temperature - temperature) > 0.1:
                print('sending sensor data update...', end=' ')
                payload = {
                    'temperature': temperature,
                    'humidity': humidity,
                    'airquality': airquality
                }
                self.mqttClient.publish("arlo/" + cam["uniqueId"] + "/sensors/environmental" , json.dumps(payload), retain=True)
                print('done')

            self.temperature = temperature
            self.humidity = humidity
            self.airquality = airquality




        except Exception as e:
            print("Reading ARLO sensors failed with" , e )




def onMQTTConnected(client, userdata, flags, rc):
    print("connect to MQTT server (" + str(rc) + ")")


def onArloEvent(arlo, event):
    try:
        if 'resource' in event:
            if "ambientSensors" in event['resource']:
                # Ambient Sensors will be handled elsewhere
                return
        # if 'properties' in event:
        #     if 'batteryLevel'
            
        print ("==== Callback =======")
        print(event)
    except Exception as e:
        print("Callback failed with: " , e)





mqtt_host = os.environ.get("MQTT_SERVER")
if not mqtt_host:
    raise ValueError('this app needs to have the "MQTT_SERVER" variable set')

client = mqtt.Client()
client.on_connect = onMQTTConnected

client.connect(mqtt_host)

client.loop_start()

stopEvent = Event()


arlo_user = os.environ.get("ARLO_USER")
if not arlo_user:
    raise ValueError('you need to set the user for ARLO in the "ARLO_USER" variable')

arlo_password = os.environ.get("ARLO_PASSWORD")
if not arlo_password:
    raise ValueError('you need to set the password for ARLO in the "ARLO_PASSWORD" variable')

try:    
    arlo = Arlo(arlo_user, arlo_password)
    
    cameras = arlo.GetDevices('camera') 

    arlo.SetTempUnit(cameras[0]["uniqueId"], "C")

    sensors = ArloSensors(client)
    sensors.readSensors(arlo, cameras[0])

except Exception as e:
    print("ARLO inititialization failed with" , e)
    quit(1)

while True:
    try:
        print('Listen for ARLO events...', end=' ')
        arlo.HandleEvents(cameras[0], onArloEvent, timeout=60.0)
    except queue.Empty as e:
        print("done")
        sensors.readSensors(arlo, cameras[0])
        # Reset ARLO
        arlo = Arlo(arlo_user, arlo_password)
        cameras = arlo.GetDevices('camera')
        continue
    except Exception as e:
        print('failed (', repr(e) , ')')
        break

    
stopEvent.set()

    

