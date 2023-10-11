mkdir -p tmp/
for i in {0..149}
do
    timestamp=$((i*6))
    ~/repos/ID2T/id2t -i mawi/202303021400_00000_20230302060000.pcap -ie -a PortscanAttack port.dst="1-60000" port.dst.shuffle=true port.open=false inject.at-timestamp=$timestamp packets.per-second=10000 bandwidth.max=1000000000 -ie -o tmp/portscan_$i.pcap
done

mergecap -w tmp/portscan.pcap tmp/portscan_*.pcap
./merge_pcaps.sh downloads/202303021400.pcap tmp/portscan.pcap downloads/mawi_portscan
