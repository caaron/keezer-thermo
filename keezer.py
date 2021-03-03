import ASUS.GPIO as GPIO

import threading
from time import sleep,time
import datetime
from tempsensor import tempsensor
from keezer_sockets import keezer_sockets
from sensortypes import sensorType


from enums import Ports,Topics,RelayState

# when this can't start because it can't open the GPIO
#"Unable to set line 23 to input"
# it's due to pulseio tying up the input
# ps aux | grep pulseio
# kill -9 that pid


class keezer:
    def __init__(self,t=38.0,h=2.0):
        self.temperature = t
        self.setpoint = t
        self.hysteresis = h
        self.sensors = []
        self.compressor_protection = 1     # in minutes
        self.compressor_protection_state = True
        self.relay_state = RelayState.OFF
        self.sockets = keezer_sockets()
        self.ok_to_switch = False
        self.signal_exit = False
        self.compressor_max_on_time = 5   # in minutes
        self.failsafe = False
        
        self.relay1 = 26
        self.relay2 = 20
        self.relay3 = 21
        self.relayPin = self.relay2
        # Pin Setup:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
        GPIO.setup(self.relayPin, GPIO.OUT)  # LED pin set as output

        # put relay in a known state
        self.relay_off()

        # add the sensors in order of priority, first added will be primary
        self.sensors.append(tempsensor(type=sensorType.DS18B20,pin=999))
        self.sensors.append(tempsensor(type=sensorType.DHT11,pin=18))
        

    def do_sockets(self):
        topic, data = self.sockets.read_sockets()
        while data is not None:
            if topic == Topics.SETPOINT.value:
                self.setpoint = int(data)
                print("new setpoint of %d" % self.setpoint)                
            elif topic == Topics.COMPR_PROTECTION.value:
                self.compressor_protection = int(data)
                print("new compressor_protection of %d" % self.compressor_protection)                
            elif topic == Topics.RELAY_STATE.value:
                self.relay_toggle()

            topic, data = self.sockets.read_sockets()

    # send the current temp and relay state
        self.sockets.publish_float(Topics.TEMP.value, self.temperature)
        self.sockets.publish_int(Topics.RELAY_STATE.value, self.relay_state.value)
        self.sockets.publish_int(Topics.COMPR_PROTECTION_STATE.value, self.compressor_protection_state)

    def do_temperatures(self):
        # average the temp sensors? 
        tmp = []
        for sensor in self.sensors:
             tmp.append(sensor.read())
        # right now, only use the first sensor
        self.temperature = tmp[0]

    def protection_timer_handler(self):
        self.ok_to_switch = True
        self.compressor_protection_state = False
        print("compressor_protection_state = False")

    def start_protection_timer(self):
        threading.Timer(self.compressor_protection * 60.0, self.protection_timer_handler).start()
        self.ok_to_switch = False
        self.compressor_protection_state = True
        print("compressor_protection_state = True for :%d minutes" % (self.compressor_protection))

    def on_time_protection_check_handler(self):
        # need to make sure not to be on forever, even if not getting down to temp
        if self.relay_state == RelayState.ON:
            self.relay_state = RelayState.OFF
            self.failsafe = True    # don't allow us to turn back on (since we don't start the protection timer again)
            # should sound some kind of alarm

    def relay_on(self):
        self.relay_state = RelayState.ON
        GPIO.output(self.relayPin, GPIO.HIGH)
        # switch value changed, restart relay timer
        self.start_protection_timer()
        print("compressor on")
        # todo: implement the on time protection timer
        #threading.Timer(self.compressor_max_on_time * 60.0, self.on_time_protection_check_handler).start()

    def relay_off(self):
        self.relay_state = RelayState.OFF
        GPIO.output(self.relayPin, GPIO.LOW)
        # switch value changed, restart relay timer
        self.start_protection_timer()
        # check and kill any protection timers
        print("compressor off")

    def relay_toggle(self):
        if self.relay_state == RelayState.OFF:
            self.relay_on()
        else:
            self.relay_off()

    def do_thermostat(self):
        self.do_temperatures()
        if self.ok_to_switch and self.failsafe == False:     # if compression saftey timer is expired
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

    def print_vars(self):
        print("setpoint:%d" %  self.setpoint)
        print("temperature:%.02f" % self.temperature)
        print("relay state:%s = %d = %r" % ("ON" if self.relay_state == RelayState.ON else "OFF",
                                            int(self.relay_state.value), bool(int(self.relay_state.value)) ))
        print("ok_to_switch:%r" % bool(self.ok_to_switch))
        print("comp protection state:%r" % bool(self.compressor_protection_state))
        print("failsafe state:%r" % bool(self.failsafe))
        print("")

    def service(self):
        self.count = 0
        self.last_temp = self.temperature
        self.print_vars()
        try:
            while not self.signal_exit:
                self.do_sockets()
                self.do_thermostat()
                #threading.Timer(1, self.service).start()
                #if True:  #(self.count % 10) == 0:
                if self.last_temp != self.temperature:
                    ct = datetime.datetime.now()
                    print("keezer service:%s  :: Temp:%.02f" % (ct,self.temperature))
                    self.last_temp = self.temperature
                    self.print_vars()
                self.count += 1
                sleep(1)
        except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
            GPIO.cleanup() # cleanup all GPIO
            print("exiting keezer service")


if __name__ == "__main__":
    mKeezer = keezer()
    mKeezer.service()
