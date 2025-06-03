# Artifact Evaluation for FABLE: Batched Evaluation on Confidential Lookup Tables in 2PC

This is the artifact evaluation for the USENIX Security '25 paper "FABLE: Batched Evaluation on Confidential Lookup Tables in 2PC". 

## Dependency Installation

Please use Docker to install the dependencies. To do this, build a Docker image using the [Dockerfile](./Dockerfile), which will install all dependencies and build FABLE in `/workspace/FABLE`. 

## Main Experiments

To reproduce the main experiments, run 
```bash
bash main_experiments.sh 1 0.0.0.0
```
and
```bash
bash main_experiments.sh 2 $HOST
```
On two machines, where `$HOST` is the IP address of the machine running the first command. 

## Baseline

### SPLUT

To reproduce the splut baseline, run 
```bash
bash baseline_splut.sh 1 0.0.0.0
```
and
```bash
bash baseline_splut.sh 2 $HOST
```
On two machines, where `$HOST` is the IP address of the machine running the first command. 

### FLORAM and 2P-DUORAM

FLORAM and 2P-DUORAM are benchmarked using their official implementation. 

## Plots

To plot the figures, please run 
1. `python microbench.py`, which will produce `plots/runtime_vs_threads.pdf` (Figure 4). 
2. `python draw.py`, which will produce
    1. `FABLE-AE/plots/time_lutsize_network_clipped.pdf` (Figure 5)
    2. `FABLE-AE/plots/24_time_bs.pdf` (Figure 6)
    3. `FABLE-AE/plots/comm.pdf` (Figure 7)
    4. `FABLE-AE/plots/time_lutsize_network.pdf` (Figure 8)

## Applications

To reproduce the applications, run 
```bash
bash applications.sh 1 $HOST
```
and
```bash
bash applications.sh 2 $HOST
```
On two machines, where `$HOST` is the IP address of the machine running the first command. 