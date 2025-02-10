#!/bin/bash
# 查找占用80端口的进程并杀死
pid=$(lsof -ti:80)
if [ -n "$pid" ]; then
    kill $pid
    echo "已杀死占用80端口的进程（PID: $pid）"
else
    echo "没有进程占用80端口。"
fi

sudo systemctl stop nkuwiki.service
sudo systemctl disable nkuwiki.service
sudo systemctl daemon-reload
