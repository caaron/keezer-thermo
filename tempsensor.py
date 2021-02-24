import math
from ds18b20 import DS18B20
import threading
from dht import DHTXX
from sensortypes import sensorType



class tempsensor:
    def __init__(self,type=sensorType.FAKE,pin=None):
        # types are 
        self.temp = 80
        self.reads = 0
        self.change = .1        
        self.pin = pin        # need to add some error/bound checking here!!!
        
        if type == sensorType.DS18B20:
            self.sensor = DS18B20()            
        elif type == sensorType.DHT11:
            self.sensor = DHTXX(type=sensorType.DHT11,pin=self.pin)
        elif type == sensorType.DHT22:
            self.sensor = DHTXX(type=sensorType.DHT22,pin=self.pin)
        else:
            self.sensor = None


    def read_sensor(self):
        # update temp is sensor is fake
        if self.sensor is None:
            result = self.temp
            self.temp += self.change
            self.reads += 1
        else:                    
            try:
                self.temp = self.sensor.tempF()
                result = self.temp
            except Exception as error:
                raise error
            
        return result

    def read(self):
        return self.read_sensor()


