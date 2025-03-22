#!/bin/bash

# 设置错误时退出
set -e

echo "====== 开始提交修改 ======"

# 1. 提交services/app的修改（微信小程序子模块）
echo "====== 提交services/app子模块的修改 ======"
cd services/app

# 检查是否有修改
if git status --porcelain | grep -q .; then
    # 有修改，则添加并提交
    git add .
    git commit -m "优化：JSON字段处理逻辑，提高小程序稳定性"
    
    # 尝试推送修改
    echo "正在推送子模块修改..."
    git push
    echo "子模块修改已推送"
else
    echo "子模块没有需要提交的修改"
fi

# 返回项目根目录
cd ../..

# 2. 提交根项目的修改
echo "====== 提交根项目的修改 ======"

# 检查是否有修改
if git status --porcelain | grep -q .; then
    # 有修改，则添加并提交
    git add .
    git commit -m "优化：增强API接口JSON字段处理，修复500错误问题"
    
    # 尝试推送修改
    echo "正在推送根项目修改..."
    git push
    echo "根项目修改已推送"
else
    echo "根项目没有需要提交的修改"
fi

echo "====== 所有修改已提交完成 ======" 