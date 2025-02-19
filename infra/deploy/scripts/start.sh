#!/bin/bash
#配置nkuwiki自启动

# 1. 创建两个服务文件
# NKUWiki主服务
sudo tee /etc/systemd/system/nkuwiki.service <<EOF
[Unit]
Description=NKUWiki Main Service
After=network.target

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki
ExecStart=/opt/venv/nkuwiki/bin/python ./app.py
Restart=always
RestartSec=3
StandardOutput=file:/var/log/nkuwiki.log
StandardError=file:/var/log/nkuwiki-error.log

[Install]
WantedBy=multi-user.target
EOF

# Coze数据源服务
sudo tee /etc/systemd/system/coze_datasource.service <<EOF
[Unit]
Description=NKUWiki Coze DataSource
After=network.target

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki
ExecStart=/opt/venv/nkuwiki/bin/python ./etl/pipeline/coze_datasource.py
Restart=always
RestartSec=3
StandardOutput=file:/var/log/coze_datasource.log
StandardError=file:/var/log/coze_datasource-error.log

[Install]
WantedBy=multi-user.target
EOF

# 后续步骤需要为两个服务执行
for service in nkuwiki coze_datasource; do
    sudo chmod 644 /etc/systemd/system/$service.service
    sudo systemctl enable $service.service
    sudo systemctl start $service.service
done

sudo systemctl daemon-reload

# 验证状态时检查两个服务
sleep 5
systemctl status nkuwiki.service 
systemctl status coze_datasource.service
