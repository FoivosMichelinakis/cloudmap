#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Foivos Michelinakis
# Date: February 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project


"""
An example "Additional options" JSON string that can be used with this container is:

"interfaces": ["op0", "op1", "op2"], "targets": ["www.ntua.gr", "www.uc3m.es", "Google.com", "Facebook.com", "Youtube.com", "Baidu.com", "Yahoo.com", "Amazon.com", "Wikipedia.org", "audio-ec.spotify.com", "mme.whatsapp.net", "sync.liverail.com", "ds.serving-sys.com", "instagramstatic-a.akamaihd.net"], "maxNumberOfInstances": 5, "executionMode": "parallel"

ip -d l -> mifis use macvlan, the other one uses veth
"""

import json
import sys
import time
import subprocess
import os
import shutil
import constants
import copy
import socket
import fcntl
import struct


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

containerTimestamp = str(int(time.time()))
usingDefaults = constants.usingDefaults  # in case the configurationfile is inaccessible

try:
    with open(constants.CONFIG_FILE, "r") as fd:
        configurationParameters = json.load(fd)
except Exception as e:
    print "Cannot retrive constants.CONFIG_FILE {}".format(e)
    print "Using default parameters......."
    configurationParameters = {}
    usingDefaults = True

try:
    with open("/nodeid", "r") as nodeIdFile:
        nodeidTemp = nodeIdFile.readlines()
        nodeId = nodeidTemp[0].strip()
except:
    nodeId = str(configurationParameters.get("nodeid", constants.nodeId))
interfaces = configurationParameters.get("interfaces", constants.interfaces)
targets = configurationParameters.get("targets", constants.targets)
# executionMode = configurationParameters.get("executionMode", constants.executionMode) # serially, serialPerInterface, parallel
maxNumberOfInstances = configurationParameters.get(
    "maxNumberOfInstances", constants.maxNumberOfInstances
    )
useTcpdump = configurationParameters.get("useTcpdump", constants.useTcpdump)
typeOfNode = configurationParameters.get("typeOfNode", constants.typeOfNode)
mccmnc = configurationParameters.get("mccmnc", constants.mccmnc)
standaloneNode = configurationParameters.get("standaloneNode", constants.standaloneNode)
containerPause = configurationParameters.get("containerPause", constants.containerPause)

if containerPause > 0:
    time.sleep(containerPause)


print "nodeId: " + str(nodeId)
print "interfaces: " + str(" ".join(interfaces))
print "targets: " + str(" ".join(targets))
print "maxNumberOfInstances: " + str(maxNumberOfInstances)
print "usingDefaults: " + str(usingDefaults)
print "mccmnc: " + str(" ".join(mccmnc))
print "standaloneNode: " + str(standaloneNode)

def getDefaultGetways(interfaces):
    import re
    defaultGatewayLine = re.compile(r'default via (\S+) dev (\S+)')
    defaultGateways = {}
    cmd = ["ip", "rule", "list"]
    output = subprocess.check_output(cmd)
    ipTables = set()
    for line in output.split("\n"):
        ipTables.add(line.strip().split(" ")[-1])
    ipTables.remove("")
    for ipTable in ipTables:
        cmd = ["ip", "route", "show", "table", ipTable]
        output = subprocess.check_output(cmd)
        for line in output.split("\n"):
            if defaultGatewayLine.search(line):
                (gateway, interface) = defaultGatewayLine.search(line).groups()
                if interface in interfaces:
                    defaultGateways[interface] = gateway
    return defaultGateways


def changeDefaultInterface(defaultGateways, interface):
    """
    first we delete the default routes but only if they exists  
    and then we add once the route we want
    """
    output_interface = None
    cmd0 = ["ip", "route", "show",  "default"]
    routingTable = subprocess.check_output(cmd0)
    while routingTable.find("default") >= 0:
        cmd1 = ["route", "del", "default"]
        try:
            subprocess.check_output(cmd1)
        except subprocess.CalledProcessError as e:
            if e.returncode == 28:
                print "Time limit exceeded"
        routingTable = subprocess.check_output(cmd0)
    gw_ip = defaultGateways[interface]
    cmd2 = ["route", "add", "default", "gw", gw_ip, interface]
    try:
        subprocess.check_output(cmd2)
        cmd3 = ["ip", "route", "get", "8.8.8.8"]
        output = subprocess.check_output(cmd3)
        output = output.strip(' \t\r\n\0')
        output_interface = output.split(" ")[4]
        if output_interface == interface:
            print "Source interface is set to " + interface
        else:
            return True  # the experiment is cancelled for this interface
    except subprocess.CalledProcessError as e:
        if e.returncode == 28:
            print "Time limit exceeded"
        return True  # the experiment is cancelled for this interface
    return False  # the experiment can continue for this interface


def getTypeOfModem(targetInterfaces):
    typeOfModem = {}
    if standaloneNode == "yes":
        for interface in targetInterfaces:
            typeOfModem[interface] = "mifi"
        return typeOfModem
    cmd = ["ip", "-d", "l"]
    out = subprocess.check_output(cmd)
    currentInterface = ""
    for line in out.splitlines():
        for interface in targetInterfaces:
            stringToMatch = ": " + interface
            if stringToMatch in line:
                currentInterface = interface
        if currentInterface not in interfaces:
            continue
        if "macvlan" in line:
            print "{} is mifi".format(currentInterface)
            typeOfModem[currentInterface] = "mifi"
        if "veth" in line:
            print "{} is new node design".format(currentInterface)
            typeOfModem[currentInterface] = "newDesign"
    for interface in targetInterfaces:
        if interface not in typeOfModem.keys():
            typeOfModem[interface] = "N/A"
    return typeOfModem


# check if dig supports the client-subnet flag (version of fig 9.10 and 9.11)
cmd = [constants.digCommand, "-v"]
output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
(digVersionMajor, digVersionMinor, digVersionBug) = output.split(" ")[1].split("-")[0].split(".")
if (int(digVersionMajor) >= 9) and (int(digVersionMinor) >= 10):
    print "the dig version is {}.{}.{} and supports the client-subnet flag".format(digVersionMajor, digVersionMinor, digVersionBug)
    digClientSubnetFlag = 1
else:
    print "the dig version is {}.{}.{} and does NOT support the client-subnet flag".format(digVersionMajor, digVersionMinor, digVersionBug)
    digClientSubnetFlag = 0


def getPulicIP():
    if typeOfNode == "Monroe":
        # I guess in this case we use the metadata.
        # maybe it would be better to use the insdie the carrier grade nat to to get the IP
        # TODO implement metadata way to get the public IP.
        cmd = ["curl", "ipinfo.io/ip"]
        PublicIP = subprocess.check_output(cmd).replace("\n", "")
        return PublicIP
    elif typeOfNode == "testing" or typeOfNode == "server":
        cmd = ["curl", "ipinfo.io/ip"]
        PublicIP = subprocess.check_output(cmd).replace("\n", "")
        return PublicIP


def prioritizeInterfaces(mccmnc, interfaces):
    """
    1) Arrange the order that the interfaces will be used based
    on the mccmnc preference sequence in the config file
    2) create an interface topology file to be inlcuded in the results,
    so that we canassociate offline the interface used with the operator
    """
    import zmq
    interfaceTopology = {}
    mccmncOperatorMapping = {}
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://172.17.0.1:5556")
    topicfilter = "MONROE.META.DEVICE.MODEM"
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
    startListening = time.time()
    while True:
        string = socket.recv()
        metaData = json.loads(string[string.find("{"):])
        if (metaData.get("InternalInterface", "No") in interfaces) and (str(metaData.get("IMSIMCCMNC", "No")) in mccmnc):
            intInterface = metaData.get("InternalInterface", "No")
            interfaceTopology[intInterface] = copy.deepcopy(metaData)
            mccmncOperatorMapping[str(metaData.get("IMSIMCCMNC", "No"))] = metaData.get("InternalInterface", "No")
        if ( (time.time() - startListening) > (2*60) ) or ( len(mccmncOperatorMapping.keys()) == len(interfaces) ):
            print mccmncOperatorMapping
            constants.saveTopologyFile(interfaceTopology)
            return [mccmncOperatorMapping[key] for key in mccmnc if key in mccmncOperatorMapping.keys()]

def compressResults(numberOfResultFiles):
    if standaloneNode == "yes":
        resultFilesList = [constants.RESULTS_DIR + element for element in os.listdir(constants.RESULTS_DIR) if ( (os.path.isfile(constants.RESULTS_DIR + element)) and (not element.endswith("tmp")) and (not element.endswith("gz")) and (not element.startswith("lost")) )]
        if len(resultFilesList) > numberOfResultFiles:
            archieveTimstamp = interface + "_" + str(int(time.time()))
            cmd = ["tar", "-czvf", constants.RESULTS_DIR + archieveTimstamp + ".tar.gz"]
            for element in resultFilesList:
                cmd.append(element)
            output = subprocess.check_output(cmd)
            print output
            for element in resultFilesList:
                os.remove(element)

# main part
startTime = time.time()
print "startTime: " + str(startTime)

defaultGateways = getDefaultGetways(interfaces)
# check which interfaces are present and run the experiment only on these, Also check whice interfaces have a 
# default gateway and run the experiment in only these (without the default gateway, we can not change the routing table
# thus there is not point to run the experiment in such an interface)
cmd = ["netstat", "-i"]
output = subprocess.check_output(cmd)
activeInterfaces = [element.strip().split(" ")[0] for element in output.split("\n")[2:-1]]
interfacesWithDefaultGateway = list(set(interfaces).intersection(defaultGateways.keys()))
experimentInterfaces = list(set(interfacesWithDefaultGateway).intersection(activeInterfaces))

if typeOfNode == "Monroe":
    # copy the configuration file to the results
    if standaloneNode == "no":
        shutil.copy2(constants.CONFIG_FILE, constants.RESULTS_DIR + "config.tmp")
        shutil.move(constants.RESULTS_DIR + "config.tmp", constants.RESULTS_DIR + "config")
    typeOfModem = getTypeOfModem(experimentInterfaces)
    if ( (len(mccmnc) != 0) and (standaloneNode == "no") ):
        # prioritize the interfaces based on the order specified in mccmnc
        safeguard = copy.deepcopy(experimentInterfaces)
        try:
            experimentInterfaces = prioritizeInterfaces(mccmnc, experimentInterfaces)
        except:
            experimentInterfaces = safeguard

defaultDnsRerolvers = {}
for interface in experimentInterfaces:
    if typeOfNode == "Monroe":
        try:
            if typeOfModem[interface] == "mifi":
                defaultDnsRerolvers[interface] = "@" + defaultGateways[interface] # use the IP of the mifi as a resolver with the correct routing! -- after changing the default route
            if typeOfModem[interface] == "newDesign":
                # launch the Dchp discover method TODO
                defaultDnsRerolvers[interface] = "N/A" # in the end this will be an IP
            if typeOfModem[interface] == "N/A":
                defaultDnsRerolvers[interface] = "N/A"
        except KeyError:
            print "it is not possible to detect the type of modem in the context of a monroe node"
            print "the typeOfModem is not set"
            defaultDnsRerolvers[interface] = "N/A" # we can not define a dns resolver. the experiments will run only on the rest of the resolvers
    elif typeOfNode == "testing" or typeOfNode == "server":
        cmd = ["cat", "/etc/resolv.conf"]
        output = subprocess.check_output(cmd)
        nameservers = []
        for line in output.splitlines():
            if line.startswith("#"):
                continue
            words = line.split(" ")
            if words[0] == "nameserver":
                nameservers.append(words[1])
        if len(nameservers) > 0:
            defaultDnsRerolvers[interface] = "@" + nameservers[0]
        else:
            defaultDnsRerolvers[interface] = "N/A"


print activeInterfaces
print ""
print experimentInterfaces
print ""
print defaultGateways
print ""
print defaultDnsRerolvers
print ""

print "entering the loop"
for interface in experimentInterfaces:
    print interface
    # first we make sure all the packets exit through that specific interface
    if typeOfNode == "Monroe": # modify the routing table only in case a monroe node is used.
        print "1"
        if changeDefaultInterface(defaultGateways, interface):
            print "2"
            # if the change of the routing table failed we do not do the experiment
            continue
    pulicIP = getPulicIP()
    print "3"
    processes = []
    for target in targets:
        print target
        while len(processes) >= maxNumberOfInstances:
            # we do the checks every one second to avoid maxing out the processor for no reason
            time.sleep(1)
            for pr in processes:
                # A None value indicates that the process hasn’t terminated yet.
                if pr.poll() != None:
                    processes.remove(pr)
        print "4"
        compressResults(5000)
        cmd = [
            "python",
            constants.SCRIPT_DIR + "individualExperiment.py",
            target,
            interface,
            containerTimestamp,
            nodeId,
            useTcpdump,
            defaultDnsRerolvers[interface],
            typeOfNode,
            str(digClientSubnetFlag),
            pulicIP
        ]
        print "before"
        print " ".join([str(element) for element in cmd])
        print "after"
        processes.append(subprocess.Popen(cmd))
    # waiting the last set of experiments to finish
    for pr in processes:
        pr.wait()
    compressResults(0)


endTime = time.time()
print "endTime: " + str(endTime)
print "duration: " + str(endTime - startTime)
#print "sleeping" # in case we need to debug, we add a delay in the end so  that the container does not exit right away and we can log it ot it
#time.sleep(10000)
