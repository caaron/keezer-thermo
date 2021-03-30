import sys
import threading
from time import sleep,time
import datetime
import random

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QVBoxLayout
from QLed import QLed
import zmq
from enums import RelayState,Topics,Ports
import sqlite3
import sys
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np


qtCreatorFile = "gui.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.ax2 = self.axes.twinx()
        self.ax2.set_ylim(-2,2)
        super(MplCanvas, self).__init__(fig)

class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(5)  # every 1000 milliseconds
        # which defines a single set of axes as self.axes.
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.setpoint = 38
        self.maxdatalength = 2000
        self.xdata = []
        self.rdata = [0] * self.maxdatalength
        self.spdata = [self.setpoint] * self.maxdatalength
        self.ydata = [self.setpoint] * self.maxdatalength
        self._plot_ref = None
        self.plotLayout.addWidget(self.sc)
        self.relay = False
        self.temp = 38.0
        self.speed = .05
        self.hysteresis = 2



    def update_display(self):
        temp = self.temp + (self.speed * ((-2 * int(self.relay) + 1)))
        self.temp = temp
        if self.relay == False and temp > self.setpoint:
            self.relay = True
        elif self.relay == True and temp < (self.setpoint - self.hysteresis):
            self.relay = False
        else:
            pass

        self.xdata = list(range(self.maxdatalength))
        self.ydata = self.ydata[1:] + [temp]
        #self.spdata = self.ydata[1:] + [random.randint(30,50)]
        self.rdata = self.rdata[1:] + [int(self.relay)]
        self.sc.axes.cla()
        self.sc.axes.plot(self.xdata,self.ydata,'r')
        self.sc.axes.plot(self.xdata,self.spdata,'b')
        self.sc.ax2.cla()
        self.sc.ax2.plot(self.xdata,self.rdata,'g')
        self.sc.draw()

app = QtWidgets.QApplication(sys.argv)
w = MyWindow()
w.show()
sys.exit(app.exec_())