import time
import board
import adafruit_dht
from sensortypes import sensorType

#dhtDevice = adafruit_dht.DHT22(board.D23)


class DHTXX:

    def __init__(self,type=sensorType.DHT22,pin=None):
        if type == sensorType.DHT11 or type == sensorType.DHT22:
            self.type = type
        else:
            self.type = None

        self.pin = pin
        self.temperature_c = -999

        if self.type == sensorType.DHT22 and self.pin is not None:
            self.dhtDevice = adafruit_dht.DHT22(self.pin)
        elif self.type == sensorType.DHT11 and self.pin is not None:
            self.dhtDevice = adafruit_dht.DHT11(self.pin)
        else:
            self.dhtDevice = None
            

# you can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
# This may be necessary on a Linux single board computer like the Raspberry Pi,
# but it will not work in CircuitPython.
# dhtDevice = adafruit_dht.DHT22(board.D18, use_pulseio=False)

    def read(self):
        read_result = False
        self.errors = 0
        while not read_result:
            try:
                # Print the values to the serial port
                self.temperature_c = self.dhtDevice.temperature
                if self.temperature_c is None:
                    print("temp read is of type None!")
                    #time.sleep(2.0)
                    continue
                self.temperature_f = self.temperature_c * (9 / 5) + 32
                self.humidity = self.dhtDevice.humidity
#                print("Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
#                        temperature_f, temperature_c, humidity)
#                      )
                read_result = True
                return read_result
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                #print("bad DHT read #%d, trying again" % self.errors)
                self.errors += 1
                if self.errors > 2:
                    print("bad DHT read #%d, trying again" % self.errors)
                continue
            except Exception as error:
                print("DHT exception:")
                print(error)
                #self.dhtDevice.exit()
                raise error

            time.sleep(2.0)
    
    def tempC(self):
        self.read()
        return self.temperature_c

    def tempF(self):
        self.read()
        return self.temperature_f
