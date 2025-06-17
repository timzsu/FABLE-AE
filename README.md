# The Artifact of FABLE: Batched Evaluation on Confidential Lookup Tables in 2PC

This is the artifact evaluation repository of the USENIX Security '25 paper "FABLE: Batched Evaluation on Confidential Lookup Tables in 2PC". 

The main implementation is at https://github.com/timzsu/FABLE, and the paper can be found at https://eprint.iacr.org/2025/1081. 

This version is for availability evaluation, where we provide
1. The code for the FABLE protocol plus the two applications. 
2. The instructions to build and execute the protocol. 
3. The instructions to reproduce all experiments in the paper. 
4. The scripts to plot all figures and report the speedup of the FABLE protocol over the baselines. 

## Dependency Installation

Please use Docker to install the dependencies. To do this, first build a Docker image with the Dockerfile in the FABLE folder, and then build a Docker image for AE using the [Dockerfile](./Dockerfile) in the FABLE-AE folder. Assume you are in the root directory of the artifact (i.e., the parent directory of `FABLE-AE`), then you can run:
```bash
sudo docker build ./FABLE -t fable:1.0
sudo docker build ./FABLE-AE -t fable-ae:1.0
```
The image `fable:1.0` contains all dependencies and a built FABLE in `/workspace/FABLE`. The image `fable-ae:1.0` contains some extra dependencies for reproduction. 

## Main Experiments

To reproduce the main experiments, first create a container on two machines: 
```bash
sudo docker run -it -p 8100:8100 --cap-add=NET_ADMIN -v $PWD/FABLE-AE:/workspace/AE -w /workspace/AE fable-ae:1.0
```
Then run 
```bash
bash main_experiments.sh 1 0.0.0.0
```
and
```bash
bash main_experiments.sh 2 $HOST
```
On two machines, where `$HOST` is the IP address of the machine running the first command. 
The logs will be written to `logs/main` in `FABLE-AE`.

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
The logs will be written to `logs/baseline` in `FABLE-AE`.

### FLORAM and 2P-DUORAM

FLORAM and 2P-DUORAM are benchmarked using their official implementation. You can skip this step if you would like to use the results we provided in `ORAMs/floram.json` and `ORAMs/duoram.json`. 

To do this, exit the docker for `FABLE-AE` and build their docker with
```bash
sudo bash ORAMs/build-dockers.sh
```
Then run the experiments with 
```bash
sudo bash ORAMs/repro-dockers.sh
```

## Plots

Before creating the plots, we need to transfer the logs from the client to the server. To do this, launch 
```bash
bash sync_log_serv.sh
```
on the client (the second machine), and run
```bash
bash sync_log_recv.sh $CLIENT
```
on the server (the first machine), where `$CLIENT` is the IP address of the client. 

To plot the figures, please run 
1. `python3 microbench.py`, which will produce `FABLE-AE/plots/runtime_vs_threads.pdf` (Figure 4). 
2. `python3 draw.py`, which will produce
    1. `FABLE-AE/plots/time_lutsize_network_clipped.pdf` (Figure 5)
    2. `FABLE-AE/plots/24_time_bs.pdf` (Figure 6)
    3. `FABLE-AE/plots/comm.pdf` (Figure 7)
    4. `FABLE-AE/plots/time_lutsize_network.pdf` (Figure 8)
You can add `--doram-baseline` to `python3 draw.py` if you prefer to use the reproduced FLORAM and DUORAM numbers instead of the ones we provided. 

You may also want to reproduce our tables (in markdown format) with `python3 breakdown_table.py` and `python3 breakdown_table.py --aes`. The first one gives the result with LowMC as the OPRF and the second one gives the result with AES as the OPRF. Table 4 in the paper is produced by merging the two tables. 

## Applications

To reproduce the applications, run 
```bash
bash applications.sh 1 0.0.0.0
```
and
```bash
bash applications.sh 2 $HOST
```
On two machines, where `$HOST` is the IP address of the machine running the first command. 

Afterwards, you can run `python3 read_app_speedup.py` to see the speedup for both applications. 

### Benchmark the Crypten baseline on your own
Note: Similar to DORAMs, we use a separate environment to benchmark to performance of the Crypten baseline. If you prefer to benchmark the baselines on your own, feel free to follow the instructions: 

To build the docker, 
```bash
sudo docker build FABLE-AE/Crypten -t crypten
```
Then launch the docker with
```bash
sudo docker run -it -p 8100:8100 --cap-add=NET_ADMIN -v $PWD/FABLE-AE:/workspace/AE -w /workspace/AE  crypten
```

To reproduce the performance, run
```bash
bash Crypten/reproduce.sh 0 $HOST $CLIENT
```
and
```bash
bash Crypten/reproduce.sh 1 $HOST $CLIENT
```
on the host and the client respectively. 

