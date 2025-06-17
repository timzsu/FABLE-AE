#!/bin/bash

# Stop all three sets of dockers.  This is useful if, for example, a run
# of repro-all-dockers is interrupted, leaving some dockers (and
# potentionally the processes therein) running.

# cd into the directory containing this script (from the bash faq 028)
if [[ $BASH_SOURCE = */* ]]; then
  cd -- "${BASH_SOURCE%/*}/" || exit
fi

docker stop motion &
docker stop crypten &
wait