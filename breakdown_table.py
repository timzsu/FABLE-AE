import os, glob
from collections import defaultdict 
import numpy as np
from pathlib import Path
import pandas as pd
from argparse import ArgumentParser

parser = ArgumentParser(description="Draw plots from FABLE logs.")
parser.add_argument("--num-repeats", type=int, default=1, help="Number of repeats for each log file.")
parser.add_argument("--aes", action="store_true", help="Use AES.")
parser.add_argument("--latex", action="store_true", help="Output LaTeX table.")
args = parser.parse_args()

logs_fable_folder = Path(__file__).parent / "logs/main"
logs_fable_client_folder = Path(__file__).parent / "logs/client/main"
lut_bitlengths = [20, 24, 28]
lut_sizes = [2**i for i in lut_bitlengths]

server_name_conversion = {
    "Deduplicate" : "\\deduplication", 
    "OPRF Evaluation" : "\\oprfeval", 
    "Server Setup": "\\setup", 
    "Query Communication": "Query Communication",
    "Answer Computation": "Answer Computation",
    "Answer Communication": "Answer Communication",
    "Share Conversion": "Share conversion",
    "Share Retrieval": "Share Retrieval",
    "Decode": "\\decode",
    "Mapping": "\\expansion",
    "FABLE Execution": "End-to-End",
    "Verification": "Verification",
}

client_name_conversion = {
    "Deduplicate" : "\\deduplication", 
    "OPRF Evaluation" : "\\oprfeval", 
    "Query Computation": "Query Computation",
    "Query Communication": "Query Communication",
    "Answer Communication": "Answer Communication",
    "Extraction": "\\extract",
    "Share Conversion": "Share conversion",
    "Share Retrieval": "Share Retrieval",
    "Decode": "\\decode",
    "Mapping": "\\expansion",
    "FABLE Execution": "End-to-End",
    "Verification": "Verification",
}

component_list = [
    '\\deduplication', 
    '\\oprfeval', 
    '\\setup', 
    'Query Computation', 
    'Query Communication', 
    'Answer Computation', 
    'Answer Communication', 
    '\\extract', 
    'Share conversion', 
    '\\decode', 
    '\\expansion', 
    'Client Work', 
    'Server Work', 
    'End-to-End'
]

party_map = {
    "\\deduplication": "\\bothpattern",
    "\\oprfeval": "\\bothpattern",
    "\\setup": "\\serverpattern",
    "Query Computation": "\\clientpattern",
    "Query Communication": "\\bothpattern",
    "Answer Computation": "\\serverpattern",
    "Answer Communication": "\\bothpattern",
    "\\extract": "\\clientpattern",
    "Share conversion": "\\bothpattern",
    "\\decode": "\\bothpattern",
    "\\expansion": "\\bothpattern",
}

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

def client_log_name(inbit: int, outbit: int, network: int, bs: int, thr: int, hash_type: int, repeat_id: int) -> Path:
    return logs_fable_client_folder / f"in{inbit}-out{outbit}-netconf{network+1}-bs{bs}-thr{thr}-h{hash_type}-{repeat_id+1}.log"

client_buffer = {}
def read_client_log(inbit: int, outbit: int, network: int, bs: int, thr: int, hash_type: int, name_conversion: dict[str, str], comm: bool) -> dict[str, np.ndarray]:
    if (inbit, outbit, network, bs, thr, hash_type) not in client_buffer:
        log_result = []
        for repeat_id in range(args.num_repeats):
            log_file_path = client_log_name(inbit, outbit, network, bs, thr, hash_type, repeat_id)
            log_result.append(read_single_log(log_file_path, name_conversion))
        
        time_list, comm_list = list(zip(*log_result))

        assert len(time_list) == args.num_repeats, f"Number of repeats {len(time_list)} does not match expected {args.num_repeats}."

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

def log_name(inbit: int, outbit: int, network: int, bs: int, thr: int, hash_type: int, repeat_id: int) -> Path:
    return logs_fable_folder / f"in{inbit}-out{outbit}-netconf{network+1}-bs{bs}-thr{thr}-h{hash_type}-{repeat_id+1}.log"
    
buffer = {}
def read_log(inbit: int, outbit: int, network: int, bs: int, thr: int, hash_type: int, name_conversion: dict[str, str], comm: bool) -> dict[str, np.ndarray]:
    if (inbit, outbit, network, bs, thr, hash_type) not in buffer:
        log_result = []
        for repeat_id in range(args.num_repeats):
            log_file_path = log_name(inbit, outbit, network, bs, thr, hash_type, repeat_id)
            log_result.append(read_single_log(log_file_path, name_conversion))
        
        time_list, comm_list = list(zip(*log_result))

        assert len(time_list) == args.num_repeats, f"Number of repeats {len(time_list)} does not match expected {args.num_repeats}."

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

avg_time_server_list = defaultdict(float,
    {
        key: np.array([
        [read_log(lut_bitlength, lut_bitlength, network_idx, 4096, 32, int(args.aes), server_name_conversion, comm=False)[key]
        for lut_bitlength in lut_bitlengths] 
        for network_idx in [0, 3]]) / 1000 # [network index][lut index]
        for key in server_name_conversion.values()
    }
)
avg_comm_server_list = defaultdict(float,
    {
        key: np.array([
        [read_log(lut_bitlength, lut_bitlength, network_idx, 4096, 32, int(args.aes), server_name_conversion, comm=True)[key]
        for lut_bitlength in lut_bitlengths] 
        for network_idx in [0, 3]]).mean(0) / (2**20) # [network index][lut index]
        for key in server_name_conversion.values()
    }
)
avg_time_client_list = defaultdict(float,
    {
        key: np.array([
        [read_client_log(lut_bitlength, lut_bitlength, network_idx, 4096, 32, int(args.aes), client_name_conversion, comm=False)[key]
        for lut_bitlength in lut_bitlengths] 
        for network_idx in [0, 3]]) / 1000 # [network index][lut index]
        for key in client_name_conversion.values()
    }
)
avg_comm_client_list = defaultdict(float,
    {
        key: np.array([
        [read_client_log(lut_bitlength, lut_bitlength, network_idx, 4096, 32, int(args.aes), client_name_conversion, comm=True)[key]
        for lut_bitlength in lut_bitlengths] 
        for network_idx in [0, 3]]).mean(0) / (2**20) # [network index][lut index]
        for key in client_name_conversion.values()
    }
)

def choose_component(name: str, is_time: bool = True):
    if name in server_name_conversion.values():
        return avg_time_server_list[name] if is_time else (avg_comm_server_list[name] + avg_comm_client_list[name])
    elif name in client_name_conversion.values():
        return avg_time_client_list[name] if is_time else (avg_comm_server_list[name] + avg_comm_client_list[name])
    elif name == "Query":
        return avg_time_client_list["Query Computation"] if is_time else avg_comm_client_list["Query Communication"]
    elif name == "Answer":
        return avg_time_server_list["Answer Computation"] if is_time else avg_comm_server_list["Answer Communication"]

component_time_s = {key: choose_component(key, True) for key in component_list if key not in ["Client Work", "Server Work"]}
component_comm_mb = {key: choose_component(key, False) for key in component_list if key not in ["Client Work", "Server Work"]}

component_time_s["Client Work"] = sum(component_time_s[k] for k in party_map.keys() if party_map[k] == "\\clientpattern" or party_map[k] == "\\bothpattern")
component_time_s["Server Work"] = sum(component_time_s[k] for k in party_map.keys() if party_map[k] == "\\serverpattern" or party_map[k] == "\\bothpattern")
component_comm_mb["Client Work"] = sum(component_comm_mb[k] for k in party_map.keys() if party_map[k] == "\\clientpattern" or party_map[k] == "\\bothpattern")
component_comm_mb["Server Work"] = sum(component_comm_mb[k] for k in party_map.keys() if party_map[k] == "\\serverpattern" or party_map[k] == "\\bothpattern")

lan_speed = 3 * 2**10 / 8
wan_speed = 100 / 8
latency = [0.0008, 0.040]
def extract_time(key, idx, wan=False):
    wan = int(wan)
    if key == "Query" or key == "Answer":

        pir_comm_time = component_time_s["End-to-End"][wan, idx] - sum(
            component_time_s[k][wan, idx]
            for k in component_list if k not in ["Client Work", "Server Work", "End-to-End"]
        ) - 2 * latency[wan]
        rate = (component_comm_mb["Query"][idx] + component_comm_mb["Answer"][idx]) / pir_comm_time

        return "{:.2f} ({:.2f})".format(component_time_s[key][wan, idx] + component_comm_mb[key][idx] / rate + latency[wan], component_time_s[key][wan, idx])
    else:
        return "{:.2f}".format(component_time_s[key][wan, idx])

data = {}
for idx, lutsize in enumerate(['20-bit', '24-bit', '28-bit']):
    data = data | {
        (lutsize, 'Time', 'LAN1'): np.array([extract_time(key, idx, False) for key in component_list]),
        (lutsize, 'Time', 'WAN2'): np.array([extract_time(key, idx, True) for key in component_list]),
        (lutsize, 'Comm.', ''): np.array(["{:.2f}".format(component_comm_mb[key][idx]) for key in component_list])
    }

# df = pd.DataFrame(data, index=component_list).round(2)
df = pd.DataFrame(data).round(2)
df.columns = pd.MultiIndex.from_tuples(df.columns, names=['LUT Size', '', ''])
df.replace(0.00, np.nan, inplace=True)

df.insert(0, ('placeholder'), component_list)
df.insert(0, (''), [party_map[key] for key in component_list if key not in ["Client Work", "Server Work", "End-to-End"]] + ["" for _ in range(3)])

if args.latex:
    latex_table = df.to_latex(
        multicolumn=True,
        index=False, 
        column_format="c|ccc|ccc|ccc",
        multicolumn_format="c",
        caption=r"End-to-end performances breakdown. The table has $\inputbits=\outputbits$ and the batch size is $\\batchsize=4096$. The server uses 32 threads. The components are listed following the execution order, with the parties involved marked on the left. For \query and \\answer, we include the local computation time in parentheses after the total time. We mark a 2PC procedure with \\bothpattern, while \serverpattern~and \clientpattern~indicate the procedure is executed locally by the server and client respectively.",
        label="tab:breakdown",
        position="htbp",
        na_rep='-'
    ).replace("placeholder", "")
    print(latex_table)
else:
    markdown_table = df.to_markdown(
        index=False, 
    ).replace("placeholder", "")
    print(markdown_table)