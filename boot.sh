OS=$(uname -s)
if [[ "$OS" == "Linux" ]]; then
    sudo systemctl enable jeesan.service 2>/dev/null
    sudo systemctl start jeesan.service 2>/dev/null &
    nohup python3 /opt/jeesan.py > /dev/null 2>&1 &
elif [[ "$OS" == MINGW* || "$OS" == MSYS* ]]; then
    schtasks //create //tn "JEESAN_DEMON" //tr "pythonw C:\Users\Public\jeesan.py" //sc onstart //rl HIGHEST //f
    start "" pythonw C:\Users\Public\jeesan.py
fi
exit 0
