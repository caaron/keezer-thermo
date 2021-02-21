import threading
from time import sleep,time
import datetime
from tempsensor import tempsensor
from keezer_sockets import keezer_sockets
from sensortypes import sensorType
import board
import adafruit_dht

class keezer:
    def __init__(self,t=38.0,h=2.0):
        self.temperature = t
        self.setpoint = t
        self.hysteresis = h
        self.sensors = []
        # add the sensors in order of priority, first added will be primary
        self.sensors.append(tempsensor(type=sensorType.DHT22,pin=board.D23))
        self.compressor_protection = .3     # in minutes
        self.sockets = keezer_sockets()
        self.ok_to_switch = False
        self.signal_exit = False
        

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
            # send the current temp and relay state

    def do_temperatures(self):
        # average the temp sensors? 
        self.temperature = self.sensors[0].read()

    def protection_timer_handler(self):
        self.ok_to_switch = True

    def start_protection_timer(self):
        threading.Timer(self.compressor_protection * 60.0, self.protection_timer_handler).start()
        self.ok_to_switch = False

    def relay_on(self):
        self.relay_state = RelayState.ON
        # switch value changed, restart relay timer
        self.start_protection_timer()

    def relay_off(self):
        self.relay_state = RelayState.OFF
        # switch value changed, restart relay timer
        self.start_protection_timer()

    def relay_toggle(self):
        self.relay_state = self.relay_state ^ 1
        # switch value changed, restart relay timer
        self.start_protection_timer()

    def do_thermostat(self):
        self.do_temperatures()
        if self.ok_to_switch:     # if compression saftey timer is expired
        # decide if switch will happen
            if self.relay_state == RelayState.OFF:
                if self.temperature > (self.setpoint + self.hysteresis):
                    self.relay_on()
            else:   # relay is ON
                if self.temperature < (self.setpoint - self.hysteresis):
                    self.relay_off()
        else:
            pass

        sleep(1)
        

    def service(self):
        self.count = 0
        while not self.signal_exit:
            self.do_sockets()
            self.do_thermostat()
            #threading.Timer(1, self.service).start()
            if True:  #(self.count % 10) == 0:
                ct = datetime.datetime.now()
                print("keezer service:%s  :: Temp:%f" % (ct,self.temperature))
            self.count += 1
            sleep(1)

if __name__ == "__main__":
    mKeezer = keezer()
    mKeezer.service()
