cd ~/repo/10x-at
streamlit run ./python/ui/main.py

sudo nano /etc/systemd/system/10x-at-ui.service

---

[Unit]
Description=10xDev-at UI (Streamlit)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ahu
Group=ahu
WorkingDirectory=/home/ahu/repo/10x-at
Environment="PYTHONUNBUFFERED=1"
# upewniamy się, że venv jest pierwszy w PATH
Environment="PATH=/home/ahu/repo/10x-at/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"

# uruchamiamy streamlit z Pythona z venv
ExecStart=/home/ahu/repo/10x-at/.venv/bin/python -m streamlit run python/ui/main.py --server.port=8501 --server.headless=true

Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target


---

sudo systemctl daemon-reload
sudo systemctl enable 10x-at-ui.service
sudo systemctl start 10x-at-ui.service

sudo systemctl status 10x-at-ui.service

journalctl -u 10x-at-ui.service -f
