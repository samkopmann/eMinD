import numpy as np
import pandas as pd
import scapy.all as scapy
import multiprocessing as mp
import ipaddress
import datetime


time_frame = 1.0


def flow_key_from_five_tuple(ip_src, ip_dst, port_src, port_dst, protocol):
    return f"{ip_src}_{ip_dst}_{port_src}_{port_dst}_{protocol}"


def analyze(pcap_file):

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
    df.to_csv(f"cic-ddos/flows_per_second_cic.csv", index=False)

    df = pd.DataFrame(flow_churn, columns=None)
    df.to_csv(f"cic-ddos/flow_churn_per_second_cic.csv", index=False)


analyze(('../data/cic-ddos/Friday-WorkingHours-DDoS.pcap'))