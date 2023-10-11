#!/bin/bash
FIRST_PCAP=$1
SECOND_PCAP=$2

FIRST_INFOS=`capinfos -aeS $FIRST_PCAP`

TIME_FIRST_PACKET=`$FIRST_INFOS | grep "First packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
TIME_LAST_PACKET=`$FIRST_INFOS | grep "Last packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`

echo "First pcap starts at $TIME_FIRST_PACKET and ends at $TIME_LAST_PACKET"
DURATION_FIRST=$(($TIME_LAST_PACKET-$TIME_FIRST_PACKET))
echo "Duration first pcap: $DURATION_FIRST"