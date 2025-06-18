from collections import defaultdict 
import numpy as np
import re
from pathlib import Path
from argparse import ArgumentParser
from typing import Dict, Tuple, DefaultDict

parser = ArgumentParser(description="Application Reader")
parser.add_argument("--crypten-baseline", action="store_true", help="Use self benchmarked baseline numbers.")
parser.add_argument("--num-repeats", type=int, default=1, help="Number of repeats for each log file.")
args = parser.parse_args()

logs_applications_folder = Path(__file__).parent / "logs/applications"
num_repeats = args.num_repeats

def read_single_log(log_file_path, name_conversion: Dict[str, str] = {"FABLE Execution": "FABLE"}) -> Tuple[DefaultDict[str, np.ndarray], DefaultDict[str, np.ndarray]]:
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

buffer = {}
def read_log(prefix: str, name_conversion: Dict[str, str]) -> Dict[str, np.ndarray]:
    if not isinstance(prefix, str):
        prefix = str(prefix)
    if prefix not in buffer:
        log_result = []
        for repeat_id in range(num_repeats):
            log_file_path = prefix + f"-{repeat_id+1}.log"
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
        buffer[prefix] = avg_time_list

    return buffer[prefix]

def read_crypten_baseline_log(netconf: int) -> float:
    mt_log_path = Path(__file__).parent / f"logs/applications/embedding-baseline-mt-netconf{netconf}.log"
    online_log_path = Path(__file__).parent / f"logs/applications/embedding-baseline-online-netconf{netconf}.log"

    online_time = 0.0
    num_arith_mt = 0
    num_binary_mt = 0
    mt_times = []

    for line in open(online_log_path).readlines():
        match = re.match(r"Total: elapsed ([\d\.]+) s", line)
        if match:
            online_time = float(match.group(1))

        match = re.match(r"Num arithmetic triples generated = (\d+)", line)
        if match:
            num_arith_mt = int(match.group(1))
            
        match = re.match(r"Num binary triples generated = (\d+)", line)
        if match:
            num_binary_mt = int(match.group(1))
    
    for line in open(mt_log_path).readlines():
        match = re.match(r"Circuit Evaluation\ +([\d\.]+) ms\ +([\d\.]+) ms\ +([\d\.]+) ms", line)
        if match:
            mt_times.append(float(match.group(1)) / (2**16))

    assert len(mt_times) == 2
    setup_time = (mt_times[0] * num_arith_mt + mt_times[1] * num_binary_mt) / 1e3

    return setup_time + online_time

if args.crypten_baseline:
    embedding_baseline_lan_time = read_crypten_baseline_log(1)
    embedding_baseline_wan_time = read_crypten_baseline_log(4)
else:
    embedding_baseline_lan_time = 12868
    embedding_baseline_wan_time = 109774
embedding_fable_lan_time = read_log(logs_applications_folder / "embedding-FABLE-netconf1", {"Embedding Lookup": "Embedding Lookup"})["Embedding Lookup"] / 1e3
embedding_fable_wan_time = read_log(logs_applications_folder / "embedding-FABLE-netconf4", {"Embedding Lookup": "Embedding Lookup"})["Embedding Lookup"] / 1e3

print(f"Embedding FABLE LAN Time: {embedding_fable_lan_time} s, speedup: {embedding_baseline_lan_time / embedding_fable_lan_time:.2f}x")
print(f"Embedding FABLE WAN Time: {embedding_fable_wan_time} s, speedup: {embedding_baseline_wan_time / embedding_fable_wan_time:.2f}x")

join_baseline_lan_time = read_log(logs_applications_folder / "join-baseline-netconf1", {"Join": "Join"})["Join"] / 1e3
join_baseline_wan_time = read_log(logs_applications_folder / "join-baseline-netconf4", {"Join": "Join"})["Join"] / 1e3
join_fable_lan_time = read_log(logs_applications_folder / "join-FABLE-netconf1", {"Join": "Join"})["Join"] / 1e3
join_fable_wan_time = read_log(logs_applications_folder / "join-FABLE-netconf4", {"Join": "Join"})["Join"] / 1e3

print(f"Join FABLE LAN Time: {join_fable_lan_time} s, speedup: {join_baseline_lan_time / join_fable_lan_time:.2f}x")
print(f"Join FABLE WAN Time: {join_fable_wan_time} s, speedup: {join_baseline_wan_time / join_fable_wan_time:.2f}x")