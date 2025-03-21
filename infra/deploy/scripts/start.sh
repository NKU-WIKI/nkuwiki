#!/bin/bash
#配置nkuwiki自启动


sudo tee /etc/systemd/system/nkuwiki.service <<EOF
[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki-shell/nkuwiki
Environment=PYTHONPATH=/home/nkuwiki/nkuwiki-shell/nkuwiki
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/venvs/nkuwiki/bin/python /home/nkuwiki/nkuwiki-shell/nkuwiki/app.py --api
Restart=always
RestartSec=3
StandardOutput=file:/var/log/nkuwiki.log
StandardError=file:/var/log/nkuwiki-error.log

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /etc/systemd/system/nkuwiki.service
sudo touch /var/log/nkuwiki.log /var/log/nkuwiki-error.log
sudo chmod 644 /var/log/nkuwiki.log /var/log/nkuwiki-error.log


sudo systemctl enable nkuwiki.service
sudo systemctl start nkuwiki.service

sudo systemctl daemon-reload

sleep 5
sudo systemctl status nkuwiki.service 