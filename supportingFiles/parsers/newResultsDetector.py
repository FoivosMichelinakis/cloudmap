#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
import results to the db and move the related files to the imported folder
"""

import os
import subprocess
import shutil
import time

pendingExperimentsDir = "/home/cloudmap/pending/experiments/"
pendingmetaDataDir = "/home/cloudmap/pending/metadata/"
stagingDirectory = "/home/cloudmap/pending/staging/"
exportedDirectory = "/home/cloudmap/pending/staging/monroe/results/"
scriptsDirectory = "/home/cloudmap/scripts/"

def list_files(dir):
    r = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            r.append(os.path.join(root, name))
    return r

while True:
    pendingResultFiles = [element for element in list_files(pendingExperimentsDir) if element.endswith(".tar.gz")]
    time.sleep(60)  # in case a file is being copied we give it one minute to finish. This delay also serves as a way to avoid having the infinite loop max out the processor
    for filename in pendingResultFiles:
        print(filename)
        try:
            cmd = ["tar", "-xvzf", filename, "-C", stagingDirectory]
            out = subprocess.check_output(cmd)
        except:
            print(filename, " failed to unapck igonirng and moving to the imported folder")
            shutil.move(filename, filename.replace("pending", "imported"))
            continue
        cmd = ["python3", scriptsDirectory + "maindbImporter.py", exportedDirectory, "1", "1"]
        out = subprocess.check_output(cmd)
        shutil.rmtree(exportedDirectory)
        shutil.move(filename, filename.replace("pending", "imported"))