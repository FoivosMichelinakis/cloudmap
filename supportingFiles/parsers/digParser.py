#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import sys
import psycopg2
from psycopg2.extensions import AsIs

experiment_id = 0
resolver = 0
resolverIP = 0
target = 0
publicIPSubnet = "0.0.0.0"
digversion = 0
startTime = 0
endTime = 0
inputFile = 0
ednsVersion = 0
protocol = 0
overallSize = 0
clientSubnetSupport = False
queryTime = 0
time = 0
messageSize = 0
server = 0
digClientSubnetFlag = "0"
dnsSecSupport = False






# regular expressions
answerLine = re.compile(r'(\S+)\s*(\d+)\s*IN\s*(\S+)\s*(\S+)')
pseudosectionLine = re.compile(r'; EDNS: version: (\d+), flags: ?(\S+)?; (\S+): (\d+)')
answerSectionHeader = re.compile(r';;\s*ANSWER\s*SECTION:')
questionSectionHeader = re.compile(r';;\s*QUESTION\s*SECTION:')
optSectionHeader = re.compile(r';;\s*OPT\s*PSEUDOSECTION:')
authoritySectionHeader = re.compile(r';;\s*AUTHORITY\s*SECTION:')
additionalSectionHeader = re.compile(r';;\s*ADDITIONAL\s*SECTION:')

print("1")

inputDirectory = sys.argv[1] # full path include the filename
experiment_id = sys.argv[2]
inputFile = inputDirectory.split("/")[-1]
print("2")
(testType, startTime, endTime, target, interface, containerTimestamp, resolver, nodeId, digClientSubnetFlag) = inputFile[:-4].split("_")
print("3")
print(testType, startTime, endTime, target, interface, containerTimestamp, resolver, nodeId, digClientSubnetFlag)



metrics = {}
metrics["experiment_id"] = experiment_id
metrics["startTime"] = startTime
metrics["endTime"] = endTime
metrics["target"] = target
metrics["interface"] = interface
metrics["containerTimestamp"] = containerTimestamp
metrics["resolverName"] = resolver
metrics["nodeId"] = nodeId
metrics["digClientSubnetFlag"] = {"0": False, "1": True}.get(digClientSubnetFlag)
metrics["filename"] = inputFile


with open(inputDirectory, "r", encoding='utf-8') as inputFileread:
    digResult = inputFileread.readlines()

line = digResult[1]

elements = line.split(" ")
digversion = elements[3].split("-")[0]
metrics["digversion"] = digversion
for ele in elements[5:]:
    if ele.startswith("@"):
        resolverIP = ele[1:]
        metrics["resolverIP"] = resolverIP
        continue
    if ele.startswith("+subnet="):
        publicIPSubnet = ele[ele.find("=") + 1:].split("/")[0]
        metrics["publicIPSubnet"] = publicIPSubnet
        continue
    if ele.find(".") >= 0:
        target = ele
        #metrics["target"] = target
        continue

if digResult[7].find("PSEUDOSECTION") >= 0:
    # the PSEUDOSECTION is present and we parse it
    line = digResult[8]
    (ednsVersion, flags, protocol, overallSize) = pseudosectionLine.search(line).groups()
    if digResult[9].find("CLIENT-SUBNET") >= 0:
        #print("CLIENT-SUBNET")
        clientSubnetSupport = True
        lines = digResult[10:]
    else:
        #print("NO")
        clientSubnetSupport = False
        lines = digResult[9:]
    try:
        if flags.find("do") >= 0:
            dnsSecSupport = "yes"
        else:
            dnsSecSupport = "no"
    except:
        dnsSecSupport = "error"
else:
    dnsSecSupport = "N/A"
    (ednsVersion, flags, protocol, overallSize) = (-1, -1, -1, -1)
    clientSubnetSupport = False # if it had there would  be a pseudosection
    lines = digResult[7:]

metrics["EDNS"] = ednsVersion
#metrics["flags"] = flags
metrics["protocol"] = protocol
metrics["acceptedSize"] = overallSize
metrics["clientSubnetSupport"] = clientSubnetSupport
metrics["dnsSecSupport"] = dnsSecSupport


sections = {
    "ans": [],
    "que": [],
    "auth": [],
    "add": [],
}

section = ""
for line in lines:
    #print(line)
    if answerSectionHeader.search(line):
        section = "ans"
    if questionSectionHeader.search(line):
        section = "que"
    if authoritySectionHeader.search(line):
        section = "auth"
    if additionalSectionHeader.search(line):
        section = "add"
    if line.startswith(";; Query time:"):
        break
    if answerLine.search(line):
        (leftSide, TTL, typeOfRecord, rightSide) = answerLine.search(line).groups()
        sections[section].append(
        {"leftSide": leftSide,
         "TTL": TTL,
         "typeOfRecord": typeOfRecord,
         "rightSide": rightSide
            }
        )
        # print(section)
        # print(leftSide)
        # print(TTL)
        # print(typeOfRecord)
        # print(rightSide)

queryTime = lines[-5].split(" ")[3].strip()
server = lines[-4].split(" ")[2].strip()
time = lines[-3][lines[-3].find(": ") + 2:].strip()
messageSize = lines[-2].split(" ")[-1].strip()

metrics["queryTime"] = queryTime
metrics["server"] = server
metrics["when_human"] = time
metrics["msgsize"] = messageSize

# print(digversion)
# print(resolverIP)
# print(publicIPSubnet)
# print(target)
# print(ednsVersion)
# print(flags)
# print(protocol)
# print(overallSize)
# print(messageSize)
# print(time)
# print(resolver)
# print(queryTime)

try:
    conn = psycopg2.connect("dbname='cloudmap' user='removedUser' host='localhost' password='removedPassword'")
    print("connected!")
except:
    print("I am unable to connect to the database")
    sys.exit(1)

cur = conn.cursor()
# cur.execute("""TRUNCATE cloudmap.digParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.digResults CASCADE;""")
conn.commit()


columnNames = []
values = []

for key, value in metrics.items():
    columnNames.append(key)
    values.append(value)

insert_statement = 'insert into cloudmap.digParameters (%s) values %s RETURNING dig_id;'

cur.execute(insert_statement, (AsIs(','.join(columnNames)), tuple(values)))

conn.commit()
rows = cur.fetchall()
dig_id = rows[0][0]
print(dig_id)


for key, value in sections.items():
    for element in value:
        cur.execute("""INSERT INTO cloudmap.digResults
        (experiment_id, dig_id, section, leftArgument, TTL, recordType, rightArgument)
        VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
        [experiment_id, dig_id, key, element["leftSide"], element["TTL"], element["typeOfRecord"], element["rightSide"]])

conn.commit()
cur.close()
conn.close()

"""
rewrite to be able to parse properly the following where the DNS IP have the same line format
as the content server IPs
also try to parse when the flags option has the parameter do


; <<>> DiG 9.9.5-3ubuntu0.13-Ubuntu <<>> graph.facebook.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 56885
;; flags: qr rd ra; QUERY: 1, ANSWER: 3, AUTHORITY: 2, ADDITIONAL: 3

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;graph.facebook.com.		IN	A

;; ANSWER SECTION:
graph.facebook.com.	475	IN	CNAME	api.facebook.com.
api.facebook.com.	480	IN	CNAME	star.c10r.facebook.com.
star.c10r.facebook.com.	28	IN	A	31.13.68.12

;; AUTHORITY SECTION:
c10r.facebook.com.	3387	IN	NS	b.ns.c10r.facebook.com.
c10r.facebook.com.	3387	IN	NS	a.ns.c10r.facebook.com.

;; ADDITIONAL SECTION:
b.ns.c10r.facebook.com.	399	IN	A	69.171.255.11
b.ns.c10r.facebook.com.	399	IN	AAAA	2a03:2880:ffff:b:face:b00c:0:99

;; Query time: 8 msec
;; SERVER: 127.0.1.1#53(127.0.1.1)
;; WHEN: Tue Feb 28 10:02:07 KST 2017
;; MSG SIZE  rcvd: 184
"""



