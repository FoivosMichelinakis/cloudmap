#!/usr/bin/python
# -*- coding: utf-8     -*-

import sys
import subprocess
import time
import constants


target = sys.argv[1]
interface = sys.argv[2]
containerTimestamp = sys.argv[3]
nodeId = sys.argv[4]
useTcpdump = sys.argv[5]
defaultDnsResolverIP = sys.argv[6]  # if it is "N/A", we do not do experiments with the default interface.
typeOfNode = sys.argv[7]
digClientSubnetFlag = sys.argv[8]
pulicIP = sys.argv[9]


resovlerOutput = {} # in case we need to parse the output to isolate the server IP
IPs = set() # The set of server IPs for the target FQDNs that the dns resolvers return (only IPv4 for now) 

resolvers = {
    "google": [
        "@8.8.8.8",
        "@8.8.4.4"
    ],
    "googleIPv6": [
        "@2001:4860:4860::8888",
        "@2001:4860:4860::8844"
    ],
    "openDNS": [
        "@208.67.222.222",
        "@208.67.220.220",
        "@208.67.222.220",
        "@208.67.220.222"
    ],
    "openDNSIPv6": [
        "@2620:0:ccc::2",
        "@2620:0:ccd::2"
    ],
    "openDNSFamilyShield": [
        "@208.67.222.123",
        "@208.67.220.123"
    ]
}


targetResolvers = ["google", "openDNS"]
resolverIPs = [resolvers[resolver][0] for resolver in targetResolvers]
print resolverIPs
print defaultDnsResolverIP
if (defaultDnsResolverIP not in resolverIPs) and (defaultDnsResolverIP.find(".") >= 0):
    # the default resolver is and IP (there is at least a dot in the string) and is different
    # than the resolvers we would do the experiment so it added in the experiemnt list. 
    targetResolvers.insert(0, "default")
    resolvers["default"] = [defaultDnsResolverIP]
    print "the default resolver will be tested"

print targetResolvers
print ""

# dig part
# There is a case where the dig command might support the subnet flag
# but the operator is blocking it, even when the target resolver does not 
# belong to the operator. so to take this case into account we define the
# digOperatorSubnetFlag. if this is true then both the operator and dig 
# support the flag is not then either of these or both do not support it.

for resolver in targetResolvers:
    digOperatorSubnetFlag = digClientSubnetFlag
    if digOperatorSubnetFlag == "1":
        try:
            clientSubnetParameter = "+subnet=" + pulicIP + "/32"
            cmd = [
                constants.digCommand,
                target,
                resolvers[resolver][0],
                "+noquestion",
                clientSubnetParameter
            ]
            print " ".join([str(element) for element in cmd])
            start = int(time.time())
            resovlerOutput[resolver] = subprocess.check_output(cmd)
            end = int(time.time())
        except:
            cmd = [
            constants.digCommand,
            target,
            resolvers[resolver][0],
            "+noquestion"
            ]
            print " ".join([str(element) for element in cmd])
            start = int(time.time())
            resovlerOutput[resolver] = subprocess.check_output(cmd)
            end = int(time.time())
            digOperatorSubnetFlag = "0"
    else:
        cmd = [
            constants.digCommand,
            target,
            resolvers[resolver][0],
            "+noquestion"
        ]
        print " ".join([str(element) for element in cmd])
        start = int(time.time())
        resovlerOutput[resolver] = subprocess.check_output(cmd)
        end = int(time.time())
    # saving the output to a file.
    filename = "dig_" + str(start) + "_" + str(end) + "_" + \
        target + "_" + interface + "_" + \
        containerTimestamp + "_" + resolver + \
        "_" + nodeId + "_" + digOperatorSubnetFlag + ".txt"
    constants.saveResultFromString(resovlerOutput[resolver], filename)
    # for now IPv4 for IPv6 do the same as below for IPlistV6
    for IP in constants.getServerIPs(resovlerOutput[resolver])["IPlistV4"]:
        IPs.add(IP)

print IPs
# for each IP we do one set of traceroute, tcp, tls, small object fetch and ping experiments
for IP in IPs:
    # traceroute part
    cmd = [
        "traceroute",
        "-n",
        "-i",
        interface,
        IP
    ]
    start = int(time.time())
    tracerouteOutput = subprocess.check_output(cmd)
    end = int(time.time())
    # saving the output to a file.
    filename = "traceroute_" + str(start) + "_" + str(end) + "_" + \
        target + "_" + interface + "_" + IP + "_" + \
        containerTimestamp + \
        "_" + nodeId + ".txt"
    constants.saveResultFromString(tracerouteOutput, filename)
    # tcp small object fetch part
    captureFilenamePort80 = "tcp_" + target + "_" + \
        interface + "_" + IP + "_" + containerTimestamp + \
        "_" + nodeId + ".dump"
    curlFilenamePort80 = captureFilenamePort80.replace(".dump", ".curl")
    cmd = [
        "bash",
        constants.SCRIPT_DIR + "tcpdumpController.sh",
        interface,
        IP,
        "80",
        captureFilenamePort80,
        constants.SCRIPT_DIR + "fetchObjects.py",
        target,
        "tcp",
        curlFilenamePort80,
        useTcpdump
    ]
    tcpFetchOutput = subprocess.check_output(cmd)
    if useTcpdump == "yes":
        constants.saveResultFromFile(captureFilenamePort80)
    constants.saveResultFromFile(curlFilenamePort80)
    # tls small object fetch part
    captureFilenamePort443 = "tls_" + target + "_" + \
        interface + "_" + IP + "_" + containerTimestamp + \
        "_" + nodeId + ".dump"
    curlFilenamePort443 = captureFilenamePort443.replace(".dump", ".curl")
    cmd = [
        "bash",
        constants.SCRIPT_DIR + "tcpdumpController.sh",
        interface,
        IP,
        "443",
        captureFilenamePort443,
        constants.SCRIPT_DIR + "fetchObjects.py",
        target,
        "tls",
        curlFilenamePort443,
        useTcpdump
    ]
    tlsFetchOutput = subprocess.check_output(cmd)
    if useTcpdump == "yes":
        constants.saveResultFromFile(captureFilenamePort443)
    constants.saveResultFromFile(curlFilenamePort443)
    # ping part
    pingFilename = "fping_" + target + "_" + \
        interface + "_" + IP + "_" + containerTimestamp + \
        "_" + nodeId + ".txt"
    cmd = [
        "fping",
        "-c",
        "10",
        "-i",
        "250", # ms
        "-I",
        interface,
        IP
    ]
    try:
        pingOutput = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        constants.saveResultFromString(pingOutput, pingFilename)
    except:
        pingOutput = "Failed"
        constants.saveResultFromString(pingOutput, pingFilename)