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
LOG_DIR=$SCRIPT_PATH/logs/applications
mkdir -p $LOG_DIR
cd $FABLE_DIR

# Secure Embedding Lookup
cmake -S . -B build -DLUT_INPUT_SIZE=20 -DLUT_OUTPUT_SIZE=512 -DLUT_MAX_LOG_SIZE=20
cmake --build ./build --target embedding --parallel
for repeat_id in $(seq 1 "$NUM_REPEAT"); do
    $FABLE_DIR/build/bin/embedding $HOST r=$R > $LOG_DIR/embedding-FABLE-$repeat_id.log
    python3 src/applications/embedding-baseline.py --addr $HOST -r $R > $LOG_DIR/embedding-baseline-$repeat_id.log
done

# Secure Join Execution
cmake -S . -B build -DLUT_INPUT_SIZE=24 -DLUT_OUTPUT_SIZE=32 -DLUT_MAX_LOG_SIZE=20
cmake --build ./build --target join --parallel
for repeat_id in $(seq 1 "$NUM_REPEAT"); do
    ./build/bin/join $HOST r=$R > $LOG_DIR/join-$repeat_id.log
    ./build/bin/join $HOST r=$R baseline=1 > $LOG_DIR/join-baseline-$repeat_id.log
done
