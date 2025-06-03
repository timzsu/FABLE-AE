import matplotlib.pyplot as plt
import scienceplots
from matplotlib import font_manager
plt.style.use(['science', 'grid', 'no-latex', 'light'])

import os, json
from collections import defaultdict 
import numpy as np
from pathlib import Path

our_name = "FABLE"
our_name_lut = our_name + r" ($\sigma=\delta$, 32 threads)"
our_name_doram = our_name + r" ($\sigma=64$, 16 threads)"
logs_fable_folder = Path(__file__).parent / "logs/main"
logs_baseline_folder = Path(__file__).parent / "logs/baseline"
num_repeats = 1
plot_folder = Path(__file__).parent / "plots"
os.makedirs(plot_folder, exist_ok=True)

log_batch_sizes = np.array([0] + list(range(8, 13)))
batch_sizes = 2 ** log_batch_sizes
lut_bitlengths = [20, 24, 28]
lut_sizes = [2**i for i in lut_bitlengths]

font_manager.fontManager.addfont(Path(__file__).parent / "fonts/Times New Roman.ttf")

plt.rcParams.update({'font.size': 12})
plt.rcParams.update({'font.family': "Times New Roman"})

def marker_gen():
    marker = ['o', 's', 'D', '^', 'X', 'P', 'H', '<', 'v', '>']
    for m in marker:
        yield m

def hatch_gen():
    hatch = ['/', 'o', '\\', '|', 'x', '*', '|', 'O', '+', '.']
    for h in hatch:
        yield h

def linestyle_gen():
    linestyle = ['-', '--', '-.', ':', (0, (5, 5)), (0, (3, 5, 1, 5))]
    for ls in linestyle:
        yield ls

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

def splut_log_name(inbit: int, outbit: int, network: int, bs: int, thr: int, repeat_id: int) -> Path:
    return logs_baseline_folder / f"splut-in{inbit}-out{outbit}-netconf{network+1}-bs{bs}-thr{thr}-{repeat_id+1}.log"

splut_buffer = {}
def read_splut_log(inbit: int, outbit: int, network: int, bs: int, thr: int, name_conversion: dict[str, str], comm: bool) -> dict[str, np.ndarray]:
    if (inbit, outbit, network, bs, thr) not in splut_buffer:
        log_result = []
        for repeat_id in range(num_repeats):
            log_file_path = splut_log_name(inbit, outbit, network, bs, thr, repeat_id)
            log_result.append(read_single_log(log_file_path, name_conversion))
        
        time_list, comm_list = list(zip(*log_result))

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
        splut_buffer[(inbit, outbit, network, bs, thr)] = (avg_time_list, avg_comm_list)

    return splut_buffer[(inbit, outbit, network, bs, thr)][int(comm)]

def draw_time_bs_big(data: list[tuple], baseline: list[dict], folder: str, ylim: tuple[float, float], yticks: list[int], ncols: int) -> None: 
    orig_fontsize = plt.rcParams.get('font.size')
    plt.rcParams.update({'font.size': 14})
    fig, axs = plt.subplots(2, 2, gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.02, 'hspace': 0.05})
    fig.set_size_inches(9, 7.5)
    fig.text(0.06, 0.5, 'Amortized Running Time (ms)', ha='center', va='center', rotation='vertical', fontweight='bold', fontsize=20)
    fig.text(0.5, 0.05, 'Batch Size', ha='center', va='center', fontweight='bold', fontsize=20)

    colors = ['#CC6677', '#332288', '#882255', '#44AA99', '#999933', '#AA4499']
    color_cnt = 0

    mgen = marker_gen()

    for row in range(len(data)):
        m = next(mgen)
        axs[0, row].plot(batch_sizes, data[row][0] / batch_sizes, label=our_name_doram if row else our_name_lut, marker=m, color=colors[color_cnt], linestyle='solid', lw=3)
        axs[1, row].plot(batch_sizes, data[row][1] / batch_sizes, label=our_name_doram if row else our_name_lut, marker=m, color=colors[color_cnt], linestyle='solid', lw=3)
        color_cnt += 1
        for name, (lan, wan) in baseline[row].items():
            m = next(mgen)
            axs[0, row].plot(batch_sizes, [lan for _ in batch_sizes], label=name, marker=m, color=colors[color_cnt], linestyle='dashed', lw=3)
            axs[1, row].plot(batch_sizes, [wan for _ in batch_sizes], label=name, marker=m, color=colors[color_cnt], linestyle='dashed', lw=3)
            color_cnt += 1
        
        axs[row, 0].set_xscale('log')
        axs[row, 0].set_yscale('log')
        axs[row, 0].set_ylim(ylim)
        axs[row, 0].set_yticks(yticks)

        axs[row, 1].set_xscale('log')
        axs[row, 1].set_yscale('log')
        axs[row, 1].set_ylim(ylim)
        axs[row, 1].set_yticks(yticks)
        axs[row, 1].tick_params(axis='y', labelright=True, labelleft=False)

    axs[0, 1].set_ylabel(r'LAN', fontweight='bold', fontsize=20, rotation=270, labelpad=18)
    axs[1, 1].set_ylabel(r'WAN', fontweight='bold', fontsize=20, rotation=270, labelpad=18)
    axs[0, 1].yaxis.set_label_position("right")
    axs[1, 1].yaxis.set_label_position("right")
    axs[0, 0].set_xticks(batch_sizes, labels=[f"$2^{{{i}}}$" for i in log_batch_sizes])
    axs[0, 1].set_xticks(batch_sizes, labels=[f"$2^{{{i}}}$" for i in log_batch_sizes])
    # axs[0, 0].xaxis.tick_top()
    # axs[0, 1].xaxis.tick_top()
    axs[0, 0].tick_params(labelbottom=False)   
    axs[0, 1].tick_params(labelbottom=False)   
    axs[1, 0].set_xticks(batch_sizes, labels=[f"$2^{{{i}}}$" for i in log_batch_sizes])
    axs[1, 1].set_xticks(batch_sizes, labels=[f"$2^{{{i}}}$" for i in log_batch_sizes])
    for ax in axs.flatten(): 
        ax.tick_params(axis='y', which='major', labelsize=16)
        ax.tick_params(axis='x', which='major', labelsize=15)

    handles0, labels0 = axs[0, 0].get_legend_handles_labels()
    handles1, labels1 = axs[0, 1].get_legend_handles_labels()
    handles = handles0 + handles1
    labels = labels0 + labels1
    handles[2], handles[3] = handles[3], handles[2]
    labels[2], labels[3] = labels[3], labels[2]
    # fig.legend(handles0 + handles1, labels0 + labels1, loc='upper center', ncol=ncols, fontsize=10, bbox_to_anchor=(0.5, 1.05))
    fig.legend(handles, labels, loc='upper center', ncol=ncols, bbox_to_anchor=(0.5, 1.06), fontsize=18)
    fig.savefig(os.path.join(folder, "24_time_bs.pdf"))
    plt.rcParams.update({'font.size': orig_fontsize})

def draw_comm_big(data: list[tuple], baseline: list[dict], folder: str, ylims: list[tuple[float, float]], yticks: list[list[int]], ncols: int): 
    fig, axs = plt.subplots(2, 2, gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.03, 'hspace': 0.03})
    fig.set_size_inches(9, 7.5)
    fig.text(0.06, 0.5, 'Amortized Communication (KB)', ha='center', va='center', rotation='vertical', fontweight='bold', fontsize=20)

    colors = ['#CC6677', '#332288', '#117733', '#882255', '#44AA99', '#999933', '#AA4499']
    color_cnt = 0

    mgen = marker_gen()

    for row in range(len(data)):
        m = next(mgen)
        axs[row, 0].plot(batch_sizes, data[row][0] / batch_sizes, label=our_name_doram if row else our_name_lut, marker=m, color=colors[color_cnt], linestyle='solid', lw=3)
        axs[row, 1].plot(lut_sizes, data[row][1] / 4096, label=our_name_doram if row else our_name_lut, marker=m, color=colors[color_cnt], linestyle='solid', lw=3)
        color_cnt += 1
        for name, comm in baseline[row].items():
            m = next(mgen)
            axs[row, 0].plot(batch_sizes, [comm[1] for _ in batch_sizes], label=name, marker=m, color=colors[color_cnt], linestyle='dashed', lw=3)
            axs[row, 1].plot(lut_sizes, comm, label=name, marker=m, color=colors[color_cnt], linestyle='dashed', lw=3)
            color_cnt += 1
        
        axs[row, 0].set_xscale('log')
        axs[row, 0].set_yscale('log')
        axs[row, 0].set_ylim(ylims[row])
        axs[row, 0].set_yticks(yticks[row])

        axs[row, 1].set_xscale('log')
        axs[row, 1].set_yscale('log')
        axs[row, 1].set_ylim(ylims[row])
        axs[row, 1].set_yticks(yticks[row])
        axs[row, 1].tick_params(axis='y', labelright=True, labelleft=False)

    axs[0, 0].set_xticks(batch_sizes, labels=[f"$2^{{{i}}}$" for i in log_batch_sizes])
    axs[0, 1].set_xticks(lut_sizes, labels=[f"$2^{{{i}}}$" for i in lut_bitlengths])
    axs[0, 0].xaxis.tick_top()
    axs[0, 1].xaxis.tick_top()
    axs[1, 0].set_xlabel("Batch Size", fontweight='bold', fontsize=20)
    axs[1, 0].set_xticks(batch_sizes, labels=[f"$2^{{{i}}}$" for i in log_batch_sizes])
    axs[1, 1].set_xlabel("LUT Size", fontweight='bold', fontsize=20)
    axs[1, 1].set_xticks(lut_sizes, labels=[f"$2^{{{i}}}$" for i in lut_bitlengths])
    for ax in axs.flatten(): 
        ax.tick_params(axis='y', which='major', labelsize=16)
        ax.tick_params(axis='x', which='major', labelsize=15)

    handles0, labels0 = axs[0, 0].get_legend_handles_labels()
    handles1, labels1 = axs[1, 0].get_legend_handles_labels()
    handles = handles0 + handles1
    labels = labels0 + labels1
    handles[4], handles[3] = handles[3], handles[4]
    labels[4], labels[3] = labels[3], labels[4]
    fig.legend(
        handles=handles, 
        labels=labels, 
        loc='upper center', ncol=ncols, bbox_to_anchor=(0.5, 1.10), fontsize=18)
    fig.savefig(os.path.join(folder, "comm.pdf"))

def bigfig(lan1_list, lan2_list, wan1_list, wan2_list, folder: str, ylim: tuple[float, float], yticks: list[int], figsize = (14, 7.5), width: float = 0.2, ncol: int = 4, gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.1, 'hspace': 0.05}): 
    orig_fontsize = plt.rcParams.get('font.size')
    plt.rcParams.update({'font.size': 14})
    x = np.arange(len(lut_sizes))  # the label locations
    multiplier = 0
    fig, axs = plt.subplots(2, 2, gridspec_kw=gridspec_kw)
    fig.set_size_inches(figsize)

    ax_00 = axs[0, 0]
    fig.text(0.08, 0.5, 'Time (ms)', ha='center', va='center', rotation='vertical', fontweight='bold', fontsize=20)
    fig.text(0.5, 0.06, 'LUT Size', ha='center', va='center', fontweight='bold', fontsize=20)
    
    lgen = linestyle_gen()
    for lan1 in lan1_list:
        for attribute, measurement in lan1.items():
            offset = width * multiplier
            rects = ax_00.bar(x + offset, measurement, width, label=attribute, edgecolor = "black", linestyle=next(lgen))
            ax_00.bar_label(rects, padding=3, rotation=90, color='black', fmt='%.5g', fontsize=15)
            multiplier += 1
        multiplier += 1
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax_00.set_title(r'LAN', y=1.02, fontweight='bold', fontsize=20)
    ax_00.set_ylabel('3Gbps, 0.8ms', fontsize=20)
    ax_00.set_xticks([])
    ax_00.set_yscale('log')
    ax_00.set_ylim(ylim)
    ax_00.set_yticks(yticks)
    ax_00.tick_params(axis='y', which='major', labelsize=16)
    ax_00.tick_params(axis='y', which='major', labelsize=16)
    ax_00.set_axisbelow(True)
    ax_00.grid(False, which='major', axis='x')
    ax_00.grid(True, which='major', axis='y', ls='dashed')

    multiplier = 0
    ax_10 = axs[1, 0]
    lgen = linestyle_gen()
    for lan2 in lan2_list:
        for attribute, measurement in lan2.items():
            offset = width * multiplier
            rects = ax_10.bar(x + offset, measurement, width, label=attribute, edgecolor = "black", linestyle=next(lgen))
            ax_10.bar_label(rects, padding=2 , rotation=90, color='black', fmt='%.5g', fontsize=15)
            multiplier += 1
        multiplier += 1
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax_10.set_ylabel('1Gbps, 0.8ms', fontsize=20)
    ax_10.set_xticks(x + ((multiplier - 2) / 2) * width, [f"$\\delta={i}$" for i in [20, 24, 28]], fontsize=20)
    ax_10.set_yscale('log')
    ax_10.set_ylim(ylim)
    ax_10.set_yticks(yticks)
    ax_10.tick_params(axis='y', which='major', labelsize=16)
    ax_10.set_axisbelow(True)
    ax_10.grid(False, which='major', axis='x')
    ax_10.grid(True, which='major', axis='y', ls='dashed')

    multiplier = 0
    ax_01 = axs[0, 1]
    lgen = linestyle_gen()
    for wan1 in wan1_list:
        for attribute, measurement in wan1.items():
            offset = width * multiplier
            rects = ax_01.bar(x + offset, measurement, width, label=attribute, edgecolor = "black", linestyle=next(lgen))
            ax_01.bar_label(rects, padding=2 , rotation=90, color='black', fmt='%.5g', fontsize=15)
            multiplier += 1
        multiplier += 1
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax_01.set_title(r'WAN', y=1.02, fontsize=20, fontweight='bold')
    ax_01.set_ylabel('200Mbps, 40ms', fontsize=20)
    ax_01.set_xticks([])
    ax_01.set_yscale('log')
    ax_01.set_ylim(ylim)
    ax_01.set_yticks(yticks)
    ax_01.tick_params(axis='y', which='major', labelsize=16)
    ax_01.tick_params(axis='y', labelright=True, labelleft=False)
    ax_01.set_axisbelow(True)
    ax_01.grid(False, which='major', axis='x')
    ax_01.grid(True, which='major', axis='y', ls='dashed')

    multiplier = 0
    ax_11 = axs[1, 1]
    lgen = linestyle_gen()
    for wan2 in wan2_list:
        for attribute, measurement in wan2.items():
            offset = width * multiplier
            rects = ax_11.bar(x + offset, measurement, width, label=attribute, edgecolor = "black", linestyle=next(lgen))
            ax_11.bar_label(rects, padding=2 , rotation=90, color='black', fmt='%.5g', fontsize=15)
            multiplier += 1
        multiplier += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax_11.set_ylabel('100Mbps, 80ms', fontsize=20)
    ax_11.set_xticks(x + ((multiplier - 2) / 2) * width, [f"$\\delta={i}$" for i in [20, 24, 28]], fontsize=20)
    ax_11.set_yscale('log')
    ax_11.set_ylim(ylim)
    ax_11.set_yticks(yticks)
    ax_11.tick_params(axis='y', which='major', labelsize=16)
    ax_11.tick_params(axis='y', labelright=True, labelleft=False)
    ax_11.set_axisbelow(True)
    ax_11.grid(False, which='major', axis='x')
    ax_11.grid(True, which='major', axis='y', ls='dashed')

    handles, labels = ax_11.get_legend_handles_labels()
    handles[2], handles[3] = handles[3], handles[2]
    labels[2], labels[3] = labels[3], labels[2]
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.09), ncol=ncol, fontsize=18)

    fig.savefig(os.path.join(folder, "time_lutsize_network.pdf"))
    plt.rcParams.update({'font.size': orig_fontsize})

def bigfig_clipped(lan1_list, wan2_list, folder: str, ylim: tuple[float, float], yticks: list[int], figsize = (7, 7.5), width: float = 0.2, ncol: int = 4, gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.1, 'hspace': 0.05}): 
    orig_fontsize = plt.rcParams.get('font.size')
    plt.rcParams.update({'font.size': 14})
    x = np.arange(len(lut_sizes))  # the label locations
    multiplier = 0
    fig, axs = plt.subplots(2, 1, gridspec_kw=gridspec_kw)
    fig.set_size_inches(figsize)

    ax_00 = axs[0]
    fig.text(0.07, 0.5, 'Time (ms)', ha='center', va='center', rotation='vertical', fontweight='bold', fontsize=20)
    fig.text(0.5, 0.05, 'LUT Size', ha='center', va='center', fontweight='bold', fontsize=20)
    
    lgen = linestyle_gen()
    for lan1 in lan1_list:
        for attribute, measurement in lan1.items():
            offset = width * multiplier
            rects = ax_00.bar(x + offset, measurement, width, label=attribute, edgecolor = "black", linestyle=next(lgen))
            ax_00.bar_label(rects, padding=3, rotation=90, color='black', fmt='%.5g', fontsize=15)
            multiplier += 1
        multiplier += 1
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax_00.set_ylabel('LAN', fontsize=20, fontweight='bold', rotation=-90, labelpad=18)
    ax_00.yaxis.set_label_position("right")
    ax_00.set_xticks([])
    ax_00.set_yscale('log')
    ax_00.set_ylim(ylim)
    ax_00.set_yticks(yticks)
    ax_00.tick_params(axis='y', which='major', labelsize=16)
    ax_00.set_axisbelow(True)
    ax_00.grid(False, which='major', axis='x')
    ax_00.grid(True, which='major', axis='y', ls='dashed')

    multiplier = 0
    ax_10 = axs[1]
    lgen = linestyle_gen()
    for wan2 in wan2_list:
        for attribute, measurement in wan2.items():
            offset = width * multiplier
            rects = ax_10.bar(x + offset, measurement, width, label=attribute, edgecolor = "black", linestyle=next(lgen))
            ax_10.bar_label(rects, padding=3, rotation=90, color='black', fmt='%.5g', fontsize=15)
            multiplier += 1
        multiplier += 1
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax_10.set_ylabel('WAN', fontsize=20, fontweight='bold', rotation=-90, labelpad=18)
    ax_10.yaxis.set_label_position("right")
    ax_10.set_xticks(x + ((multiplier - 2) / 2) * width, [f"$\\delta={i}$" for i in [20, 24, 28]], fontsize=20)
    ax_10.set_yscale('log')
    ax_10.set_ylim(ylim)
    ax_10.set_yticks(yticks)
    ax_10.tick_params(axis='y', which='major', labelsize=16)
    ax_10.set_axisbelow(True)
    ax_10.grid(False, which='major', axis='x')
    ax_10.grid(True, which='major', axis='y', ls='dashed')

    handles, labels = ax_00.get_legend_handles_labels()
    handles[2], handles[3] = handles[3], handles[2]
    labels[2], labels[3] = labels[3], labels[2]
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.06), ncol=ncol, fontsize=18)

    fig.set_size_inches(figsize)
    fig.savefig(os.path.join(folder, "time_lutsize_network_clipped.pdf"))
    plt.rcParams.update({'font.size': orig_fontsize})

fable_name_conversion = {"FABLE Execution": our_name}

opt_bs_time_32thr = np.array([
    [read_log(lut_bitlength, lut_bitlength, network_idx, 4096, 32, 0, fable_name_conversion, comm=False)[our_name] 
    for lut_bitlength in lut_bitlengths] 
    for network_idx in range(4)
]) # [network index][lut index]
varyingbs_32thr = np.array([
    [read_log(24, 24, network_idx, bs, 32, 0, fable_name_conversion, comm=False)[our_name] 
    for bs in batch_sizes] 
    for network_idx in [0, 3]
]) # [network index][batch index]

opt_bs_time_16thr = np.array([
    [read_log(lut_bitlength, 64, network_idx, 4096, 16, 0, fable_name_conversion, comm=False)[our_name] 
    for lut_bitlength in lut_bitlengths] 
    for network_idx in range(4)
]) # [network index][lut index]
varyingbs_16thr = np.array([
    [read_log(24, 64, network_idx, bs, 16, 0, fable_name_conversion, comm=False)[our_name] 
    for bs in batch_sizes] 
    for network_idx in [0, 3]
]) # [network index][batch index]

opt_bs_comm_oi = np.array([
    [read_log(lut_bitlength, lut_bitlength, network_idx, 4096, 32, 0, fable_name_conversion, comm=True)[our_name] 
    for lut_bitlength in lut_bitlengths] 
    for network_idx in range(4)
]).mean(0) / (2**10) # [network index][lut index]
varyingbs_comm_oi = np.array([
    [read_log(24, 24, network_idx, bs, 32, 0, fable_name_conversion, comm=True)[our_name] 
    for bs in batch_sizes] 
    for network_idx in [0, 3]
]).mean(0) / (2**10) # [network index][batch index]

opt_bs_comm_o64 = np.array([
    [read_log(lut_bitlength, 64, network_idx, 4096, 16, 0, fable_name_conversion, comm=True)[our_name] 
    for lut_bitlength in lut_bitlengths] 
    for network_idx in range(4)
]).mean(0) / (2**10) # [network index][lut index]
varyingbs_comm_o64 = np.array([
    [read_log(24, 64, network_idx, bs, 16, 0, fable_name_conversion, comm=True)[our_name] 
    for bs in batch_sizes] 
    for network_idx in [0, 3]
]).mean(0) / (2**10) # [network index][batch index]

# Load ORAM jsons
floram_json = json.load(open(Path(__file__).parent / 'ORAMs/floram.json'))
duoram_json = json.load(open(Path(__file__).parent / 'ORAMs/duoram.json'))

splut_name_conversion = {"SPLUT+": "SP-LUT+"}
splut_factors = np.array([256, 16, 1])
splut_avg_time = np.array([
    [read_splut_log(lut_bitlength, lut_bitlength, network_idx, splut_factor, 32, splut_name_conversion, comm=False)["SP-LUT+"] / splut_factor
    for lut_bitlength, splut_factor in zip(lut_bitlengths, splut_factors)] 
    for network_idx in range(4)
]) # [network index][lut index]
splut_avg_comm = np.array([
    [read_splut_log(lut_bitlength, lut_bitlength, network_idx, splut_factor, 32, splut_name_conversion, comm=True)["SP-LUT+"] / splut_factor
    for lut_bitlength, splut_factor in zip(lut_bitlengths, splut_factors)] 
    for network_idx in range(4)
]).mean(0) / (2**10) # [network index][lut index]

flute_comm = np.array([4.236 * (2**l - l - 1) + 2*l for l in lut_bitlengths]) / 8 / (2**10)

# varying batch size

draw_time_bs_big(
    [varyingbs_32thr, varyingbs_16thr], 
    baseline=[
        {
            "SP-LUT+": (splut_avg_time[0, 1], splut_avg_time[3, 1]),
        }, {
            "FLORAM": (floram_json["3Gbps"][1], floram_json["100Mbps"][1]),
            "2P-DUORAM": (duoram_json["3Gbps"][1], duoram_json["100Mbps"][1]),
            "2P-DUORAM+": (duoram_json["3Gbps"][1] / 2, duoram_json["100Mbps"][1] / 2),
    }], 
    folder=plot_folder, 
    ylim=(5, 3*1e5), 
    yticks=[10, 100, 1000, 10000, 1e5], 
    ncols=2
)

draw_comm_big(
    [(varyingbs_comm_oi, opt_bs_comm_oi), (varyingbs_comm_o64, opt_bs_comm_o64)], 
    baseline=[{
        "SP-LUT+": splut_avg_comm,
        "FLUTE": flute_comm, 
    }, {
        "FLORAM": np.array(floram_json["Communication"]) * 2 / (2 ** 10),
        "2P-DUORAM": np.array(duoram_json["Communication"]) * 2 / (2 ** 10),
        "2P-DUORAM+":  np.array(duoram_json["Communication"]) * 2 / (2 ** 10) / 2,
    }], 
    folder=plot_folder, 
    ylims=[(100, 2*1e6), (2, 2*1e6)], 
    yticks=[[100, 1000, 10000, 1e5, 1e6], [10, 100, 1000, 10000, 1e5, 1e6]], 
    ncols=2, 
)

# The big figure
lan1_doram = {
    our_name_doram: opt_bs_time_16thr[0] / 4096, 
    "FLORAM": np.array(floram_json["3Gbps"]), 
    "2P-DUORAM": np.array(duoram_json["3Gbps"]), 
    "2P-DUORAM+": np.array(duoram_json["3Gbps"]) / 2, 
}
lan2_doram = {
    our_name_doram: opt_bs_time_16thr[1] / 4096, 
    "FLORAM": np.array(floram_json["1Gbps"]), 
    "2P-DUORAM": np.array(duoram_json["1Gbps"]), 
    "2P-DUORAM+": np.array(duoram_json["1Gbps"]) / 2, 
}
wan1_doram = {
    our_name_doram: opt_bs_time_16thr[2] / 4096, 
    "FLORAM": np.array(floram_json["200Mbps"]), 
    "2P-DUORAM": np.array(duoram_json["200Mbps"]), 
    "2P-DUORAM+": np.array(duoram_json["200Mbps"]) / 2, 
}
wan2_doram = {
    our_name_doram: opt_bs_time_16thr[3] / 4096, 
    "FLORAM": np.array(floram_json["100Mbps"]), 
    "2P-DUORAM": np.array(duoram_json["100Mbps"]), 
    "2P-DUORAM+": np.array(duoram_json["100Mbps"]) / 2, 
}
print("2p-duoram lan1: {:.2f}x ~ {:.2f}x".format(
    np.min(lan1_doram['2P-DUORAM'] / lan1_doram[our_name_doram]), 
    np.max(lan1_doram['2P-DUORAM'] / lan1_doram[our_name_doram])
))
print("2p-duoram lan2: {:.2f}x ~ {:.2f}x".format(
    np.min(lan2_doram['2P-DUORAM'] / lan2_doram[our_name_doram]),
    np.max(lan2_doram['2P-DUORAM'] / lan2_doram[our_name_doram])
))
print("2p-duoram wan1: {:.2f}x ~ {:.2f}x".format(
    np.min(wan1_doram['2P-DUORAM'] / wan1_doram[our_name_doram]),
    np.max(wan1_doram['2P-DUORAM'] / wan1_doram[our_name_doram])
))
print("2p-duoram wan2: {:.2f}x ~ {:.2f}x".format(
    np.min(wan2_doram['2P-DUORAM'] / wan2_doram[our_name_doram]),
    np.max(wan2_doram['2P-DUORAM'] / wan2_doram[our_name_doram])
))

print("2p-duoram+ lan1: {:.2f}x ~ {:.2f}x".format(
    np.min(lan1_doram['2P-DUORAM'] / 2 / lan1_doram[our_name_doram]), 
    np.max(lan1_doram['2P-DUORAM'] / 2 / lan1_doram[our_name_doram])
))
print("2p-duoram+ lan2: {:.2f}x ~ {:.2f}x".format(
    np.min(lan2_doram['2P-DUORAM'] / 2 / lan2_doram[our_name_doram]),
    np.max(lan2_doram['2P-DUORAM'] / 2 / lan2_doram[our_name_doram])
))
print("2p-duoram+ wan1: {:.2f}x ~ {:.2f}x".format(
    np.min(wan1_doram['2P-DUORAM'] / 2 / wan1_doram[our_name_doram]),
    np.max(wan1_doram['2P-DUORAM'] / 2 / wan1_doram[our_name_doram])
))
print("2p-duoram+ wan2: {:.2f}x ~ {:.2f}x".format(
    np.min(wan2_doram['2P-DUORAM'] / 2 / wan2_doram[our_name_doram]),
    np.max(wan2_doram['2P-DUORAM'] / 2 / wan2_doram[our_name_doram])
))


print("floram lan1: {:.2f}x ~ {:.2f}x".format(
    np.min(lan1_doram['FLORAM'] / lan1_doram[our_name_doram]), 
    np.max(lan1_doram['FLORAM'] / lan1_doram[our_name_doram])
))
print("floram lan2: {:.2f}x ~ {:.2f}x".format(
    np.min(lan2_doram['FLORAM'] / lan2_doram[our_name_doram]),
    np.max(lan2_doram['FLORAM'] / lan2_doram[our_name_doram])
))
print("floram wan1: {:.2f}x ~ {:.2f}x".format(
    np.min(wan1_doram['FLORAM'] / wan1_doram[our_name_doram]),
    np.max(wan1_doram['FLORAM'] / wan1_doram[our_name_doram])
))
print("floram wan2: {:.2f}x ~ {:.2f}x".format(
    np.min(wan2_doram['FLORAM'] / wan2_doram[our_name_doram]),
    np.max(wan2_doram['FLORAM'] / wan2_doram[our_name_doram])
))

lan1_lut = {
    our_name_lut: opt_bs_time_32thr[0] / 4096, 
    "SP-LUT+": splut_avg_time[0], 
}
lan2_lut = {
    our_name_lut: opt_bs_time_32thr[1] / 4096, 
    "SP-LUT+": splut_avg_time[1],
}
wan1_lut = {
    our_name_lut: opt_bs_time_32thr[2] / 4096, 
    "SP-LUT+": splut_avg_time[2],
}
wan2_lut = {
    our_name_lut: opt_bs_time_32thr[3] / 4096, 
    "SP-LUT+": splut_avg_time[3],
}
print("SP-LUT lan1: {:.2f}x ~ {:.2f}x".format(
    np.min(lan1_lut['SP-LUT+'] / lan1_lut[our_name_lut]), 
    np.max(lan1_lut['SP-LUT+'] / lan1_lut[our_name_lut]), 
))
print("SP-LUT lan2: {:.2f}x ~ {:.2f}x".format(
    np.min(lan2_lut['SP-LUT+'] / lan2_lut[our_name_lut]), 
    np.max(lan2_lut['SP-LUT+'] / lan2_lut[our_name_lut]), 
))
print("SP-LUT wan1: {:.2f}x ~ {:.2f}x".format(
    np.min(wan1_lut['SP-LUT+'] / wan1_lut[our_name_lut]), 
    np.max(wan1_lut['SP-LUT+'] / wan1_lut[our_name_lut]), 
))
print("SP-LUT wan2: {:.2f}x ~ {:.2f}x".format(
    np.min(wan2_lut['SP-LUT+'] / wan2_lut[our_name_lut]), 
    np.max(wan2_lut['SP-LUT+'] / wan2_lut[our_name_lut]), 
))

bigfig(
    [lan1_lut, lan1_doram], 
    [lan2_lut, lan2_doram], 
    [wan1_lut, wan1_doram], 
    [wan2_lut, wan2_doram], 
    plot_folder, 
    (1, 2*1e6), 
    [1, 10, 100, 1000, 10000, 1e5, 1e6], 
    width=0.1, 
    ncol=3, 
    figsize=(18, 7.5), 
    gridspec_kw={
        'width_ratios': [1, 1], 
        'wspace': 0.07, 
        'hspace': 0.05
    }
)

bigfig_clipped(
    [lan1_lut, lan1_doram], 
    [wan2_lut, wan2_doram], 
    plot_folder, 
    (1, 2*1e6), 
    [1, 10, 100, 1000, 10000, 1e5, 1e6], 
    width=0.1, 
    ncol=2, 
    figsize=(9,7.5), 
    gridspec_kw={
        'hspace': 0.05
    }
)

print()
print("over best baseline: lan1: {:.2f}x ~ {:.2f}x".format(
    np.min(np.minimum(np.minimum(lan1_doram['2P-DUORAM'], lan1_doram['FLORAM']) / lan1_doram[our_name_doram], lan1_lut['SP-LUT+'] / lan1_lut[our_name_lut])), 
    np.max(np.minimum(np.minimum(lan1_doram['2P-DUORAM'], lan1_doram['FLORAM']) / lan1_doram[our_name_doram], lan1_lut['SP-LUT+'] / lan1_lut[our_name_lut]))
))
print("over best baseline: lan2: {:.2f}x ~ {:.2f}x".format(
    np.min(np.minimum(np.minimum(lan2_doram['2P-DUORAM'], lan2_doram['FLORAM']) / lan2_doram[our_name_doram], lan2_lut['SP-LUT+'] / lan2_lut[our_name_lut])), 
    np.max(np.minimum(np.minimum(lan2_doram['2P-DUORAM'], lan2_doram['FLORAM']) / lan2_doram[our_name_doram], lan2_lut['SP-LUT+'] / lan2_lut[our_name_lut]))
))
print("over best baseline: wan1: {:.2f}x ~ {:.2f}x".format(
    np.min(np.minimum(np.minimum(wan1_doram['2P-DUORAM'], wan1_doram['FLORAM']) / wan1_doram[our_name_doram], wan1_lut['SP-LUT+'] / wan1_lut[our_name_lut])), 
    np.max(np.minimum(np.minimum(wan1_doram['2P-DUORAM'], wan1_doram['FLORAM']) / wan1_doram[our_name_doram], wan1_lut['SP-LUT+'] / wan1_lut[our_name_lut]))
))
print("over best baseline: wan2: {:.2f}x ~ {:.2f}x".format(
    np.min(np.minimum(np.minimum(wan2_doram['2P-DUORAM'], wan2_doram['FLORAM']) / wan2_doram[our_name_doram], wan2_lut['SP-LUT+'] / wan2_lut[our_name_lut])), 
    np.max(np.minimum(np.minimum(wan2_doram['2P-DUORAM'], wan2_doram['FLORAM']) / wan2_doram[our_name_doram], wan2_lut['SP-LUT+'] / wan2_lut[our_name_lut]))
))

# print(lan2_doram['2P-DUORAM'] / lan2_doram[our_name_doram])
# print(lan2_doram['FLORAM'] / lan2_doram[our_name_doram])
# print(lan2_lut['SP-LUT+'] / lan2_lut[our_name_lut])
