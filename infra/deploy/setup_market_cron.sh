#!/bin/bash
#
# nkuwiki market.py 定时任务配置脚本
#
# 功能:
# 1. 检查 market.py 的 cron 定时任务是否已存在。
# 2. 如果不存在，则添加一个每30分钟执行一次的任务。
# 3. 任务的输出(包括错误)会被重定向到 logs/market_crawler.log 文件。
#
set -e

# --- 配置 ---
# 获取脚本所在的目录，并向上两级，从而确定项目根目录
# 这使得脚本可以在任何位置被安全地调用
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" &> /dev/null && pwd )"

# Python解释器和目标脚本的绝对路径
PYTHON_EXEC_PATH="/opt/venvs/base/bin/python"
MARKET_SCRIPT_PATH="$PROJECT_ROOT/etl/crawler/market.py"

# 日志文件的绝对路径
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/cron.log"

# 用于在crontab中唯一标识此任务的注释
CRON_JOB_COMMENT="# NKUWiki Market Crawler Job"

# 最终要添加到crontab的命令
CRON_COMMAND="*/30 * * * * $PYTHON_EXEC_PATH $MARKET_SCRIPT_PATH >> $LOG_FILE 2>&1"


# --- 主逻辑 ---

# 确保日志目录存在
mkdir -p "$LOG_DIR"

echo "============================================="
echo " NKUWiki Market Crawler Cron Job Setup"
echo "============================================="
echo "项目根目录: $PROJECT_ROOT"
echo "将要配置的Cron任务:"
echo "$CRON_COMMAND"
echo ""

# 检查定时任务是否已经存在 (通过我们添加的唯一注释)
if crontab -l 2>/dev/null | grep -Fq -- "$CRON_JOB_COMMENT"; then
    echo "✅ 定时任务已经配置好了，无需重复添加。"
    echo "   您可以通过 'crontab -l' 命令查看。"
else
    echo "⏳ 正在添加新的定时任务..."
    # 使用现有crontab内容，并附加我们的新任务和注释
    (crontab -l 2>/dev/null; echo ""; echo "$CRON_JOB_COMMENT"; echo "$CRON_COMMAND") | crontab -
    if [ $? -eq 0 ]; then
        echo "🎉 定时任务添加成功！"
        echo "   现在，market.py脚本将每30分钟自动运行一次。"
        echo "   日志将保存在: $LOG_FILE"
    else
        echo "❌ 错误：无法添加定时任务。请检查 'crontab' 命令是否可用以及权限是否正确。"
        exit 1
    fi
fi

echo ""
echo "---"
echo "后续操作提示:"
echo "  - 查看所有定时任务: crontab -l"
echo "  - 实时查看日志: tail -f $LOG_FILE"
echo "  - 手动编辑/移除任务: crontab -e"
echo "=============================================" 