#!/bin/bash
#
# nkuwiki market.py 定时任务配置脚本
#
# 功能:
# 1. 检查 market.py 的 cron 定时任务是否已存在。
# 2. 如果不存在，则添加一个每小时执行一次的任务。
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
CRON_COMMAND="0 * * * * $PYTHON_EXEC_PATH $MARKET_SCRIPT_PATH >> $LOG_FILE 2>&1"


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

# 检查并更新定时任务
echo "⏳ 正在配置/更新定时任务..."

# 从现有的crontab中移除旧的定时任务（通过注释和脚本路径识别），以确保配置总是最新的。
# 使用 grep -v 来排除匹配的行。
# 2>/dev/null 会抑制 `crontab -l` 在没有crontab时的错误输出。
CLEANED_CRON=$(crontab -l 2>/dev/null | grep -vF -- "$CRON_JOB_COMMENT" | grep -vF -- "$MARKET_SCRIPT_PATH")

# 添加新的任务
# 使用管道将清理后的crontab内容和新任务一起写入crontab
(echo "$CLEANED_CRON"; echo ""; echo "$CRON_JOB_COMMENT"; echo "$CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo "🎉 定时任务配置/更新成功！"
    echo "   现在，market.py脚本将每小时自动运行一次。"
    echo "   日志将保存在: $LOG_FILE"
else
    echo "❌ 错误：无法配置定时任务。请检查 'crontab' 命令是否可用以及权限是否正确。"
    exit 1
fi

echo ""
echo "---"
echo "后续操作提示:"
echo "  - 查看所有定时任务: crontab -l"
echo "  - 实时查看日志: tail -f $LOG_FILE"
echo "  - 手动编辑/移除任务: crontab -e"
echo "=============================================" 