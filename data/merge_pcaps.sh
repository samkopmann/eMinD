#!/bin/bash
FIRST_PCAP=$1
SECOND_PCAP=$2
OUTPUT_PCAP=$3

TIME_FIRST_PACKET=`capinfos -aeS $FIRST_PCAP | grep "First packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
TIME_LAST_PACKET=`capinfos -aeS $FIRST_PCAP | grep "Last packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
TIME_FIRST_PACKET_2=`capinfos -aeS $SECOND_PCAP  | grep "First packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
TIME_LAST_PACKET_2=`capinfos -aeS $SECOND_PCAP | grep "Last packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`

echo "First pcap starts at $TIME_FIRST_PACKET and ends at $TIME_LAST_PACKET"
DURATION_FIRST=$(($TIME_LAST_PACKET-$TIME_FIRST_PACKET))
echo "Duration first pcap: $DURATION_FIRST"

echo "Second pcap starts at $TIME_FIRST_PACKET_2 and ends at $TIME_LAST_PACKET_2"
DURATION_SECOND=$(($TIME_LAST_PACKET_2-$TIME_FIRST_PACKET_2))
echo "Duration second pcap: $DURATION_SECOND"

DIFF=$(($TIME_FIRST_PACKET_2-$TIME_FIRST_PACKET))
echo "Time difference between first packets: $DIFF"
ABSOLUTE_DIFF=$(($DIFF<0 ? $DIFF*-1 : $DIFF))
if [ $DIFF -lt 0 ]; then
    echo "Second pcap starts before first pcap. Shift second pcap by $ABSOLUTE_DIFF seconds"
    editcap -t $ABSOLUTE_DIFF $SECOND_PCAP second_shifted.pcap
    cp $FIRST_PCAP first_shifted.pcap
else
    echo "First pcap starts before second pcap. Shift first pcap by $ABSOLUTE_DIFF seconds"
    editcap -t $ABSOLUTE_DIFF $FIRST_PCAP first_shifted.pcap
    cp $SECOND_PCAP second_shifted.pcap
fi

echo "Test difference again"
TIME_FIRST_PACKET=`capinfos -aS first_shifted.pcap | grep "First packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
TIME_SECOND_PACKET=`capinfos -aS second_shifted.pcap | grep "First packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
DIFF=$(($TIME_SECOND_PACKET-$TIME_FIRST_PACKET))
echo "Time difference between first packets: $DIFF"

echo "Merge pcaps"
`mergecap -w $3.pcap first_shifted.pcap second_shifted.pcap`
TIME_FIRST_PACKET=`capinfos -aS $3.pcap | grep "First packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
TIME_LAST_PACKET=`capinfos -aS $3.pcap | grep "Last packet time" | cut -f2 -d ":" | cut -f1 -d "," | xargs`
echo "Merged pcap starts at $TIME_FIRST_PACKET and ends at $TIME_LAST_PACKET"
DURATION_MERGED=$(($TIME_LAST_PACKET-$TIME_FIRST_PACKET))
echo "Duration merged pcap: $DURATION_MERGED"

rm first_shifted.pcap
rm second_shifted.pcap