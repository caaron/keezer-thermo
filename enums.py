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
    ONTIME = 7
    OFFTIME = 8
    AIR_TEMPERATURE = 9
    RELAYTIME = 10
    CO2_LEVEL = 11
    CO2_WEIGHT = 12
    AIR_HUMIDITY = 13

class RelayState(Enum):
    OFF = 0
    ON = 1
    TOGGLE = 2

class LoadCells(Enum):
    CO2 = 0
    KEG1 = 1
    KEG2 = 2
    KEG3 = 3
