#!/bin/bash

interface=${1}
hostIP=${2}
hostPort=${3}
captureFilename=${4}
executableLocation=${5}
URL=${6}
protocol=${7}
curlFilename=${8}
useTcpdump=${9}


curlOPtions="\nSomeMetrics:\thttp_code\t%{http_code}\thttp_connect\t%{http_connect}\tlocal_ip\t%{local_ip}\tlocal_port\t%{local_port}\tnum_redirects\t%{num_redirects}\tsize_download\t%{size_download}\tspeed_download\t%{speed_download}\ttime_appconnect\t%{time_appconnect}\ttime_connect\t%{time_connect}\ttime_namelookup\t%{time_namelookup}\ttime_pretransfer\t%{time_pretransfer}\ttime_redirect\t%{time_redirect}\ttime_starttransfer\t%{time_starttransfer}\ttime_total\t%{time_total}\tssl_verify_result\t%{ssl_verify_result}\t\n\n"

if [ "$useTcpdump" == "yes" ]
then
/usr/sbin/tcpdump tcp and port "$hostPort" and host "$hostIP" -i "$interface" -n -s 100 -U -l -w "$captureFilename" &>log.txt &
serverTCPdumpID="$!"
# delay to make sure the tcpdump has launched
sleep 3
echo $serverTCPdumpID
trap "echo 'Exiting...........'; kill -9 $serverTCPdumpID; exit" SIGINT SIGTERM
#chmod 777 "$executableLocation"
#python ${executableLocation} "$URL" "$hostIP" "$protocol"
fi

if [ "$protocol" == "tcp" ]
then
curl --header "Host: $URL" -k http://"$hostIP":80/favicon.ico -o /dev/null -w "$curlOPtions" -o ./curl.out &> "$curlFilename"
fi

if [ "$protocol" == "tls" ]
then
curl --header "Host: $URL" -k https://"$hostIP":443/favicon.ico -o /dev/null -w "$curlOPtions" -o ./curl.out &> "$curlFilename"
fi

if [ "$useTcpdump" == "yes" ]
then
# delay to make sure the tcpdump has flushed its buffers
sleep 3
kill -9 $serverTCPdumpID
fi