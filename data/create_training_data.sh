
echo "Cut DDoS attack from Friday-WorkingHours.pcap between 15:56 and 16:16 in CANADA time zone"
echo "Note that the time stamps are recorded in Canada and need to be adjusted accorting to your machine's time zone."

echo "Cut DDoS attack"
mkdir -p cic-ddos
editcap -A "2017-07-07 20:57:00" -B "2017-07-07 21:15:00" downloads/Friday-WorkingHours.pcap cic-ddos/Friday-WorkingHours-DDoS.pcap

echo "Cut Benign traffic"
mkdir -p cic-benign
editcap -A "2017-07-07 20:37:00" -B "2017-07-07 20:55:00" -F pcap downloads/Friday-WorkingHours.pcap cic-benign/Friday-WorkingHours-Benign.pcap

echo "Cut Port Scan (Friday Afternoon Port Scan //Firewall rules off//)"
mkdir -p cic-portscan
editcap -A "2017-07-07 19:51:45" -B "2017-07-07 20:29:59" -F pcap downloads/Friday-WorkingHours.pcap cic-portscan/Friday-WorkingHours-PortScan.pcap

mkdir -p mawi-benign
echo "Split mawi file into chunks of 1 min duration to enable parallel processing"
editcap -i 60 downloads/202303021400.pcap mawi-benign/
echo "Done"

echo "Create caida mawi data"
./merge_pcaps.sh downloads/202303021400.pcap downloads/caida.pcap downloads/caida_mawi
mkdir -p mawi-ddos
editcap -i 60 downloads/caida_mawi.pcap mawi-ddos/
echo "Done"

echo "Create 15 minutes of port scan traffic"
mkdir -p mawi-portscan
./inject_mawi_portscan.sh
editcap -i 60 downloads/mawi_portscan.pcap mawi-portscan/
echo "Done"

mkdir training
python aggregation.py mawi-benign mawi_benign
python aggregation.py mawi-ddos mawi_ddos
python aggregation.py mawi-portscan mawi_portscan

python aggregation.py cic-ddos cic_ddos
python aggregation.py cic-benign cic_benign
python aggregation.py cic-portscan cic_portscan

