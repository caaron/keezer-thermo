import math
from os import pathconf
from ds18b20 import DS18B20
import threading
from DHTXX import DHT11,DHT11Result
from sensortypes import sensorType
import time

class temperature_measurement:
    def __init__(self,type=sensorType.FAKE, topic=None, temp=None, humidity=None) -> None:
        self.sensor = type
        self.topic = topic
        self.temperature = temp
        self.humidity = humidity

class tempsensors:
    def __init__(self) -> None:
        self.sensors = []

    def addSensor(self,t=None,topic=None,pin=None):
        self.sensors.append(tempsensor(type=t, pin=pin, topic=topic))

    def readAll(self):
        result = []
        idx = 0
        for s in self.sensors:
        #        if s.type == sensorType.DS18B20: 
            result.append(s.read_sensor(index=idx))
            idx += 1
        return result

    def getNumSensors(self):
        return len(self.sensors)



class tempsensor:
    def __init__(self,type=sensorType.FAKE,pin=None,topic=None):
        # types are 
        self.temp = 80
        self.reads = 0
        self.change = .1        
        self.pin = pin        # need to add some error/bound checking here!!!
        self.topic = topic
        self.humidity = None
        self.type = type
        
        if self.type == sensorType.DS18B20:
            self.sensor = DS18B20()            
        elif self.type == sensorType.DHT11:
            self.sensor = DHT11(pin=self.pin)
        elif self.type == sensorType.DHT22:
            self.sensor = DHT11(pin=self.pin)
        else:
            self.sensor = None

 
    def read_sensor(self,index=None,topic=None):
        # update temp is sensor is fake
        if self.sensor is None:
            result = self.temp
            self.temp += self.change
            self.reads += 1
        else:                    
            result = None
            try:
                if type(self.sensor) == DHT11:
                    err = 1
                    errors = 0
                    while err is not DHT11Result.ERR_NO_ERROR and errors < 10:
                        r = self.sensor.read()
                        err = r.error_code
                        if err is DHT11Result.ERR_NO_ERROR:
                            self.temp = r.temperature_f
                            result = self.temp
                            self.humidity = r.humidity
                        else:
                            errors += 1
                            time.sleep(2)
                    
                elif type(self.sensor) == DS18B20: 
                    #index = self.getIndex(topic)
                    self.temp = self.sensor.tempF(index)
                    result = self.temp
                else:
                    tempC = self.sensor.read()
                    self.temp = (tempC * 9.0/5.0) + 32
                    result = self.temp
            except Exception as error:
                print(error)
                raise error
            
        tresult = temperature_measurement(self.sensor,self.topic,self.temp,self.humidity)
        return tresult

    def read_sensor_humidity(self):
        result = None
        if self.sensor is not None:
            try:
                if type(self.sensor) == DHT11:
                    result = self.humidity

            except Exception as error:
                print(error)
                raise error
            
        tresult = temperature_measurement(self.sensor,self.topic,self.temp,self.humidity)
        return tresult

    def read(self):
        return self.read_sensor()


