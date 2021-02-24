import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import zmq


qtCreatorFile = "gui.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        #setup receiving set temp socket
        self.socket.connect("tcp://10.0.0.154:%s" % 5558)

        self.socket.subscribe("")
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.temperature = 0
        self.setpoint = 38
        self.lcdNumber.display("%.1f" % self.setpoint)

        self.pushButton_2.clicked.connect(self.sp_up_pressed)
        self.pushButton.clicked.connect(self.sp_down_pressed)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)  # every 1000 milliseconds


    def update_display(self):
        active_socks = dict(self.poller.poll(timeout=10))
        if self.socket in active_socks and active_socks[self.socket] == zmq.POLLIN:
            while self.socket in active_socks and active_socks[self.socket] == zmq.POLLIN:
                msg = self.socket.recv()
                #print(msg)
                if int(msg) == 3:       # temperature
                    data = self.socket.recv()
                    temp = "%.1f" % float(data)
                    self.lcdNumber_2.display(temp)
                elif int(msg) == 4:
                active_socks = dict(self.poller.poll(timeout=10))

        self.lcdNumber.display("%.1f" % self.setpoint)
        #self.results_output.setText(total_price_string)

    def sp_up_pressed(self):
        self.setpoint += 1
        self.lcdNumber.display("%.1f" % self.setpoint)

    def sp_down_pressed(self):
        self.setpoint -= 1
        self.lcdNumber.display("%.1f" % self.setpoint)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())