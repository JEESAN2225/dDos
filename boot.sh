#!/bin/bash
echo "[☠] Initializing JEESAN v6.66..."
apt update
apt install -y python3 python3-pip tor privoxy git curl net-tools procps
pip3 install scapy requests h2 stem colorama dnspython psutil

systemctl enable tor && systemctl start tor
systemctl enable privoxy && systemctl start privoxy

cd /tmp || exit
git clone https://github.com/JEESAN2225/dDos.git
cd jeesan
cp jeesan.py /opt/jeesan-core.py
cp jeesan.service /etc/systemd/system/
systemctl daemon-reexec
systemctl enable jeesan.service
systemctl start jeesan.service

echo "[🔥] JEESAN IS NOW LIVE. RUN: sudo python3 /opt/jeesan-core.py"
