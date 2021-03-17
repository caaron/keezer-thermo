import math
from ds18b20 import DS18B20
import threading
from DHTXX import DHT11,DHT11Result
from sensortypes import sensorType
import time



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
                    err = 1
                    while err is not DHT11Result.ERR_NO_ERROR:
                        r = self.sensor.read()
                        err = r.error_code
                        if err is DHT11Result.ERR_NO_ERROR:
                            self.temp = r.temperature_f
                            self.humidity = r.humidity
                        result = self.temp
                    
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

    def read_sensor_humidity(self):
        result = None
        if self.sensor is not None:
            try:
                if type(self.sensor) == DHT11:
                    result = self.humidity

            except Exception as error:
                print(error)
                raise error
            
        return result

    def read(self):
        return self.read_sensor()


