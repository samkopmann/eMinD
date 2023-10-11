echo "Access to CAIDA data is restricted and must be granted by CAIDA individually."

mkdir -p caida
cp data.caida.org/datasets/security/ddos-20070804/*1419*.gz caida/
cp data.caida.org/datasets/security/ddos-20070804/*1424*.gz caida/
cp data.caida.org/datasets/security/ddos-20070804/*1429*.gz caida/
gzip -d caida/*
mergecap -w caida.pcap caida/*.pcap
rm -rf caida/
rm -rf data.caida.org/
