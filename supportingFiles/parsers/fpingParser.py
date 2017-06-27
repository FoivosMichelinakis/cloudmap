#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import psycopg2


inputDirectory = sys.argv[1] # full path include the filename
experiment_id = sys.argv[2]
inputFile = inputDirectory.split("/")[-1]

(testType, targetdomainname, interface, IpDst, containerTimestamp, nodeId) = inputFile[:-4].split("_")
protocol = "ICMP"
print(testType, targetdomainname, interface, IpDst, containerTimestamp, nodeId)
print(inputFile)

with open(inputDirectory, "r", encoding='utf-8') as inputFileread:
    tracerouteResult = inputFileread.readlines()


try:
    conn = psycopg2.connect("dbname='cloudmap' user='removedUser' host='localhost' password='removedPassword'")
    print("connected!")
except:
    print("I am unable to connect to the database")
    sys.exit(1)

cur = conn.cursor()
# cur.execute("""TRUNCATE cloudmap.pingParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.tracerouteResults CASCADE;""")
# conn.commit()

successfulExperiment = True
if tracerouteResult[-1].find("Failed") >= 0:
    print("This ping experiment failed")
    successfulExperiment = False
    cur.execute("""INSERT INTO cloudmap.pingParameters
    (experiment_id, targetdomainname, interface, IpDst, containerTimestamp, nodeId, successfulExperiment, protocol, filename)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING ping_id;""", 
    [experiment_id, targetdomainname, interface, IpDst, containerTimestamp, nodeId, successfulExperiment, protocol, inputFile])
    conn.commit()
else:
    print("This ping experiment was successful.")
    successfulExperiment = True
    averageStatistics = tracerouteResult[-1].replace("\n", "").split(" ")
    [xmt, rcv, loss] = averageStatistics[4].split("/")
    [minRtt, avgRtt, maxRtt] = averageStatistics[-1].split("/")
    print([experiment_id, targetdomainname, interface, IpDst, containerTimestamp, nodeId, successfulExperiment, protocol, inputFile,
    minRtt, avgRtt, maxRtt, xmt, rcv, loss.replace("%", "")])
    cur.execute("""INSERT INTO cloudmap.pingParameters
    (experiment_id, targetdomainname, interface, IpDst, containerTimestamp, nodeId, successfulExperiment, protocol, filename,
    minRtt, avgRtt, maxRtt, xmt, rcv, loss)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING ping_id;""", 
    [experiment_id, targetdomainname, interface, IpDst, containerTimestamp, nodeId, successfulExperiment, protocol, inputFile,
    minRtt, avgRtt, maxRtt, xmt, rcv, loss.replace("%,", "")])
    conn.commit()
    rows = cur.fetchall()
    ping_id = rows[0][0]
    for line in tracerouteResult:
        if line.find("(") >= 0:
            if line.find("[<") >= 0:
                print("This line seems to be an artifact:")
                print(line)
                continue
            probeElements = line.replace("\n", "").split(" ")
            print(line)
            print([experiment_id, ping_id, probeElements[2].replace("[", "").replace("],", ""),
            probeElements[0], probeElements[3], probeElements[5], probeElements[7].replace("(", "",),
            probeElements[9].replace("%", "")])
            
            cur.execute("""INSERT INTO cloudmap.pingResults
            (experiment_id, ping_id, probeNumber, IP, probeSize, rtt, movingAverageRtt, movingAverageLoss)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""", 
            [experiment_id, ping_id, probeElements[2].replace("[", "").replace("],", ""),
            probeElements[0], probeElements[3], probeElements[5], probeElements[7].replace("(", "",),
            probeElements[9].replace("%", "")])
    conn.commit()

cur.close()
conn.close()
