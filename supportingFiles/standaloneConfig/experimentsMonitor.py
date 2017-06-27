#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import os
import shutil
import subprocess
import time

sshConfig = """
Host cloudmap
HostName 163.117.140.154   
Port 2280
User cloudmap
IdentityFile ~/.ssh/cloudmap
IdentitiesOnly yes

"""

lastTimeCurrentMetadataFileUpdated = 0

while True:
    # chech if the ssh config file has the entry for cloudmap
    with open("/root/.ssh/config", "r") as fd:
        configText = " ".join(fd.readlines())

    if configText.find("cloudmap") >= 0:
        print("The configuration is correct")
    else:
        print("The configuration is wrong. Fixing.....")
        with open("/root/.ssh/config", "a") as fd:
            fd.write("\n\n")
            fd.write(sshConfig)

    # check if other containers are running
    cmd  = ["docker", "ps"]
    output = subprocess.check_output(cmd)
    runningContainers = [ele for ele in output.split("\n")[1:-1]]
    if (len(runningContainers) == 1) and (runningContainers[0].find("foivosm/basic_dns_tests") >= 0):
        print("The container is running and there are no other containers running")
    elif len(runningContainers) > 1: 
        os.system("service cron stop; service watchdog stop; service marvind stop; service rsyslog stop; docker stop -t 0 $(docker ps -q);")
    elif runningContainers[0].find("foivosm/basic_dns_tests") < 0:
        pass # find a way to launch the "infiniteLoop.sh" in the background
    else:
        pass

    # check if the metadata service is running
    metadataFiles = [ele for ele in os.listdir(".") if ele.startswith("meta_tracking")]
    metadataFilesAndTimestamps = []
    for ele in metadataFiles:
        try:
            mtime = os.path.getmtime(ele)
        except OSError:
            mtime = 0
        metadataFilesAndTimestamps.append([ele, mtime])

    metadataFilesAndTimestamps.sort(key=lambda x: x[1])
    # rename old files so that they can be transfered
    for element in metadataFilesAndTimestamps[:-1]:
        print("Renaming old metadata files that were found")
        print(element[0])
        shutil.move(element[0], element[0].replace("meta_tracking", "metadata_"))

    # check if the timestamp has been modified.
    if metadataFilesAndTimestamps[-1][1] != lastTimeCurrentMetadataFileUpdated:
        lastTimeCurrentMetadataFileUpdated = metadataFilesAndTimestamps[-1][1]
    else:
        print("the metadata file has not been updated. Reseting the sercives.")
        cmd = ["biteback", "-f"]
        output = subprocess.check_output(cmd)
        os.system("service cron stop; service watchdog stop; service marvind stop; service rsyslog stop; docker stop -t 0 $(docker ps -q);")
    time.sleep(10 * 60)
