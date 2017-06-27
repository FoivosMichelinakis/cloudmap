#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import psycopg2
from psycopg2.extensions import AsIs
import os
import json
import shutil
import time


PENDING_DIR = "/home/cloudmap/pending/metadata/"
IMPORTED_DIR = PENDING_DIR.replace("pending", "imported")

while True:
    pendingResultFiles = os.listdir(PENDING_DIR)

    try:
        conn = psycopg2.connect("dbname='cloudmap' user='removedUser' host='localhost' password='removedPassword'")
        print("connected!")
    except:
        print("I am unable to connect to the database")
        sys.exit(1)

    cur = conn.cursor()
    # cur.execute("""TRUNCATE cloudmap.metadata CASCADE;""")
    # conn.commit()

    for inputFile in pendingResultFiles:
        (metadatString, nodeId, LoggerTimestamp) = inputFile[:-4].split("_")
        print(metadatString, nodeId, LoggerTimestamp)
        with open(PENDING_DIR + inputFile, "r", encoding='utf-8') as inputFileread:
            metadataResult = inputFileread.readlines()
        for element in metadataResult:
            try:
                entry = json.loads(element.replace("\n", ""))
            except:
                print(element)
                continue
            del entry["DataId"]
            del entry["DataVersion"]
            temp = entry["Timestamp"]
            del entry["Timestamp"]
            entry["timestampNode"] = temp
            entry["nodeId"] = nodeId
            columnNames = []
            values = []
            if len(entry["Operator"]) > 20:
                entry["Operator"] = entry["Operator"][:20]
            for key, value in entry.items():
                columnNames.append(key)
                values.append(value)
            insert_statement = 'insert into cloudmap.metadata (%s) values %s;'
            try:
                cur.execute(insert_statement, (AsIs(','.join(columnNames)), tuple(values)))
            except psycopg2.IntegrityError:
                print("duplicate entry. Ignoring.......")
                conn.rollback()
            else:
                conn.commit()
        shutil.move(PENDING_DIR + inputFile, IMPORTED_DIR + inputFile)
    cur.close()
    conn.close()
    time.sleep(10* 60) # some delays to avoid maxing out the processor in case there are no metadata files to be imported

