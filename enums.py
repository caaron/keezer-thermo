from enum import Enum

class Ports(Enum):
    SUB_PORT = 5556
    SUB_HYSTERESIS = 5557
    PUBLISH_PORT = 5558
    
    
class Topics(Enum):
    SETPOINT = 1
    HYSTERESIS = 2
    TEMP = 3
    RELAY_STATE = 4
    COMPR_PROTECTION = 5
    COMPR_PROTECTION_STATE = 6

class RelayState(Enum):
    OFF = 0
    ON = 1
    TOGGLE = 2