#!/bin/bash
# nkuwiki_service_manager.sh - 管理nkuwiki双服务（8000端口1个worker和8001端口8个worker）
# 用法: ./nkuwiki_service_manager.sh [命令] [参数]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 常量
NGINX_CONF_DIR="/etc/nginx/conf.d"
NGINX_SITES_DIR="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
HTTP_CONF="${NGINX_SITES_DIR}/nkuwiki.conf"
HTTPS_CONF="${NGINX_SITES_DIR}/nkuwiki-ssl.conf"
UPSTREAM_CONF="${NGINX_CONF_DIR}/upstream.conf"
SSL_CERT_PATH="/etc/ssl/certs/nkuwiki.com.crt"
SSL_KEY_PATH="/etc/ssl/private/nkuwiki.com.key"

# 帮助信息
function show_help {
    echo -e "${BLUE}nkuwiki服务管理脚本${NC}"
    echo -e "${YELLOW}功能:${NC} 管理nkuwiki双实例服务（8000端口1个worker和8001端口8个worker）"
    echo -e "${YELLOW}版本:${NC} 1.0.0"
    echo ""
    echo -e "${BLUE}用法:${NC} $0 命令 [参数]"
    echo ""
    echo -e "${GREEN}== 基本命令 ==${NC}"
    echo -e "  ${YELLOW}deploy${NC}                      - 一键部署双服务配置"
    echo -e "  ${YELLOW}start${NC}                      - 启动所有nkuwiki服务"
    echo -e "  ${YELLOW}restart${NC}                    - 重启所有nkuwiki服务"
    echo -e "  ${YELLOW}status${NC}                     - 查看所有nkuwiki服务状态"
    echo -e "  ${YELLOW}cleanup${NC}                    - 清理所有服务"
    echo -e "  ${YELLOW}help${NC}                       - 显示此帮助信息"
    echo ""
    echo -e "${GREEN}== 使用示例 ==${NC}"
    echo -e "  $0 deploy                  - 一键部署双服务配置"
    echo -e "  $0 start                   - 启动所有服务"
    echo -e "  $0 restart                 - 重启所有服务"
    echo -e "  $0 status                  - 查看所有服务状态"
    echo -e "  $0 cleanup                 - 清理所有服务"
    echo ""
    echo -e "${BLUE}注意事项:${NC}"
    echo -e "  1. 本脚本需要root权限执行"
    echo -e "  2. 会创建两个服务：端口8000(1个worker)和端口8001(8个worker)"
    echo -e "  3. 服务配置默认使用最少连接负载均衡策略"
    echo -e "  4. 清理命令会停止所有服务并删除服务文件"
}

# 检查是否是root用户
function check_root {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}错误: 此脚本需要root权限${NC}"
        exit 1
    fi
}

# 检查端口是否已被占用
function check_port_available {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        return 1  # 端口已被占用
    else
        return 0  # 端口可用
    fi
}

# 创建两个特定配置的API服务
function create_dual_service {
    echo -e "${BLUE}创建两个特定配置的API服务...${NC}"
    
    # 检查端口可用性
    local ports_conflict=0
    for port in 8000 8001; do
        if ! check_port_available $port; then
            process=$(netstat -tulnp | grep ":$port " | awk '{print $7}')
            echo -e "${YELLOW}警告: 端口 $port 已被进程 $process 占用${NC}"
            ports_conflict=1
        fi
    done
    
    # 如果有端口冲突，提示用户
    if [ $ports_conflict -eq 1 ]; then
        echo -e "${YELLOW}检测到端口冲突！您可以:${NC}"
        echo -e "  1. 停止占用端口的进程"
        read -p "是否继续创建服务? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}操作已取消${NC}"
            exit 1
        fi
    fi
    
    # 创建8000端口服务 - 1个worker
    local service_path="/etc/systemd/system/nkuwiki.service"
    cat > "$service_path" << EOF
[Unit]
Description=NKU Wiki API Service (Port 8000, 1 Worker)
After=network.target nginx.service mysql.service

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki-shell/nkuwiki
ExecStart=/opt/venvs/nkuwiki/bin/python3 app.py --api --port 8000 --workers 1
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
CPUQuota=30%
MemoryLimit=2G
TasksMax=64
TimeoutStartSec=30
TimeoutStopSec=30
OOMScoreAdjust=-500
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}创建服务文件: $service_path (端口: 8000, Worker: 1)${NC}"
    
    # 创建8001端口服务 - 4个worker
    service_path="/etc/systemd/system/nkuwiki-8001.service"
    cat > "$service_path" << EOF
[Unit]
Description=NKU Wiki API Service (Port 8001, 1 Worker)
After=network.target nginx.service mysql.service

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki-shell/nkuwiki
ExecStart=/opt/venvs/nkuwiki/bin/python3 app.py --api --port 8001 --workers 1
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
CPUQuota=70%
MemoryLimit=4G
TasksMax=128
TimeoutStartSec=30
TimeoutStopSec=30
OOMScoreAdjust=-500
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}创建服务文件: $service_path (端口: 8001, Worker: 1)${NC}"
    
    # 重新加载systemd配置
    systemctl daemon-reload
    echo -e "${GREEN}所有服务文件已创建并加载${NC}"
}

# 生成简化的Nginx upstream配置
function generate_nginx_config {
    echo -e "${BLUE}生成Nginx配置...${NC}"
    
    # 确保目录存在
    mkdir -p "$NGINX_SITES_ENABLED"
    mkdir -p "$NGINX_CONF_DIR"
    mkdir -p "$NGINX_SITES_DIR"
    
    # 创建upstream配置
    cat > "$UPSTREAM_CONF" << EOF
# nkuwiki API服务负载均衡upstream配置
# 由nkuwiki_service_manager.sh自动生成
# 生成时间: $(date)

upstream nkuwiki_backend {
    # 负载均衡策略: least_conn (最少连接)
    least_conn;
    
    # 后端服务器列表 - 特定配置
    server 127.0.0.1:8000 weight=1; # 1 个worker，低负载
    server 127.0.0.1:8001 weight=1; # 1 个worker，高负载
    
    # 长连接配置
    keepalive 32;
}
EOF
    
    # 生成HTTP配置
    cat > "$HTTP_CONF" << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name nkuwiki.com www.nkuwiki.com;

    # 记录访问日志
    access_log /var/log/nginx/nkuwiki.access.log;
    error_log /var/log/nginx/nkuwiki.error.log;
    
    # 字符集设置
    charset utf-8;

    # 默认添加CORS头部
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
    
    # 安全相关头部
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";

    # 健康检查端点
    location /health {
        proxy_pass http://nkuwiki_backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
        proxy_read_timeout 5s;
    }

    # 为了支持Let's Encrypt的验证
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # 反向代理到负载均衡后端
    location / {
        proxy_pass http://nkuwiki_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # 静态文件缓存
    location ~* \.(css|js)$ {
        proxy_pass http://nkuwiki_backend;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        proxy_pass http://nkuwiki_backend/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /assets/ {
        proxy_pass http://nkuwiki_backend/assets/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /img/ {
        proxy_pass http://nkuwiki_backend/img/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    # 创建HTTP配置链接
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki.conf" ]; then
        rm -f "$NGINX_SITES_ENABLED/nkuwiki.conf"
    fi
    ln -sf "$HTTP_CONF" "$NGINX_SITES_ENABLED/nkuwiki.conf"
    
    # 生成HTTPS配置
    cat > "$HTTPS_CONF" << EOF
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name nkuwiki.com www.nkuwiki.com;

    # SSL证书配置
    ssl_certificate ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};
    
    # SSL协议设置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 记录访问日志
    access_log /var/log/nginx/nkuwiki-ssl.access.log;
    error_log /var/log/nginx/nkuwiki-ssl.error.log;
    
    # 字符集设置
    charset utf-8;

    # 安全相关设置
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # 默认添加CORS头部
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;

    # 反向代理到负载均衡后端
    location / {
        proxy_pass http://nkuwiki_backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://nkuwiki_backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        access_log off;
        proxy_read_timeout 5s;
    }

    # 静态文件缓存
    location ~* \\.(css|js)$ {
        proxy_pass http://nkuwiki_backend;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        proxy_pass http://nkuwiki_backend/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /assets/ {
        proxy_pass http://nkuwiki_backend/assets/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /img/ {
        proxy_pass http://nkuwiki_backend/img/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # 创建HTTPS配置链接
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf" ]; then
        rm -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    fi
    ln -sf "$HTTPS_CONF" "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    
    # 验证Nginx配置
    echo -e "${BLUE}验证Nginx配置...${NC}"
    nginx -t
    
    echo -e "${GREEN}Nginx配置已生成${NC}"
}

# 获取所有nkuwiki服务
function get_all_services {
    # 使用ls命令列出所有匹配的服务文件，并提取服务名称
    ls /etc/systemd/system/nkuwiki*.service 2>/dev/null | xargs -n1 basename 2>/dev/null || echo ""
}

# 清空logs目录
function clean_logs_directory {
    echo -e "${YELLOW}清空logs目录...${NC}"
    if [ -d "/home/nkuwiki/nkuwiki-shell/nkuwiki/logs" ]; then
        rm -rf /home/nkuwiki/nkuwiki-shell/nkuwiki/logs/*
        echo -e "${GREEN}logs目录已清空${NC}"
    else
        mkdir -p /home/nkuwiki/nkuwiki-shell/nkuwiki/logs
        echo -e "${GREEN}logs目录已创建${NC}"
    fi
}

# 启动所有服务
function start_services {
    echo -e "${BLUE}启动所有nkuwiki服务实例...${NC}"
    
    # 清空logs目录
    clean_logs_directory
    
    # 检查并启动主服务
    if systemctl is-active nkuwiki.service >/dev/null 2>&1; then
        echo -e "${GREEN}主服务 nkuwiki.service 已在运行${NC}"
    else
        echo -e "${YELLOW}启动 nkuwiki.service...${NC}"
        systemctl start nkuwiki.service
        sleep 2
        if ! systemctl is-active nkuwiki.service >/dev/null 2>&1; then
            echo -e "${RED}启动 nkuwiki.service 失败，检查日志: journalctl -u nkuwiki.service${NC}"
        else
            echo -e "${GREEN}主服务 nkuwiki.service 已启动${NC}"
        fi
    fi
    
    # 启动其他服务
    local failed_services=()
    
    for service in $(get_all_services); do
        # 跳过主服务，已在上面处理
        if [ "$service" = "nkuwiki.service" ]; then
            continue
        fi
        
        if systemctl is-active "$service" >/dev/null 2>&1; then
            echo -e "${GREEN}服务 $service 已在运行${NC}"
        else
            echo -e "${YELLOW}启动 $service...${NC}"
            systemctl start "$service"
            sleep 1
            
            # 检查服务是否成功启动
            if ! systemctl is-active "$service" >/dev/null 2>&1; then
                echo -e "${RED}启动 $service 失败${NC}"
                failed_services+=("$service")
            else
                echo -e "${GREEN}服务 $service 已启动${NC}"
            fi
        fi
    done
    
    # 如果有启动失败的服务，显示错误信息
    if [ ${#failed_services[@]} -gt 0 ]; then
        echo -e "${RED}以下服务启动失败:${NC}"
        for failed_service in "${failed_services[@]}"; do
            echo -e "${RED}- $failed_service${NC}"
            echo -e "${YELLOW}查看日志: journalctl -u $failed_service${NC}"
        done
    fi
}

# 一键部署简化双服务配置
function deploy_dual {
    echo -e "${BLUE}开始一键部署双服务配置...${NC}"
    
    # 1. 创建两个特定配置的服务
    create_dual_service
    
    # 2. 生成Nginx配置
    generate_nginx_config
    
    # 3. 启动所有服务
    start_services
    
    # 4. 设置开机自启
    echo -e "${BLUE}启用所有nkuwiki服务开机自启...${NC}"
    for service in $(get_all_services); do
        echo -e "启用 $service..."
        systemctl enable $service
    done
    
    # 5. 重载Nginx配置
    echo -e "${BLUE}重载Nginx配置...${NC}"
    nginx -t && systemctl reload nginx
    
    echo -e "${GREEN}双服务配置部署完成!${NC}"
}

# 重启所有服务
function restart_services {
    echo -e "${BLUE}重启所有nkuwiki服务实例...${NC}"
    
    # 清空logs目录
    clean_logs_directory
    
    # 重启主服务
    echo -e "${YELLOW}重启 nkuwiki.service...${NC}"
    systemctl restart nkuwiki.service
    
    if ! systemctl is-active nkuwiki.service >/dev/null 2>&1; then
        echo -e "${RED}重启 nkuwiki.service 失败，检查日志: journalctl -u nkuwiki.service${NC}"
    else
        echo -e "${GREEN}主服务 nkuwiki.service 已重启${NC}"
    fi
    
    # 重启其他服务
    local failed_services=()
    
    for service in $(get_all_services | grep -v "^nkuwiki.service$"); do
        echo -e "${YELLOW}重启 $service...${NC}"
        systemctl restart "$service"
        
        # 检查服务是否成功重启
        if ! systemctl is-active "$service" >/dev/null 2>&1; then
            echo -e "${RED}重启 $service 失败${NC}"
            failed_services+=("$service")
        else
            echo -e "${GREEN}服务 $service 已重启${NC}"
        fi
    done
    
    # 如果有重启失败的服务，显示错误信息
    if [ ${#failed_services[@]} -gt 0 ]; then
        echo -e "${RED}以下服务重启失败:${NC}"
        for failed_service in "${failed_services[@]}"; do
            echo -e "${RED}- $failed_service${NC}"
            echo -e "${YELLOW}查看日志: journalctl -u $failed_service${NC}"
        done
    fi
}

# 清理服务
function cleanup_services {
    echo -e "${BLUE}清理所有nkuwiki服务...${NC}"
    
    # 先停止服务
    for service in $(get_all_services); do
        echo -e "停止 $service..."
        systemctl stop $service 2>/dev/null || true
        
        echo -e "禁用 $service..."
        systemctl disable $service 2>/dev/null || true
        
        service_path="/etc/systemd/system/$service"
        if [ -f "$service_path" ]; then
            echo -e "删除 $service_path..."
            rm -f "$service_path"
        fi
    done
    
    # 清理Nginx配置
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki.conf" ]; then
        echo -e "删除 $NGINX_SITES_ENABLED/nkuwiki.conf..."
        rm -f "$NGINX_SITES_ENABLED/nkuwiki.conf"
    fi
    
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf" ]; then
        echo -e "删除 $NGINX_SITES_ENABLED/nkuwiki-ssl.conf..."
        rm -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    fi
    
    if [ -f "$UPSTREAM_CONF" ]; then
        echo -e "删除 $UPSTREAM_CONF..."
        rm -f "$UPSTREAM_CONF"
    fi
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 重载Nginx配置
    echo -e "${BLUE}重载Nginx配置...${NC}"
    nginx -t && systemctl reload nginx
    
    echo -e "${GREEN}清理完成${NC}"
}

# 检查所有服务状态
function check_service_status {
    echo -e "${BLUE}检查所有nkuwiki服务状态...${NC}"
    
    echo -e "\n${GREEN}=== 服务状态摘要 ===${NC}"
    local all_services=$(get_all_services)
    
    if [ -z "$all_services" ]; then
        echo -e "${YELLOW}未发现任何nkuwiki服务${NC}"
        return
    fi
    
    local active_count=0
    local inactive_count=0
    local failed_count=0
    
    for service in $all_services; do
        local status=$(systemctl is-active "$service" 2>/dev/null)
        local enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "disabled")
        
        case "$status" in
            active)
                echo -e "${GREEN}✓ $service - 运行中${NC} (自启: $enabled)"
                active_count=$((active_count+1))
                ;;
            failed)
                echo -e "${RED}✗ $service - 失败${NC} (自启: $enabled)"
                failed_count=$((failed_count+1))
                ;;
            *)
                echo -e "${YELLOW}○ $service - 未运行${NC} (自启: $enabled)"
                inactive_count=$((inactive_count+1))
                ;;
        esac
    done
    
    echo -e "\n${GREEN}=== 统计信息 ===${NC}"
    echo -e "服务总数: ${#all_services[@]}"
    echo -e "运行中: ${GREEN}$active_count${NC}"
    echo -e "未运行: ${YELLOW}$inactive_count${NC}"
    echo -e "失败: ${RED}$failed_count${NC}"
    
    echo -e "\n${GREEN}=== Nginx和负载均衡状态 ===${NC}"
    if [ -f "$UPSTREAM_CONF" ]; then
        echo -e "${GREEN}✓ 负载均衡配置已存在${NC}"
        echo -e "配置文件: $UPSTREAM_CONF"
    else
        echo -e "${RED}✗ 负载均衡配置不存在${NC}"
    fi
    
    if systemctl is-active nginx >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Nginx服务运行中${NC}"
        nginx -t 2>/dev/null
    else
        echo -e "${RED}✗ Nginx服务未运行${NC}"
    fi
    
    # 检查端口状态
    echo -e "\n${GREEN}=== 端口状态 ===${NC}"
    for port in 8000 8001; do
        if netstat -tuln | grep -q ":$port "; then
            local pid=$(netstat -tulnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
            local process=$(ps -p $pid -o comm= 2>/dev/null || echo "未知")
            echo -e "${GREEN}✓ 端口 $port - 已使用${NC} (进程: $process, PID: $pid)"
        else
            echo -e "${RED}✗ 端口 $port - 未使用${NC}"
        fi
    done
    
    echo -e "\n${BLUE}状态检查完成${NC}"
}

# 主函数
function main {
    check_root
    
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    case "$1" in
        deploy)
            deploy_dual
            ;;
        start)
            start_services
            ;;
        restart)
            restart_services
            ;;
        status)
            check_service_status
            ;;
        cleanup)
            cleanup_services
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知命令 $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 