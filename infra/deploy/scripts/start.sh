#!/bin/bash
#配置nkuwiki自启动

# 1. 创建服务文件（使用sudo）
sudo tee /etc/systemd/system/nkuwiki.service <<EOF
[Unit]
Description=NKUWiki Chat Service
After=network.target

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki
ExecStart=/usr/local/bin/python3.12 ./app.py
Restart=always
RestartSec=3
StandardOutput=file:/var/log/nkuwiki.log
StandardError=file:/var/log/nkuwiki-error.log

[Install]
WantedBy=multi-user.target
EOF

# 2. 设置文件权限
sudo chmod 644 /etc/systemd/system/nkuwiki.service

# 3. 重载systemd配置
sudo systemctl daemon-reload

# 4. 启用开机启动
sudo systemctl enable nkuwiki.service

# 5. 启动服务
sudo systemctl start nkuwiki.service

# 6. 验证服务状态

sleep 10

systemctl status nkuwiki.service
