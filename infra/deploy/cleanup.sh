#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLEANUP_PY="${SCRIPT_DIR}/cleanup_untitled_posts.py"

# 1. 清理包缓存
echo "=== 清理包缓存 ==="
apt-get clean

# 2. 清理 pip 缓存
echo "=== 清理 pip 缓存 ==="
if command -v pip &>/dev/null; then
    pip cache purge
fi
rm -rf ~/.cache/pip

# 3. 清理所有系统日志
echo "=== 清理所有系统日志 ==="
find /var/log -type f -exec rm -f {} \;
echo "=== 清理 /var/log/syslog ==="
rm -f /var/log/syslog*

# 4. 清理临时文件
echo "=== 清理临时文件 ==="
/bin/rm -rf /tmp/*
/bin/rm -rf /var/tmp/*

# 5. 清理无标题帖子（如脚本存在）
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
        mkdir -p "${PROJECT_ROOT}/logs"
        $PYTHON_PATH "$CLEANUP_PY" >> "${PROJECT_ROOT}/logs/cleanup_untitled_posts.log" 2>&1
    fi
else
    echo "未找到 $CLEANUP_PY，跳过无标题帖子清理。"
fi

# 6. 显示当前空间占用前20的大文件（未自动删除，仅供参考）
echo "=== 当前空间占用前20的大文件（未自动删除，仅供参考）==="
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k 5 -rh | head -20

echo "=== 清理完成 ==="
df -h 