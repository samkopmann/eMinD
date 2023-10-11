import numpy as np
import pandas as pd
import scapy.all as scapy
import multiprocessing as mp
import ipaddress
import datetime

time_frame = 1.0


def flow_key_from_five_tuple(ip_src, ip_dst, port_src, port_dst, protocol):
    return f"{ip_src}_{ip_dst}_{port_src}_{port_dst}_{protocol}"


def analyze(pcap_file, index):

    flow_count = []
    flow_churn = []

    active_flows = {}
    old_active_flows = {}

    first_arrival_time = 0.0
    time_frame_counter = 0

    for pkt in scapy.PcapReader(pcap_file):
      
  
        if first_arrival_time == 0.0:
            first_arrival_time = float(pkt.time)
        arrival_time = float(pkt.time) - first_arrival_time

        if "IP" in pkt:
            src_ip = str(ipaddress.IPv4Address(pkt["IP"].src))
            dst_ip = str(ipaddress.IPv4Address(pkt["IP"].dst))

            if "TCP" in pkt:
                src_port = str(pkt["TCP"].sport)
                dst_port = str(pkt["TCP"].dport)
                flow_key = flow_key_from_five_tuple(src_ip, dst_ip, src_port, dst_port, "TCP")
                active_flows[flow_key] = 1
            elif "UDP" in pkt:
                src_port = str(pkt["UDP"].sport)
                dst_port = str(pkt["UDP"].dport)
                flow_key = flow_key_from_five_tuple(src_ip, dst_ip, src_port, dst_port, "UDP")
                active_flows[flow_key] = 1

        if arrival_time > (time_frame_counter*time_frame):
            flow_count.append(len(active_flows))
            old_flows = set(old_active_flows.keys())
            new_flows = set(active_flows.keys())

            number_of_vanishing_flows = len(list(old_flows.difference(new_flows)))
            number_of_new_flows = len(list(new_flows.difference(old_flows)))
            
            flow_churn.append(number_of_vanishing_flows + number_of_new_flows)
            
            old_active_flows = active_flows
            active_flows = {}

            time_frame_counter = time_frame_counter + 1

        

    #Save dataframe as cic_friday_{timeframeduration}
    df = pd.DataFrame(flow_count, columns=None)
    df.to_csv(f"mawi-ddos/flows_per_second_caida_{index}.csv", index=False)

    df = pd.DataFrame(flow_churn, columns=None)
    df.to_csv(f"mawi-ddos/flow_churn_per_second_caida_{index}.csv", index=False)

files = ["_00000_20230302060000",
         "_00001_20230302060100",
         "_00002_20230302060200",
         "_00003_20230302060300",
         "_00004_20230302060400",
         "_00005_20230302060500",
         "_00006_20230302060600",
         "_00007_20230302060700",
         "_00008_20230302060800",
         "_00009_20230302060900",
         "_00010_20230302061000",
         "_00011_20230302061100",
         "_00012_20230302061200",
         "_00013_20230302061300",
         "_00014_20230302061400",]
parameter_sets = []
for file in files:
    parameter_sets.append(('../data/mawi-ddos/' + file, files.index(file)))

print("Number of parameter sets: %s" % len(parameter_sets))

awaited_results = []
with mp.Pool(processes=15) as pool:
    multiple_results = [pool.apply_async(analyze, (parameter_sets[i])) for i in range(len(parameter_sets))]
    awaited_results = [np.array(res.get(timeout=360000)) for res in multiple_results]