#!/bin/bash

echo "=== 清理包缓存 ==="
apt-get clean

echo "=== 清理 pip 缓存 ==="
if command -v pip &>/dev/null; then
    pip cache purge
fi
rm -rf ~/.cache/pip

echo "=== 清理所有系统日志 ==="
find /var/log -type f -exec rm -f {} \;
echo "=== 清理 /var/log/syslog ==="
rm -f /var/log/syslog*

echo "=== 清理临时文件 ==="
/bin/rm -rf /tmp/*
/bin/rm -rf /var/tmp/*

echo "=== 清理7天前的日志 ==="
find /var/log -type f -mtime +7 -exec rm -f {} \;

echo "=== 压缩7天内未压缩的日志 ==="
find /var/log -type f -name "*.log" -mtime +1 ! -name "*.gz" -exec gzip {} \;

echo "=== 当前空间占用前20的大文件（未自动删除，仅供参考）==="
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k 5 -rh | head -20

echo "=== 清理完成 ==="
df -h