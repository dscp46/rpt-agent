# rpt-agent
Remote Repeater Control agent

## Install guide
1. Install `paho-mqtt` for python3.

This can be done either by your package manager or with pip.

Installing the package using apt.
```bash
apt install python3-paho-mqtt

```

Installing pip and the package with Python <3.9
```bash
wget "https://bootstrap.pypa.io/pip/3.4/get-pip.py"
sed -i 's/env python/env python3/' get-pip.py
chmod +x get-pip.py
./get-pip.py
pip install paho-mqtt
```

Installing pip and the package with Python >=3.9
```bash
wget "https://bootstrap.pypa.io/get-pip.py"
sed -i 's/env python/env python3/' get-pip.py
chmod +x get-pip.py
./get-pip.py
pip install paho-mqtt
```

2. Edit file `rpt-agent` to set the repeater callsign you've set up on your MQTT server, the server's hostname and the MQTT password.

3. Make `install.sh` executable and run it.
