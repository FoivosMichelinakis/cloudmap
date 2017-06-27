-- the results are updated in the db once the loop is over, before there is nothing you can see
-- http://stackoverflow.com/questions/22351039/committing-records-into-the-table-while-executing-a-postgreql-function

DO
$do$
declare 
        tracerouterow RECORD;
BEGIN 
FOR tracerouterow IN
    SELECT 
        experiment_id,
        traceroute_id,
        nodeid,
        interface,
        startTime,
        endTime,
        targetdomainname,
        containerTimestamp,
        IpDst,
        experimentMetadataTimedifferenceStart,
        metadataTimestampStart,
        experimentMetadataTimedifferenceEnd,
        metadataTimestampEnd,
        sufficientMetadataValues,
        modemIP,
        mccmcn,
        operator,
        networkTechnology,
        DeviceState
    FROM cloudmap.tracerouteParameters
    WHERE sufficientMetadataValues AND
    experimentMetadataTimedifferenceEnd >= 20 --AND
    -- to_timestamp(startTime) AT TIME ZONE 'UTC' >= CURRENT_TIMESTAMP - INTERVAL '1 week'
LOOP
    UPDATE cloudmap.pingParameters 
        SET sufficientMetadataValues = tracerouterow.sufficientMetadataValues,
        modemIP = tracerouterow.modemIP,
        mccmcn = tracerouterow.mccmcn,
        operator = tracerouterow.operator,
        networkTechnology = tracerouterow.networkTechnology,
        DeviceState = tracerouterow.DeviceState
    WHERE
        (pingParameters.sufficientMetadataValues IS NULL OR NOT pingParameters.sufficientMetadataValues) AND
        tracerouterow.targetdomainname like pingParameters.targetdomainname AND
        tracerouterow.interface like pingParameters.interface AND
        tracerouterow.containerTimestamp = pingParameters.containerTimestamp AND
        tracerouterow.nodeId = pingParameters.nodeId AND
        tracerouterow.IpDst = pingParameters.IpDst;

    UPDATE cloudmap.fetchParameters 
        SET sufficientMetadataValues = tracerouterow.sufficientMetadataValues,
        modemIP = tracerouterow.modemIP,
        mccmcn = tracerouterow.mccmcn,
        operator = tracerouterow.operator,
        networkTechnology = tracerouterow.networkTechnology,
        DeviceState = tracerouterow.DeviceState
    WHERE
        (fetchParameters.sufficientMetadataValues IS NULL OR NOT fetchParameters.sufficientMetadataValues) AND
        tracerouterow.targetdomainname like fetchParameters.targetdomainname AND
        tracerouterow.interface like fetchParameters.interface AND
        tracerouterow.containerTimestamp = fetchParameters.containerTimestamp AND
        tracerouterow.nodeId = fetchParameters.nodeId AND
        tracerouterow.IpDst = fetchParameters.IpDst;
END LOOP;
END
$do$;
