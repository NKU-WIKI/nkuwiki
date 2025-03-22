#!/bin/bash

# 设置错误时退出
set -e

echo "====== 开始提交用户信息修复 ======"

# 1. 提交services/app的修改（微信小程序子模块）
echo "====== 提交services/app子模块的修改 ======"
cd services/app

# 检查是否有修改
if git status --porcelain | grep -q .; then
    # 有修改，则添加并提交
    git add .
    git commit -m "修复：用户信息获取统一管理，解决个人信息不同步问题"
    
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
    git commit -m "修复：添加用户信息统一管理模块，解决小程序用户信息同步问题"
    
    # 尝试推送修改
    echo "正在推送根项目修改..."
    git push
    echo "根项目修改已推送"
else
    echo "根项目没有需要提交的修改"
fi

echo "====== 所有修改已提交完成 ======" 