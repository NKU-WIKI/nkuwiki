#!/bin/bash
# nkuwiki_service_manager.sh - 管理nkuwiki单服务（8000端口2个worker）
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
SSL_CERT_PATH="/etc/ssl/certs/nkuwiki.com.crt"
SSL_KEY_PATH="/etc/ssl/private/nkuwiki.com.key"
PROJECT_ROOT="/home/nkuwiki/nkuwiki-shell/nkuwiki"
MIHOMO_SERVICE="mihomo.service"
MIHOMO_CONFIG_DIR="/etc/mihomo"
MIHOMO_API_PORT="9090"
ENABLE_PROXY=0

function show_help {
    echo -e "${BLUE}nkuwiki服务管理脚本${NC}"
    echo -e "${YELLOW}功能:${NC} 管理nkuwiki单实例服务（8000端口2个worker）"
    echo -e "${YELLOW}版本:${NC} 1.0.0"
    echo ""
    echo -e "${BLUE}用法:${NC} $0 命令 [参数]"
    echo ""
    echo -e "${GREEN}== 基本命令 ==${NC}"
    echo -e "  ${YELLOW}deploy${NC}                      - 一键部署服务配置"
    echo -e "  ${YELLOW}start${NC}                      - 启动nkuwiki服务"
    echo -e "  ${YELLOW}restart${NC}                    - 重启nkuwiki服务"
    echo -e "  ${YELLOW}status${NC}                     - 查看nkuwiki服务状态"
    echo -e "  ${YELLOW}cleanup${NC}                    - 清理服务"
    echo -e "  ${YELLOW}help${NC}                       - 显示此帮助信息"
    echo -e "${GREEN}== Mihomo服务命令 ==${NC}"
    echo -e "  ${YELLOW}restart-mihomo${NC}             - 重启mihomo代理服务"
    echo -e "  ${YELLOW}proxy-status${NC}               - 检查代理状态"
    echo ""
    echo -e "${GREEN}== 参数 ==${NC}"
    echo -e "  ${YELLOW}--proxy${NC}                    - 启用代理 (适用于deploy/start/restart)"
    echo -e "  ${YELLOW}--no-proxy${NC}                 - 禁用代理 (适用于deploy/start/restart) [默认]"
    echo ""
    echo -e "${GREEN}== 使用示例 ==${NC}"
    echo -e "  $0 deploy                  - 一键部署服务配置 (默认禁用代理)"
    echo -e "  $0 deploy --proxy          - 一键部署服务配置并启用代理"
    echo -e "  $0 start --proxy           - 启动服务并启用代理"
    echo -e "  $0 restart --no-proxy      - 重启服务并禁用代理"
    echo -e "  $0 status                  - 查看服务状态"
    echo -e "  $0 cleanup                 - 清理服务"
    echo -e "  $0 restart-mihomo          - 重启mihomo代理服务"
    echo -e "  $0 proxy-status            - 检查代理状态"
    echo ""
    echo -e "${BLUE}注意事项:${NC}"
    echo -e "  1. 本脚本需要root权限执行"
    echo -e "  2. 只创建一个服务：端口8000(2个worker)"
    echo -e "  3. 清理命令会停止服务并删除服务文件"
    echo -e "  4. 默认禁用代理，如需启用代理，请使用 --proxy 参数"
}

function check_root {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}错误: 此脚本需要root权限${NC}"
        exit 1
    fi
}

function check_port_available {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        return 1
    else
        return 0
    fi
}

function create_service {
    echo -e "${BLUE}创建API服务...${NC}"
    if ! check_port_available 8000; then
        process=$(netstat -tulnp | grep ":8000 " | awk '{print $7}')
        echo -e "${YELLOW}警告: 端口 8000 已被进程 $process 占用${NC}"
        read -p "是否继续创建服务? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}操作已取消${NC}"
            exit 1
        fi
    fi
    if [ $ENABLE_PROXY -eq 0 ]; then
        exec_start_pre='ExecStartPre=/bin/bash -c "unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY"'
    else
        exec_start_pre='# 代理已启用，保留环境变量'
    fi
    local service_path="/etc/systemd/system/nkuwiki.service"
    cat > "$service_path" << EOF
[Unit]
Description=NKU Wiki API Service (Port 8000, 2 Workers)
After=network.target nginx.service mysql.service

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki-shell/nkuwiki
$exec_start_pre
ExecStart=/opt/venvs/nkuwiki/bin/python3 app.py --api --port 8000 --workers 2
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
$(if [ $ENABLE_PROXY -eq 1 ]; then echo -e "Environment=\"http_proxy=http://127.0.0.1:7890\"\nEnvironment=\"https_proxy=http://127.0.0.1:7890\"\nEnvironment=\"all_proxy=socks5://127.0.0.1:7890\"\nEnvironment=\"no_proxy=localhost,127.0.0.1,192.168.*,10.*\""; fi)
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
    echo -e "${GREEN}创建服务文件: $service_path (端口: 8000, Worker: 2)${NC}"
    systemctl daemon-reload
    echo -e "${GREEN}服务文件已创建并加载${NC}"
}

function generate_nginx_config {
    echo -e "${BLUE}生成Nginx配置...${NC}"
    mkdir -p "$NGINX_SITES_ENABLED"
    mkdir -p "$NGINX_CONF_DIR"
    mkdir -p "$NGINX_SITES_DIR"
    # 自动修改nginx.conf的worker_connections
    NGINX_CONF="/etc/nginx/nginx.conf"
    if grep -q 'worker_connections' "$NGINX_CONF"; then
        sed -i 's/worker_connections[[:space:]]*[0-9]*;/worker_connections 2048;/' "$NGINX_CONF"
    else
        sed -i '/events {/a \    worker_connections 2048;' "$NGINX_CONF"
    fi
    cat > "$HTTP_CONF" << EOF
server {
    listen 80;
    listen [::]:80;
    server_name nkuwiki.com www.nkuwiki.com;
    access_log /var/log/nginx/nkuwiki.access.log;
    error_log /var/log/nginx/nkuwiki.error.log;
    charset utf-8;
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    location /mihomo {
        alias /var/www/html/mihomo;
        index index.html;
        try_files \$uri \$uri/ /mihomo/index.html;
    }
    location /mihomo/assets/ {
        alias /var/www/html/mihomo/assets/;
        expires 1d;
    }
    location ^~ /mihomo-api/ {
        proxy_pass http://127.0.0.1:9090/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' '*' always;
        error_log /var/log/nginx/mihomo-api.error.log debug;
        access_log /var/log/nginx/mihomo-api.access.log;
    }
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        access_log off;
        proxy_read_timeout 5s;
    }
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
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
    location ~* \\.(css|js) {
        proxy_pass http://127.0.0.1:8000;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /static/ {
        proxy_pass http://127.0.0.1:8000/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /assets/ {
        proxy_pass http://127.0.0.1:8000/assets/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /img/ {
        proxy_pass http://127.0.0.1:8000/img/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki.conf" ]; then
        rm -f "$NGINX_SITES_ENABLED/nkuwiki.conf"
    fi
    ln -sf "$HTTP_CONF" "$NGINX_SITES_ENABLED/nkuwiki.conf"
    cat > "$HTTPS_CONF" << EOF
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name nkuwiki.com www.nkuwiki.com;
    ssl_certificate ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    access_log /var/log/nginx/nkuwiki-ssl.access.log;
    error_log /var/log/nginx/nkuwiki-ssl.error.log;
    charset utf-8;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
    location /mihomo {
        alias /var/www/html/mihomo;
        index index.html;
        try_files \$uri \$uri/ /mihomo/index.html;
    }
    location /mihomo/assets/ {
        alias /var/www/html/mihomo/assets/;
        expires 1d;
    }
    location ^~ /mihomo-api/ {
        proxy_pass http://127.0.0.1:9090/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' '*' always;
        error_log /var/log/nginx/mihomo-api-ssl.error.log debug;
        access_log /var/log/nginx/mihomo-api-ssl.access.log;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
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
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        access_log off;
        proxy_read_timeout 5s;
    }
    location ~* \\.(css|js) {
        proxy_pass http://127.0.0.1:8000;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /static/ {
        proxy_pass http://127.0.0.1:8000/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /assets/ {
        proxy_pass http://127.0.0.1:8000/assets/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /img/ {
        proxy_pass http://127.0.0.1:8000/img/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf" ]; then
        rm -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    fi
    ln -sf "$HTTPS_CONF" "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    echo -e "${BLUE}验证Nginx配置...${NC}"
    nginx -t
    echo -e "${GREEN}Nginx配置已生成${NC}"
}

function clean_logs_directory {
    echo -e "${YELLOW}清空所有日志文件...${NC}"
    if [ -d "/home/nkuwiki/nkuwiki-shell/nkuwiki/logs" ]; then
        find /home/nkuwiki/nkuwiki-shell/nkuwiki/logs -type f -name "*.log" -exec truncate -s 0 {} \;
        find /home/nkuwiki/nkuwiki-shell/nkuwiki/logs -type f -name "*.log.*" -delete
        find /home/nkuwiki/nkuwiki-shell/nkuwiki/logs/*/  -type f -name "*.log" -exec truncate -s 0 {} \; 2>/dev/null || true
        find /home/nkuwiki/nkuwiki-shell/nkuwiki/logs/*/  -type f -name "*.log.*" -delete 2>/dev/null || true
        echo -e "${GREEN}所有日志文件已清空${NC}"
    else
        mkdir -p /home/nkuwiki/nkuwiki-shell/nkuwiki/logs
        echo -e "${GREEN}logs目录已创建${NC}"
    fi
}

function start_service {
    echo -e "${BLUE}启动nkuwiki服务...${NC}"
    clean_logs_directory
    echo -e "${BLUE}设置无标题帖子清理定时任务...${NC}"
    if [ -f "${PROJECT_ROOT}/infra/deploy/cleanup.sh" ]; then
        bash "${PROJECT_ROOT}/infra/deploy/cleanup.sh"
    else
        echo -e "${YELLOW}清理脚本不存在: ${PROJECT_ROOT}/infra/deploy/cleanup.sh${NC}"
    fi
    if systemctl is-active nkuwiki.service >/dev/null 2>&1; then
        echo -e "${GREEN}服务 nkuwiki.service 已在运行${NC}"
    else
        echo -e "${YELLOW}启动 nkuwiki.service...${NC}"
        systemctl start nkuwiki.service
        sleep 2
        if ! systemctl is-active nkuwiki.service >/dev/null 2>&1; then
            echo -e "${RED}启动 nkuwiki.service 失败，检查日志: journalctl -u nkuwiki.service${NC}"
        else
            echo -e "${GREEN}服务 nkuwiki.service 已启动${NC}"
        fi
    fi
}

function deploy {
    echo -e "${BLUE}开始一键部署服务配置...${NC}"
    create_service
    generate_nginx_config
    start_service
    echo -e "${BLUE}启用nkuwiki服务开机自启...${NC}"
    systemctl enable nkuwiki.service
    echo -e "${BLUE}重载Nginx配置...${NC}"
    nginx -t && systemctl reload nginx
    echo -e "${GREEN}服务配置部署完成!${NC}"
}

function restart_service {
    unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
    export no_proxy="*"
    export NO_PROXY="*"
    echo -e "${GREEN}已禁用所有代理环境变量${NC}"
    echo -e "${BLUE}重启nkuwiki服务...${NC}"
    clean_logs_directory
    echo -e "${YELLOW}重启 nkuwiki.service...${NC}"
    systemctl restart nkuwiki.service
    if ! systemctl is-active nkuwiki.service >/dev/null 2>&1; then
        echo -e "${RED}重启 nkuwiki.service 失败，检查日志: journalctl -u nkuwiki.service${NC}"
    else
        echo -e "${GREEN}服务 nkuwiki.service 已重启${NC}"
    fi
}

function cleanup_service {
    echo -e "${BLUE}清理nkuwiki服务...${NC}"
    systemctl stop nkuwiki.service 2>/dev/null || true
    systemctl disable nkuwiki.service 2>/dev/null || true
    service_path="/etc/systemd/system/nkuwiki.service"
    if [ -f "$service_path" ]; then
        echo -e "删除 $service_path..."
        rm -f "$service_path"
    fi
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki.conf" ]; then
        echo -e "删除 $NGINX_SITES_ENABLED/nkuwiki.conf..."
        rm -f "$NGINX_SITES_ENABLED/nkuwiki.conf"
    fi
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf" ]; then
        echo -e "删除 $NGINX_SITES_ENABLED/nkuwiki-ssl.conf..."
        rm -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    fi
    if [ -f "$HTTP_CONF" ]; then
        rm -f "$HTTP_CONF"
    fi
    if [ -f "$HTTPS_CONF" ]; then
        rm -f "$HTTPS_CONF"
    fi
    systemctl daemon-reload
    echo -e "${BLUE}重载Nginx配置...${NC}"
    nginx -t && systemctl reload nginx
    echo -e "${GREEN}清理完成${NC}"
}

function check_service_status {
    echo -e "${BLUE}检查nkuwiki服务状态...${NC}"
    local status=$(systemctl is-active nkuwiki.service 2>/dev/null)
    local enabled=$(systemctl is-enabled nkuwiki.service 2>/dev/null || echo "disabled")
    case "$status" in
        active)
            echo -e "${GREEN}✓ nkuwiki.service - 运行中${NC} (自启: $enabled)"
            ;;
        failed)
            echo -e "${RED}✗ nkuwiki.service - 失败${NC} (自启: $enabled)"
            ;;
        *)
            echo -e "${YELLOW}○ nkuwiki.service - 未运行${NC} (自启: $enabled)"
            ;;
    esac
    echo -e "\n${GREEN}=== Nginx状态 ===${NC}"
    if systemctl is-active nginx >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Nginx服务运行中${NC}"
        nginx -t 2>/dev/null
    else
        echo -e "${RED}✗ Nginx服务未运行${NC}"
    fi
    echo -e "\n${GREEN}=== 端口状态 ===${NC}"
    if netstat -tuln | grep -q ":8000 "; then
        local pid=$(netstat -tulnp 2>/dev/null | grep ":8000 " | awk '{print $7}' | cut -d'/' -f1)
        local process=$(ps -p $pid -o comm= 2>/dev/null || echo "未知")
        echo -e "${GREEN}✓ 端口 8000 - 已使用${NC} (进程: $process, PID: $pid)"
    else
        echo -e "${RED}✗ 端口 8000 - 未使用${NC}"
    fi
    echo -e "\n${BLUE}状态检查完成${NC}"
}

# Mihomo相关函数保持不变
# ... existing code ...
# 主函数
function main {
    check_root
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    local command="$1"
    shift
    while [ $# -gt 0 ]; do
        case "$1" in
            --proxy)
                ENABLE_PROXY=1
                echo -e "${GREEN}已启用代理${NC}"
                ;;
            --no-proxy)
                ENABLE_PROXY=0
                echo -e "${GREEN}已禁用代理${NC}"
                ;;
            *)
                echo -e "${RED}警告: 未知参数 $1${NC}"
                ;;
        esac
        shift
    done
    case "$command" in
        deploy)
            deploy
            ;;
        start)
            start_service
            ;;
        restart)
            restart_service
            ;;
        status)
            check_service_status
            ;;
        cleanup)
            cleanup_service
            ;;
        help)
            show_help
            ;;
        restart-mihomo)
            restart_mihomo
            ;;
        proxy-status)
            check_proxy_status
            ;;
        *)
            echo -e "${RED}错误: 未知命令 $command${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@" 