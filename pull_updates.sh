#!/bin/bash

# 颜色设置
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否执行成功
check_result() {
    if [ $? -ne 0 ]; then
        log_error "$1"
        exit 1
    fi
}

# 主函数
main() {
    # 获取脚本开始执行时间
    start_time=$(date +%s)
    
    log_info "开始更新 nkuwiki 项目..."
    
    # 确保我们在项目根目录
    if [ ! -d ".git" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 更新根项目
    log_info "正在更新根项目..."
    git fetch
    check_result "根项目 fetch 失败"
    
    git_status=$(git status -uno)
    
    # 检查是否有本地修改
    if echo "$git_status" | grep -q "Changes not staged"; then
        log_warning "本地有未提交的修改，将尝试 stash"
        git stash
        local_changes=true
    fi
    
    # 获取当前分支
    current_branch=$(git branch --show-current)
    log_info "当前分支: $current_branch"
    
    # 拉取更新
    git pull origin $current_branch
    check_result "根项目更新失败"
    log_success "根项目更新完成"
    
    # 如果有 stash 的更改，恢复
    if [ "$local_changes" = true ]; then
        log_info "恢复本地修改..."
        git stash pop
        if [ $? -ne 0 ]; then
            log_warning "恢复本地修改时出现冲突，请手动解决"
        fi
    fi
    
    # 检查 services/app 子模块是否存在
    if [ ! -d "services/app" ]; then
        log_error "services/app 子模块不存在"
        exit 1
    fi
    
    # 更新子模块
    log_info "正在更新 services/app 子模块..."
    cd services/app
    check_result "无法进入 services/app 目录"
    
    git fetch
    check_result "子模块 fetch 失败"
    
    git_status=$(git status -uno)
    
    # 检查子模块是否有本地修改
    if echo "$git_status" | grep -q "Changes not staged"; then
        log_warning "子模块有未提交的修改，将尝试 stash"
        git stash
        submodule_changes=true
    fi
    
    # 获取子模块当前分支
    submodule_branch=$(git branch --show-current)
    log_info "子模块当前分支: $submodule_branch"
    
    # 拉取子模块更新
    git pull origin $submodule_branch
    check_result "子模块更新失败"
    log_success "子模块更新完成"
    
    # 如果子模块有 stash 的更改，恢复
    if [ "$submodule_changes" = true ]; then
        log_info "恢复子模块本地修改..."
        git stash pop
        if [ $? -ne 0 ]; then
            log_warning "恢复子模块本地修改时出现冲突，请手动解决"
        fi
    fi
    
    # 返回项目根目录
    cd ../..
    
    # 更新子模块引用
    log_info "更新子模块引用..."
    git submodule update --remote services/app
    check_result "子模块引用更新失败"
    
    # 如果子模块引用有更新，提示用户提交
    if git status | grep -q "modified.*services/app"; then
        log_warning "子模块引用已更新，可能需要提交此更改"
    fi
    
    # 获取脚本结束执行时间并计算用时
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    log_success "所有更新完成！用时 ${duration} 秒"
}

# 执行主函数
main 