#!/bin/bash
# 设置定时清理无标题帖子的crontab任务
# 版本: 1.0.0
# 创建日期: 2025-04-21
# 维护者: NKU Wiki Team
# 用法: bash setup_cleanup_cron.sh

# 确保脚本可执行
chmod +x "$(dirname "$0")/cleanup_untitled_posts.py"

# 获取项目根目录的绝对路径
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PYTHON_PATH="/opt/venvs/nkuwiki/bin/python3"
SCRIPT_PATH="${PROJECT_ROOT}/infra/deploy/cleanup_untitled_posts.py"

# 检查Python路径是否存在
if [ ! -f "$PYTHON_PATH" ]; then
    echo "错误: Python路径不存在: $PYTHON_PATH"
    echo "请修改脚本中的PYTHON_PATH变量为正确的Python路径"
    exit 1
fi

# 创建临时crontab文件
TEMP_CRONTAB=$(mktemp)
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "" > "$TEMP_CRONTAB"

# 检查是否已经存在相同的任务
if grep -q "cleanup_untitled_posts.py" "$TEMP_CRONTAB"; then
    echo "定时任务已存在，无需重复添加"
else
    # 添加定时任务（每天凌晨3点执行）
    echo "# 每天凌晨3点执行清理无标题帖子的任务" >> "$TEMP_CRONTAB"
    echo "0 3 * * * cd ${PROJECT_ROOT} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${PROJECT_ROOT}/logs/cleanup_cron.log 2>&1" >> "$TEMP_CRONTAB"
    
    # 应用新的crontab配置
    crontab "$TEMP_CRONTAB"
    echo "已成功添加定时任务：每天凌晨3点执行清理无标题帖子的任务"
fi

# 清理临时文件
rm -f "$TEMP_CRONTAB"

echo "设置完成！"
echo "您可以运行 'crontab -l' 查看所有定时任务"

# 提示用户可以手动测试脚本
echo ""
echo "如需立即测试脚本，请运行:"
echo "cd ${PROJECT_ROOT} && ${PYTHON_PATH} ${SCRIPT_PATH}" 