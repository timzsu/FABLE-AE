#!/bin/bash

# Run a command on all three repro scripts

# cd into the directory containing this script (from the bash faq 028)
if [[ $BASH_SOURCE = */* ]]; then
  cd -- "${BASH_SOURCE%/*}/" || exit
fi

# Stop any running dockers
bash stop-dockers.sh

FLORAM_LOGDIR=$PWD/../logs/baseline/floram
DUORAM_LOGDIR=$PWD/../logs/baseline/duoram

run_floram() {
    logfile="$FLORAM_LOGDIR/${2}_${3}_${4}_${5}.out"
    echo "$((date)): Running FLORAM with $1 $2 $3 $4 $5, logging to $logfile"
    ./set-networking $3 $4
    echo "Network setup: $3 $4" > $logfile
    ./run-experiment $1 $2 $5 >> $logfile
}

run_duoram() {
    logfile="$DUORAM_LOGDIR/${2}_${3}_${4}_${5}.out"
    echo "$((date)): Running 2P-DUORAM with $1 $2 $3 $4 $5, logging to $logfile"
    maxgb=16 # The default configuration in DUORAM
    ./set-networking $3 $4
    echo "Network setup: $3 $4" > $logfile
    ./run-experiment $1 $2 $5 online 2P $maxgb >> $logfile
}

latency_list=("800us" "800us" "40ms" "80ms")
bandwidth_list=("3gbit" "1gbit" "200mbit" "100mbit")

repro_floram() {
    echo "Running test experiment..."
    mkdir -p $FLORAM_LOGDIR

    for bit in {20..28..4}
    do
        for i in "${!latency_list[@]}"
        do
            run_floram read $bit ${latency_list[i]} ${bandwidth_list[i]} 5
        done
    done
}

repro_duoram() {
    echo "Running test experiment..."
    mkdir -p $DUORAM_LOGDIR

    for bit in {20..28..4}
    do
        for i in "${!latency_list[@]}"
        do
            run_duoram read $bit ${latency_list[i]} ${bandwidth_list[i]} 5
        done
    done
}

# Floram
echo
echo Running Floram repro
echo 
cd floram-docker
echo "Starting Floram dockers" && ./start-docker
repro_floram 
echo "Stopping Floram dockers" && ./stop-docker
cd ..

# Duoram
echo
echo Running Duoram repro
echo
cd duoram/Docker
echo "Starting Duoram dockers" && ./start-docker
repro_duoram
echo "Stopping Duoram dockers" && ./stop-docker
cd ../..