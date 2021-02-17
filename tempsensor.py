import math
from ds18b20 import DS18B20
import threading




class tempsensor:
    def __init__(self,fake=False):
        self.temp = 80
        self.reads = 0
        self.change = .1
        self.fake = fake
        if not self.fake:
            self.sensor = DS18B20()
        else:
            self.sensor = None

        #self.t =
        threading.Timer(5,self.read_sensor).start()

            #5,self.read_sensor())

    def start(self):
        #self.t.start()
        pass

    def stop(self):
        self.t.cancel()

    def read_sensor(self):
        result = self.temp
        # update temp
        if self.fake is True:
            self.temp += self.change
            self.reads += 1
        else:
            self.temp = self.sensor.tempF(0)

        #self.t = threading.Timer(10,self.read_sensor)
        threading.Timer(5, self.read_sensor).start()

        return result

    def read(self):
        return self.temp