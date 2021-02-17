import threading
from time import sleep

from tempsensor import tempsensor
from keezer_sockets import keezer_sockets

class keezer:
    def __init__(self,t=38.0,h=2.0):
        self.temperature = t
        self.setpoint = t
        self.hysteresis = h
        self.sensor = tempsensor(fake=True)
        self.compressor_protection = .3
        self.sockets = keezer_sockets()
        self.sensor.start()
        threading.Timer(1, self.service).start()

    def do_sockets(self):
        if False:
            # this is a silly way to do this, but it allows me
            # to hit breakpoints when there are changes
            if self.setpoint != self.sockets.setpoint:
                self.setpoint = self.sockets.setpoint
            if self.protection_time != self.sockets.compressor_protection:
                self.protection_time = self.sockets.compressor_protection
            # read temp values
            if self.protection_time != self.sockets.protection_time:
                self.protection_time = self.sockets.protection_time

    def do_temperatures(self):
        self.temperature = self.sensor.temp

    def service(self):
        self.do_sockets()
        self.do_temperatures()
        threading.Timer(1, self.service).start()
