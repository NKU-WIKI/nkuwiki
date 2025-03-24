#!/bin/bash

# 设置Python环境
PYTHON=/opt/venvs/nkuwiki/bin/python
export PYTHONPATH=$PYTHONPATH:$(pwd)/../..

# 设置日志文件路径
LOG_FILE="../../logs/nkuwiki.log"
WARNING_LOG_FILE="../../logs/nkuwiki(warning).log"

# 清理旧的测试日志
echo "清理旧的测试日志..."
echo "" > $LOG_FILE
echo "" > $WARNING_LOG_FILE

# 重启服务
echo "重启nkuwiki服务..."
sudo systemctl restart nkuwiki.service

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 监控日志文件
tail -f $LOG_FILE $WARNING_LOG_FILE | grep -i "error\|warning\|critical" &
LOG_PID=$!

# 运行测试
echo "开始运行测试..."
$PYTHON -m pytest -v \
    --disable-warnings \
    --capture=no \
    --log-cli-level=DEBUG \
    test_wxapp.py \
    test_mysql.py \
    test_agent.py

# 获取测试结果
TEST_RESULT=$?

# 停止日志监控
kill $LOG_PID

# 检查日志中的错误
echo "检查测试日志..."
ERROR_COUNT=$(grep -i "error" $LOG_FILE $WARNING_LOG_FILE | wc -l)
WARNING_COUNT=$(grep -i "warning" $LOG_FILE $WARNING_LOG_FILE | wc -l)

# 输出测试结果
if [ $TEST_RESULT -eq 0 ]; then
    echo "测试用例全部通过！"
else
    echo "测试失败，请检查日志。"
fi

# 输出日志统计
echo "日志统计:"
echo "- 错误数: $ERROR_COUNT"
echo "- 警告数: $WARNING_COUNT"

# 如果有错误，显示错误详情
if [ $ERROR_COUNT -gt 0 ]; then
    echo -e "\n错误详情:"
    grep -i "error" $LOG_FILE $WARNING_LOG_FILE
fi

exit $TEST_RESULT
