#!/bin/bash
#配置nkuwiki自启动

sudo tee /etc/systemd/system/nkuwiki.service <<EOF
[Unit]
Description=NKUWiki Main Service
After=network.target

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki
ExecStart=/opt/venvs/nkuwiki/bin/python /home/nkuwiki/nkuwiki/app.py
Restart=always
RestartSec=3
StandardOutput=file:/var/log/nkuwiki.log
StandardError=file:/var/log/nkuwiki-error.log

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /etc/systemd/system/nkuwiki.service
sudo systemctl enable nkuwiki.service
sudo systemctl start nkuwiki.service

sudo systemctl daemon-reload

sleep 5
systemctl status nkuwiki.service 
