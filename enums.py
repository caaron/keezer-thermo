from enum import Enum

class Ports(Enum):
    SUB_PORT = 5556
    SUB_HYSTERESIS = 5557
    PUBLISH_PORT = 5558
    
    
class Topics(Enum):
    SETPOINT = 1001
    HYSTERESIS = 1002
    KEEZER_WATER_TEMP = 1003
    RELAY_STATE = 1004
    COMPR_PROTECTION = 1005
    COMPR_PROTECTION_STATE = 1006
    ONTIME = 1007
    OFFTIME = 1008
    AIR_TEMP_DHT11 = 1009
    RELAYTIME = 1010
    CO2_LEVEL = 1011
    CO2_WEIGHT = 1012
    AIR_HUMIDITY_DHT11 = 1013
    ROOM_TEMP_DS18B20 = 1014
    AIR_TEMP_DS18B20 = 1015

class RelayState(Enum):
    OFF = 0
    ON = 1
    TOGGLE = 2

class LoadCells(Enum):
    CO2 = 0
    KEG1 = 1
    KEG2 = 2
    KEG3 = 3
