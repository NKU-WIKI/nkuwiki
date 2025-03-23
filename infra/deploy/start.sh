#!/bin/bash
#配置nkuwiki自启动


sudo tee /etc/systemd/system/nkuwiki.service <<EOF
[Unit]
Description=NKU Wiki API Service
After=network.target nginx.service mysql.service

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki-shell/nkuwiki
ExecStart=/opt/venvs/nkuwiki/bin/python3 app.py --api
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

# 性能优化环境变量
Environment=PYTHONOPTIMIZE=1
Environment=PYTHONHASHSEED=random

# 资源限制 - 高性能配置
CPUQuota=90%
MemoryLimit=6G
TasksMax=256
TimeoutStopSec=60

# OOM配置
OOMScoreAdjust=-500  # 降低被OOM杀死的可能性

# 日志设置
StandardOutput=journal
StandardError=journal

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