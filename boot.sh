#!/bin/bash
set -e

echo "[🔥] JEESAN CORE – Installing..."

if command -v apt &>/dev/null; then
    apt update && apt install -y python3 python3-pip tor curl
elif command -v yum &>/dev/null; then
    yum install -y python3 python3-pip tor curl
elif command -v pacman &>/dev/null; then
    pacman -Sy --noconfirm python python-pip tor curl
fi

systemctl start tor || echo "tor not found, skipping"
pip3 install --upgrade pip --break-system-packages 2>/dev/null || pip3 install --upgrade pip
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt

if [ -f jeesan.service ]; then
    cp jeesan.service /etc/systemd/system/jeesan.service
    systemctl daemon-reload
    systemctl enable jeesan.service
    systemctl start jeesan.service
    echo "[✓] Service installed"
fi

chmod +x jeesan.py
nohup python3 jeesan.py &>/dev/null &
echo "[☠] JEESAN CORE alive – PID $!"
