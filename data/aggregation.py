import numpy as np
import pandas as pd
import scapy.all as scapy
import multiprocessing as mp
import ipaddress
import glob
import time
import argparse

FIN = 0x01
SYN = 0x02
bins = 1000
IPs_per_bin = (2**32 // bins) + 1
ports_per_bin = (2**16 // bins) + 1


def create_dataset(pcap_file, index, time_frame, naming_scheme):
    first_arrival_time = 0.0
    last_arrival_time = 0.0

    packet_count = 0.0
    TCP_count = 0.0
    SYN_count = 0.0
    FIN_count = 0.0
    UDP_count = 0.0
    IATs = [0.0]
    src_IPs = [0.0]*1000
    src_ports = [0.0]*1000
    dst_IPs = [0.0]*1000
    dst_ports = [0.0]*1000
    packet_lengths = [0.0]

    total_packets = 0

    #Variables to check if time frame should be appended to frames containing port scans.
    #This is required for the cic port scan dataset, as the port scan is very sparse in the given time interval
    #and is not contained in every consecutive time frame
    is_cic_portscan = "cic_portscan" in naming_scheme
    cic_portscan_source = "172.16.0.1"
    cic_portscan_from_source = False
    #We only consider port scans that have at least 200 SYN packets in the given time frame,
    #as we do not focus on stealth scans. (pps = ports per second)
    pps_threshold = 200

    #Iterate over packets and store them in list. Aggregate features and write dataframe line after time frame duration
    #Packet count, TCP count, UDP count, IAT mean, IAT variance, IAT min, IAT max, number of unique source IPs, number of unique destination IPs,
    #number of unique source ports, number of unique destination ports, SYN count, FIN count, Packet length mean,
    #packet length var, packet length min, packet length max
    features = ["Packet count", "TCP count", "UDP count", "Mean IAT", "IAT var", "Unique src IPs",
            "Unique dst IPs", "Unique src ports", "Unique dst ports", "SYN count", "FIN count",
            "Mean packet length", "Packet length var"]
    
    feature_values = np.zeros((0, len(features)))
    
    time_frame_counter = 0
    for pkt in scapy.PcapReader(pcap_file):
        total_packets = total_packets + 1
        if first_arrival_time == 0.0:
            first_arrival_time = float(pkt.time)
        arrival_time = float(pkt.time) - first_arrival_time
        IATs.append(arrival_time - last_arrival_time)
        last_arrival_time = arrival_time
        packet_count = packet_count + 1
        packet_lengths.append(float(len(pkt)))

        if "IP" in pkt:
            if pkt["IP"].src == cic_portscan_source:
                cic_portscan_from_source = True

            src_ip_as_int = int(ipaddress.IPv4Address(pkt["IP"].src))
            dst_ip_as_int = int(ipaddress.IPv4Address(pkt["IP"].dst))
            src_IPs[src_ip_as_int//IPs_per_bin] = 1
            dst_IPs[dst_ip_as_int//IPs_per_bin] = 1
            if "TCP" in pkt:
                TCP_count = TCP_count + 1
                src_ports[int(pkt["TCP"].sport)//ports_per_bin] = 1
                dst_ports[int(pkt["TCP"].dport)//ports_per_bin] = 1
                if pkt["TCP"].flags & SYN:
                    SYN_count = SYN_count + 1
                if pkt["TCP"].flags & FIN:
                    FIN_count = FIN_count + 1
            elif "UDP" in pkt:
                UDP_count = UDP_count + 1
                src_ports[int(pkt["UDP"].sport)//ports_per_bin] = 1
                dst_ports[int(pkt["UDP"].dport)//ports_per_bin] = 1

        if arrival_time > (time_frame_counter*time_frame):
            time_frame_counter = arrival_time // time_frame + 1

            #write features to np array and reset their values
            if not is_cic_portscan or (is_cic_portscan and cic_portscan_from_source and SYN_count > (pps_threshold*time_frame)):
                feature_values = np.append(feature_values, np.array([packet_count, TCP_count, UDP_count, np.mean(IATs), np.var(IATs), np.sum(src_IPs), np.sum(dst_IPs), np.sum(src_ports), np.sum(dst_ports), SYN_count, FIN_count, np.mean(packet_lengths), np.var(packet_lengths)]).reshape(1, len(features)), axis=0)
                        
            packet_count = 0.0
            TCP_count = 0.0
            SYN_count = 0.0
            FIN_count = 0.0
            UDP_count = 0.0
            IATs = [0.0]
            src_IPs = [0.0]*1000
            src_ports = [0.0]*1000
            dst_IPs = [0.0]*1000
            dst_ports = [0.0]*1000
            packet_lengths = [0.0]

    #Save dataframe as cic_friday_{timeframeduration}
    df = pd.DataFrame(feature_values, columns=features)
    df.to_csv(f"./training/{naming_scheme}_{index}_{time_frame}.csv", index=False)
    return df

#Parse command line arguments and create list of parameter sets
#First argument: Directory of pcap files
#Second argument: naming scheme of output files
#Third argument: Number of bins
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process input.')
    parser.add_argument('pcap_dir', type=str, help='Directory of pcap files')
    parser.add_argument('output_name', type=str, help='Naming scheme of output files')
    args = parser.parse_args()

    output_name = args.output_name

    #Create list of parameter sets
    pcap_files = glob.glob(args.pcap_dir + "/*")
    parameter_sets = []
    for time_frame in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]:
        for i in range(len(pcap_files)):
            parameter_sets.append([pcap_files[i], i, time_frame, output_name])

    #Create dataset for each parameter set
    start_time = time.time()
    with mp.Pool(mp.cpu_count()) as pool:
        results = pool.starmap(create_dataset, parameter_sets)
    print(f"Finished in {time.time() - start_time} seconds")