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
    
    # 子模块分支名称
    SUBMODULE_BRANCH="feature-search"
    
    # 更新根项目
    log_info "正在更新根项目..."
    git fetch
    check_result "根项目 fetch 失败"
    
    git_status=$(git status -uno)
    
    # 检查是否有本地修改并提交
    if echo "$git_status" | grep -q "Changes not staged\|Untracked files"; then
        log_info "检测到本地修改，准备提交..."
        
        # 添加所有修改
        git add -A
        check_result "添加文件失败"
        
        # 提交修改
        git commit -m "Auto commit local changes before update: $(date)"
        check_result "提交修改失败"
        
        log_success "本地修改已提交"
    fi
    
    # 获取当前分支
    current_branch=$(git branch --show-current)
    log_info "当前分支: $current_branch"
    
    # 拉取更新
    git pull origin $current_branch
    check_result "根项目更新失败"
    log_success "根项目更新完成"
    
    # 检查 services/app 子模块是否存在
    if [ ! -d "services/app" ]; then
        log_error "services/app 子模块不存在"
        exit 1
    fi
    
    # 更新子模块
    log_info "正在更新 services/app 子模块..."
    cd services/app
    check_result "无法进入 services/app 目录"
    
    git fetch origin
    check_result "子模块 fetch 失败"
    
    # 检查子模块是否在分支上
    submodule_branch=$(git branch --show-current)
    if [ -z "$submodule_branch" ]; then
        log_warning "子模块当前不在任何分支上，将检出 $SUBMODULE_BRANCH 分支"
        git checkout $SUBMODULE_BRANCH
        if [ $? -ne 0 ]; then
            log_info "尝试从远程创建 $SUBMODULE_BRANCH 分支"
            git checkout -b $SUBMODULE_BRANCH origin/$SUBMODULE_BRANCH
            check_result "无法创建并检出 $SUBMODULE_BRANCH 分支"
        fi
    else
        log_info "子模块当前分支: $submodule_branch"
        if [ "$submodule_branch" != "$SUBMODULE_BRANCH" ]; then
            log_warning "子模块不在 $SUBMODULE_BRANCH 分支上，正在切换..."
            git checkout $SUBMODULE_BRANCH
            check_result "切换到 $SUBMODULE_BRANCH 分支失败"
        fi
    fi
    
    # 检查子模块是否有本地修改并提交
    git_status=$(git status -uno)
    if echo "$git_status" | grep -q "Changes not staged\|Untracked files"; then
        log_info "检测到子模块有本地修改，准备提交..."
        
        # 添加所有修改
        git add -A
        check_result "添加子模块文件失败"
        
        # 提交修改
        git commit -m "Auto commit submodule local changes before update: $(date)"
        check_result "提交子模块修改失败"
        
        log_success "子模块本地修改已提交"
    fi
    
    # 拉取子模块更新
    log_info "拉取子模块 $SUBMODULE_BRANCH 分支更新..."
    git pull origin $SUBMODULE_BRANCH
    check_result "子模块更新失败"
    log_success "子模块更新完成"
    
    # 返回项目根目录
    cd ../..
    
    # 更新子模块引用
    log_info "更新子模块引用..."
    git add services/app
    
    # 如果子模块引用有更新，提交更改
    if git status | grep -q "modified.*services/app"; then
        log_info "提交子模块引用更新..."
        git commit -m "Update submodule services/app reference to latest commit"
        check_result "提交子模块引用更新失败"
        log_success "子模块引用更新已提交"
    else
        log_info "子模块引用没有变化"
    fi
    
    # 获取脚本结束执行时间并计算用时
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    log_success "所有更新完成！用时 ${duration} 秒"
    log_info "本地修改已提交，子模块已设置为 $SUBMODULE_BRANCH 分支"
}

# 执行主函数
main 