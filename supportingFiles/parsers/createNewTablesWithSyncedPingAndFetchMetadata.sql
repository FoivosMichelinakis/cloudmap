CREATE TABLE cloudmap.pingParameters_new AS
SELECT
pingParameters.experiment_id,
pingParameters.ping_id,
pingParameters.targetdomainname,
pingParameters.interface,
pingParameters.IpDst,
pingParameters.protocol,
pingParameters.containerTimestamp,
pingParameters.nodeId,
pingParameters.filename,
pingParameters.successfulExperiment,
pingParameters.minRtt,
pingParameters.avgRtt,
pingParameters.maxRtt,
pingParameters.xmt,
pingParameters.rcv,
pingParameters.loss,
tracerouteParameters.operator,
tracerouteParameters.networkTechnology,
tracerouteParameters.publicIP,
tracerouteParameters.DeviceState,
tracerouteParameters.modemIP,
tracerouteParameters.mccmcn,
tracerouteParameters.experimentMetadataTimedifferenceStart,
tracerouteParameters.metadataTimestampStart,
tracerouteParameters.experimentMetadataTimedifferenceEnd,
tracerouteParameters.metadataTimestampEnd,
tracerouteParameters.sufficientMetadataValues
FROM   cloudmap.pingParameters
INNER JOIN   cloudmap.tracerouteParameters ON
-- (pingParameters.sufficientMetadataValues IS NULL OR NOT pingParameters.sufficientMetadataValues) AND --not needed when creating a new table (instead of updating). We need to copy all the relevant rows
tracerouteParameters.targetdomainname like pingParameters.targetdomainname AND
tracerouteParameters.interface like pingParameters.interface AND
tracerouteParameters.containerTimestamp = pingParameters.containerTimestamp AND
tracerouteParameters.nodeId = pingParameters.nodeId AND
tracerouteParameters.IpDst = pingParameters.IpDst
WHERE tracerouteParameters.sufficientMetadataValues AND
tracerouteParameters.experimentMetadataTimedifferenceEnd >= 20
ORDER BY pingParameters.ping_id;

-- we have to add a primary key to be able to use the id column in the group by close 
ALTER TABLE pingParameters_new ADD PRIMARY KEY (ping_id);


CREATE TABLE cloudmap.fetchParameters_new AS
SELECT
fetchParameters.experiment_id,
fetchParameters.fetch_id,
fetchParameters.targetdomainname,
fetchParameters.interface,
fetchParameters.IpDst,
fetchParameters.protocol,
fetchParameters.containerTimestamp,
fetchParameters.nodeId,
fetchParameters.filename,
fetchParameters.ssl_verify_result, -- might not be populated used for now
fetchParameters.http_code,
fetchParameters.http_connect,
fetchParameters.local_ip,
fetchParameters.local_port,
fetchParameters.num_redirects,
fetchParameters.size_download,
fetchParameters.speed_download,
fetchParameters.time_appconnect,
fetchParameters.time_connect,
fetchParameters.time_namelookup,
fetchParameters.time_pretransfer,
fetchParameters.time_redirect,
fetchParameters.time_starttransfer,
fetchParameters.time_total,
tracerouteParameters.operator,
tracerouteParameters.networkTechnology,
tracerouteParameters.publicIP,
tracerouteParameters.DeviceState,
tracerouteParameters.modemIP,
tracerouteParameters.mccmcn,
tracerouteParameters.experimentMetadataTimedifferenceStart,
tracerouteParameters.metadataTimestampStart,
tracerouteParameters.experimentMetadataTimedifferenceEnd,
tracerouteParameters.metadataTimestampEnd,
tracerouteParameters.sufficientMetadataValues
FROM   cloudmap.fetchParameters
INNER JOIN   cloudmap.tracerouteParameters ON
-- (fetchParameters.sufficientMetadataValues IS NULL OR NOT fetchParameters.sufficientMetadataValues) AND --not needed when creating a new table (instead of updating). We need to copy all the relevant rows
tracerouteParameters.targetdomainname like fetchParameters.targetdomainname AND
tracerouteParameters.interface like fetchParameters.interface AND
tracerouteParameters.containerTimestamp = fetchParameters.containerTimestamp AND
tracerouteParameters.nodeId = fetchParameters.nodeId AND
tracerouteParameters.IpDst = fetchParameters.IpDst
WHERE tracerouteParameters.sufficientMetadataValues AND
tracerouteParameters.experimentMetadataTimedifferenceEnd >= 20
ORDER BY fetchParameters.fetch_id;


ALTER TABLE fetchParameters_new ADD PRIMARY KEY (fetch_id);