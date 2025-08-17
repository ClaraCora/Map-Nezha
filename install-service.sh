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

# 全局变量
TEMP_SERVICE=""
CURRENT_DIR=""
CURRENT_USER=""

# 清理函数
cleanup() {
    if [[ -n "$TEMP_SERVICE" && -f "$TEMP_SERVICE" ]]; then
        rm -f "$TEMP_SERVICE"
        print_message "已清理临时文件: $TEMP_SERVICE"
    fi
}

# 错误处理
error_handler() {
    local exit_code=$?
    print_error "脚本执行失败 (退出码: $exit_code)"
    cleanup
    exit $exit_code
}

# 设置错误处理
trap error_handler ERR
trap cleanup EXIT

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

# 验证虚拟环境和依赖
verify_environment() {
    print_step "验证虚拟环境..."
    
    # 检查虚拟环境中的Python
    if [[ ! -f "$CURRENT_DIR/venv/bin/python" ]]; then
        print_error "虚拟环境中找不到Python解释器"
        exit 1
    fi
    
    # 检查虚拟环境中的pip
    if [[ ! -f "$CURRENT_DIR/venv/bin/pip" ]]; then
        print_error "虚拟环境中找不到pip"
        exit 1
    fi
    
    # 检查关键依赖包
    print_message "检查关键依赖包..."
    if ! "$CURRENT_DIR/venv/bin/python" -c "import flask" 2>/dev/null; then
        print_error "Flask未安装，请先运行: $CURRENT_DIR/venv/bin/pip install -r requirements.txt"
        exit 1
    fi
    
    if ! "$CURRENT_DIR/venv/bin/python" -c "import flask_cors" 2>/dev/null; then
        print_error "Flask-CORS未安装，请先运行: $CURRENT_DIR/venv/bin/pip install -r requirements.txt"
        exit 1
    fi
    
    print_message "虚拟环境验证通过"
}

# 配置服务文件
configure_service() {
    print_step "配置服务文件..."
    
    # 获取Python解释器的绝对路径
    PYTHON_PATH=$(readlink -f "$CURRENT_DIR/venv/bin/python")
    if [[ ! -f "$PYTHON_PATH" ]]; then
        print_error "无法找到Python解释器: $PYTHON_PATH"
        exit 1
    fi
    print_message "Python解释器路径: $PYTHON_PATH"
    
    # 获取Python版本信息
    PYTHON_VERSION=$("$PYTHON_PATH" --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_message "Python版本: $PYTHON_VERSION"
    
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
ExecStart=$PYTHON_PATH $CURRENT_DIR/app.py
ExecReload=/bin/kill -HUP \$MAINPID

# 环境变量 - 设置虚拟环境路径和Python模块路径
Environment=PATH=$CURRENT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=VIRTUAL_ENV=$CURRENT_DIR/venv
Environment=PYTHONPATH=$CURRENT_DIR/venv/lib/python$PYTHON_VERSION/site-packages

# 重启策略
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

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

# 显示服务配置
show_service_config() {
    print_step "生成的服务配置:"
    echo ""
    cat "$TEMP_SERVICE"
    echo ""
    
    # 询问用户是否继续
    read -p "是否继续安装服务? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "用户取消安装"
        exit 0
    fi
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

# 测试服务配置
test_service_config() {
    print_step "测试服务配置..."
    
    # 检查服务文件语法
    if ! systemd-analyze verify /etc/systemd/system/nezha-api.service; then
        print_error "服务文件语法错误"
        systemctl status nezha-api.service
        exit 1
    fi
    
    print_message "服务配置验证通过"
}

# 启动服务
start_service() {
    print_step "启动服务..."
    
    # 启动服务
    systemctl start nezha-api.service
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet nezha-api.service; then
        print_message "服务启动成功"
    else
        print_error "服务启动失败"
        print_message "查看详细状态:"
        systemctl status nezha-api.service
        print_message "查看日志:"
        journalctl -u nezha-api -n 20 --no-pager
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
    verify_environment
    configure_service
    show_service_config
    install_service
    test_service_config
    start_service
    show_service_info
    
    print_message "安装完成！"
    print_message "服务将在系统启动时自动运行"
}

# 运行主函数
main "$@"

# 如果脚本被直接调用，检查参数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        uninstall)
            print_step "卸载 nezha-api 服务..."
            systemctl stop nezha-api.service 2>/dev/null || true
            systemctl disable nezha-api.service 2>/dev/null || true
            rm -f /etc/systemd/system/nezha-api.service
            systemctl daemon-reload
            print_message "服务已卸载"
            ;;
        status)
            print_step "检查服务状态..."
            systemctl status nezha-api.service
            ;;
        logs)
            print_step "查看服务日志..."
            journalctl -u nezha-api -f
            ;;
        help|--help|-h)
            echo "使用方法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  (无参数)  安装并启动服务"
            echo "  uninstall 卸载服务"
            echo "  status    查看服务状态"
            echo "  logs      查看服务日志"
            echo "  help      显示此帮助信息"
            ;;
        *)
            # 默认行为是安装服务
            main "$@"
            ;;
    esac
fi 