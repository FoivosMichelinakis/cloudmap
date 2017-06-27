#!/bin/bash

BASEDIR=/monroe/cdnmob
TODIR=/monroe/cdnmob
URL_CDNMOB=foivosm/basic_dns_tests

URL_BASE=monroe/base
URL_NOOP=monroe/noop
URL_PING=monroe1.cs.kau.se:5000/monroe/ping
URL_HTTP=monroe1.cs.kau.se:5000/monroe/http_download

REPO=rsync@repo.monroe-system.eu
USER_REPO=rsync@repo.monroe-system.eu
KEY=/etc/keys/repo.monroe-system.eu

function mk_disk {
 mkdir -p $BASEDIR/$1
 if mountpoint -q $BASEDIR/$1; then
   echo "$1 outdir is mounted."
 else
   MNTPNT=""
   if [ -b /dev/vg-monroe/cont-$1 ]; then
     echo "logical volume exists on vg-monroe";
     MNTPNT=/dev/vg-monroe/cont-$1
   elif [ -b /dev/Monroe-X-vg/cont-$1 ]; then
     echo "logical volume exists on Monroe-X-vg (deprecated)";
     MNTPNT=/dev/Monroe-X-vg/cont-$1
   else
     mkdir -p $BASEDIR/$1
     if [ $(lvcreate -L 300M vg-monroe -n cont-$1) ]; then
       MNTPNT=/dev/vg-monroe/cont-$1
     elif [ $(lvcreate -L 300M Monroe-X-vg -n cont-$1) ]; then
       MNTPNT=/dev/Monroe-X-vg/cont-$:w1
     else
       if [ ! -f $BASEDIR/$1.disk ]; then
         dd if=/dev/zero of=$BASEDIR/$1.disk bs=100000000 count=1
       fi
       MNTPNT=$BASEDIR/$1.disk
     fi
   fi;
   if [ -z "$(file -sL $MNTPNT | grep ext4)" ]; then
     mkfs.ext4 $MNTPNT -F -L $1
   fi
   mount -t ext4 $MNTPNT $BASEDIR/$1
 fi
}

docker pull $URL_CURL
NODEID=$(cat /etc/nodeid)
# run the container in the host namespace
mk_disk "cdnmob_host"
IMAGEID=$(docker images $URL_CDNMOB | head -n 1)

echo "{\"nodeid\":"$NODEID", \
       \"guid\":\""$IMAGEID"."$NODEID".cdnmob.monroe\" \
       }" > $BASEDIR/cdnmob.conf

docker run --rm --privileged --net=host \
           -v $BASEDIR/cdnmob_host:/monroe/results \
           -v /etc/nodeid:/nodeid:ro \
           -v $BASEDIR/cdnmob.conf:/monroe/config:ro  $URL_CDNMOB

