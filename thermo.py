import signal
import sys
from enum import Enum
from time import sleep
import threading
from keezer import keezer


class RelayState(Enum):
    ON = 1
    OFF = 0


signal_exit = False

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    signal_exit = True

signal.signal(signal.SIGINT, signal_handler)

class therm_service():
    def __init__(self):
        self.keezer = keezer()
        self.signal_exit = False
        self.ok_to_switch = False
        self.relay_state = RelayState.OFF

    def start(self):
        self.start_protection_timer()
        self.main()

    def stop(self):
        self.signal_exit = True

    def protection_timer_handler(self):
        self.ok_to_switch = True
        self.relay_timer = None

    def start_protection_timer(self):
        threading.Timer(self.keezer.compressor_protection * 60.0, self.protection_timer_handler).start()
        self.ok_to_switch = False

    def relay_on(self):
        self.relay_state = RelayState.ON
        self.start_protection_timer()

    def relay_off(self):
        self.relay_state = RelayState.OFF
        self.start_protection_timer()

    def relay_toggle(self):
        self.relay_state = self.relay_state ^ 1
        self.start_protection_timer()

    def main(self):
        while not self.signal_exit:
            # update values received from sockets
            if self.ok_to_switch:
                if self.relay_state == RelayState.OFF:
                    if self.keezer.temperature > (self.keezer.setpoint + self.keezer.hysteresis):
                        self.relay_on()
                else:   # relay is ON
                    if self.keezer.temperature < (self.keezer.setpoint - self.keezer.hysteresis):
                        self.relay_off()
            else:
                pass

        # decide if switch will happen
        # if switch value changed, restart relay timer
            sleep(1)

if __name__ == "__main__":
    tservice = therm_service()
    tservice.start()
    #print any relevant messages
    # wait for ctrl-C to stop
    while (signal_exit is False):
        sleep(1)

    # do any needed cleanup
    signal.pause()
    tservice.stop()
