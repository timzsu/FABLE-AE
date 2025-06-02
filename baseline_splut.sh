#!/bin/bash

# Scripts to launch SPLUT baseline experiments. 

R=$1
HOST=${2:-'127.0.0.1'}
NUM_REPEAT=${3:-1}
FABLE_DIR=${4:-'/workspace/FABLE'}
NET_INTERFACE="$(ip link show | grep UP | sed -n '2p' | awk '{print $2}' | cut -d: -f1 | cut -d@ -f1)"

netunset() {
    if tc qdisc list dev $NET_INTERFACE | grep -q netem; then
        tc qdisc del dev $NET_INTERFACE root; 
    fi
}
alias netctrl1="tc qdisc add dev $NET_INTERFACE root netem delay 800us rate 3gbit"
alias netctrl2="tc qdisc add dev $NET_INTERFACE root netem delay 800us rate 1gbit"
alias netctrl3="tc qdisc add dev $NET_INTERFACE root netem delay 40ms rate 200mbit"
alias netctrl4="tc qdisc add dev $NET_INTERFACE root netem delay 80ms rate 100mbit"

SCRIPT_PATH="$(dirname "$(readlink -f "$0")")"
LOG_DIR=$SCRIPT_PATH/logs/baseline
mkdir -p $LOG_DIR
cd $FABLE_DIR

cmake -S . -B build
cmake --build ./build --target splut --parallel

for s in {1..4}; do
    netunset
    ${BASH_ALIASES[netctrl$s]}
    for repeat_id in $(seq 1 "$NUM_REPEAT"); do
        $FABLE_DIR/build/bin/splut ip=$HOST p=8100 len=20 l=1 bs=256 thr=32 r=$R > $LOG_DIR/splut-in20-out20-netconf$s-bs256-thr32-$repeat_id.log
        $FABLE_DIR/build/bin/splut ip=$HOST p=8100 len=24 l=1 bs=16 thr=32 r=$R > $LOG_DIR/splut-in24-out24-netconf$s-bs16-thr32-$repeat_id.log
        $FABLE_DIR/build/bin/splut ip=$HOST p=8100 len=28 l=1 bs=1 thr=32 r=$R > $LOG_DIR/splut-in28-out28-netconf$s-bs1-thr32-$repeat_id.log
    done
done