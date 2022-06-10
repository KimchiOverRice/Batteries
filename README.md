# elcon-bms

# Install

add elcon-bms to /home

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 main.py
```

# Setup on Pi

https://www.pragmaticlinux.com/2021/10/can-communication-on-the-raspberry-pi-with-socketcan/

1. Add this line to /boot/config.txt:

cd /    --> type this to get into root

```
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000
```

2. Run `sudo raspi-config`, go to page 3 and enable SPI (option P4).

```
sudo modprobe can
sudo modprobe can_raw
```

3. Enable the SocketCAN network interface:
```
sudo ip link set can0 type can bitrate 250000 restart-ms 100
sudo ip link set up can0
sudo apt install can-utils
```

# After reboot (everytime)

```
cd elcon-bms
source venv/bin/activate

sudo modprobe can
sudo modprobe can_raw

sudo ip link set can0 type can bitrate 250000 restart-ms 100
sudo ip link set up can0

python3 main.py
```

# Utilities 

Monitor raw CAN traffic:

```
candump -tz can0
```

Chekc if CAN Hat is recognized
ip addr | grep "can"