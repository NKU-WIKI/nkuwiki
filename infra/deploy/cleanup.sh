#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLEANUP_PY="${SCRIPT_DIR}/cleanup_untitled_posts.py"

# 显示清理前的磁盘使用情况
echo "=== 清理前磁盘使用情况 ==="
df -h

# 0. 显示清理前的Docker磁盘使用情况
echo "=== 清理前Docker磁盘使用情况 ==="
if command -v docker &> /dev/null; then
    docker system df
fi

# 1. 清理不再需要的软件包和依赖
echo "=== 清理不再需要的软件包和依赖 ==="
# 卸载服务器上非必要的图形化应用，如Google Chrome
if dpkg -l | grep -q "google-chrome-stable"; then
    echo "发现并卸载 Google Chrome..."
    apt-get purge google-chrome-stable -y
fi
# 移除已安装但不再需要的孤立依赖包
echo "清理孤立的依赖项..."
apt-get autoremove -y

# 2. 清理包缓存
echo "=== 清理包缓存 ==="
apt-get clean

# 3. 清理 pip 缓存
echo "=== 清理 pip 缓存 ==="
if command -v pip &>/dev/null; then
    pip cache purge
fi
rm -rf ~/.cache/pip

# 4. 清理应用级缓存 (Playwright等)
echo "=== 清理应用级缓存 ==="
PLAYWRIGHT_CACHE="/root/.cache/ms-playwright"
if [ -d "$PLAYWRIGHT_CACHE" ]; then
    echo "清理 Playwright 缓存: $PLAYWRIGHT_CACHE"
    rm -rf "$PLAYWRIGHT_CACHE"
else
    echo "Playwright 缓存目录不存在，跳过。"
fi

# 5. 清理所有系统日志
echo "=== 清理所有系统日志 ==="
echo "清空主要的系统日志文件..."
truncate -s 0 /var/log/syslog >/dev/null 2>&1
truncate -s 0 /var/log/kern.log >/dev/null 2>&1

echo "删除旧的轮转日志、.log文件和归档..."
rm -f /var/log/syslog.*
rm -f /var/log/kern.log.*
# 清理/var/log/下的所有.log文件和归档文件
find /var/log -name "*.log" -print -delete
find /var/log -name "*.gz" -print -delete

# 清理journald日志
if command -v journalctl &> /dev/null; then
    echo "清理journald日志..."
    journalctl --rotate
    journalctl --vacuum-time=1d
fi
echo "系统日志清理完成。"

# 6. 清理fail2ban日志文件
echo "=== 清理fail2ban日志 ==="
FAIL2BAN_LOG_PATH="/home/nkuwiki/nkuwiki-shell/docker-data/dms/mail-logs/"
if [ -d "$FAIL2BAN_LOG_PATH" ]; then
    echo "清理 $FAIL2BAN_LOG_PATH 下的 fail2ban.log* ..."
    # 使用-print会打印出被删除的文件名
    find "$FAIL2BAN_LOG_PATH" -name "fail2ban.log*" -print -delete
else
    echo "目录不存在: $FAIL2BAN_LOG_PATH"
fi

# 7. 清理临时文件
echo "=== 清理临时文件 ==="
/bin/rm -rf /tmp/*
/bin/rm -rf /var/tmp/*

# 8. 清理Docker容器日志
echo "=== 清理正在运行的Docker容器日志 ==="
if command -v docker &> /dev/null && [ -n "$(docker ps -q)" ]; then
    echo "查找并清空所有正在运行容器的日志文件..."
    # 使用 xargs 并行处理，提高效率
    docker ps -q | xargs docker inspect --format='{{.LogPath}}' | xargs -r -L1 truncate -s 0
    echo "Docker容器日志清理完成。"
else
    echo "没有正在运行的Docker容器或未安装Docker，跳过日志清理。"
fi

# 9. 清理无标题帖子（如脚本存在）
echo "=== 清理无标题帖子 ==="
if [ -f "$CLEANUP_PY" ]; then
    # 检测python路径
    if [ -x "/opt/venvs/nkuwiki/bin/python3" ]; then
        PYTHON_PATH="/opt/venvs/nkuwiki/bin/python3"
    elif command -v python3 &>/dev/null; then
        PYTHON_PATH="$(command -v python3)"
    else
        echo "未找到可用的python3路径，跳过无标题帖子清理。"
        PYTHON_PATH=""
    fi
    if [ -n "$PYTHON_PATH" ]; then
        # 确保日志目录存在
        mkdir -p "${PROJECT_ROOT}/logs"
        
        # 切换到项目根目录再执行Python脚本，以确保相对路径正确
        CURRENT_DIR=$(pwd)
        cd "$PROJECT_ROOT"
        $PYTHON_PATH "$CLEANUP_PY" >> "${PROJECT_ROOT}/logs/cleanup_untitled_posts.log" 2>&1
        cd "$CURRENT_DIR"  # 恢复原来的目录
    fi
else
    echo "未找到 $CLEANUP_PY，跳过无标题帖子清理。"
fi

# 10. 清理Docker系统
echo "=== 清理Docker系统 ==="
if command -v docker &>/dev/null; then
    echo "--- 清理所有未使用的Docker资源 (包括非悬空镜像和构建缓存) ---"
    docker system prune -af
    
    echo "--- 清理无用的数据卷 ---"
    docker volume prune -f
    
    echo "--- 清理后Docker磁盘使用情况 ---"
    docker system df
else
    echo "Docker未安装，跳过Docker清理。"
fi

# 11. 显示当前空间占用前20的大文件（未自动删除，仅供参考）
echo "=== 当前空间占用前20的大文件（未自动删除，仅供参考）==="
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k 5 -rh | head -20

# 12. 设置或验证定时任务
echo "=== 设置或验证定时任务 ==="
if command -v crontab &> /dev/null; then
    # 获取脚本的绝对路径，确保在crontab中能正确执行
    SCRIPT_PATH="$(realpath "$0")"
    LOG_FILE="${PROJECT_ROOT}/logs/cron_cleanup.log"

    # 定义定时任务
    # 每天凌晨3点执行
    CRON_SCHEDULE="0 3 * * *"
    CRON_COMMAND="/bin/bash ${SCRIPT_PATH} >> ${LOG_FILE} 2>&1"
    CRON_JOB="${CRON_SCHEDULE} ${CRON_COMMAND}"

    # 检查定时任务是否已存在
    # crontab -l 可能因没有cron job而返回非0退出码，所以用|| true来忽略
    if ! (crontab -l 2>/dev/null || true) | grep -Fxq -- "${CRON_JOB}"; then
        echo "未找到定时清理任务，正在添加..."
        # 使用子shell将现有任务和新任务合并，然后导入crontab
        (crontab -l 2>/dev/null; echo "${CRON_JOB}") | crontab -
        if [ $? -eq 0 ]; then
            echo "定时任务已成功创建："
            echo "${CRON_JOB}"
        else
            echo "创建定时任务失败。请检查权限或手动添加。"
        fi
    else
        echo "定时清理任务已存在，无需操作。"
        # 高亮显示已存在的任务
        (crontab -l 2>/dev/null || true) | grep --color=always -F -- "${CRON_JOB}"
    fi
else
    echo "未找到crontab命令，请手动设置定时任务。"
fi

echo "=== 清理完成 ==="
df -h 