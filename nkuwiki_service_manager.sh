#!/bin/bash
# nkuwiki_service_manager.sh - 管理nkuwiki的main和dev分支服务
# 版本: 2.1.0 (简化版)
# 用法: ./nkuwiki_service_manager.sh [命令] [分支]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# --- 配置 ---
# 注意：此脚本应该位于项目根目录中
# (例如 /home/nkuwiki/nkuwiki-shell/nkuwiki/ 或者 /home/nkuwiki/nkuwiki-shell/nkuwiki-dev/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 主 Nginx 配置文件模板的路径
NGINX_CONF_TEMPLATE="${SCRIPT_DIR}/nkuwiki.nginx.conf"
NGINX_SSL_CONF_TEMPLATE="${SCRIPT_DIR}/nkuwiki-ssl.nginx.conf"

# Nginx 最终配置文件的路径
NGINX_CONF_FINAL="/etc/nginx/sites-available/nkuwiki.conf"
NGINX_SSL_CONF_FINAL="/etc/nginx/sites-available/nkuwiki-ssl.conf"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"

# 根据分支设置变量
function set_branch_variables {
    BRANCH=$1
    if [ "$BRANCH" == "main" ]; then
        API_PORT=8000
        COMPOSE_PROJECT_NAME="nkuwiki_main"
    elif [ "$BRANCH" == "dev" ]; then
        API_PORT=8001
        COMPOSE_PROJECT_NAME="nkuwiki_dev"
    else
        echo -e "${RED}错误: 无效的分支 '$BRANCH'. 请使用 'main' 或 'dev'.${NC}"
        exit 1
    fi
}

function show_help {
    echo -e "${BLUE}NKUWiki 服务管理脚本 (main & dev) - v2.1.0${NC}"
    echo -e "${YELLOW}功能:${NC} 使用 Docker Compose 管理 nkuwiki 的 main 和 dev 分支服务"
    echo ""
    echo -e "${BLUE}用法:${NC} $0 [命令] [分支]"
    echo ""
    echo -e "${GREEN}== 服务命令 (需要指定分支) ==${NC}"
    echo -e "  ${YELLOW}start [main|dev]${NC}     - 构建并启动指定分支的服务"
    echo -e "  ${YELLOW}stop [main|dev]${NC}      - 停止指定分支的服务"
    echo -e "  ${YELLOW}restart [main|dev]${NC}   - 重启指定分支的服务"
    echo -e "  ${YELLOW}status [main|dev]${NC}    - 查看指定分支的容器状态"
    echo -e "  ${YELLOW}logs [main|dev]${NC}      - 查看指定分支的应用日志"
    echo -e "  ${YELLOW}update-nginx${NC}       - 更新并重载Nginx配置 (通常在start时自动完成)"
    echo ""
    echo -e "${GREEN}== Systemd 服务管理 (需要root权限) ==${NC}"
    echo -e "  ${YELLOW}install-service [main|dev]${NC} - 为指定分支安装并启用 systemd 服务"
    echo -e "  ${YELLOW}uninstall-service [main|dev]${NC}- 卸载指定分支的 systemd 服务"
    echo -e "  ${YELLOW}cleanup-services${NC}           - 清理已卸载的服务模板"
    echo ""
    echo -e "${GREEN}== 基础设施命令 (共享) ==${NC}"
    echo -e "  ${YELLOW}start-infra${NC}        - 启动共享的基础设施服务 (mysql, redis, etc.)"
    echo -e "  ${YELLOW}stop-infra${NC}         - 停止共享的基础设施服务"
    echo -e "  ${YELLOW}status-infra${NC}       - 查看基础设施服务状态"
    echo -e "  ${YELLOW}logs-infra [service]${NC}- 查看指定基础设施服务日志 (可选)"
    echo ""
    echo -e "${GREEN}== 使用示例 ==${NC}"
    echo -e "  $0 start-infra         - 首先，启动所有共享服务"
    echo -e "  $0 start main           - 然后，部署 main 分支的应用"
    echo -e "  $0 status dev            - 查看 dev 分支应用的状态"
}

function check_root {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}错误: 此脚本需要root权限${NC}"
        exit 1
    fi
}

function check_docker {
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        echo -e "${RED}错误: Docker 或 Docker Compose V2 未安装或不可用。${NC}"
        exit 1
    fi
}

function unproxy {
    echo -e "${BLUE}正在取消系统和代理设置...${NC}"
    unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY
    
    echo -e "${GREEN}代理环境变量已成功取消。${NC}"
}

# 为 Docker Compose 创建 .env 文件
function create_dotenv_file {
    echo -e "${BLUE}在 $SCRIPT_DIR 为分支 '$BRANCH' 创建 .env 文件...${NC}"
    
    > "${SCRIPT_DIR}/.env"

    cat >> "${SCRIPT_DIR}/.env" << EOF
# --- Docker Compose Environment Variables ---

# Branch-specific settings
BRANCH=${BRANCH}
API_PORT=${API_PORT}

# Database credentials (from config.json)
MYSQL_DATABASE=nkuwiki
MYSQL_USER=nkuwiki
MYSQL_ROOT_PASSWORD=Nkuwiki0!
MYSQL_PASSWORD=Nkuwiki0!
EOF
    echo -e "${GREEN}.env 文件已创建/更新。${NC}"
}

function update_nginx {
    echo -e "${BLUE}更新Nginx配置...${NC}"
    if [ ! -f "$NGINX_CONF_TEMPLATE" ] || [ ! -f "$NGINX_SSL_CONF_TEMPLATE" ]; then
        echo -e "${RED}错误: Nginx模板文件未找到。请确保 nkuwiki.nginx.conf 和 nkuwiki-ssl.nginx.conf 都存在。${NC}"
        exit 1
    fi
    
    # 复制 HTTP 和 HTTPS 配置文件
    echo -e "${BLUE}复制 HTTP 和 HTTPS 的Nginx配置文件...${NC}"
    cp "$NGINX_CONF_TEMPLATE" "$NGINX_CONF_FINAL"
    cp "$NGINX_SSL_CONF_TEMPLATE" "$NGINX_SSL_CONF_FINAL"
    
    # 启用两个配置文件
    echo -e "${BLUE}在 sites-enabled 中创建软链接...${NC}"
    ln -sf "$NGINX_CONF_FINAL" "${NGINX_SITES_ENABLED}/nkuwiki.conf"
    ln -sf "$NGINX_SSL_CONF_FINAL" "${NGINX_SITES_ENABLED}/nkuwiki-ssl.conf"
    
    # 测试并重载 Nginx
    echo -e "${BLUE}测试并重载Nginx配置...${NC}"
    if nginx -t; then
        systemctl reload nginx
        echo -e "${GREEN}Nginx配置已成功更新并重载!${NC}"
    else
        echo -e "${RED}Nginx配置测试失败。请检查 $NGINX_CONF_FINAL 文件。${NC}"
        exit 1
    fi
}

function start_service {
    echo -e "${GREEN}== 启动分支 '$BRANCH' ==${NC}"

    # 直接调用脚本内部定义的 unproxy 函数
    unproxy

    cd "$SCRIPT_DIR"
    
    # 1. 创建 .env 文件
    create_dotenv_file

    # 2. 构建并启动 Docker Compose 服务
    echo -e "${BLUE}使用 Docker Compose 构建和启动服务...${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" up -d --build --remove-orphans api
    
    # 3. 确保 Nginx 配置是最新的
    update_nginx
    
    # 4. 自动安装/更新 systemd 服务
    echo -e "${BLUE}正在安装/更新 systemd 服务...${NC}"
    install_service
    
    echo -e "${GREEN}分支 '$BRANCH' 部署完成! API 运行在端口 ${API_PORT}${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" ps
}

function stop_service {
    echo -e "${YELLOW}== 停止分支 '$BRANCH' ==${NC}"
    cd "$SCRIPT_DIR"
    docker compose -p "$COMPOSE_PROJECT_NAME" stop api
    echo -e "${GREEN}服务已停止.${NC}"
}

function restart_service {
    echo -e "${BLUE}== 重启分支 '$BRANCH' ==${NC}"
    cd "$SCRIPT_DIR"
    create_dotenv_file # 确保环境变量正确
    docker compose -p "$COMPOSE_PROJECT_NAME" restart api
    echo -e "${GREEN}服务已重启.${NC}"
    docker compose -p "$COMPOSE_PROJECT_NAME" ps
}

function get_status {
    echo -e "${BLUE}== 查看分支 '$BRANCH' 状态 ==${NC}"
    cd "$SCRIPT_DIR"
    docker compose -p "$COMPOSE_PROJECT_NAME" ps api
}

function get_logs {
    echo -e "${BLUE}== 查看分支 '$BRANCH' 日志 ==${NC}"
    cd "$SCRIPT_DIR"
    docker compose -p "$COMPOSE_PROJECT_NAME" logs -f --tail=100 api
}


# --- Systemd Service Management ---
function install_service {
    SERVICE_INSTANCE="nkuwiki@${BRANCH}.service"
    SERVICE_TEMPLATE_FILE="/etc/systemd/system/nkuwiki@.service"

    echo -e "${GREEN}== 为分支 '$BRANCH' 安装 systemd 服务 ==${NC}"

    # 1. 创建服务模板文件
    echo -e "${BLUE}在 ${SERVICE_TEMPLATE_FILE} 创建 systemd 服务模板...${NC}"
    cat > "${SERVICE_TEMPLATE_FILE}" << EOF
[Unit]
Description=NKUWiki Service (%i branch)
Documentation=https://github.com/NKU-Wiki/NKU-Wiki-Shell
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/nkuwiki_service_manager.sh start %i
ExecStop=${SCRIPT_DIR}/nkuwiki_service_manager.sh stop %i
# Docker-compose 自行处理容器重启，因此禁用 systemd 的重启

[Install]
WantedBy=multi-user.target
EOF

    # 2. 重载 systemd
    echo -e "${BLUE}重载 systemd daemon...${NC}"
    systemctl daemon-reload

    # 3. 启用特定实例
    echo -e "${BLUE}启用服务实例 ${SERVICE_INSTANCE}...${NC}"
    systemctl enable "${SERVICE_INSTANCE}"

    echo -e "${GREEN}服务 ${SERVICE_INSTANCE} 已成功安装.${NC}"
    echo -e "${YELLOW}服务已启用，将随系统启动。如需手动管理，请使用 'systemctl [start|stop|status] ${SERVICE_INSTANCE}'${NC}"
}

function uninstall_service {
    SERVICE_INSTANCE="nkuwiki@${BRANCH}.service"
    
    echo -e "${RED}== 卸载分支 '$BRANCH' 的 systemd 服务 ==${NC}"

    # 1. 停止并禁用实例
    echo -e "${BLUE}正在停止并禁用 ${SERVICE_INSTANCE}...${NC}"
    if systemctl is-active --quiet "${SERVICE_INSTANCE}"; then
        systemctl stop "${SERVICE_INSTANCE}"
    fi
    if systemctl is-enabled --quiet "${SERVICE_INSTANCE}"; then
        systemctl disable "${SERVICE_INSTANCE}"
    fi

    echo -e "${GREEN}服务实例 ${SERVICE_INSTANCE} 已停止并禁用.${NC}"
    echo -e "${YELLOW}服务模板文件 (/etc/systemd/system/nkuwiki@.service) 仍保留以备其他分支使用.${NC}"
    echo -e "${YELLOW}在卸载所有分支的服务后，可运行 'cleanup-services' 来移除它.${NC}"
    
    # 2. 重载 systemd
    systemctl daemon-reload
}

function cleanup_services {
    SERVICE_TEMPLATE_FILE="/etc/systemd/system/nkuwiki@.service"
    if [ -f "${SERVICE_TEMPLATE_FILE}" ]; then
        echo -e "${RED}正在清理服务模板 ${SERVICE_TEMPLATE_FILE}...${NC}"
        # 检查是否仍有已启用的 nkuwiki 服务实例
        if systemctl list-unit-files | grep -q "nkuwiki@.*\.service.*enabled"; then
            echo -e "${RED}错误: 存在一个或多个已启用的 nkuwiki 服务。请先将其卸载.${NC}"
            systemctl list-unit-files | grep "nkuwiki@.*\.service"
            exit 1
        fi
        rm -f "${SERVICE_TEMPLATE_FILE}"
        systemctl daemon-reload
        echo -e "${GREEN}服务模板已移除.${NC}"
    else
        echo -e "${YELLOW}未找到服务模板，无需清理.${NC}"
    fi
}


# --- 基础设施命令 ---
function start_infra {
    echo -e "${BLUE}启动共享基础设施服务...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.infra.yml" up -d
    echo -e "${GREEN}基础设施服务已启动。${NC}"
}

function stop_infra {
    echo -e "${YELLOW}停止共享基础设施服务...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.infra.yml" down
    echo -e "${GREEN}基础设施服务已停止。${NC}"
}

function status_infra {
    echo -e "${BLUE}查看共享基础设施状态...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.infra.yml" ps
}

function logs_infra {
    echo -e "${BLUE}查看基础设施日志...${NC}"
    if [ -z "$1" ]; then
        docker compose -f "${SCRIPT_DIR}/docker-compose.infra.yml" logs -f --tail=100
    else
        docker compose -f "${SCRIPT_DIR}/docker-compose.infra.yml" logs -f --tail=100 "$1"
    fi
}


# --- 主函数 ---
function main {
    check_root
    check_docker

    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    COMMAND=$1
    shift
    
    # 基础设施或全局命令
    case "$COMMAND" in
        help) show_help; exit 0 ;;
        update-nginx) update_nginx; exit 0 ;;
        start-infra) start_infra; exit 0 ;;
        stop-infra) stop_infra; exit 0 ;;
        status-infra) status_infra; exit 0 ;;
        logs-infra) logs_infra "$@"; exit 0 ;;
        cleanup-services) cleanup_services; exit 0 ;;
    esac

    # 需要分支的应用命令
    if [ -z "$1" ]; then
        echo -e "${RED}错误: 此命令需要指定分支 (main 或 dev).${NC}"
        show_help
        exit 1
    fi
    
    set_branch_variables "$1"
    shift

    case "$COMMAND" in
        start) start_service ;;
        stop) stop_service ;;
        restart) restart_service ;;
        status) get_status ;;
        logs) get_logs ;;
        install-service) install_service ;;
        uninstall-service) uninstall_service ;;
        *)
            echo -e "${RED}错误: 未知命令 '$COMMAND'${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@" 