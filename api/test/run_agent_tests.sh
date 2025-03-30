#!/bin/bash
# 运行Agent相关测试

echo "=== 开始测试Agent接口 ==="

# 确保API服务已启动
echo "检查API服务是否正常运行..."
if ! curl -s "http://localhost:8000/api/health" > /dev/null; then
  echo "API服务未启动或不可访问，尝试重启服务..."
  kill -9 $(lsof -t -i:8000) 2>/dev/null
  python app.py --api --port 8000 &
  echo "等待服务启动..."
  sleep 10
  
  if ! curl -s "http://localhost:8000/api/health" > /dev/null; then
    echo "服务重启失败，请手动启动服务后再运行测试"
    exit 1
  fi
  echo "API服务已成功启动"
else
  echo "API服务正常运行"
fi

# 创建日志目录
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="api/test/logs"
mkdir -p $LOG_DIR

# 运行测试脚本
echo "运行Agent状态测试..."
python api/test/test_agent.py > "${LOG_DIR}/agent_basic_${TIMESTAMP}.log" 2>&1
BASIC_RESULT=$?

echo "运行完整Agent测试..."
python api/test/test_agent_full.py > "${LOG_DIR}/agent_full_${TIMESTAMP}.log" 2>&1
FULL_RESULT=$?

echo "运行Agent端点测试..."
python api/test/test_agent_endpoints.py > "${LOG_DIR}/agent_endpoints_${TIMESTAMP}.log" 2>&1
ENDPOINTS_RESULT=$?

# 查看测试结果
if [ $BASIC_RESULT -eq 0 ] && [ $FULL_RESULT -eq 0 ] && [ $ENDPOINTS_RESULT -eq 0 ]; then
  echo "✅ 所有测试通过！"
else
  echo "❌ 测试失败！"
  if [ $BASIC_RESULT -ne 0 ]; then
    echo "  - 基础测试失败"
  fi
  if [ $FULL_RESULT -ne 0 ]; then
    echo "  - 完整测试失败"
  fi
  if [ $ENDPOINTS_RESULT -ne 0 ]; then
    echo "  - 端点测试失败"
  fi
  echo "请检查日志以获取详细信息: ${LOG_DIR}"
fi

echo "日志已保存到: ${LOG_DIR}"
echo "=== 测试完成 ===" 