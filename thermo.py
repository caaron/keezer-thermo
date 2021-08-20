import sys
import threading
from time import sleep,time
import datetime
import random
from collections import deque

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QVBoxLayout
#from QLed import QLed
import zmq
from enums import RelayState,Topics,Ports
import sys
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np


qtCreatorFile = "gui.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax1 = fig.add_subplot(221)
        self.ax2 = self.ax1.twinx()
        self.ax2.set_ylim(-2,2)
        self.ax3 = fig.add_subplot(222)
        self.ax4 = fig.add_subplot(223)
        self.ax5 = fig.add_subplot(224)
        super(MplCanvas, self).__init__(fig)

class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.context = zmq.Context()
        self.rpi_IP = "10.0.0.197"
        self.rcvsocket = self.context.socket(zmq.SUB)
        #setup receiving set temp socket (publish port on the rpi side)
        self.rcvsocket.connect("tcp://%s:%s" % (self.rpi_IP,Ports.PUBLISH_PORT.value))
        # send rpi the setpoint
        self.pubsocket = self.context.socket(zmq.PUB)
        #setup sending setpoint socket (subscribe port on the rpi side)
        self.pubsocket.connect("tcp://%s:%s" % (self.rpi_IP,Ports.SUB_PORT.value))

        self.rcvsocket.subscribe("")
        self.poller = zmq.Poller()
        self.poller.register(self.rcvsocket, zmq.POLLIN)

        self.temperature = None
        self.air_temperature = None
        self.humidity = None
        self.setpoint = 38
        self.lcdNumber.display("%.1f" % self.setpoint)

        self.useSQL = False

        self.pushButton_2.clicked.connect(self.sp_up_pressed)
        self.pushButton.clicked.connect(self.sp_down_pressed)
        #self.pushButton_enable.clicked.connect(self.enable_pressed)
        #self.pushButton_toggle.clicked.connect(self.toggle_pressed)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)  # every 1000 milliseconds

        self.label_relaystate.setText("Relay State")
        self.led_relay = QtWidgets.QLabel("OFF")
        #self.led_relay.setReadOnly(True)
        self.gridLayout_relay.addWidget(self.led_relay)

        self.label_comp_protect_state.setText("Comp Timer")
        self.led_ptime = QtWidgets.QLabel("ON")
        #self.led_ptime.setReadOnly(True)
        self.gridLayout_protection.addWidget(self.led_ptime)
        
         # Create the maptlotlib FigureCanvas object, 
        # which defines a single set of axes as self.ax1.
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        
        self.maxdatalength = 2500
        self.setpoint_data = deque([],self.maxdatalength)
        self.relay_data = deque([],self.maxdatalength)
        self.water_temperature_data = deque([],self.maxdatalength)
        self.air_temperature_data = deque([],self.maxdatalength)
        self.co2data = deque([],self.maxdatalength)
        self.humidity_data = deque([],self.maxdatalength)

        self.plotLayout.addWidget(self.sc)
        
        self.ontime = 0
        self.offtime = 0
        self.relayOnTime = 0
        self.relayOffTime = 0
        self.CO2_weight = None
        tmp = time()
        
        if self.useSQL:
            self.sql = sqlite3.connect("keezer.sql")
            self.sql_tablename = "events"
            self.init_db(self.sql)
        
    def __del__(self):
        if self.sql:
            self.sql.close()

    def init_db(self,db):
        try:
            c = self.sql.cursor()
            name = self.sql_tablename
            #get the count of tables with the name
            c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='%s' ''' % name)

            #if the count is 1, then table exists
            tmp = c.fetchone()
            if tmp[0]==0:
                sql_create_projects_table = """CREATE TABLE IF NOT EXISTS %s (
                                        sensor_index integer NOT NULL,
                                        time real NOT NULL,
                                        relay_state integer NOT NULL,
                                        temperature real NOT NULL
                                    );"""  % name


                print('creating table.')
                c.execute(sql_create_projects_table)
                self.sql.commit()
                return True

        except Exception as e:
            print("exception!!:%s" % e)
            return False

    def add_db_event(self,sensor_idx=0,time=-1,rs=-1,temp=-1):
        try:
            sql_insert_event = """insert into "%s" values(%d,%f,%d,%.1f);""" % (self.sql_tablename,sensor_idx, time,rs,temp)
            c = self.sql.cursor()
            c.execute(sql_insert_event)
            self.sql.commit()
            return c.lastrowid

        except Exception as e:
            print("exception!!:%s" % e)
            return -1


    def get_msgs(self):
        topic, data = None, None
        active_socks = dict(self.poller.poll(timeout=10))
        if self.rcvsocket in active_socks and active_socks[self.rcvsocket] == zmq.POLLIN:
            active_socks = dict(self.poller.poll(timeout=10))
            if self.rcvsocket in active_socks and active_socks[self.rcvsocket] == zmq.POLLIN:
                msg = self.rcvsocket.recv()
                topic = int(msg)
                data = self.rcvsocket.recv()
        return topic, data

    def average(self,x):
        avg = 0.0
        for a in x:
            avg += a
        avg = avg / len(x)
        return avg

    def all_valid(self,items):
        return all(x is not None for x in items)

    def plot_temps(self,time,temp):
        t2 = datetime.datetime.fromtimestamp(time)
        t = t2.strftime("%H:%M:%S")
        #self.xdata = list(range(self.maxdatalength))
        
        tmp = self.label_co2_weight.text()

        ledstate = 1 if self.led_relay.text() == "ON" else 0
        required_values = [self.temperature, self.air_temperature, self.humidity]
        self.sc.ax1.cla()
        self.sc.ax2.cla()
        self.sc.ax3.cla()
        self.sc.ax4.cla()
        self.sc.ax5.cla()
        
        #if self.all_valid(required_values):

        #if self.temperature is not None and self.air_temperature is not None:
        if self.temperature is not None:
            self.water_temperature_data.append(self.temperature)
            self.setpoint_data.append(self.setpoint)
            self.relay_data.append(ledstate)
            self.air_temperature_data.append(self.air_temperature)
            self.humidity_data.append(self.humidity)
            x = list(range(len(self.water_temperature_data)))
            self.avg = [self.average(self.water_temperature_data)] * len(x)

            self.sc.ax1.plot(x,self.water_temperature_data,'r',label='water temperature')
            self.sc.ax1.plot(x,self.setpoint_data,'b',label='setpoint')
            self.sc.ax1.plot(x,self.avg,'tab:orange',label='average')
            self.sc.ax2.plot(x,self.relay_data,'g')
            self.sc.ax2.set_title('Temperature')
            self.sc.ax1.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=2, borderaxespad=0, frameon=False)

        if self.air_temperature is not None:
            self.sc.ax4.plot(x,self.air_temperature_data,'tab:purple',label='air temp')
            self.sc.ax4.set_title('Air Temperature')

        if self.humidity is not None:
            self.sc.ax5.plot(x,self.humidity_data,'tab:orange',label='humidity')
            self.sc.ax5.set_title('Humidity')
        
        if self.CO2_weight is not None:
            self.co2data.append(self.CO2_weight)
            x = list(range(len(self.co2data)))
            self.sc.ax3.cla()
            self.sc.ax3.plot(x,self.co2data,'b')
            self.sc.ax3.set_title('CO2')

        self.sc.draw()




    def update_display(self):
        topic, data = self.get_msgs()
        while topic is not None:
            if topic == Topics.TEMP.value:       # temperature
                temp = round(float(data),1)
                t=time()
                v = self.lcdNumber_2.value()
                if temp != v:
                    ledstate = 1 if self.led_relay.text == "ON" else 0
                    if self.useSQL:
                        self.add_db_event(0,time=t,rs=int(ledstate),temp=v)
                self.lcdNumber_2.display(temp)
                self.temperature = temp
                self.plot_temps(round(t),temp)

            elif topic == Topics.RELAY_STATE.value:
                self.led_relay.setText("ON" if int(data) == 1 else "OFF")
            elif topic == Topics.COMPR_PROTECTION_STATE.value:
                self.led_ptime.setText("ON" if int(data) == 1 else "OFF")
            elif topic == Topics.ONTIME.value:
                self.ontime = int(data)
                on_percentage = float(self.ontime)*100/float(self.ontime + self.offtime)
                self.label_ontime.setText("ON:%d\n%.1f%%\n%s seconds" % (self.relayOnTime,on_percentage, int(data)))
            elif topic == Topics.OFFTIME.value:
                self.offtime = int(data)
                off_percentage = float(self.offtime)*100/float(self.ontime + self.offtime)
                self.label_offtime.setText("OFF:%d\n%.1f%%\n%s seconds" % (self.relayOffTime,off_percentage,  int(data)))
            elif topic == Topics.SETPOINT.value:
                if self.setpoint != int(data):
                    self.setpoint = int(data)
            elif topic == Topics.RELAYTIME.value:                
                if self.led_relay.text == "ON":
                    self.relayOnTime = int(data)
                    self.relayOffTime = 0
                else:
                    self.relayOffTime = int(data)
                    self.relayOnTime = 0
            elif topic == Topics.CO2_LEVEL.value:
                tmp = int(data)
                if tmp > 100:
                    tmp = 100
                elif tmp < 0:
                    tmp = 0
                self.CO2_progressBar.setValue(tmp)
                if self.CO2_progressBar.isTextVisible() is True:
                    self.CO2_progressBar.text = str(tmp)
            elif topic == Topics.CO2_WEIGHT.value:
                self.CO2_weight = float(data)
                self.label_co2_weight.setText("%.1f grams" % (self.CO2_weight))
            elif topic == Topics.AIR_TEMPERATURE.value:
                self.air_temperature = float(data)
            elif topic == Topics.AIR_HUMIDITY.value:
                self.humidity = float(data)

                #print("rcvd setpoint")

            topic, data = self.get_msgs()

        self.lcdNumber.display("%.1f" % self.setpoint)

    def send_setpoint(self,x):
        self.pubsocket.send_multipart([b"%d" % Topics.SETPOINT.value, b"%d" % x])

    def sp_up_pressed(self):
        self.setpoint += 1
        self.send_setpoint(self.setpoint)
        self.lcdNumber.display("%.1f" % self.setpoint)

    def sp_down_pressed(self):
        self.setpoint -= 1
        self.send_setpoint(self.setpoint)
        self.lcdNumber.display("%.1f" % self.setpoint)

    def toggle_enable_timeout_handler(self):
        self.pushButton_toggle.setEnabled(False)

    def enable_pressed(self):
        self.pushButton_toggle.setEnabled(True)
        threading.Timer(30, self.toggle_enable_timeout_handler).start()

    def toggle_pressed(self):
        self.pubsocket.send_multipart([b"%d" % Topics.RELAY_STATE.value, b"%d" % RelayState.TOGGLE.value])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
