#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
https://curl.haxx.se/docs/manual.html

PROGRESS METER
 
  The progress meter exists to show a user that something actually is
  happening. The different fields in the output have the following meaning:
 
  % Total    % Received % Xferd  Average Speed          Time             Curr.
                                 Dload  Upload Total    Current  Left    Speed
  0  151M    0 38608    0     0   9406      0  4:41:43  0:00:04  4:41:39  9287
 
  From left-to-right:
   %             - percentage completed of the whole transfer
   Total         - total size of the whole expected transfer
   %             - percentage completed of the download
   Received      - currently downloaded amount of bytes
   %             - percentage completed of the upload
   Xferd         - currently uploaded amount of bytes
   Average Speed
   Dload         - the average transfer speed of the download
   Average Speed
   Upload        - the average transfer speed of the upload
   Time Total    - expected time to complete the operation
   Time Current  - time passed since the invoke
   Time Left     - expected time left to completion
   Curr.Speed    - the average transfer speed the last 5 seconds (the first
                   5 seconds of a transfer is based on less time of course.)
 
  The -# option will display 

Since the above are included in the options we pring at the end of the file, we ignore them and just parse the options at the end of the file.
"""

import sys
import psycopg2
from psycopg2.extensions import AsIs
import os.path
import os
import csv

inputDirectory = sys.argv[1] # full path include the filename
experiment_id = sys.argv[2]
convertDumpToCsv = int(sys.argv[3]) # if a dump exists convert it to csv
insertDumpToDb = int(sys.argv[4]) # if a dump exists convert it to csv and insert it in the database
inputFile = inputDirectory.split("/")[-1]

csvColumnNames = ["frame_number",
"frame_time_epoch",
"frame_len",
"frame_cap_len",
"ip_proto", 
"ip_src",
"tcp_srcport", 
"ip_dst",
"tcp_dstport",
"tcp_stream", 
"tcp_seq", 
"tcp_ack", 
"tcp_flags_res", 
"tcp_flags_ns", 
"tcp_flags_cwr", 
"tcp_flags_ecn", 
"tcp_flags_urg", 
"tcp_flags_ack",
"tcp_flags_push",
"tcp_flags_reset",
"tcp_flags_syn",
"tcp_flags_fin",
"tcp_analysis_acks_frame", 
"tcp_analysis_ack_rtt",
"http_request_uri",
"col_Protocol",
"ssl_record_version",
"ssl_record_content_type",
"ssl_record_length"]


(protocol, targetdomainname, interface, IpDst, containerTimestamp, nodeId) = inputFile[:-5].split("_")

with open(inputDirectory, "r", encoding='utf-8') as inputFileread:
    curlResult = inputFileread.readlines()

metricsList = curlResult[-2].split("\t")

metrics = {
"ssl_verify_result": "N/A",
"http_code": "N/A",
"http_connect": "N/A",
"local_ip": "N/A",
"local_port": "N/A",
"num_redirects": "N/A",
"size_download": "N/A",
"speed_download": "N/A",
"time_appconnect": "N/A",
"time_connect": "N/A",
"time_namelookup": "N/A",
"time_pretransfer": "N/A",
"time_redirect": "N/A",
"time_starttransfer": "N/A",
"time_total": "N/A"
}

for metricKey in metrics.keys():
  if metricKey in metricsList:
    position = metricsList.index(metricKey)
    value = metricsList[position + 1]
    if value.replace(".","").isdigit():
      metrics[metricKey] = value

metrics["experiment_id"] = experiment_id
metrics["protocol"] = protocol
metrics["targetdomainname"] = targetdomainname
metrics["interface"] = interface
metrics["IpDst"] = IpDst
metrics["containerTimestamp"] = containerTimestamp
metrics["nodeId"] = nodeId
metrics["filename"] = inputFile

columnNames = []
values = []

for key, value in metrics.items():
    if value == "N/A":
        continue
    columnNames.append(key)
    values.append(value)

try:
    conn = psycopg2.connect("dbname='cloudmap' user='removedUser' host='localhost' password='removedPassword'")
    print("connected!")
except:
    print("I am unable to connect to the database")
    sys.exit(1)

cur = conn.cursor()
# cur.execute("""TRUNCATE cloudmap.fetchParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.fetchPacketCapture CASCADE;""")
# conn.commit()

insert_statement = 'insert into cloudmap.fetchParameters (%s) values %s RETURNING fetch_id;'

cur.execute(insert_statement, (AsIs(','.join(columnNames)), tuple(values)))

conn.commit()
rows = cur.fetchall()
fetch_id = rows[0][0]
print(fetch_id)


if (convertDumpToCsv == 1) or (insertDumpToDb == 1):
    # check if the dump file exists
    dumpDirectory = inputDirectory[:-5] + ".dump"
    csvDirectory = inputDirectory[:-5] + ".csv"
    if os.path.isfile(dumpDirectory):
        print("converting: ", dumpDirectory)
        conversionCommand = """tshark -t e -V -T fields \
        -e frame.number \
        -e frame.time_epoch \
        -e frame.len \
        -e frame.cap_len \
        -e ip.proto \
        -e ip.src \
        -e tcp.srcport \
        -e ip.dst \
        -e tcp.dstport \
        -e tcp.stream \
        -e tcp.seq \
        -e tcp.ack \
        -e tcp.flags.res \
        -e tcp.flags.ns \
        -e tcp.flags.cwr  \
        -e tcp.flags.ecn  \
        -e tcp.flags.urg \
        -e tcp.flags.ack  \
        -e tcp.flags.push  \
        -e tcp.flags.reset  \
        -e tcp.flags.syn \
        -e tcp.flags.fin \
        -e tcp.analysis.acks_frame \
        -e tcp.analysis.ack_rtt  \
        -e http.request.uri \
        -e _ws.col.Protocol \
        -e ssl.record.version  \
        -e ssl.record.content_type  \
        -e ssl.record.length  \
        -r {} > {}""".format(dumpDirectory, csvDirectory)
        os.system(conversionCommand)
        if (insertDumpToDb == 1):
            with open(csvDirectory, "r", encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    packet = {}
                    packet["experiment_id"] = experiment_id
                    packet["fetch_id"] = fetch_id
                    elements = row[0].split("\t")
                    for i in range(len(elements)):
                        if len(elements[i]) > 0:
                            #print(i, "\t", csvColumnNames[i], "\t", elements[i])
                            if (i >= 12) and (i <= 21):
                                if elements[i] == "0":
                                    packet[csvColumnNames[i]] = False
                                elif elements[i] == "1":
                                    packet[csvColumnNames[i]] = True
                                else:
                                    print("error the value of a flag is not 0 or 1")
                            else:
                                packet[csvColumnNames[i]] = elements[i]
                    columnNames = []
                    values = []
                    for key, value in packet.items():
                        columnNames.append(key)
                        values.append(value)
                    insert_statement = 'insert into cloudmap.fetchPacketCapture (%s) values %s;'
                    cur.execute(insert_statement, (AsIs(','.join(columnNames)), tuple(values)))
                conn.commit()
cur.close()
conn.close()



