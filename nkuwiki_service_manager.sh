#!/bin/bash
# nkuwiki_service_manager.sh - 管理nkuwiki的main和dev分支服务
# 用法: ./nkuwiki_service_manager.sh [命令] [分支] [参数]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 常量
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
PROJECT_ROOT_MAIN="/home/nkuwiki/nkuwiki-shell/nkuwiki"
PROJECT_ROOT_DEV="/home/nkuwiki/nkuwiki-shell/nkuwiki-dev"
MIHOMO_SERVICE="mihomo.service"
MIHOMO_CONFIG_DIR="/etc/mihomo"
MIHOMO_API_PORT="9090"
ENABLE_PROXY=0

# 根据分支设置变量
function set_branch_variables {
    BRANCH=$1
    if [ "$BRANCH" == "main" ]; then
        PROJECT_ROOT=$PROJECT_ROOT_MAIN
        API_PORT=8000
        COMPOSE_PROJECT_NAME="nkuwiki_main"
    elif [ "$BRANCH" == "dev" ]; then
        PROJECT_ROOT=$PROJECT_ROOT_DEV
        API_PORT=8001
        COMPOSE_PROJECT_NAME="nkuwiki_dev"
    else
        echo -e "${RED}错误: 无效的分支 '$BRANCH'. 请使用 'main' 或 'dev'.${NC}"
        exit 1
    fi
    NGINX_CONF="${NGINX_CONF_DIR}/nkuwiki-${BRANCH}-locations.conf"
}

function show_help {
    echo -e "${BLUE}NKUWiki 服务管理脚本 (main & dev)${NC}"
    echo -e "${YELLOW}功能:${NC} 使用 Docker Compose 管理 nkuwiki 的 main 和 dev 分支服务"
    echo -e "${YELLOW}版本:${NC} 2.0.0"
    echo ""
    echo -e "${BLUE}用法:${NC} $0 [命令] [分支] [参数]"
    echo ""
    echo -e "${GREEN}== 服务命令 (需要指定分支) ==${NC}"
    echo -e "  ${YELLOW}deploy [main|dev]${NC}            - 部署指定分支的应用服务"
    echo -e "  ${YELLOW}start [main|dev]${NC}             - 启动指定分支的应用服务"
    echo -e "  ${YELLOW}stop [main|dev]${NC}              - 停止指定分支的应用服务"
    echo -e "  ${YELLOW}restart [main|dev]${NC}           - 重启指定分支的应用服务"
    echo -e "  ${YELLOW}status [main|dev]${NC}            - 查看指定分支的应用容器状态"
    echo -e "  ${YELLOW}logs [main|dev]${NC}              - 查看指定分支的应用日志"
    echo -e "  ${YELLOW}cleanup [main|dev]${NC}           - 清理指定分支的应用服务 (Nginx配置和Docker容器)"
    echo ""
    echo -e "${GREEN}== 基础设施命令 (共享) ==${NC}"
    echo -e "  ${YELLOW}start-infra${NC}                - 启动共享的基础设施服务 (mysql, redis, etc.)"
    echo -e "  ${YELLOW}stop-infra${NC}                 - 停止共享的基础设施服务"
    echo -e "  ${YELLOW}status-infra${NC}               - 查看基础设施服务状态"
    echo -e "  ${YELLOW}logs-infra [service]${NC}        - 查看指定基础设施服务日志 (可选)"
    echo ""
    echo -e "${GREEN}== 全局命令 (无需指定分支) ==${NC}"
    echo -e "  ${YELLOW}proxy-status${NC}               - 检查Mihomo代理状态"
    echo -e "  ${YELLOW}restart-mihomo${NC}             - 重启Mihomo代理服务"
    echo -e "  ${YELLOW}help${NC}                       - 显示此帮助信息"
    echo ""
    echo -e "${GREEN}== 参数 ==${NC}"
    echo -e "  ${YELLOW}--proxy${NC}                    - 为容器启用代理 (适用于 deploy/start/restart)"
    echo ""
    echo -e "${GREEN}== 使用示例 ==${NC}"
    echo -e "  $0 start-infra               - 首先，启动所有共享服务"
    echo -e "  $0 deploy main                 - 然后，部署 main 分支的应用"
    echo -e "  $0 status-infra              - 查看共享服务的状态"
    echo -e "  $0 status dev                  - 查看 dev 分支应用的状态"
    echo -e "  $0 stop-infra                - 停止所有共享服务"
}

function check_root {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}错误: 此脚本需要root权限${NC}"
        exit 1
    fi
}

function check_docker {
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        echo -e "${RED}错误: Docker 或 Docker Compose V2 未安装或不可用。请先安装/配置它们。${NC}"
        exit 1
    fi
}

# 为 Docker Compose 创建 .env 文件
function create_dotenv_file {
    cd "$PROJECT_ROOT"
    echo -e "${BLUE}在 $PROJECT_ROOT 为分支 '$BRANCH' 创建 .env 文件...${NC}"
    
    # 移除旧的环境变量设置，如果存在
    if grep -q "http_proxy" .env 2>/dev/null; then
        sed -i '/http_proxy/d' .env
        sed -i '/https_proxy/d' .env
        sed -i '/all_proxy/d' .env
        sed -i '/no_proxy/d' .env
    fi

    # 根据代理设置写入新的环境变量
    if [ $ENABLE_PROXY -eq 1 ]; then
        echo -e "${YELLOW}为容器启用代理...${NC}"
        cat >> .env << EOF
http_proxy=http://172.17.0.1:7890
https_proxy=http://172.17.0.1:7890
all_proxy=socks5://172.17.0.1:7890
no_proxy=localhost,127.0.0.1,nkuwiki-mysql,nkuwiki-redis,nkuwiki-qdrant
EOF
    else
        echo -e "${GREEN}容器不使用代理。${NC}"
        # 如果需要，可以写入空的代理变量
    fi
}

function generate_nginx_config {
    echo -e "${BLUE}为分支 '$BRANCH' 生成Nginx配置...${NC}"
    mkdir -p "$NGINX_CONF_DIR"
    mkdir -p "$NGINX_SITES_ENABLED"
    
    # 定义 Nginx location 块的内容
    # 注意：main 分支作为默认服务，dev 分支使用 /dev/ 路径前缀
    if [ "$BRANCH" == "main" ]; then
        PROXY_PATH="/"
        SERVER_NAME="nkuwiki.com www.nkuwiki.com"
        LISTEN_PORT="80"
    else
        PROXY_PATH="/dev/"
        # dev 分支不需要 server_name，它将通过 include 被主配置文件引用
        SERVER_NAME="_"
        LISTEN_PORT="" # 不监听，将被 include
    fi

    cat > "$NGINX_CONF" << EOF
location ${PROXY_PATH} {
    proxy_pass http://127.0.0.1:${API_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_read_timeout 300s;
    
    # 如果是 dev 分支，重写路径
    if (\$request_uri ~* "^/dev/(.*)\$") {
        rewrite ^/dev/(.*) /\$1 break;
    }
}
EOF

    echo -e "${GREEN}Nginx location 块已生成: $NGINX_CONF${NC}"
}

# 创建主 Nginx 配置文件，并包含分支的 location 配置
function create_main_nginx_config {
    echo -e "${BLUE}创建或更新主 Nginx 配置文件...${NC}"
    MAIN_NGINX_CONF="${NGINX_CONF_DIR}/nkuwiki.conf"
    
    cat > "$MAIN_NGINX_CONF" << EOF
server {
    listen 80;
    listen [::]:80;
    server_name nkuwiki.com www.nkuwiki.com;

    access_log /var/log/nginx/nkuwiki.access.log;
    error_log /var/log/nginx/nkuwiki.error.log;
    
    charset utf-8;
    
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";

    # 包含 main 分支的 location 配置 (/)
    include ${NGINX_CONF_DIR}/nkuwiki-main-locations.conf;

    # 包含 dev 分支的 location 配置 (/dev/)
    include ${NGINX_CONF_DIR}/nkuwiki-dev-locations.conf;

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
        access_log off;
    }

    # SSL 证书申请路径
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
EOF
    # 启用主配置文件
    ln -sf "$MAIN_NGINX_CONF" "${NGINX_SITES_ENABLED}/nkuwiki.conf"
    echo -e "${GREEN}主 Nginx 配置文件已创建并启用: ${NGINX_SITES_ENABLED}/nkuwiki.conf${NC}"
}

function deploy_service {
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}在 $PROJECT_ROOT 部署分支 '$BRANCH'...${NC}"
    
    # 确保在部署前清理环境，防止冲突
    echo -e "${YELLOW}正在停止并移除 '$BRANCH' 分支的旧应用容器...${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" stop api_${BRANCH} && docker compose -p "$COMPOSE_PROJECT_NAME" rm -f api_${BRANCH}
    
    # 1. 生成 Nginx 配置
    generate_nginx_config
    
    # 2. 总是更新主 Nginx 文件以确保 include 是正确的
    create_main_nginx_config

    # 3. 为 Docker Compose 创建 .env 文件
    create_dotenv_file

    # 4. 构建并启动 Docker Compose 服务
    echo -e "${BLUE}使用 Docker Compose 构建和启动应用服务...${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" up -d --build api_${BRANCH}
    
    # 5. 重启 Nginx
    echo -e "${BLUE}重启Nginx以应用配置...${NC}"
    systemctl restart nginx
    
    echo -e "${GREEN}分支 '$BRANCH' 部署完成! API 运行在端口 ${API_PORT}${NC}"
}

function start_service {
    cd "$PROJECT_ROOT"
    echo -e "${BLUE}启动 '$BRANCH' 分支的应用服务...${NC}"
    create_dotenv_file # 确保代理设置正确
    docker compose -p "$COMPOSE_PROJECT_NAME" up -d api_${BRANCH}
    echo -e "${GREEN}服务已启动.${NC}"
}

function stop_service {
    cd "$PROJECT_ROOT"
    echo -e "${YELLOW}停止 '$BRANCH' 分支的应用服务...${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" stop api_${BRANCH}
    echo -e "${GREEN}服务已停止.${NC}"
}

function restart_service {
    cd "$PROJECT_ROOT"
    echo -e "${BLUE}重启 '$BRANCH' 分支的应用服务...${NC}"
    create_dotenv_file # 确保代理设置正确
    docker compose -p "$COMPOSE_PROJECT_NAME" restart api_${BRANCH}
    echo -e "${GREEN}服务已重启.${NC}"
}

function get_status {
    cd "$PROJECT_ROOT"
    echo -e "${BLUE}查看 '$BRANCH' 分支的 Docker 状态...${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" ps api_${BRANCH}
}

function get_logs {
    cd "$PROJECT_ROOT"
    echo -e "${BLUE}查看 '$BRANCH' 分支的日志...${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" logs -f --tail=100 api_${BRANCH}
}

function cleanup_service {
    cd "$PROJECT_ROOT"
    echo -e "${RED}开始清理 '$BRANCH' 分支...${NC}"
    
    # 1. 停止并移除 Docker 容器
    echo -e "${YELLOW}停止并删除 Docker 应用容器...${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" stop api_${BRANCH} && docker compose -p "$COMPOSE_PROJECT_NAME" rm -f api_${BRANCH}
    
    # 2. 删除 Nginx 配置文件
    if [ -f "$NGINX_CONF" ]; then
        echo -e "${YELLOW}删除 Nginx 配置文件: $NGINX_CONF${NC}"
        rm -f "$NGINX_CONF"
    fi
    
    # 3. 检查是否需要移除主配置文件
    if [ ! -f "${NGINX_CONF_DIR}/nkuwiki-main-locations.conf" ] && [ ! -f "${NGINX_CONF_DIR}/nkuwiki-dev-locations.conf" ]; then
        echo -e "${YELLOW}两个分支都已清理，删除主 Nginx 配置文件和链接...${NC}"
        rm -f "${NGINX_CONF_DIR}/nkuwiki-main-locations.conf"
        rm -f "${NGINX_CONF_DIR}/nkuwiki-dev-locations.conf"
        rm -f "${NGINX_SITES_ENABLED}/nkuwiki.conf"
    else
        echo -e "${BLUE}另一个分支的配置仍然存在，保留主 Nginx 配置文件。${NC}"
    fi

    # 4. 重启 Nginx
    systemctl restart nginx
    
    echo -e "${GREEN}分支 '$BRANCH' 清理完成!${NC}"
}

function proxy_status {
    echo -e "${BLUE}检查Mihomo代理状态...${NC}"
    if curl -s -x http://127.0.0.1:7890 "https://www.google.com" -o /dev/null --head --max-time 5; then
        echo -e "${GREEN}代理工作正常 (通过google.com测试)${NC}"
        return 0
    else
        echo -e "${RED}代理无法连接到google.com${NC}"
        return 1
    fi
}

function start_infra {
    echo -e "${BLUE}启动共享基础设施服务...${NC}"
    docker compose -f docker-compose.infra.yml up -d
    echo -e "${GREEN}基础设施服务已启动。${NC}"
}

function stop_infra {
    echo -e "${YELLOW}停止共享基础设施服务...${NC}"
    docker compose -f docker-compose.infra.yml down
    echo -e "${GREEN}基础设施服务已停止。${NC}"
}

function status_infra {
    echo -e "${BLUE}查看共享基础设施状态...${NC}"
    docker compose -f docker-compose.infra.yml ps
}

function logs_infra {
    echo -e "${BLUE}查看基础设施日志...${NC}"
    if [ -z "$1" ]; then
        docker compose -f docker-compose.infra.yml logs -f --tail=100
    else
        docker compose -f docker-compose.infra.yml logs -f --tail=100 "$1"
    fi
}

function main {
    check_root
    check_docker

    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    COMMAND=$1
    shift

    # 解析代理参数
    if [[ " $@ " =~ " --proxy " ]]; then
                ENABLE_PROXY=1
        # 从参数列表中移除 --proxy
        set -- "${@/--proxy/}"
    fi
    
    # 全局/基础设施命令
    case "$COMMAND" in
        help)
            show_help
            ;;
        proxy-status)
            proxy_status
            ;;
        restart-mihomo)
            restart_mihomo
            ;;
        start-infra)
            start_infra
            ;;
        stop-infra)
            stop_infra
            ;;
        status-infra)
            status_infra
            ;;
        logs-infra)
            shift # 移除 logs-infra 命令
            logs_infra "$@"
            ;;
        *)
            # 需要分支的应用命令
            if [ -z "$1" ]; then
                echo -e "${RED}错误: 此命令需要指定分支 (main 或 dev).${NC}"
                show_help
                exit 1
            fi
            
            set_branch_variables "$1"
        shift

            case "$COMMAND" in
        deploy)
                    deploy_service
            ;;
        start)
            start_service
            ;;
                stop)
                    stop_service
                    ;;
        restart)
            restart_service
            ;;
        status)
                    get_status
                    ;;
                logs)
                    get_logs
            ;;
        cleanup)
            cleanup_service
            ;;
                *)
                    echo -e "${RED}错误: 未知命令 '$COMMAND'${NC}"
            show_help
            exit 1
                    ;;
            esac
            ;;
    esac
}

main "$@" 