import zmq
import random
import sys
import time
import threading
from enum import Enum


class Ports(Enum):
    SET_TEMP = 5556
    SET_HYSTERESIS = 5557
    PUB_TEMP = 5558

class keezer_sockets():
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        #setup receiving set temp socket
        self.socket.bind("tcp://*:%s" % Ports.SET_TEMP.value)
        #setup receiving set hysteresis socket
        self.socket.bind("tcp://*:%s" % Ports.SET_HYSTERESIS.value)
        #setup publishing temp socket
        self.socket.bind("tcp://*:%s" % Ports.PUB_TEMP.value)

    def read_sockets(self):
        try:
            if self.socket.recv(flags=NOBLOCK) != None:
                #process some data
                pass

        except zmq.ZMQError as e:
            if e.strerror is stupid:
                pass


    def start(self):
        self.t = threading.Timer(1,self.read_sockets())

        while True:
            #self.socket.send("Server message to client3")
            msg = self.socket.recv()
            time.sleep(1)

    def stop(self):
        self.t.cancel()

