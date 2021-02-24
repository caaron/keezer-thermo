import zmq
import random
import sys
import time
import threading
from enums import Ports,Topics




class keezer_sockets():
    def __init__(self):
        self.context = zmq.Context()
        self.rcvsocket = self.context.socket(zmq.SUB)
        self.sndsocket = self.context.socket(zmq.PUB)
        #setup receiving set temp socket
        self.rcvsocket.bind("tcp://*:%s" % Ports.SUB_PORT.value)
        #setup publishing temp socket
        self.sndsocket.bind("tcp://*:%s" % Ports.PUBLISH_PORT.value)
        self.rcvsocket.subscribe("")
        self.poller = zmq.Poller()
        self.poller.register(self.rcvsocket, zmq.POLLIN)
        self.temperature = 0
        self.compressor_protection = 0
        self.setpoint = 0

#poll for any new messages
    def read_sockets(self):
        try:
            active_socks = dict(self.poller.poll(timeout=10))
            if self.rcvsocket in active_socks and active_socks[self.rcvsocket] == zmq.POLLIN:
                while self.rcvsocket in active_socks and active_socks[self.rcvsocket] == zmq.POLLIN:
                    msg = self.rcvsocket.recv()
                    if int(msg) == Topics.SETPOINT.value:       # setpoint
                        data = self.rcvsocket.recv()
                        self.setpoint = "%d" % float(data)
                        print("new setpoint of %d" % (self.setpoint))

        except zmq.ZMQError as e:
            if e.strerror is stupid:
                pass

    def publish_float(self,topic,x):
        self.sndsocket.send_multipart([b"%d" % topic, b"%f" % x])

    def publish_int(self,topic,x):        
        self.sndsocket.send_multipart([b"%d" % topic, b"%d" % x])

    def start(self):
        self.t = threading.Timer(1,self.read_sockets())

        while True:
            #self.socket.send("Server message to client3")
            msg = self.socket.recv()
            time.sleep(1)

    def stop(self):
        self.t.cancel()

