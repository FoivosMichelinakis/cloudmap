#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import psycopg2
from psycopg2.extensions import AsIs
import time


secondApartLimit = 300

try:
    conn = psycopg2.connect("dbname='cloudmap' user='removedUser' host='localhost' password='removedPassword'")
    print("connected!")
except:
    print("I am unable to connect to the database")
    sys.exit(1)
cur = conn.cursor()


# case for traceroute and dig
# since we run this periodically we want to update only the ones that do not already have an entry, hence the "metadataTimestamp is NULL"
# since the fetch time of the results and the metadata differ, we accept as valid entries only metadata that are at most 10 minutes away from the starTime and endTime
# if we can not find that we do not put metadata
digQuery = """select experiment_id, dig_id, nodeid, interface, startTime, endTime
from cloudmap.digParameters
where (sufficientMetadataValues IS NULL OR NOT sufficientMetadataValues);"""
cur.execute(digQuery)
conn.commit()
rows = cur.fetchall()


for element in rows:
    [experiment_id, dig_id, nodeid, interface, startTime, endTime] = element
    # metadata Before Query
    cur.execute("""select IPAddress, IMSIMCCMNC, Operator, DeviceMode, DeviceState, timestampNode, %s - timestampNode AS diff
    from cloudmap.metadata
    where nodeId = %s and InterfaceName like %s and timestampNode <= %s
    order by timestampNode DESC   
    limit 1;""",
    [endTime, nodeid, interface, startTime])
    conn.commit()
    res = cur.fetchall()
    before = res
    print(res)

    # metadata Between Query
    cur.execute("""select IPAddress, IMSIMCCMNC, Operator, DeviceMode, DeviceState, timestampNode
    from cloudmap.metadata
    where nodeId = %s and InterfaceName like %s and timestampNode between %s and %s
    order by timestampNode
    limit 1;""",
    [nodeid, interface, startTime, endTime])
    conn.commit()
    res = cur.fetchall()
    between = res
    print(res)

    # metadata After Query
    cur.execute("""select IPAddress, IMSIMCCMNC, Operator, DeviceMode, DeviceState, timestampNode, timestampNode - %s AS diff
    from cloudmap.metadata
    where nodeId = %s and InterfaceName like %s and timestampNode >= %s
    order by timestampNode
    limit 1;""",
    [startTime, nodeid, interface, endTime])
    conn.commit()
    res = cur.fetchall()
    after = res
    print(res)

    if (  (len(before) == 0) or (len(after) == 0) ):
        # not enough metadata
        sufficientMetadataValues = False
    else:
        total = [(ele[0], ele[1], ele[2], ele[3], ele[4]) for ele in before + between + after]

        if (  (len(set(total)) == 1)  and (before[0][-1] <= secondApartLimit) and (after[0][-1] <= secondApartLimit) ):
            # the relatated values have remained the same for the whole duration of the experiment
            # the related metadata entries are not too far in time apart from the experiment\
            sufficientMetadataValues = True
        else:
            sufficientMetadataValues = False


        print([int(before[0][-1]), before[0][-2], int(after[0][-1]), after[0][-2],
            sufficientMetadataValues,
            total[0][0], total[0][1], total[0][2], total[0][3], total[0][4],
            dig_id])

    if sufficientMetadataValues:
        cur.execute("""UPDATE cloudmap.digParameters
        SET experimentMetadataTimedifferenceStart = %s,
        metadataTimestampStart = %s,
        experimentMetadataTimedifferenceEnd = %s,
        metadataTimestampEnd = %s,
        sufficientMetadataValues = %s,
        modemIP = %s,
        mccmcn = %s,
        operator = %s,
        networkTechnology = %s,
        DeviceState = %s
        WHERE dig_id = %s""",
        [int(before[0][-1]), before[0][-2], int(after[0][-1]), after[0][-2],
        sufficientMetadataValues, 
        total[0][0], total[0][1], total[0][2], total[0][3], total[0][4],
        dig_id])
    else:
        cur.execute("""UPDATE cloudmap.digParameters
        SET sufficientMetadataValues = %s
        WHERE dig_id = %s""",
        [sufficientMetadataValues, dig_id])
    conn.commit()
cur.close()
conn.close()



