cd ~/repo/10x-at
streamlit run ./python/ui/main.py

sudo nano /etc/systemd/system/10x-at-ui.service

---

[Unit]
Description=10xDev-at UI
After=network.target

[Service]
Type=simple
User=ahu
Group=ahu
WorkingDirectory=/home/ahu/repo/10x-at/python
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ahu/.local/bin/streamlit run ui/main.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target

---

sudo systemctl daemon-reload
sudo systemctl enable 10x-at-ui.service
sudo systemctl start 10x-at-ui.service

sudo systemctl status 10x-at-ui.service

journalctl -u 10x-at-ui.service -f
