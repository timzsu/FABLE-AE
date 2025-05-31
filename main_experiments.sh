#!/bin/bash

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
LOG_DIR=$SCRIPT_PATH/logs
mkdir -p $LOG_DIR
cd $FABLE_DIR

echo "running SPLUT-like table configuration"
for bit in {20..28..4}; do

    cmake -S . -B build -DLUT_INPUT_SIZE=$bit -DLUT_OUTPUT_SIZE=$bit -DLUT_MAX_LOG_SIZE=$bit
    cmake --build ./build --target fable --parallel

    for s in {1..4}; do
        netunset
        ${BASH_ALIASES[netctrl$s]}
        echo "config: inputbitsize=$bit, outputbitsize=$bit, netconfig=$s"
        for repeat_id in $(seq 1 "$NUM_REPEAT"); do
            $FABLE_DIR/build/bin/fable $HOST l=1 bs=4096 thr=32 h=0 r=$R > $LOG_DIR/in$bit-out$bit-netconf$s-bs4096-thr32-h0-$repeat_id.log
        done
    done

    # AES OPRF (table 4)
    for s in {1..4..3}; do
        netunset
        ${BASH_ALIASES[netctrl$s]}
        echo "config: inputbitsize=$bit, outputbitsize=$bit, netconfig=$s"
        for repeat_id in $(seq 1 "$NUM_REPEAT"); do
            $FABLE_DIR/build/bin/fable $HOST l=1 bs=4096 thr=32 h=1 r=$R > $LOG_DIR/in$bit-out$bit-netconf$s-bs4096-thr32-h1-$repeat_id.log
        done
    done

    # Varying batch size (figure 6&7)
    if [ $bit -eq 24 ]; then
        for s in {1..4..3}; do
            netunset
            ${BASH_ALIASES[netctrl$s]}
            echo "netconfig=$s"
            for bs in 1 256 512 1024 2048; do
                for repeat_id in $(seq 1 "$NUM_REPEAT"); do
                    $FABLE_DIR/build/bin/fable $HOST l=1 bs=$bs thr=32 h=0 r=$R > $LOG_DIR/in$bit-out$bit-netconf$s-bs$bs-thr32-h0-$repeat_id.log
                done
            done
        done
    fi
    
    # Varying number of threads (figure 4)
    if [ $bit -eq 24 ]; then
        for s in {1..4..3}; do
            netunset
            ${BASH_ALIASES[netctrl$s]}
            echo "netconfig=$s"
            for thr in 1 2 4 8 16; do
                for repeat_id in $(seq 1 "$NUM_REPEAT"); do
                    $FABLE_DIR/build/bin/fable $HOST l=1 bs=4096 thr=$thr h=0 r=$R > $LOG_DIR/in$bit-out$bit-netconf$s-bs4096-thr$thr-h0-$repeat_id.log
                done
            done
        done
    fi

done

echo "running DORAM-like table configuration"
for bit in {20..28..4}
do

    cmake -S . -B build -DLUT_INPUT_SIZE=$bit -DLUT_OUTPUT_SIZE=64 -DLUT_MAX_LOG_SIZE=$bit
    cmake --build ./build --target fable --parallel

    for s in {1..4}; do
        netunset
        ${BASH_ALIASES[netctrl$s]}
        echo "config: inputbitsize=$bit, outputbitsize=$bit, netconfig=$s"
        for repeat_id in $(seq 1 "$NUM_REPEAT"); do
            $FABLE_DIR/build/bin/fable $HOST l=1 bs=4096 thr=16 h=0 r=$R > $LOG_DIR/in$bit-out64-netconf$s-bs4096-thr32-h0-$repeat_id.log
        done
    done
    
    # Varying batch size (figure 6&7)
    if [ $bit -eq 24 ]; then
        for s in {1..4..3}; do
            netunset
            ${BASH_ALIASES[netctrl$s]}
            echo "netconfig=$s"
            for bs in 1 256 512 1024 2048; do
                for repeat_id in $(seq 1 "$NUM_REPEAT"); do
                    $FABLE_DIR/build/bin/fable $HOST l=1 bs=$bs thr=32 h=0 r=$R > $LOG_DIR/in$bit-out64-netconf$s-bs$bs-thr32-h0-$repeat_id.log
                done
            done
        done
    fi

done