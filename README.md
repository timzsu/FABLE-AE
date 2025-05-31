# Artifact Evaluation for FABLE: Batched Evaluation on Confidential Lookup Tables in 2PC

This is the artifact evaluation for the USENIX Security '25 paper "FABLE: Batched Evaluation on Confidential Lookup Tables in 2PC". 

## Dependency Installation

Please use Docker to install the dependencies. To do this, build a Docker image using the [Dockerfile](./Dockerfile), which will install all dependencies and build FABLE in `/workspace/FABLE`. 

## Main Experiments

To reproduce the main experiments, run 
```bash
bash main_experiments.sh 1 $HOST
```
and
```bash
bash main_experiments.sh 2 $HOST
```
On two machines, where `$HOST` is the IP address of the machine running the first command. 