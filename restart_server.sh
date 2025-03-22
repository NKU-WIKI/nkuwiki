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

# 主函数
main() {
    log_info "开始执行重启脚本..."
    
    # 杀死占用80端口的进程
    log_info "查找并杀死占用80端口的进程..."
    PORT_80_PIDS=$(lsof -ti:80)
    if [ -n "$PORT_80_PIDS" ]; then
        log_warning "找到以下占用80端口的进程: $PORT_80_PIDS"
        kill -9 $PORT_80_PIDS
        log_success "已终止占用80端口的进程"
    else
        log_info "没有进程占用80端口"
    fi
    
    # 杀死占用443端口的进程
    log_info "查找并杀死占用443端口的进程..."
    PORT_443_PIDS=$(lsof -ti:443)
    if [ -n "$PORT_443_PIDS" ]; then
        log_warning "找到以下占用443端口的进程: $PORT_443_PIDS"
        kill -9 $PORT_443_PIDS
        log_success "已终止占用443端口的进程"
    else
        log_info "没有进程占用443端口"
    fi
    
    # 等待一秒确保端口完全释放
    sleep 1
    
    # 检查端口是否已经释放
    if lsof -ti:80 >/dev/null 2>&1 || lsof -ti:443 >/dev/null 2>&1; then
        log_error "端口释放失败，请手动检查"
        exit 1
    else
        log_success "端口已成功释放"
    fi
    
    # 启动应用
    log_info "正在启动应用程序..."
    
    # 检查nohup命令是否可用，以便应用在后台运行
    if command -v nohup >/dev/null 2>&1; then
        # 使用nohup启动应用并将输出重定向到日志文件
        nohup python app.py --api > app.log 2>&1 &
        APP_PID=$!
        log_success "应用已在后台启动，PID: $APP_PID"
        log_info "日志保存在 app.log 文件中"
    else
        # 如果nohup不可用，直接启动
        python app.py --api &
        APP_PID=$!
        log_success "应用已启动，PID: $APP_PID"
    fi
    
    # 等待几秒检查应用是否成功启动
    sleep 3
    if ps -p $APP_PID > /dev/null; then
        log_success "应用程序运行正常"
    else
        log_error "应用程序启动失败，请检查日志"
        exit 1
    fi
    
    log_info "脚本执行完成"
}

# 确保用户有足够权限
if [ "$(id -u)" -ne 0 ]; then
    log_warning "此脚本可能需要管理员权限来杀死系统进程"
    log_info "尝试继续执行..."
fi

# 执行主函数
main 