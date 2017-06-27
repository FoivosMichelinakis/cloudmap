#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import collections
import psycopg2

resultDirectory = sys.argv[1] # import all the files 
convertDumpToCsv = 1 # if a dump exists convert it to csv
insertDumpToDb = 1 # if a dump exists convert it to csv and insert it in the database

# check if the name has underscores and change it. like invenio_tracking_
files = [ele for ele in os.listdir(resultDirectory)]
for filename in files:
    if filename.find("invenio_tracking_") >= 0:
        os.rename(resultDirectory + filename, resultDirectory + filename.replace("invenio_tracking_", "invenio.tracking."))
files = [ele for ele in os.listdir(resultDirectory) if ( (os.path.isfile(resultDirectory + ele)) and ( ( ele.endswith(".txt")) or ( ele.endswith(".curl")) )  )]


# every element of experiments dict will be a list of all the epxeriments created from an execution of 
# the individualExperiment.py The idea is to import all the files of an single experiment instance at the same time.
experiments = collections.defaultdict(list)
for filename in files:
    if filename.startswith("dig"):
        (testType, start, end, target, interface, containerTimestamp, resolver, nodeId, digClientSubnetFlag) = filename[:-4].split("_")
    elif filename.startswith("traceroute"):
        (testType, start, end, target, interface, IP, containerTimestamp, nodeId) = filename[:-4].split("_")
    elif filename.startswith("tcp") or filename.startswith("tls"):
        (testType, target, interface, IP, containerTimestamp, nodeId) = filename[:-5].split("_")
    elif filename.startswith("fping"):
        (testType, target, interface, IP, containerTimestamp, nodeId) = filename[:-4].split("_")
    else:
        pass
    experiments[(target, interface, containerTimestamp, nodeId)].append(filename)

try:
    conn = psycopg2.connect("dbname='cloudmap' user='removedUser' host='localhost' password='removedPassword'")
    print("connected!")
except:
    print("I am unable to connect to the database")
    sys.exit(1)

cur = conn.cursor()

# cur.execute("""TRUNCATE cloudmap.experiment CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.inventory CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.digParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.digResults CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.tracerouteParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.tracerouteResults CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.pingParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.pingResults CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.fetchParameters CASCADE;""")
# cur.execute("""TRUNCATE cloudmap.fetchPacketCapture CASCADE;""")
# conn.commit()


for key, value in experiments.items():
    print(key)
    cur.execute("""SELECT experiment_id FROM cloudmap.experiment WHERE target = %s AND interface = %s AND containerTimestamp = %s AND nodeId = %s;""", [key[0], key[1], key[2], key[3]]) 
    rows = cur.fetchall()
    if rows == []:
        cur.execute("""INSERT INTO cloudmap.experiment (target, interface, containerTimestamp, nodeId) VALUES (%s, %s, %s, %s) RETURNING experiment_id;""", [key[0], key[1], key[2], key[3]])
        rows = cur.fetchall()
    else:
        experiment_id = rows[0][0]
        print("The experiment has already been inserted with experiment_id %s", experiment_id)
        print("The related files will not be added to the database")
        continue
    experiment_id = rows[0][0]
    print("""Importing the experiments of {} with experiment_id {}""".format("_".join(list(key)), experiment_id))
    conn.commit()
    for filename in [fi for fi in value if fi.startswith("dig")]:
        #continue # REMOVE THIS BEGORE PUSHING Maybe check if it has already been imported and cancel otherwise
        print("Importing ", filename)
        cmd = [
            "python3",
            "digParser.py",
            resultDirectory + filename,
            str(experiment_id)
        ]
        #output = subprocess.check_output(cmd)
        pipes = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_out, std_err = pipes.communicate()
        if pipes.returncode != 0:
            print("an error happened!")
            err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            if err_msg.find("duplicate key value violates unique constraint") >= 0:
                print("This file seems to be in the database already based on the Uniuqe constraint of the related table")
                print(cmd[2].split("/")[-1])
                print("Ignoring................")
            else:
                continue
                raise Exception(err_msg)
    for filename in [fi for fi in value if fi.startswith("traceroute")]:
        print("Importing ", filename)
        #continue # REMOVE THIS BEGORE PUSHING Maybe check if it has already been imported and cancel otherwise
        cmd = [
            "python3",
            "tracerouteParser.py",
            resultDirectory + filename,
            str(experiment_id),
            "no"
        ]
        #output = subprocess.check_output(cmd)
        pipes = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_out, std_err = pipes.communicate()
        if pipes.returncode != 0:
            print("an error happened!")
            err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            if err_msg.find("duplicate key value violates unique constraint") >= 0:
                print("This file seems to be in the database already based on the Uniuqe constraint of the related table")
                print(cmd[2].split("/")[-1])
                print("Ignoring................")
            else:
                continue
                raise Exception(err_msg)
    for filename in [fi for fi in value if fi.startswith("fping")]:
        print("Importing ", filename)
        #continue # REMOVE THIS BEGORE PUSHING Maybe check if it has already been imported and cancel otherwise
        cmd = [
            "python3",
            "fpingParser.py",
            resultDirectory + filename,
            str(experiment_id)
        ]
        #output = subprocess.check_output(cmd)
        pipes = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_out, std_err = pipes.communicate()
        if pipes.returncode != 0:
            print("an error happened!")
            err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            if err_msg.find("duplicate key value violates unique constraint") >= 0:
                print("This file seems to be in the database already based on the Uniuqe constraint of the related table")
                print(cmd[2].split("/")[-1])
                print("Ignoring................")
            else:
                continue
                raise Exception(err_msg)
    for filename in [fi for fi in value if ( ( (fi.startswith("tcp") ) or (fi.startswith("tls")) )  )]:
        print("Importing ", filename)
        #continue # REMOVE THIS BEGORE PUSHING Maybe check if it has already been imported and cancel otherwise
        cmd = [
            "python3",
            "fetchParser.py",
            resultDirectory + filename,
            str(experiment_id),
            str(convertDumpToCsv),
            str(insertDumpToDb)
        ]
        #output = subprocess.check_output(cmd)
        pipes = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_out, std_err = pipes.communicate()
        if pipes.returncode != 0:
            print("an error happened!")
            err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            if err_msg.find("duplicate key value violates unique constraint") >= 0:
                print("This file seems to be in the database already based on the Uniuqe constraint of the related table")
                print(cmd[2].split("/")[-1])
                print("Ignoring................")
            else:
                continue
                raise Exception(err_msg)
#conn.commit()
cur.close()
conn.close()