CLIENT_HOST=$1

cd logs
rm -rf client
wget --progress=bar:force:noscroll --recursive --no-parent http://$CLIENT_HOST:8100 -P client

mv client/$CLIENT_HOST:8100/* client
rmdir client/$CLIENT_HOST:8100
find client -name "index.html" -exec rm "{}" \;