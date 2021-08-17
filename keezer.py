from hx711 import HX711
import ASUS.GPIO as GPIO
import threading
from time import sleep,time
import datetime
from tempsensor import tempsensor
from keezer_sockets import keezer_sockets
from sensortypes import sensorType
#import sqlite3
from tank import Tank
from enums import Ports,Topics,RelayState
#from influxdb_client import InfluxDBClient, Point, WritePrecision
#from influxdb_client.client.write_api import SYNCHRONOUS

# when this can't start because it can't open the GPIO
#"Unable to set line 23 to input"
# it's due to pulseio tying up the input
# ps aux | grep pulseio
# kill -9 that pid


class keezer:
    def __init__(self,t=39.0,h=1.0):
        self.temperature = t
        self.humidity = 0
        self.air_temperature = t
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
        self.simulate = False
        #self.sql = sqlite3.connect("keezer.sql")
        self.ontime = 1
        self.offtime = 1
        self.relayStateTime = 0
        self.relayTime = time()
        self.relayChangeTime = time()
        from datetime import datetime


        # You can generate a Token from the "Tokens Tab" in the UI
#        self.influx_token = "LS_CSh06vCL049Eiuk1NrC2Q9XQdtHOh0KX5f3cP6KSWiPDk5uBvQ_0mOQIO1IFidbd2XMH5T_G-FoGfT5aqRg=="
#        self.influx_org = "c.aaron.hall@gmail.com"
#        self.influx_bucket = "c.aaron.hall's Bucket"

#        self.influx_client = InfluxDBClient(url="https://us-central1-1.gcp.cloud2.influxdata.com", token=self.influx_token)
#        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)

        #data = "mem,host=host1 used_percent=23.43234543"
        #self.write_api.write(self.influx_bucket, self.influx_org, data)

        
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

        # I had to follow this pinout to find the proper pins
        # for BOARD.BCM
        # https://www.raspberrypi.org/documentation/usage/gpio/
        self.load_cells = []
        self.load_cells.append(Tank(dryWeight=3084,s=HX711(dout=25,pd_sck=23)))
        # this is just setting the full weight based on the current weight, not a long term solution
        self.load_cells[0].set_full_weight(self.load_cells[0].get_weight())


    def __del__(self):
        if self.sql:
            self.sql.close()

    def init_db(self):
        c = self.sql.cursor()
        name = "runtimes"
        #get the count of tables with the name
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='%s' ''' % name)

        #if the count is 1, then table exists
        if c.fetchone()[0]==0:
            sql_create_projects_table = """CREATE TABLE IF NOT EXISTS %s (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    priority integer,
                                    status_id integer NOT NULL,
                                    project_id integer NOT NULL,
                                    begin_date text NOT NULL,
                                    end_date text NOT NULL,
                                    FOREIGN KEY (project_id) REFERENCES projects (id)
                                );"""  % name


            print('creating table.')
            create_table(self.sql, sql_create_projects_table)

    def publish_stat_to_influx(self, name, data):
        try:
            # publish temperature to influx DB
            point = Point("temp")\
                .tag("host", "host1")\
                .field(name, data)\
                .time(datetime.datetime.utcnow(), WritePrecision.NS)
            self.write_api.write(self.influx_bucket, self.influx_org, point)

        except Exception as e:
            print("Exception on influxDB write!")


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
        self.sockets.publish_int(Topics.ONTIME.value, self.ontime)
        self.sockets.publish_int(Topics.OFFTIME.value, self.offtime)
        self.sockets.publish_int(Topics.SETPOINT.value, self.setpoint)
        self.sockets.publish_int(Topics.AIR_TEMPERATURE.value, self.air_temperature)
        self.sockets.publish_int(Topics.RELAYTIME.value, self.relayStateTime)
        self.sockets.publish_int(Topics.CO2_LEVEL.value, self.load_cells[0].level)
        self.sockets.publish_int(Topics.CO2_WEIGHT.value, self.load_cells[0].value)
        self.sockets.publish_int(Topics.AIR_HUMIDITY.value, self.humidity)
        
        
            # publish temperature to influx DB
 #       self.publish_stat_to_influx("temperature", self.temperature)
            # publish DHT11 temperature to influx DB
#        self.publish_stat_to_influx("air_temperature", self.air_temperature)            
            # publish DHT11 humidity to influx DB
#        self.publish_stat_to_influx("DHT_humidity", self.humidity)
            # publish relaystate to influx DB
#        self.publish_stat_to_influx("RelayState", int(self.relay_state.value))

        if False:
            try:
                # publish temperature to influx DB
                point = Point("temp")\
                    .tag("host", "host1")\
                    .field("temperature", self.temperature)\
                    .time(datetime.datetime.utcnow(), WritePrecision.NS)
                self.write_api.write(self.influx_bucket, self.influx_org, point)
                # publish DHT11 temperature to influx DB
                point = Point("temp")\
                    .tag("host", "host1")\
                    .field("air_temperature", self.air_temperature)\
                    .time(datetime.datetime.utcnow(), WritePrecision.NS)
                self.write_api.write(self.influx_bucket, self.influx_org, point)
                # publish DHT11 humidity to influx DB
                point = Point("temp")\
                    .tag("host", "host1")\
                    .field("DHT_humidity", self.humidity)\
                    .time(datetime.datetime.utcnow(), WritePrecision.NS)
                self.write_api.write(self.influx_bucket, self.influx_org, point)
                # publish relaystate to influx DB
                point = Point("temp")\
                    .tag("host", "host1")\
                    .field("RelayState", int(self.relay_state.value))\
                    .time(datetime.datetime.utcnow(), WritePrecision.NS)
                self.write_api.write(self.influx_bucket, self.influx_org, point)
                if int(self.relay_state.value) != 0 and int(self.relay_state.value) != 1:
                    print("relat state is %f" % self.relay_state.value)
            except Exception as e:
                print("Exception on influxDB write!")


        #data = "mem,host=host1 used_percent=23.43234543"
        #self.write_api.write(self.influx_bucket, self.influx_org, data)
        
    def do_load_cells(self):
        for tank in self.load_cells:
            tank.get_weight()
            tank.get_value()

    def do_temperatures(self):
        # average the temp sensors? 
        tmp = []
        humids = []
        for sensor in self.sensors:
             tmp.append(sensor.read())             
             humids.append(sensor.read_sensor_humidity())
        # right now, only use the first sensor
        self.temperature = tmp[0]
        self.humidity = humids[1]
        if tmp[1] > 0 and tmp[1] < 100:
            self.air_temperature = tmp[1]
        else:
            print("received an out of bounds DHT temp!!")


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

    def do_relay_times_after_change(self):
        diff = time() - self.relayChangeTime
        if self.relay_state == RelayState.ON:
            self.offtime += diff
        else:
            self.ontime += diff
        self.relayChangeTime = time()
        self.relayStateTime = 0

    def do_relay_times(self):
        diff = time() - self.relayTime
        if self.relay_state == RelayState.ON:
            self.ontime += diff
        else:
            self.offtime += diff
        self.relayStateTime += int(diff)
        self.relayTime = time()

    def relay_on(self):
        self.relay_state = RelayState.ON
        GPIO.output(self.relayPin, GPIO.HIGH)
        # switch value changed, restart relay timer
        self.start_protection_timer()
        print("compressor on")
        self.do_relay_times_after_change()
        # todo: implement the on time protection timer
        #threading.Timer(self.compressor_max_on_time * 60.0, self.on_time_protection_check_handler).start()

    def relay_off(self):
        self.relay_state = RelayState.OFF
        GPIO.output(self.relayPin, GPIO.LOW)
        # switch value changed, restart relay timer
        self.start_protection_timer()
        # check and kill any protection timers
        print("compressor off")
        self.do_relay_times_after_change()

    def relay_toggle(self):
        if self.relay_state == RelayState.OFF:
            self.relay_on()
        else:
            self.relay_off()

    def do_thermostat(self):
        self.do_temperatures()
        if self.ok_to_switch and self.failsafe == False and self.simulate == False:     # if compression saftey timer is expired
        # decide if switch will happen
            if self.relay_state == RelayState.OFF:
                if self.temperature > (self.setpoint + self.hysteresis):
                    self.relay_on()
            else:   # relay is ON
                if self.temperature < (self.setpoint):
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
        on_percentage = float(self.ontime)*100/float(self.ontime + self.offtime)
        print("ontime:%.2f  %d seconds" % (on_percentage,self.ontime))
        off_percentage = float(self.offtime)*100/float(self.ontime + self.offtime)
        print("offtime:%.2f  %d seconds" % (off_percentage,self.offtime))
        print("CO2 weight:%f  CO2_level:%f" %(self.load_cells[0].weight, self.load_cells[0].level)) 
        print("")

    def service(self):
        self.count = 0
        self.last_temp = self.temperature
        self.print_vars()
        try:
            while not self.signal_exit:
                self.do_sockets()
                self.do_thermostat()
                self.do_relay_times()
                self.do_load_cells()
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
