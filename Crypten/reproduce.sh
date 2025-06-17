MYID=$1
HOST=$2
CLIENT=$3
PORT_HOST=${4:-8100}
PORT_CLIENT=${5:-8200}

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
LOGDIR="$SCRIPT_PATH/../logs/applications"
mkdir -p $LOGDIR

for s in {1..4..3}; do
    netunset
    ${BASH_ALIASES[netctrl$s]}
    echo "netconfig=$s"
    /workspace/MOTION/build/bin/benchmark_providers --my-id $MYID --parties 0,$HOST,$PORT_HOST 1,$CLIENT,$PORT_CLIENT --batch-size $((2**16)) --repetitions 5 > $LOGDIR/embedding-baseline-mt-netconf$s.log
    python $SCRIPT_PATH/embedding-baseline.py -r $MYID -a $HOST -p $PORT_HOST > $LOGDIR/embedding-baseline-online-netconf$s.log
done