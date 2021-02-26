import sys
import threading

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QVBoxLayout
from QLed import QLed
import zmq
from enums import RelayState,Topics,Ports

qtCreatorFile = "gui.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.context = zmq.Context()
        self.rcvsocket = self.context.socket(zmq.SUB)
        #setup receiving set temp socket (publish port on the rpi side)
        self.rcvsocket.connect("tcp://10.0.0.154:%s" % Ports.PUBLISH_PORT.value)
        # send rpi the setpoint
        self.pubsocket = self.context.socket(zmq.PUB)
        #setup sending setpoint socket (subscribe port on the rpi side)
        self.pubsocket.connect("tcp://10.0.0.154:%s" % Ports.SUB_PORT.value)

        self.rcvsocket.subscribe("")
        self.poller = zmq.Poller()
        self.poller.register(self.rcvsocket, zmq.POLLIN)

        self.temperature = 0
        self.setpoint = 38
        self.lcdNumber.display("%.1f" % self.setpoint)

        self.pushButton_2.clicked.connect(self.sp_up_pressed)
        self.pushButton.clicked.connect(self.sp_down_pressed)
        self.pushButton_enable.clicked.connect(self.enable_pressed)
        self.pushButton_toggle.clicked.connect(self.toggle_pressed)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)  # every 1000 milliseconds

        self.label_relaystate.setText("Relay State")
        self.led_relay = QLed(self, onColour=QLed.Green, shape=QLed.Circle)
        self.led_relay.value = False
        self.gridLayout_relay.addWidget(self.led_relay)

        self.label_comp_protect_state.setText("Comp Timer")
        self.led_ptime = QLed(self, onColour=QLed.Green, shape=QLed.Circle)
        self.led_ptime.value = False
        self.gridLayout_protection.addWidget(self.led_ptime)


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


    def update_display(self):
        topic, data = self.get_msgs()
        while topic is not None:
            if topic == Topics.TEMP.value:       # temperature
                temp = "%.1f" % float(data)
                self.lcdNumber_2.display(temp)
            elif topic == Topics.RELAY_STATE.value:
                self.led.value = int(data)
            elif topic == Topics.COMPR_PROTECTION_STATE.value:
                self.led.value = int(data)

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