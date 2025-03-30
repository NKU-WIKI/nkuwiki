#!/bin/bash

# 设置Python环境
PYTHON=/opt/venvs/nkuwiki/bin/python
export PYTHONPATH=$PYTHONPATH:$(pwd)/../..

# 设置日志文件路径
LOG_DIR="../../logs"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/nkuwiki.log"
WARNING_LOG_FILE="$LOG_DIR/nkuwiki_warning.log"
TEST_LOG_FILE="$LOG_DIR/test_results.log"

# 清理旧的测试日志
echo "清理旧的测试日志..."
echo "" > $LOG_FILE
echo "" > $WARNING_LOG_FILE
echo "" > $TEST_LOG_FILE

# 检查API服务是否运行
check_api_running() {
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health
}

# 尝试启动API服务
start_api_service() {
    echo "启动或重启nkuwiki API服务..."
    
    # 尝试停止现有进程
    if pgrep -f "python app.py --api" > /dev/null; then
        echo "停止现有API服务..."
        kill -9 $(lsof -t -i:8000) 2>/dev/null
        sleep 2
    fi
    
    # 启动新的API服务进程
    cd ../..
    nohup $PYTHON app.py --api --port 8000 > $LOG_DIR/api_service.log 2>&1 &
    cd - > /dev/null
    
    # 等待服务启动
    echo "等待服务启动..."
    for i in {1..30}; do
        if [ "$(check_api_running)" == "200" ]; then
            echo "API服务已启动"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo "API服务启动超时，请检查日志"
    return 1
}

# 启动服务
start_api_service || exit 1

# 监控日志文件
tail -f $LOG_FILE $WARNING_LOG_FILE | grep -i "error\|warning\|critical" &
LOG_PID=$!

# 设置测试超时(秒)
TEST_TIMEOUT=120

# 插入测试数据
echo "插入测试数据..."
$PYTHON insert_test_data.py

# 运行测试
echo "开始运行测试..."
timeout $TEST_TIMEOUT $PYTHON -m pytest -v \
    --disable-warnings \
    --capture=no \
    --log-cli-level=INFO \
    test_wxapp.py \
    test_agent.py \
    test_admin.py 2>&1 | tee $TEST_LOG_FILE

# 获取测试结果
TEST_RESULT=$?

# 停止日志监控
kill $LOG_PID 2>/dev/null

# 检查测试是否超时
if [ $TEST_RESULT -eq 124 ]; then
    echo "测试超时，可能存在卡住的测试用例或性能问题"
    TEST_RESULT=1
fi

# 检查日志中的错误
echo "检查测试日志..."
ERROR_COUNT=$(grep -i "error" $LOG_FILE $WARNING_LOG_FILE | wc -l)
WARNING_COUNT=$(grep -i "warning" $LOG_FILE $WARNING_LOG_FILE | wc -l)

# 输出测试结果
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "\n\033[32m测试用例全部通过！\033[0m"
else
    echo -e "\n\033[31m测试失败，请检查日志。\033[0m"
fi

# 输出日志统计
echo -e "\n日志统计:"
echo "- 错误数: $ERROR_COUNT"
echo "- 警告数: $WARNING_COUNT"

# 如果有错误，显示错误详情
if [ $ERROR_COUNT -gt 0 ]; then
    echo -e "\n错误详情:"
    grep -i "error" $LOG_FILE $WARNING_LOG_FILE
fi

# 输出测试覆盖率报告
echo -e "\n测试覆盖情况:"
echo "wxapp API: $(grep -c "test_" test_wxapp.py) 个测试用例"
echo "agent API: $(grep -c "test_" test_agent.py) 个测试用例"
echo "admin API: $(grep -c "test_" test_admin.py) 个测试用例"
TOTAL_TESTS=$(grep -c "test_" test_*.py)
echo "总计: $TOTAL_TESTS 个测试用例"

exit $TEST_RESULT
