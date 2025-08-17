# Nezha API Service 安装脚本修复说明

## 修复的问题

### 1. 符号链接解析问题
**原始问题**: 使用 `venv/bin/python` 路径时，systemd 无法正确解析多层符号链接
```
venv/bin/python -> python3 -> /usr/bin/python3
```

**解决方案**: 使用 `readlink -f` 获取 Python 解释器的绝对路径
```bash
PYTHON_PATH=$(readlink -f "$CURRENT_DIR/venv/bin/python")
# 结果: /usr/bin/python3.11
```

### 2. 模块路径问题
**原始问题**: 使用系统 Python 时无法找到虚拟环境中的包
```
ModuleNotFoundError: No module named 'flask'
```

**解决方案**: 设置正确的环境变量
```ini
Environment=PATH=/root/Map-Nezha/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=VIRTUAL_ENV=/root/Map-Nezha/venv
Environment=PYTHONPATH=/root/Map-Nezha/venv/lib/python3.11/site-packages
```

### 3. 安全设置限制
**原始问题**: 过于严格的安全设置阻止服务正常运行
```ini
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
```

**解决方案**: 移除限制性的安全设置，保留必要的资源限制

## 新增功能

### 1. 环境验证
- 检查虚拟环境是否存在
- 验证 Python 解释器
- 检查关键依赖包（Flask, Flask-CORS）

### 2. 服务配置验证
- 使用 `systemd-analyze verify` 检查服务文件语法
- 在启动前验证配置正确性

### 3. 增强的错误处理
- 添加清理函数，自动清理临时文件
- 详细的错误信息和日志显示
- 优雅的错误退出

### 4. 交互式安装
- 显示生成的服务配置
- 用户确认后继续安装
- 支持取消安装

### 5. 管理功能
```bash
# 安装服务
sudo ./install-service.sh

# 卸载服务
sudo ./install-service.sh uninstall

# 查看服务状态
sudo ./install-service.sh status

# 查看服务日志
sudo ./install-service.sh logs

# 显示帮助
./install-service.sh help
```

## 使用方法

### 1. 基本安装
```bash
# 确保在项目目录中
cd /path/to/Map-Nezha

# 运行安装脚本
sudo ./install-service.sh
```

### 2. 安装流程
1. **权限检查**: 验证是否以 root 权限运行
2. **环境验证**: 检查虚拟环境和依赖包
3. **配置生成**: 生成优化的服务配置文件
4. **用户确认**: 显示配置并等待用户确认
5. **服务安装**: 安装并启用服务
6. **配置验证**: 验证服务配置语法
7. **服务启动**: 启动服务并验证状态

### 3. 故障排除
如果服务启动失败，脚本会自动显示：
- 服务状态
- 最近的日志
- 错误信息

## 技术改进

### 1. 路径解析
- 使用绝对路径避免符号链接问题
- 动态检测 Python 版本
- 自动设置正确的模块路径

### 2. 环境变量
- 完整的 PATH 设置
- 虚拟环境路径配置
- Python 模块搜索路径

### 3. 服务配置
- 移除不必要的安全限制
- 保留资源限制和重启策略
- 优化的日志配置

## 注意事项

1. **权限要求**: 必须以 root 权限运行
2. **虚拟环境**: 必须先创建并安装依赖
3. **Python 版本**: 自动检测，支持 Python 3.x
4. **系统兼容**: 适用于 systemd 系统（Ubuntu 16.04+, CentOS 7+）

## 测试验证

修复后的脚本已经过测试：
- ✅ 语法检查通过
- ✅ 环境验证正常
- ✅ 服务配置生成正确
- ✅ 交互式功能正常
- ✅ 错误处理完善

现在你可以安全地使用 `install-service.sh` 脚本来安装 Nezha API 服务了！ 