#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import sys
import collections
import psycopg2

IPv4_RE = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
IPv4WithParenthesis_RE = re.compile(r'^\((?:[0-9]{1,3}\.){3}[0-9]{1,3}\)$')
characterExists_re = re.compile(r'([A-Za-z]+)')
float_re = re.compile(r'\d+\.\d+')
int_re = re.compile(r'\d+')
HEADER_RE = re.compile(r'traceroute to (\S+) \((\d+\.\d+\.\d+\.\d+)\), ([0-9]+) hops max, ([0-9]+) byte packets')

inputDirectory = sys.argv[1] # full path include the filename
experiment_id = sys.argv[2]
hostnameResolution = sys.argv[3] # if "no" the "-n" flag was used while running the command
inputFile = inputDirectory.split("/")[-1]

(testType, startTime, endTime, targetdomainname, interface, IpDst, containerTimestamp, nodeId) = inputFile[:-4].split("_")
protocol = "NA"

with open(inputDirectory, "r", encoding='utf-8') as inputFileread:
    tracerouteResult = inputFileread.readlines()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def parseSimpleTraceroute(lines):
    while lines[0].startswith("[WARN]"):
        lines.pop(0)

    if (lines[0].find("Name or service not known") >= 0) or (lines[0].find("ERROR") >= 0):
        print("broken traceroute")
        return

    hops = collections.OrderedDict()

    header = lines[0].split()
    if header[0] != "traceroute" or header[1] != "to":
        print("failed to parse header. Header does not have standard format")
        return
    (NameDst, IpDst, numberOfHops, sizeOfProbes) = (header[2], header[3][1:-2], header[4], header[7])
    hops["header"] = (NameDst, IpDst, numberOfHops, sizeOfProbes)
    
    # parse the hop lines
    HopCount = 0
    for line in lines[1:]:
        if len(line) == 0:  # check if the line is empty
            continue
        HopCount += 1
        elements = line.split()
        hopNumber = elements.pop(0)
        hops[hopNumber] = {}
        lastIPFound = ""
        while len(elements) > 0:
            if elements[0] == "*":
                elements.pop(0)
                continue
            elif IPv4_RE.match(elements[0]) or \
            IPv4WithParenthesis_RE.match(elements[0]) or \
            (elements[0].find(":") >= 0) or \
            ((characterExists_re.search(elements[0])) and (elements[0].find(":") < 0)):
                if hostnameResolution == "yes":
                    #IPv4 or IPv6 or Name (Human readable)
                    if (elements[0].find("(") < 0) and \
                        (elements[1].find("(") >= 0) and \
                        (float_re.match(elements[2]) or int_re.match(elements[2])) and \
                        (elements[3] == "ms"):
                        
                        HopName = elements[0]
                        HopIp = elements[1]
                        lastIPFound = elements[1]
                        HopRTT = int(1000 * float(elements[2])) # The RTT value has to be an interger in order to enter the database, so it is stored as us
                        if len(elements) >= 5 and (not is_number(elements[4])) and elements[4] != "*" and (elements[4].find("!") >= 0):
                            # This probe has an annotation that we have to keep track of
                            annotation = elements[4]
                            if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                                hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                                hops[hopNumber][HopIp]["annotation"].append(annotation)
                            else:
                                hops[hopNumber][HopIp] = {
                                "HopName": HopName,
                                "HopRTT": [HopRTT],
                                "annotation": [annotation]
                                }
                            elements = elements[5:]
                            continue
                        elements = elements[4:]
                        if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                            hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                            hops[hopNumber][HopIp]["annotation"].append(0)
                        else:
                            hops[hopNumber][HopIp] = {
                            "HopName": HopName,
                            "HopRTT": [HopRTT],
                            "annotation": [0]
                            }
                    else:
                        print("parse failure at hop: %d" % (HopCount))
                        #user_input = raw_input("Some input please: ")
                        break # it breaks the while. If we fail at a hop, we continue at the next one.
                if hostnameResolution == "no":
                    if  (float_re.match(elements[1]) or int_re.match(elements[1])) and \
                        (elements[2] == "ms"):
                        HopIp = elements[0]
                        lastIPFound = elements[0]
                        HopRTT = int(1000 * float(elements[1])) # The RTT value has to be an interger in order to enter the database, so it is stored as us
                        if len(elements) >= 4 and (not is_number(elements[3])) and elements[3] != "*" and (elements[3].find("!") >= 0):
                            # This probe has an annotation that we have to keep track of
                            annotation = elements[3]
                            if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                                hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                                hops[hopNumber][HopIp]["annotation"].append(annotation)
                            else:
                                hops[hopNumber][HopIp] = {
                                "HopRTT": [HopRTT],
                                "annotation": [annotation]
                                }
                            elements = elements[4:]
                            continue
                        elements = elements[3:]
                        if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                            hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                            hops[hopNumber][HopIp]["annotation"].append(0)
                        else:
                            hops[hopNumber][HopIp] = {
                            "HopRTT": [HopRTT],
                            "annotation": [0]
                            }
                    else:
                        print("parse failure at hop: %d" % (HopCount))
                        #user_input = raw_input("Some input please: ")
                        break # it breaks the while. If we fail at a hop, we continue at the next one.
            elif (float_re.match(elements[0]) or int_re.match(elements[0])) and \
            (elements[1] == "ms"):
                # probe of the same IP address
                try:
                    if len(elements) >= 3 and (not is_number(elements[2])) and elements[2] != "*" and (elements[2].find("!") >= 0):
                        hops[hopNumber][lastIPFound]["HopRTT"].append(int(1000 * float(elements[0])))
                        hops[hopNumber][lastIPFound]["annotation"].append(elements[2])
                        elements = elements[3:]
                        continue
                    hops[hopNumber][lastIPFound]["HopRTT"].append(int(1000 * float(elements[0])))
                    hops[hopNumber][lastIPFound]["annotation"].append(0)
                    elements = elements[2:]
                except:
                    print("Not able to associate an RTT value with an  IP for hop: %s" % (hopNumber))
                    continue
    return hops


hops = parseSimpleTraceroute(tracerouteResult)

try:
    conn = psycopg2.connect("dbname='cloudmap' user='removedUser' host='localhost' password='removedPassword'")
    print("connected!")
except:
    print("I am unable to connect to the database")
    sys.exit(1)

cur = conn.cursor()
# cur.execute("""TRUNCATE cloudmap.tracerouteParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.tracerouteResults CASCADE;""")
# conn.commit()



cur.execute("""INSERT INTO cloudmap.tracerouteParameters
(experiment_id, startTime, endTime, targetdomainname, interface, IpDst, numberOfHops, sizeOfProbes, protocol, containerTimestamp, nodeId, filename)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING traceroute_id;""", 
[experiment_id, startTime, endTime, targetdomainname, interface, IpDst, hops["header"][2], hops["header"][3], protocol, containerTimestamp, nodeId, inputFile ])

conn.commit()
rows = cur.fetchall()
traceroute_id = rows[0][0]

print(traceroute_id)

for key, value in hops.items():
    if key == "header":
        continue
    for IP, parameters in value.items():
        cur.execute("""INSERT INTO cloudmap.tracerouteResults
        (experiment_id, traceroute_id, hop, IP, RTTSection, annotationSection)
        VALUES (%s, %s, %s, %s, %s, %s);""", 
        [experiment_id, traceroute_id, key, IP, parameters['HopRTT'], parameters['annotation']])

conn.commit()
cur.close()
conn.close()






