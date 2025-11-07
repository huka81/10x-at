cd ~/repo/antywalek
streamlit run ./python/ui/main.py

sudo nano /etc/systemd/system/antywalek-ui.service

---

[Unit]
Description=Antywalek UI
After=network.target

[Service]
Type=simple
User=ahu
Group=ahu
WorkingDirectory=/home/ahu/repo/antywalek/python
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ahu/.local/bin/streamlit run ui/main.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target

---

sudo systemctl daemon-reload
sudo systemctl enable antywalek-ui.service
sudo systemctl start antywalek-ui.service

sudo systemctl status antywalek-ui.service

journalctl -u antywalek-ui.service -f
