import math
from ds18b20 import DS18B20
import threading
from DHTXX import DHT11,DHT11Result
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
            self.sensor = DHT11(pin=self.pin)
        elif type == sensorType.DHT22:
            self.sensor = DHT11(pin=self.pin)
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
                if type(self.sensor) == DHT11:
                    self.temp = self.sensor.read()
                    result = self.temp.temperature_f
                elif type(self.sensor) == DS18B20: 
                    self.temp = self.sensor.tempF()
                    result = self.temp
                else:
                    tempC = self.sensor.read()
                    self.temp = (tempC * 9.0/5.0) + 32
                    result = self.temp
            except Exception as error:
                print(error)
                raise error
            
        return result

    def read(self):
        return self.read_sensor()


