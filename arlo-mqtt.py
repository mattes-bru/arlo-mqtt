import paho.mqtt.client as mqtt
from Arlo import Arlo
from threading import Thread, Event
import os
import queue




class ArloSensorsThread(Thread):
    def __init__(self, stopEvent, arlo, cam, mqttClient):
        Thread.__init__(self,name="ArloSensors")
        self.stopped = stopEvent
        self.arlo = arlo
        self.cam = cam
        self.mqttClient = mqttClient
        self.airquality = 0.0
        self.temperature = 0.0
        self.humidity = 0.0
    
    def run(self):
        print("ARLO sensors thread started")
        while not self.stopped.wait(1.0):            
            try:
                print("reading sensors...")
                sensor_config = self.arlo.GetSensorConfig(self.cam)
                data = sensor_config['properties']
                temperature = data['temperature']['value'] / data['temperature']['scalingFactor']
                humidity = data['humidity']['value'] / data['humidity']['scalingFactor']
                airquality = data['airQuality']['value'] / data['airQuality']['scalingFactor']
                
                

                if abs(self.temperature - temperature) > 0.1:
                    self.mqttClient.publish("arlo/" + self.cam["uniqueId"] + "/sensors/temperature" , temperature, retain=True)
                if abs(self.humidity - humidity) > 0.1:
                    self.mqttClient.publish("arlo/" + self.cam["uniqueId"] + "/sensors/humidity" , humidity, retain=True)
                if abs(self.airquality - airquality) > 0.1:
                    self.mqttClient.publish("arlo/" + self.cam["uniqueId"] + "/sensors/airquality" , airquality, retain=True)

                self.temperature = temperature
                self.humidity = humidity
                self.airquality = airquality
                print( "Temperature:" , self.temperature , "Humidity:" , self.humidity, "air quality:" , self.airquality)

            except Exception as e:
                print("Reading ARLO sensors failed with" , e )
        print("ARLO sensors thread stopped")




def onMQTTConnected(client, userdata, flags, rc):
    print("connect to MQTT server (" + str(rc) + ")")


def onArloEvent(arlo, event):
    try:
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

    arloSensorThread = ArloSensorsThread(stopEvent, arlo, cameras[0], client)
    arloSensorThread.start()
except Exception as e:
    print("ARLO inititialization failed with" , e)
    quit(1)

while True:
    try:
        arlo.HandleEvents(cameras[0], onArloEvent)
    except queue.Empty as e:
        print('Timeout waiting for events')
        continue
    except Exception as e:
        print('Exception in handle Arlo events:', repr(e))
        break

    
stopEvent.set()

    

