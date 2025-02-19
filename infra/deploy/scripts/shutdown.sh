#!/bin/bash
# 查找占用80和8000端口的进程并杀死
pid=$(lsof -ti:80,8000)
if [ -n "$pid" ]; then
    kill $pid
    echo "已杀死占用80和8000端口的进程（PID: $pid）"
else
    echo "没有进程占用80和8000端口。"
fi

sudo systemctl stop nkuwiki.service
sudo systemctl disable nkuwiki.service
sudo systemctl daemon-reload
