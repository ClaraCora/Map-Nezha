#!/bin/bash

# Nezha API Service 安装脚本
# 使用方法: sudo ./install-service.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        print_message "请使用: sudo $0"
        exit 1
    fi
}

# 获取当前用户信息
get_user_info() {
    print_step "获取用户信息..."
    
    # 获取当前目录
    CURRENT_DIR=$(pwd)
    print_message "当前目录: $CURRENT_DIR"
    
    # 获取当前用户
    CURRENT_USER=$(who am i | awk '{print $1}')
    if [[ -z "$CURRENT_USER" ]]; then
        CURRENT_USER=$(logname)
    fi
    print_message "当前用户: $CURRENT_USER"
    
    # 检查虚拟环境是否存在
    if [[ ! -d "$CURRENT_DIR/venv" ]]; then
        print_warning "虚拟环境不存在，请先运行 deploy.sh"
        exit 1
    fi
    
    # 检查app.py是否存在
    if [[ ! -f "$CURRENT_DIR/app.py" ]]; then
        print_error "app.py 文件不存在"
        exit 1
    fi
}

# 配置服务文件
configure_service() {
    print_step "配置服务文件..."
    
    # 创建临时服务文件
    TEMP_SERVICE="/tmp/nezha-api.service"
    
    cat > "$TEMP_SERVICE" << EOF
[Unit]
Description=Nezha API Python Service
Documentation=https://github.com/your-repo/nezha-api
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER

# 工作目录和可执行文件路径
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/app.py
ExecReload=/bin/kill -HUP \$MAINPID

# 环境变量（可选，如果使用.env文件则不需要）
# Environment=NEZHA_DASHBOARD_URL=https://your-panel.com
# Environment=NEZHA_USERNAME=your_username
# Environment=NEZHA_PASSWORD=your_password

# 重启策略
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$CURRENT_DIR/logs

# 日志设置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nezha-api

# 超时设置
TimeoutStartSec=30
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF
    
    print_message "服务文件已生成: $TEMP_SERVICE"
}

# 安装服务
install_service() {
    print_step "安装服务..."
    
    # 复制服务文件到系统目录
    cp "$TEMP_SERVICE" /etc/systemd/system/nezha-api.service
    
    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable nezha-api.service
    
    print_message "服务已安装并启用"
}

# 启动服务
start_service() {
    print_step "启动服务..."
    
    # 启动服务
    systemctl start nezha-api.service
    
    # 检查服务状态
    if systemctl is-active --quiet nezha-api.service; then
        print_message "服务启动成功"
    else
        print_error "服务启动失败"
        systemctl status nezha-api.service
        exit 1
    fi
}

# 显示服务信息
show_service_info() {
    print_step "服务信息:"
    echo ""
    echo "服务名称: nezha-api"
    echo "配置文件: /etc/systemd/system/nezha-api.service"
    echo "工作目录: $CURRENT_DIR"
    echo "用户: $CURRENT_USER"
    echo ""
    echo "常用命令:"
    echo "  查看状态: sudo systemctl status nezha-api"
    echo "  启动服务: sudo systemctl start nezha-api"
    echo "  停止服务: sudo systemctl stop nezha-api"
    echo "  重启服务: sudo systemctl restart nezha-api"
    echo "  查看日志: sudo journalctl -u nezha-api -f"
    echo ""
}

# 主函数
main() {
    echo "=========================================="
    echo "    Nezha API Service 安装脚本"
    echo "=========================================="
    echo ""
    
    check_root
    get_user_info
    configure_service
    install_service
    start_service
    show_service_info
    
    print_message "安装完成！"
    print_message "服务将在系统启动时自动运行"
}

# 运行主函数
main "$@" 