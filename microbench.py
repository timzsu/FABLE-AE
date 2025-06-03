import matplotlib.pyplot as plt
import scienceplots
from matplotlib import font_manager
plt.style.use(['science', 'grid', 'light', 'no-latex'])

import os
from collections import defaultdict 
import numpy as np
from pathlib import Path

font_manager.fontManager.addfont(Path(__file__).parent / "fonts/Times New Roman.ttf")
plt.rcParams.update({'font.family': "Times New Roman"})

our_name = "FABLE"
our_name_lut = our_name + r" ($\sigma=\delta$, 32 threads)"
our_name_doram = our_name + r" ($\sigma=64$, 16 threads)"
logs_fable_folder = Path(__file__).parent / "logs/main"
logs_baseline_folder = Path(__file__).parent / "logs/baseline"
num_repeats = 1
plot_folder = Path(__file__).parent / "plots"
os.makedirs(plot_folder, exist_ok=True)

server_name_conversion = {
    "Protocol Preparation" : "Protocol Preparation", 
    "Input Preparation" : "Input Preparation", 
    "Deduplicate" : "Deduplication", 
    "OPRF Evaluation" : "OPRF Evaluation", 
    "Server Setup": "Server Setup", 
    "Query Communication": "Query Communication",
    "Answer Computation": "Answer Computation",
    "Answer Communication": "Answer Communication",
    "Share Conversion": "Share Conversion",
    "Share Retrieval": "Share Retrieval",
    "Decode": "Decoding",
    "Mapping": "Mapping",
    "FABLE Execution": "FABLE",
    "Verification": "Verification",
}

client_name_conversion = {
    "Deduplicate" : "Deduplication", 
    "OPRF Evaluation" : "OPRF Evaluation", 
    "Query Computation": "Query Computation",
    "Query Communication": "Query Communication",
    "Answer Communication": "Answer Communication",
    "Extraction": "Extract",
    "Share Conversion": "Share Conversion",
    "Share Retrieval": "Share Retrieval",
    "Decode": "Decoding",
    "Mapping": "Mapping",
    "FABLE Execution": "FABLE",
    "Verification": "Verification",
}

component_list = ['Deduplication', 'OPRF Evaluation', 'Server Setup', 'Query', 'Answer', 'Extract', 'Share Conversion', 'Decoding', 'Mapping']

def read_single_log(log_file_path, name_conversion: dict[str, str] = {"FABLE Execution": "FABLE"}) -> tuple[defaultdict[str, np.ndarray], defaultdict[str, np.ndarray]]:
    assert Path(log_file_path).exists(), f"Log file {log_file_path} does not exist."
    with open(log_file_path, 'r') as file:
        lines = file.readlines()
    
    time_list = defaultdict(lambda : [])
    comm_list = defaultdict(lambda : [])

    i = 0
    while i < len(lines):
        for name, print_name in name_conversion.items():
            if lines[i].startswith(name):
                if i + 2 < len(lines) and lines[i + 1].strip().startswith("elapsed"):
                    time_ms = int(lines[i + 1].strip().split()[1])
                    bytes = int(lines[i + 2].strip().split()[1])
                    time_list[print_name].append(time_ms)
                    comm_list[print_name].append(bytes)
                i += 2
                break
        i += 1
    
    for name in name_conversion.values():
        time_list[name] = np.array(time_list[name])
        comm_list[name] = np.array(comm_list[name])

    return time_list, comm_list

def log_name(inbit: int, outbit: int, network: int, bs: int, thr: int, hash_type: int, repeat_id: int) -> Path:
    return logs_fable_folder / f"in{inbit}-out{outbit}-netconf{network+1}-bs{bs}-thr{thr}-h{hash_type}-{repeat_id+1}.log"

buffer = {}
def read_log(inbit: int, outbit: int, network: int, bs: int, thr: int, hash_type: int, name_conversion: dict[str, str], comm: bool) -> dict[str, np.ndarray]:
    if (inbit, outbit, network, bs, thr, hash_type) not in buffer:
        log_result = []
        for repeat_id in range(num_repeats):
            log_file_path = log_name(inbit, outbit, network, bs, thr, hash_type, repeat_id)
            log_result.append(read_single_log(log_file_path, name_conversion))
        
        time_list, comm_list = list(zip(*log_result))

        assert len(time_list) == num_repeats, f"Number of repeats {len(time_list)} does not match expected {num_repeats}."

        avg_time_list: dict[str, np.ndarray] = {}
        avg_comm_list: dict[str, np.ndarray] = {}
        # collect from time_list and comm_list
        for key in name_conversion.values():
            avg_time_list[key] = sum([time_list[k][key] for k in range(len(time_list))]) / len(time_list)
            avg_comm_list[key] = sum([comm_list[k][key] for k in range(len(comm_list))]) / len(comm_list)
            if isinstance(avg_time_list[key], np.ndarray):
                avg_time_list[key] = avg_time_list[key].item()
            if isinstance(avg_comm_list[key], np.ndarray):
                avg_comm_list[key] = avg_comm_list[key].item()
        buffer[(inbit, outbit, network, bs, thr, hash_type)] = (avg_time_list, avg_comm_list)

    return buffer[(inbit, outbit, network, bs, thr, hash_type)][int(comm)]

num_threads = [2**i for i in range(6)]
avg_time_3Gbps = [read_log(24, 24, 0, 4096, thr, 0, server_name_conversion, comm=False)[our_name] / 1e3 for thr in num_threads]
avg_time_100Mbps = [read_log(24, 24, 3, 4096, thr, 0, server_name_conversion, comm=False)[our_name] / 1e3 for thr in num_threads]

plt.figure()
plt.plot(num_threads, avg_time_3Gbps, label="LAN", marker='o')
plt.plot(num_threads, avg_time_100Mbps, label="WAN", marker='^')
plt.xlabel("Number of Threads", fontweight='bold')
plt.xscale('log')
plt.xticks(num_threads, labels=[f"$2^{i}$" for i in range(6)])
plt.ylabel("Time (s)", fontweight='bold')
plt.yscale('log')
plt.yticks([100, 1000])
plt.legend()
plt.tight_layout()
plt.savefig(plot_folder / "runtime_vs_threads.pdf")
plt.clf()