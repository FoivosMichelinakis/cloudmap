import zmq
import json
import time
import subprocess
import os
import socket
import fcntl
import struct
import socket


Norway = ["211", "24"]
Spain = ["193", "213"] # non working 213
Polito = ["37", "199"]  # non working 199
Sweden = ["51", "248"]


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


context = zmq.Context()
socketzmq = context.socket(zmq.SUB)
socketzmq.connect("tcp://172.17.0.1:5556")
topicfilter = "MONROE.META.DEVICE.MODEM"
socketzmq.setsockopt(zmq.SUBSCRIBE, topicfilter)

LoggerTimestamp = str(int(time.time()))
nodeId = subprocess.check_output(["cat", "/etc/nodeid"]).replace("\n", "")

filename = "meta_tracking" + nodeId + "_" + LoggerTimestamp + ".txt"
startTime = time.time()
transmissionPeriod = 12*60*60
while True:
    while ((time.time() - startTime) < (transmissionPeriod)):
        string = socketzmq.recv()
        metaData = json.loads(string[string.find("{"):])
        if metaData["InterfaceName"].find("usb") >= 0:
            if ((nodeId in Spain) or (nodeId in Polito)) and (metaData["Operator"].find("oda") >= 0):
                # the interface IP of the interface that has the vodadone card
                IP = metaData['InternalIPAddress']
                with open("PreferedModemAddress.txt", 'w') as f:
                    f.write(IP)
            with open(filename, 'a') as f:
                json.dump(metaData, f)
                f.write(os.linesep)
    filenameComplete = "metadata_" + nodeId + "_" + LoggerTimestamp + ".txt"
    os.rename(filename, filenameComplete)
    startTime = time.time()
    LoggerTimestamp = str(int(time.time()))
    filename = "meta_tracking" + nodeId + "_" + LoggerTimestamp + ".txt"
