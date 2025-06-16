#!/bin/bash

# Use this script to build the three docker images: one for Duoram (our
# work), and one each for Floram and 3P Circuit ORAM (the two systems we
# compare against).  We made the dockerization scripts for these latter
# two systems as well.

# Pass as an argument the git tag or branch to use.  Defaults to
# "usenixsec23_artifact".

tag=usenixsec23_artifact
if [ "$1" != "" ]; then
    tag="$1"
fi

# cd into the directory containing this script (from the bash faq 028)
if [[ $BASH_SOURCE = */* ]]; then
  cd -- "${BASH_SOURCE%/*}/" || exit
fi

# See if we need to clone those other two repos
if [ -d floram-docker/.git ]; then
    ( cd floram-docker && git fetch --tags -f origin && git checkout $tag ) || exit 1
else
    ( git clone https://git-crysp.uwaterloo.ca/iang/floram-docker && cd floram-docker && git checkout $tag ) || exit 1
fi

if [ -d duoram/.git ]; then
    ( cd duoram && git fetch --tags -f origin && git checkout $tag ) || exit 1
else
    ( git clone https://git-crysp.uwaterloo.ca/avadapal/duoram && cd duoram && git checkout $tag ) || exit 1
fi

# Stop any existing dockers
bash ./stop-dockers.sh

# Build the three docker images
echo "Building Duoram docker..."
echo
( cd duoram/Docker && bash ./build-docker ) || exit 1
echo
echo "Building Floram docker..."
echo
( cd floram-docker && bash ./build-docker ) || exit 1
echo
