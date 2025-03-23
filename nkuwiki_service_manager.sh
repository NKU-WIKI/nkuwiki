#!/bin/bash
# nkuwiki_service_manager.sh - 管理多端口nkuwiki服务
# 用法: ./nkuwiki_service_manager.sh [命令] [参数]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 常量
SERVICE_TEMPLATE="/etc/systemd/system/nkuwiki.service"
NGINX_CONF_DIR="/etc/nginx/conf.d"
NGINX_SITES_DIR="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
CLOUDFLARE_CONF="${NGINX_CONF_DIR}/cloudflare.conf"
HTTP_CONF="${NGINX_SITES_DIR}/nkuwiki.conf"
HTTPS_CONF="${NGINX_SITES_DIR}/nkuwiki-ssl.conf"
UPSTREAM_CONF="${NGINX_CONF_DIR}/upstream.conf"
BASE_PORT=8000
SSL_CERT_PATH="/etc/ssl/certs/nkuwiki.com.pem"
SSL_KEY_PATH="/etc/ssl/private/nkuwiki.com.key"

# 帮助信息
function show_help {
    echo -e "${BLUE}nkuwiki服务管理脚本${NC}"
    echo -e "${YELLOW}功能:${NC} 管理nkuwiki多实例服务、负载均衡和Nginx配置"
    echo -e "${YELLOW}版本:${NC} 1.0.0"
    echo ""
    echo -e "${BLUE}用法:${NC} $0 命令 [参数]"
    echo ""
    echo -e "${GREEN}== 服务实例管理 ==${NC}"
    echo -e "  ${YELLOW}create${NC} [起始端口] [实例数]   - 创建指定数量的服务实例，从起始端口开始"
    echo -e "  ${YELLOW}start${NC}                      - 启动所有nkuwiki服务"
    echo -e "  ${YELLOW}stop${NC}                       - 停止所有nkuwiki服务"
    echo -e "  ${YELLOW}restart${NC}                    - 重启所有nkuwiki服务"
    echo -e "  ${YELLOW}status${NC}                     - 显示所有nkuwiki服务状态和端口监听情况"
    echo -e "  ${YELLOW}enable${NC}                     - 启用所有nkuwiki服务开机自启"
    echo -e "  ${YELLOW}disable${NC}                    - 禁用所有nkuwiki服务开机自启"
    echo ""
    echo -e "${GREEN}== Nginx配置管理 ==${NC}"
    echo -e "  ${YELLOW}nginx${NC} [起始端口] [实例数]   - 生成Nginx负载均衡配置，包括upstream、HTTP和HTTPS配置"
    echo -e "  ${YELLOW}cloudflare${NC}                 - 配置Cloudflare IP范围和真实IP获取支持"
    echo -e "  ${YELLOW}setup-ssl${NC}                  - 设置SSL证书路径并验证证书是否存在"
    echo ""
    echo -e "${GREEN}== 一键操作 ==${NC}"
    echo -e "  ${YELLOW}deploy${NC} [起始端口] [实例数]  - 一键部署服务和配置(创建服务+负载均衡+SSL配置+启动服务)"
    echo -e "  ${YELLOW}cleanup${NC}                    - 清理所有创建的服务(不包括主服务)"
    echo -e "  ${YELLOW}cleanup-config${NC}             - 清理所有生成的Nginx配置文件"
    echo -e "  ${YELLOW}help${NC}                       - 显示此帮助信息"
    echo ""
    echo -e "${GREEN}== 使用示例 ==${NC}"
    echo -e "  $0 create 8000 4           - 创建4个服务，监听端口8000-8003"
    echo -e "  $0 nginx 8000 4            - 为端口8000-8003生成Nginx负载均衡配置"
    echo -e "  $0 deploy 8000 4           - 一键部署4个服务实例并配置Nginx"
    echo -e "  $0 status                  - 显示所有服务状态和端口监听情况"
    echo -e "  $0 cleanup && $0 cleanup-config - 完全清理服务和配置"
    echo ""
    echo -e "${BLUE}注意事项:${NC}"
    echo -e "  1. 本脚本需要root权限执行"
    echo -e "  2. 服务实例从指定起始端口开始，端口8000默认为主服务"
    echo -e "  3. 配置使用的域名默认为nkuwiki.com，可在脚本中修改"
    echo -e "  4. SSL证书默认路径为 ${SSL_CERT_PATH} 和 ${SSL_KEY_PATH}"
    echo -e "  5. 使用Cloudflare时，建议设置SSL/TLS模式为Full或Full(Strict)"
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

# 创建服务文件
function create_service {
    local start_port=$1
    local count=$2
    
    # 验证参数
    if ! [[ "$start_port" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 起始端口必须是数字${NC}"
        exit 1
    fi
    
    if ! [[ "$count" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 实例数必须是数字${NC}"
        exit 1
    fi
    
    # 检查模板文件是否存在
    if [ ! -f "$SERVICE_TEMPLATE" ]; then
        echo -e "${RED}错误: 服务模板文件 $SERVICE_TEMPLATE 不存在${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}开始创建 $count 个服务实例，从端口 $start_port 开始...${NC}"
    
    # 检查各端口是否可用
    local ports_conflict=0
    for ((i=0; i<count; i++)); do
        port=$((start_port + i))
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
        echo -e "  2. 使用不同的起始端口"
        read -p "是否继续创建服务? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}操作已取消${NC}"
            exit 1
        fi
    fi
    
    # 跳过主服务文件nkuwiki.service
    for ((i=0; i<count; i++)); do
        port=$((start_port + i))
        
        # 跳过端口8000的服务（已作为主服务)
        if [ "$port" -eq 8000 ]; then
            echo -e "${YELLOW}跳过端口 8000，已作为主服务${NC}"
            continue
        fi
        
        service_name="nkuwiki-$port.service"
        service_path="/etc/systemd/system/$service_name"
        
        # 创建服务文件
        cat > "$service_path" << EOF
[Unit]
Description=NKU Wiki API Service (Port $port)
After=network.target nginx.service mysql.service

[Service]
User=root
WorkingDirectory=/home/nkuwiki/nkuwiki-shell/nkuwiki
ExecStart=/opt/venvs/nkuwiki/bin/python3 app.py --api --port $port
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

# 移除PYTHONOPTIMIZE=1，可能导致不稳定
# Environment=PYTHONOPTIMIZE=1
Environment=PYTHONHASHSEED=random

# 资源限制 - 稳定性配置
CPUQuota=70%
MemoryLimit=4G
TasksMax=128
TimeoutStartSec=30
TimeoutStopSec=30

# OOM配置
OOMScoreAdjust=-500

# 日志设置
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        echo -e "${GREEN}创建服务文件: $service_path${NC}"
    done
    
    # 重新加载systemd配置
    systemctl daemon-reload
    echo -e "${GREEN}所有服务文件已创建并加载${NC}"
}

# 生成Nginx upstream配置
function generate_upstream_config {
    local start_port=$1
    local count=$2
    
    # 验证参数
    if ! [[ "$start_port" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 起始端口必须是数字${NC}"
        exit 1
    fi
    
    if ! [[ "$count" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 实例数必须是数字${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}生成Nginx upstream配置...${NC}"
    
    # 创建upstream配置
    cat > "$UPSTREAM_CONF" << EOF
# nkuwiki API服务负载均衡upstream配置
# 由nkuwiki_service_manager.sh自动生成
# 生成时间: $(date)

upstream nkuwiki_backend {
    # 负载均衡策略: least_conn (最少连接)
    least_conn;
    
    # 后端服务器列表
EOF
    
    for ((i=0; i<count; i++)); do
        port=$((start_port + i))
        echo "    server 127.0.0.1:$port;" >> "$UPSTREAM_CONF"
    done
    
    # 继续添加配置
    cat >> "$UPSTREAM_CONF" << 'EOF'
    
    # 长连接配置
    keepalive 32;
}
EOF
    
    echo -e "${GREEN}Nginx upstream配置已生成: $UPSTREAM_CONF${NC}"
}

# 生成Cloudflare IP配置
function generate_cloudflare_config {
    echo -e "${BLUE}生成Cloudflare IP范围配置...${NC}"
    
    cat > "$CLOUDFLARE_CONF" << 'EOF'
# Cloudflare IP ranges
# IPv4
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
set_real_ip_from 141.101.64.0/18;
set_real_ip_from 108.162.192.0/18;
set_real_ip_from 190.93.240.0/20;
set_real_ip_from 188.114.96.0/20;
set_real_ip_from 197.234.240.0/22;
set_real_ip_from 198.41.128.0/17;
set_real_ip_from 162.158.0.0/15;
set_real_ip_from 172.64.0.0/13;
set_real_ip_from 131.0.72.0/22;

# IPv6
set_real_ip_from 2400:cb00::/32;
set_real_ip_from 2606:4700::/32;
set_real_ip_from 2803:f800::/32;
set_real_ip_from 2405:b500::/32;
set_real_ip_from 2405:8100::/32;
set_real_ip_from 2a06:98c0::/29;
set_real_ip_from 2c0f:f248::/32;

# 从Cloudflare头部获取真实IP
real_ip_header CF-Connecting-IP;
EOF
    
    echo -e "${GREEN}Cloudflare IP范围配置已生成: $CLOUDFLARE_CONF${NC}"
}

# 生成HTTP配置
function generate_http_config {
    echo -e "${BLUE}生成HTTP配置...${NC}"
    
    cat > "$HTTP_CONF" << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name nkuwiki.com www.nkuwiki.com;

    # 记录访问日志
    access_log /var/log/nginx/nkuwiki.access.log;
    error_log /var/log/nginx/nkuwiki.error.log;

    # 包含Cloudflare IP范围配置
    include /etc/nginx/conf.d/cloudflare.conf;
    
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

    # 静态文件缓存设置 - 优化缓存配置
    location ~* \.(css|js)$ {
        proxy_pass http://nkuwiki_backend;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        proxy_pass http://nkuwiki_backend/static/;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /assets/ {
        proxy_pass http://nkuwiki_backend/assets/;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /img/ {
        proxy_pass http://nkuwiki_backend/img/;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    echo -e "${GREEN}HTTP配置已生成: $HTTP_CONF${NC}"
    
    # 创建符号链接启用配置
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki.conf" ]; then
        rm -f "$NGINX_SITES_ENABLED/nkuwiki.conf"
    fi
    ln -sf "$HTTP_CONF" "$NGINX_SITES_ENABLED/nkuwiki.conf"
    echo -e "${GREEN}HTTP配置已启用${NC}"
}

# 生成HTTPS配置
function generate_https_config {
    echo -e "${BLUE}生成HTTPS配置...${NC}"
    
    # 检查SSL证书是否存在
    if [ ! -f "$SSL_CERT_PATH" ] || [ ! -f "$SSL_KEY_PATH" ]; then
        echo -e "${YELLOW}警告: SSL证书文件不存在，请确保以下文件存在:${NC}"
        echo -e "  - 证书: $SSL_CERT_PATH"
        echo -e "  - 密钥: $SSL_KEY_PATH"
        echo -e "${YELLOW}HTTPS配置将继续生成，但可能无法正常工作，直到证书文件准备好${NC}"
    fi
    
    cat > "$HTTPS_CONF" << 'EOF'
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name nkuwiki.com www.nkuwiki.com;

    # SSL证书配置
    ssl_certificate /etc/ssl/certs/nkuwiki.com.pem;
    ssl_certificate_key /etc/ssl/private/nkuwiki.com.key;
    
    # SSL协议设置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 记录访问日志
    access_log /var/log/nginx/nkuwiki-ssl.access.log;
    error_log /var/log/nginx/nkuwiki-ssl.error.log;

    # 包含Cloudflare IP范围配置
    include /etc/nginx/conf.d/cloudflare.conf;
    
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://nkuwiki_backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
        proxy_read_timeout 5s;
    }

    # 静态文件缓存设置 - 优化缓存配置
    location ~* \.(css|js)$ {
        proxy_pass http://nkuwiki_backend;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        proxy_pass http://nkuwiki_backend/static/;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /assets/ {
        proxy_pass http://nkuwiki_backend/assets/;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /img/ {
        proxy_pass http://nkuwiki_backend/img/;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    echo -e "${GREEN}HTTPS配置已生成: $HTTPS_CONF${NC}"
    
    # 创建符号链接启用配置
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf" ]; then
        rm -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    fi
    ln -sf "$HTTPS_CONF" "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    echo -e "${GREEN}HTTPS配置已启用${NC}"
}

# 生成完整Nginx配置(包括upstream、HTTP和HTTPS)
function generate_nginx_config {
    local start_port=$1
    local count=$2
    
    # 确保必要的目录存在
    mkdir -p "$NGINX_SITES_ENABLED"
    
    # 生成upstream配置
    generate_upstream_config "$start_port" "$count"
    
    # 生成Cloudflare IP配置
    generate_cloudflare_config
    
    # 生成HTTP配置
    generate_http_config
    
    # 生成HTTPS配置
    generate_https_config
    
    # 验证Nginx配置
    echo -e "${BLUE}验证Nginx配置...${NC}"
    nginx -t
    
    echo -e "${YELLOW}要应用配置，请运行: systemctl reload nginx${NC}"
}

# 设置SSL配置
function setup_ssl {
    echo -e "${BLUE}设置SSL配置...${NC}"
    
    # 检查SSL证书是否存在
    if [ ! -f "$SSL_CERT_PATH" ] || [ ! -f "$SSL_KEY_PATH" ]; then
        echo -e "${YELLOW}SSL证书文件不存在，您需要手动准备以下文件:${NC}"
        echo -e "  - 证书: $SSL_CERT_PATH"
        echo -e "  - 密钥: $SSL_KEY_PATH"
        echo -e "${YELLOW}可以使用Let's Encrypt或其他提供商获取SSL证书${NC}"
        
        # 创建目录
        mkdir -p "$(dirname "$SSL_CERT_PATH")"
        mkdir -p "$(dirname "$SSL_KEY_PATH")"
        
        return 1
    else
        echo -e "${GREEN}SSL证书已就绪${NC}"
        return 0
    fi
}

# 获取所有nkuwiki服务
function get_all_services {
    # 使用ls命令列出所有匹配的服务文件，并提取服务名称
    ls /etc/systemd/system/nkuwiki*.service 2>/dev/null | xargs -n1 basename 2>/dev/null || echo ""
}

# 启动所有服务
function start_services {
    echo -e "${BLUE}启动所有nkuwiki服务实例...${NC}"
    
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

# 配置Nginx
function configure_nginx {
    local start_port=$1
    local count=$2
    
    # 验证参数
    if ! [[ "$start_port" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 起始端口必须是数字${NC}"
        exit 1
    fi
    
    if ! [[ "$count" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 实例数必须是数字${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}开始配置Nginx负载均衡...${NC}"
    
    # 1. 生成upstream配置
    generate_upstream_config "$start_port" "$count"
    
    # 2. 生成Cloudflare IP配置
    generate_cloudflare_config
    
    # 3. 生成HTTP配置
    generate_http_config
    
    # 4. 生成HTTPS配置
    generate_https_config
    
    echo -e "${GREEN}Nginx配置完成!${NC}"
    echo -e "${YELLOW}请使用 'nginx -t && systemctl reload nginx' 检查并应用配置${NC}"
}

# 一键部署
function deploy {
    local start_port=$1
    local count=$2
    
    # 设置默认值
    start_port=${start_port:-8000}
    count=${count:-8}
    
    echo -e "${BLUE}一键部署nkuwiki服务 (端口: $start_port, 实例数: $count)${NC}"
    
    # 1. 创建服务文件
    create_service "$start_port" "$count"
    
    # 2. 配置Nginx
    configure_nginx "$start_port" "$count"
    
    # 3. 重新加载Nginx配置
    echo -e "${BLUE}重新加载Nginx配置...${NC}"
    nginx -t && systemctl reload nginx
    if [ $? -ne 0 ]; then
        echo -e "${RED}Nginx配置测试失败，请检查配置${NC}"
        return 1
    fi
    
    # 4. 启动所有服务
    start_services
    
    # 5. 启用所有服务开机自启
    echo -e "${BLUE}设置所有服务开机自启...${NC}"
    systemctl enable nkuwiki.service
    
    for service in $(get_all_services); do
        # 跳过主服务，已在上面处理
        if [ "$service" = "nkuwiki.service" ]; then
            continue
        fi
        systemctl enable "$service"
    done
    
    # 6. 显示部署结果
    echo -e "${GREEN}部署完成!${NC}"
    status_services
}

# 停止所有服务
function stop_services {
    echo -e "${BLUE}停止所有nkuwiki服务...${NC}"
    for service in $(get_all_services); do
        echo -e "停止 $service..."
        systemctl stop $service
    done
    echo -e "${GREEN}所有服务已停止${NC}"
}

# 重启所有服务
function restart_services {
    echo -e "${BLUE}重启所有nkuwiki服务...${NC}"
    for service in $(get_all_services); do
        echo -e "重启 $service..."
        systemctl restart $service
    done
    echo -e "${GREEN}所有服务已重启${NC}"
}

# 显示所有服务状态
function status_services {
    echo -e "${BLUE}nkuwiki服务状态:${NC}"
    echo -e "${BLUE}-------------------------------------${NC}"
    
    # 检查主服务状态
    local main_status=$(systemctl is-active nkuwiki.service 2>/dev/null)
    if [ "$main_status" == "active" ]; then
        echo -e "${GREEN}主服务 nkuwiki.service: $main_status${NC}"
    else
        echo -e "${RED}主服务 nkuwiki.service: $main_status${NC}"
    fi
    
    # 检查其他服务状态
    local active_count=1  # 初始计数包括主服务
    local total_count=1
    
    # 直接列出所有端口服务
    for service_file in /etc/systemd/system/nkuwiki-*.service; do
        if [ -f "$service_file" ]; then
            service=$(basename "$service_file")
            total_count=$((total_count + 1))
            
            local status=$(systemctl is-active "$service" 2>/dev/null)
            if [ "$status" == "active" ]; then
                active_count=$((active_count + 1))
                echo -e "${GREEN}$service: $status${NC}"
            else
                echo -e "${RED}$service: $status${NC}"
            fi
        fi
    done
    
    # 显示摘要信息
    echo -e "${BLUE}-------------------------------------${NC}"
    echo -e "${YELLOW}活跃服务: $active_count / $total_count${NC}"
    
    # 显示进程信息
    echo -e "${BLUE}-------------------------------------${NC}"
    echo -e "${YELLOW}进程信息:${NC}"
    ps aux | grep -E "python3.*app.py.*--port" | grep -v grep
    
    # 显示端口监听情况 - 改进这部分以显示所有nkuwiki相关端口
    echo -e "${BLUE}-------------------------------------${NC}"
    echo -e "${YELLOW}端口监听情况:${NC}"
    # 收集所有可能的端口号
    local ports=$(grep -oE "port [0-9]+" /etc/systemd/system/nkuwiki*.service 2>/dev/null | awk '{print $2}' | sort -n | uniq | tr '\n' '|')
    if [ -n "$ports" ]; then
        ports=${ports%|}  # 移除最后一个|
        # 使用收集到的所有端口号构建grep模式
        netstat -tulnp | grep -E ":(${ports})" | sort -n -k 4
    else
        # 如果无法从服务文件中获取端口，则使用默认范围
        netstat -tulnp | grep -E ":(8000|8001|8002|8003|8004|8005|8006|8007|8008|8009)" | sort -n -k 4
    fi
    
    # 显示Nginx状态
    echo -e "${BLUE}-------------------------------------${NC}"
    echo -e "${YELLOW}Nginx状态:${NC}"
    systemctl status nginx --no-pager | head -n 3
    nginx -T 2>/dev/null | grep -E "upstream|server.*8[0-9]{3}" | head -n 15
}

# 启用所有服务开机自启
function enable_services {
    echo -e "${BLUE}启用所有nkuwiki服务开机自启...${NC}"
    for service in $(get_all_services); do
        echo -e "启用 $service..."
        systemctl enable $service
    done
    echo -e "${GREEN}所有服务已启用开机自启${NC}"
}

# 禁用所有服务开机自启
function disable_services {
    echo -e "${BLUE}禁用所有nkuwiki服务开机自启...${NC}"
    for service in $(get_all_services); do
        echo -e "禁用 $service..."
        systemctl disable $service
    done
    echo -e "${GREEN}所有服务已禁用开机自启${NC}"
}

# 清理服务(除了主服务)
function cleanup_services {
    echo -e "${BLUE}清理所有nkuwiki服务(除主服务外)...${NC}"
    
    # 先停止服务
    for service in $(get_all_services | grep -v "^nkuwiki.service$"); do
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
    
    # 重新加载systemd配置
    systemctl daemon-reload
    echo -e "${GREEN}清理完成${NC}"
}

# 清理所有配置文件
function cleanup_config {
    echo -e "${BLUE}清理所有Nginx配置文件...${NC}"
    
    # 移除启用的配置链接
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki.conf" ]; then
        echo -e "删除 $NGINX_SITES_ENABLED/nkuwiki.conf..."
        rm -f "$NGINX_SITES_ENABLED/nkuwiki.conf"
    fi
    
    if [ -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf" ]; then
        echo -e "删除 $NGINX_SITES_ENABLED/nkuwiki-ssl.conf..."
        rm -f "$NGINX_SITES_ENABLED/nkuwiki-ssl.conf"
    fi
    
    # 移除配置文件
    if [ -f "$HTTP_CONF" ]; then
        echo -e "删除 $HTTP_CONF..."
        rm -f "$HTTP_CONF"
    fi
    
    if [ -f "$HTTPS_CONF" ]; then
        echo -e "删除 $HTTPS_CONF..."
        rm -f "$HTTPS_CONF"
    fi
    
    if [ -f "$UPSTREAM_CONF" ]; then
        echo -e "删除 $UPSTREAM_CONF..."
        rm -f "$UPSTREAM_CONF"
    fi
    
    if [ -f "$CLOUDFLARE_CONF" ]; then
        echo -e "删除 $CLOUDFLARE_CONF..."
        rm -f "$CLOUDFLARE_CONF"
    fi
    
    # 重启Nginx应用更改
    echo -e "${BLUE}重启Nginx应用配置修改...${NC}"
    nginx -t && systemctl restart nginx
    
    echo -e "${GREEN}所有配置文件已清理${NC}"
}

# 主函数
function main {
    check_root
    
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    case "$1" in
        create)
            if [ $# -lt 3 ]; then
                echo -e "${RED}错误: create命令需要起始端口和实例数参数${NC}"
                show_help
                exit 1
            fi
            create_service $2 $3
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            status_services
            ;;
        enable)
            enable_services
            ;;
        disable)
            disable_services
            ;;
        nginx)
            if [ $# -lt 3 ]; then
                echo -e "${RED}错误: nginx命令需要起始端口和实例数参数${NC}"
                show_help
                exit 1
            fi
            generate_nginx_config $2 $3
            ;;
        cloudflare)
            generate_cloudflare_config
            ;;
        setup-ssl)
            setup_ssl
            ;;
        deploy)
            if [ $# -lt 3 ]; then
                echo -e "${RED}错误: deploy命令需要起始端口和实例数参数${NC}"
                show_help
                exit 1
            fi
            deploy $2 $3
            ;;
        cleanup)
            cleanup_services
            ;;
        cleanup-config)
            cleanup_config
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