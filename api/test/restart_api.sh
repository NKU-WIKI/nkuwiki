#!/bin/bash

# 设置Python环境
PYTHON=python
export PYTHONPATH=$PYTHONPATH:$(pwd)/../..

# 停止现有进程
echo "停止现有API服务..."
lsof -t -i:8000 | xargs -r kill -9
sleep 2

# 启动新的API服务进程
echo "启动API服务..."
cd ../..
nohup $PYTHON app.py --api --port 8000 > logs/api_service.log 2>&1 &
sleep 3

# 检查服务是否启动
echo "检查API服务状态..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health

echo -e "\n重启完成，测试接口..."
curl -X GET "http://localhost:8000/api/health" 