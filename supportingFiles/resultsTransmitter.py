#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import fcntl
import struct
import time
import os
import subprocess
import shutil


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


nodeId = subprocess.check_output(["cat", "/etc/nodeid"]).replace("\n", "")
RESULTS_DIR = "/monroe/cdnmob/cdnmob_host/"
HOME_DIR = "/home/monroe/"


def getEthernetAddress():
    try:
        ethernetIP = get_ip_address("eth0")
        return ethernetIP
    except:
        return ""


def getPreferedModemAddress(nodeId):
    try:
        with open("PreferedModemAddress.txt", 'w') as f:
            modemIP = f.read()
            return modemIP.replace("\n", "")
    except:
        return ""


def copyExperimentalResults():
    ethernetIP = getEthernetAddress()
    modemIP = getPreferedModemAddress(nodeId)
    # first try to copy from the normal result directory
    toCopy = [RESULTS_DIR + filename for filename in os.listdir(RESULTS_DIR) if filename.endswith(".tar.gz")]
    if len(toCopy) > 0:
        time.sleep(30)  # in case we see the file while it is being created we wait a bit
        for ressultFile in toCopy:
            if ethernetIP != "":
                cmd = ["rsync", "--address=" + ethernetIP, "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/experiments/" + nodeId + "/"]
            elif modemIP != "":
                cmd = ["rsync", "--address=" + modemIP, "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/experiments/" + nodeId + "/"]
            else:
                cmd = ["rsync", "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/experiments/" + nodeId + "/"]
            try:
                out = subprocess.check_output(cmd)
            except:
                # the server probably is down so we move the result file to a location another location more suitable for storage (more space and more inodes)
                filename = ressultFile.split("/")[-1]
                shutil.move(ressultFile, HOME_DIR + filename)
                continue
            out = subprocess.check_output(["rm", ressultFile])
    # try to copy from the home directory any possible experimental results there
    toCopy = [HOME_DIR + filename for filename in os.listdir(HOME_DIR) if filename.endswith(".tar.gz")]
    if len(toCopy) > 0:
        for ressultFile in toCopy:
            if ethernetIP != "":
                cmd = ["rsync", "--address=" + ethernetIP, "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/experiments/" + nodeId + "/"]
            elif modemIP != "":
                cmd = ["rsync", "--address=" + modemIP, "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/experiments/" + nodeId + "/"]
            else:
                cmd = ["rsync", "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/experiments/" + nodeId + "/"]
            try:
                out = subprocess.check_output(cmd)
            except:
                # the server probably is down so we move the result file to a location another location more suitable for storage (more space and more inodes)
                continue
            out = subprocess.check_output(["rm", ressultFile])
    # try to copy metadata
    toCopy = [HOME_DIR + filename for filename in os.listdir(HOME_DIR) if filename.startswith("metadata_")]
    if len(toCopy) > 0:
        for ressultFile in toCopy:
            if ethernetIP != "":
                cmd = ["rsync", "--address=" + ethernetIP, "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/metadata/"]
            elif modemIP != "":
                cmd = ["rsync", "--address=" + modemIP, "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/metadata/"]
            else:
                cmd = ["rsync", "--compress", "-r", ressultFile, "cloudmap:/home/cloudmap/pending/metadata/"]
            try:
                out = subprocess.check_output(cmd)
            except:
                # the server probably is down so we move the result file to a location another location more suitable for storage (more space and more inodes)
                continue
            out = subprocess.check_output(["rm", ressultFile])
    return


while True:
    copyExperimentalResults()
    time.sleep(1 * 60 * 60)  # we check again in one hour