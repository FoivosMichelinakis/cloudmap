-- usefull commands for development
-- drop schema cloudmap cascade;
-- TRUNCATE ... CASCADE quickly removes all rows from a set of tables
-- ALTER TABLE products RENAME COLUMN product_no TO product_number;
-- how to export the query to csv http://stackoverflow.com/questions/29190632/how-to-export-a-postgresql-query-output-to-a-csv-file?answertab=votes#tab-top
-- to fix the permission problem of user postgres when exporting https://askubuntu.com/questions/487527/give-specific-user-permission-to-write-to-a-folder-using-w-notation


-- the mccmcn in the epxeriment tables is derived from the IMSIMCCMNC field of the metadata.
-- WARNING: if joining on double precision values, cast them first as bigint. This cast meet return dublicate rows since it is possible that 2
-- different rows can be equal when you compare as integers. To solve this "group by" the id of the table and then order by the min of the difference of the 2 values that 
-- you are comparing. That way only on row will be returned.

CREATE SCHEMA cloudmap;

CREATE TABLE cloudmap.inventory (
    nodeId int PRIMARY KEY,
    location varchar(50),
    type varchar(20), -- monroe, server, mobile, static, etc.
    digversion varchar(10),
    operators varchar(20)[]
);

CREATE TABLE cloudmap.experiment (
    experiment_id serial PRIMARY KEY, -- one entry per call to the individualExperiment.py
    target varchar(500) NOT NULL,
    interface varchar(10) NOT NULL,
    containerTimestamp integer NOT NULL,
    nodeId int NOT NULL,
    publicIP inet,
    modemIP inet, -- taken from the metadata of the device if applicable
    mccmcn int, -- taken from the metadata of the device if applicable
    operator varchar(50), -- taken from the metadata of the device if applicable
    networkTechnology varchar(20), -- taken from the metadata of the device if applicable
    UNIQUE (target, interface, containerTimestamp, nodeId)
);


CREATE TABLE cloudmap.digParameters (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    dig_id serial PRIMARY KEY,
    resolverName varchar(10),
    resolverIP inet, -- taken from the result file
    target varchar(500) NOT NULL,
    publicIPSubnet inet, -- taken from the result file, as the parameter of the subnet flag
    digversion varchar(10), -- taken from the result file
    startTime integer,
    endTime integer,
    digclientsubnetflag boolean, -- if in the experiment we attempted to use the client-subnet flag
    filename varchar(500),
    EDNS smallint,
    protocol varchar(10),
    acceptedSize smallint, -- number right after protocol in the opt section
    clientSubnetSupport boolean, -- if the server took the subnet flag into account (there was a "CLIENT-SUBNET" line in the resutlts)
    queryTime int, --ms
    when_human varchar(100),
    when_timestamp timestamptz, -- parsed from the result file
    msgsize smallint,
    server varchar(100), -- the value of the server field in the text
    dnsSecSupport varchar(10), -- yes, no, error
    containerTimestamp integer NOT NULL,
    nodeId int NOT NULL,
    interface varchar(10) NOT NULL,
    operator varchar(50), -- taken from the metadata of the device if applicable
    networkTechnology varchar(20), -- taken from the metadata of the device if applicable
    publicIP inet,
    DeviceState smallint, -- taken from the metadata of the device if applicable
    modemIP inet, -- taken from the metadata of the device if applicable
    mccmcn int, -- taken from the metadata of the device if applicable
    experimentMetadataTimedifferenceStart integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment started
    metadataTimestampStart double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
    experimentMetadataTimedifferenceEnd integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment Ended
    metadataTimestampEnd double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
    sufficientMetadataValues boolean -- the related metadata values a) have consistent values in the before after and in between results and b) the before and after values are not more than 5 minutes away from the start and end of the experiment. If this is the case we also update the values of the following experiments that do not have start and end times recorded.
    UNIQUE (target, interface, containerTimestamp, nodeId, resolverIP, resolverName)
);

CREATE TABLE cloudmap.digResults (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    dig_id integer REFERENCES cloudmap.digParameters (dig_id),
    section varchar(20), -- answer, authority, addtional
    leftArgument varchar(500),
    TTL int,
    recordType varchar(10),
    rightArgument varchar(500)
);

CREATE TABLE cloudmap.tracerouteParameters (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    traceroute_id serial PRIMARY KEY,
    startTime integer,
    endTime integer,
    targetdomainname   varchar(500),
    interface varchar(10) NOT NULL,
    IpDst              inet,
    numberOfHops       smallint,
    sizeOfProbes       smallint,
    protocol varchar(10),
    containerTimestamp integer NOT NULL,
    nodeId int NOT NULL,
    filename varchar(500),
    operator varchar(50), -- taken from the metadata of the device if applicable
    networkTechnology varchar(20), -- taken from the metadata of the device if applicable
    publicIP inet,
    DeviceState smallint, -- taken from the metadata of the device if applicable
    modemIP inet, -- taken from the metadata of the device if applicable
    mccmcn int, -- taken from the metadata of the device if applicable
    experimentMetadataTimedifferenceStart integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment started
    metadataTimestampStart double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
     experimentMetadataTimedifferenceEnd integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment Ended
    metadataTimestampEnd double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
    sufficientMetadataValues boolean -- the related metadata values a) have consistent values in the before after and in between results and b) the before and after values are not more than 5 minutes away from the start and end of the experiment. If this is the case we also update the values of the following experiments that do not have start and end times recorded.
    UNIQUE (targetdomainname, interface, containerTimestamp, nodeId, IpDst, protocol)
);

CREATE TABLE cloudmap.tracerouteResults (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    traceroute_id integer REFERENCES cloudmap.tracerouteParameters (traceroute_id),
    hop                smallint,
    IP                 inet,
    RTTSection         int[], -- in ms 
    annotationSection  varchar(20)[],
    UNIQUE (experiment_id, traceroute_id, hop, IP)
);

CREATE TABLE cloudmap.pingParameters (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    ping_id serial PRIMARY KEY,
    targetdomainname   varchar(500),
    interface varchar(10) NOT NULL,
    IpDst              inet,
    protocol varchar(10),
    containerTimestamp integer NOT NULL,
    nodeId int NOT NULL,
    filename varchar(500),
    successfulExperiment boolean,
    minRtt real, -- ms
    avgRtt real, -- ms
    maxRtt real, -- ms
    xmt integer,
    rcv integer,
    loss real, -- it is a percentage
    operator varchar(50), -- taken from the metadata of the device if applicable
    networkTechnology varchar(20), -- taken from the metadata of the device if applicable
    publicIP inet,
    DeviceState smallint, -- taken from the metadata of the device if applicable
    modemIP inet, -- taken from the metadata of the device if applicable
    mccmcn int, -- taken from the metadata of the device if applicable
    experimentMetadataTimedifferenceStart integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment started
    metadataTimestampStart double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
     experimentMetadataTimedifferenceEnd integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment Ended
    metadataTimestampEnd double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
    sufficientMetadataValues boolean -- the related metadata values a) have consistent values in the before after and in between results and b) the before and after values are not more than 5 minutes away from the start and end of the experiment. If this is the case we also update the values of the following experiments that do not have start and end times recorded.
    UNIQUE (targetdomainname, interface, containerTimestamp, nodeId, IpDst, protocol)
);

CREATE TABLE cloudmap.pingResults (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    ping_id integer REFERENCES cloudmap.pingParameters (ping_id),
    probeNumber smallint,
    IP                 inet,
    probeSize smallint, --bytes
    rtt real,
    movingAverageRtt real,
    movingAverageLoss real, -- it is a percentage
    UNIQUE (experiment_id, ping_id, probeNumber, IP)
);

CREATE TABLE cloudmap.fetchParameters (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    fetch_id serial PRIMARY KEY,
    protocol varchar(10), -- tcp, tls
    targetdomainname   varchar(500),
    interface varchar(10) NOT NULL,
    IpDst              inet,
    containerTimestamp integer NOT NULL,
    nodeId int NOT NULL,
    filename varchar(500),
    operator varchar(50), -- taken from the metadata of the device if applicable
    networkTechnology varchar(20), -- taken from the metadata of the device if applicable
    publicIP inet,
    DeviceState smallint, -- taken from the metadata of the device if applicable
    modemIP inet, -- taken from the metadata of the device if applicable
    mccmcn int, -- taken from the metadata of the device if applicable
    ssl_verify_result smallint, -- might not be populated used for now
    http_code smallint,
    http_connect real,
    local_ip inet,
    local_port integer,
    num_redirects smallint,
    size_download integer,
    speed_download real,
    time_appconnect real,
    time_connect real,
    time_namelookup real,
    time_pretransfer real,
    time_redirect real,
    time_starttransfer real,
    time_total real,
    experimentMetadataTimedifferenceStart integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment started
    metadataTimestampStart double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
     experimentMetadataTimedifferenceEnd integer, --difference in seconds of the timestamps of the closest metadata value and the time the experiment Ended
    metadataTimestampEnd double precision, -- the timestamp of the related metadata entry (column name: timestampNode). Entry timestamp (in seconds since UNIX epoch with microsecond precision.
    sufficientMetadataValues boolean -- the related metadata values a) have consistent values in the before after and in between results and b) the before and after values are not more than 5 minutes away from the start and end of the experiment. If this is the case we also update the values of the following experiments that do not have start and end times recorded.
    UNIQUE (targetdomainname, interface, containerTimestamp, nodeId, IpDst, protocol)
);

CREATE TABLE cloudmap.fetchPacketCapture (
    experiment_id integer REFERENCES cloudmap.experiment (experiment_id),
    fetch_id integer REFERENCES cloudmap.fetchParameters (fetch_id),
    frame_number smallint, 
    frame_time_epoch double precision,
    frame_len smallint,
    frame_cap_len smallint,
    ip_proto smallint, -- if the value is 6 we have an TCP packet, if 17 we have UDP
    ip_src inet,
    tcp_srcport integer, 
    ip_dst inet,
    tcp_dstport integer,
    tcp_stream smallint, -- the index of the TCP stream
    tcp_seq integer, -- relative sequence number of the packet
    tcp_ack integer, -- relative TCP ack
    tcp_flags_res boolean, -- reserved
    tcp_flags_ns boolean, -- Nonce
    tcp_flags_cwr  boolean, -- Congestion Window Reduced
    tcp_flags_ecn  boolean, -- ECN-Echo
    tcp_flags_urg boolean, -- urgent
    tcp_flags_ack  boolean,
    tcp_flags_push  boolean,
    tcp_flags_reset  boolean,
    tcp_flags_syn boolean,
    tcp_flags_fin boolean,
    tcp_analysis_acks_frame smallint, -- This is an ack to the segment in frame ##
    tcp_analysis_ack_rtt  double precision, -- The RTT to ACK the segment was ## seconds
    http_request_uri varchar(400),
    col_Protocol varchar(20), -- It is the top layer Protocol
    ssl_record_version  varchar(20),
    ssl_record_content_type  smallint,
    ssl_record_length  smallint,
    UNIQUE (experiment_id, fetch_id, frame_number)
);

CREATE TABLE cloudmap.metadata (
    -- remove from the entering in the database del d[key]--> DataId "MONROE.META.DEVICE.MODEM", DataVersion 2, rename Timestamp to timestampNode
    nodeId int,
    InterfaceName varchar(5), --Name of the interface in the MONROE node, e.g., “usb0”, “usb1”, “usb2”, “eth0”, . . .
    CID integer, -- Cell ID
    PCI integer, -- Physical Cell ID.
    DeviceState smallint, -- State of the device reported to the network: UNKNOWN (0) - Device state is unknwon; REGISTERED (1) - Device is registered to the network; UNREGISTERED (2) - Device is unregistered from the network; CONNECTED (3) - Device is connected to the network; DISCONNECTED (4) - Device is disconnected from the network.
    SequenceNumber integer, --Monotonically increasing message counter. 
    timestampNode double precision, -- Entry timestamp (in seconds since UNIX epoch with microsecond precision)
    NWMCCMNC integer, --Mobile Country Code (MCC) and Mobile Network Code (MNC) from network (read from the network). The tuple uniquely identifies a mobile network operator (carrier) that is using the GSM (including GSM-R), UMTS, and LTE public land mobile networks.
    Band smallint, --Band corresponding to the frequency used (e.g., 3, 7 or 20 in Europe)
    RSSI smallint, -- Received Signal Strength Indicator
    IPAddress inet, --IP address assigned to the modem by the operator.
    IMSIMCCMNC integer,  --Mobile Country Code (MCC) and Mobile Network Code (MNC).
    DeviceMode smallint, --Connection mode of the modem (e.g., 2G, 3G, LTE) indicating the radio access technology the modem uses.
    DeviceSubmode smallint, --Connection submode for 3G connections (e.g., CDMA, WCDMA, UMTS).
    ECIO  smallint, --EC/IO, quality/cleanliness of signal from the tower to the modem (dB).
    InternalInterface varchar(5), --Name of the interface inside the containers, e.g., “op0”, “op1”, “op2”, “eth0”, “wlan0”, . . . Experiments in containers have to bind to these interface names.
    IMEI varchar(15), --International Mobile Station Equipment Identity.
    RSRQ smallint, --Reference Signal Received Quality (valid only for LTE networks). The RSRQ measurement provides additionalinformation when Reference Signal Received Power (RSRP) is not sufficient to make a reliable handover or cell reselection decision. RSRQ considers both the Received Signal Strength Indicator (RSSI) and the number of used Resource Blocks (N) RSRQ = (N ∗ RSRP)/RSSI measured over the same bandwidth.
    RSRP smallint, --Reference Signal Received Power (LTE).
    RSCP smallint, --Received Signal Code Power (UMTS).
    ENODEBID varchar(10), --Evolved base station ID.
    LAC varchar(10), --Local Area Code for the current cell (hex).
    Frequency smallint, --Frequency in MHz (e.g., 700, 800, 900, 1800 or 2600 in Europe).
    InternalIPAddress inet, --Internal IP address of the modem in the MONROE node.
    Operator varchar(20), --Operator name as reported by the network for the interface in which the experiment was run.
    ICCID varchar(20), --Internationally defined integrated circuit card identifier of the SIM card.
    IMSI varchar(15), --Internation Mobile Subscriber Identity.
    UNIQUE (nodeId, InterfaceName, timestampNode)
);
