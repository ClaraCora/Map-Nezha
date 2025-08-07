# Nezha 监控数据 Web API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 从哪吒监控面板获取服务器实时数据，以 ECharts 友好的 JSON 格式通过 API 提供。支持多国家聚合、自动国家坐标映射，适合前端地图可视化。

## 📋 目录

- [功能特性](#-功能特性)
- [快速开始](#-快速开始)
- [配置说明](#-配置说明)
- [部署指南](#-部署指南)
- [API 文档](#-api-文档)
- [常见问题](#-常见问题)
- [维护建议](#-维护建议)
- [项目结构](#-项目结构)

## ✨ 功能特性

- 🔐 **安全认证**：支持哪吒面板登录认证和 Nginx Basic Auth
- 🌍 **多国家支持**：自动国家代码映射和坐标定位
- 📊 **实时数据**：通过 WebSocket 获取实时流量统计
- 🗺️ **地图友好**：输出 ECharts 兼容的 JSON 格式
- ⚡ **高性能**：支持多进程部署和负载均衡
- 🔧 **易于配置**：支持 `.env` 文件和环境变量配置

## 🚀 快速开始

### 环境要求

- **操作系统**：Linux (Debian/Ubuntu/CentOS) / macOS / Windows
- **Python 版本**：3.8 及以上
- **包管理器**：pip

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/ClaraCora/Map-Nezha.git
   cd Map-Nezha
   ```

2. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或 venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **配置环境**
   ```bash
   cp env.example .env
   # 编辑 .env 文件，填入您的哪吒面板配置
   ```

5. **启动服务**
   ```bash
   python app.py
   ```

6. **测试 API**
   ```bash
   curl http://localhost:5001/api/v1/traffic-stats
   ```

7. **安装为系统服务（可选）**
   ```bash
   sudo ./install-service.sh
   ```

## ⚙️ 配置说明

### 方式一：.env 文件（推荐）

1. **复制配置文件**
   ```bash
   cp env.example .env
   ```

2. **编辑配置**
   ```bash
   # 哪吒监控面板地址
   NEZHA_DASHBOARD_URL=https://your-nezha-panel.com
   
   # 哪吒监控登录凭据
   NEZHA_USERNAME=your_username
   NEZHA_PASSWORD=your_password
   
   # Nginx Basic Auth 配置（可选）
   NGINX_BASIC_AUTH_USER=
   NGINX_BASIC_AUTH_PASS=
   ```

### 方式二：环境变量

```bash
export NEZHA_DASHBOARD_URL="https://your-nezha-panel.com"
export NEZHA_USERNAME="your_username"
export NEZHA_PASSWORD="your_password"
export NGINX_BASIC_AUTH_USER="nginx_user"
export NGINX_BASIC_AUTH_PASS="nginx_pass"
```

### 方式三：代码配置（仅用于测试）

```python
NEZHA_DASHBOARD_URL = "https://your-nezha-panel.com"
NEZHA_USERNAME = "your_username"
NEZHA_PASSWORD = "your_password"
```

## 🚀 部署指南

### 开发环境

```bash
# 启动开发服务器
source venv/bin/activate
python app.py

# 访问地址
# http://localhost:5001
# API: http://localhost:5001/api/v1/traffic-stats
```

### 一键部署脚本

```bash
# 赋予执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

### 自动服务安装脚本

我们提供了智能安装脚本，可以自动配置和安装 systemd 服务：

```bash
# 1. 首先运行部署脚本创建环境
./deploy.sh

# 2. 安装并启动服务
sudo ./install-service.sh
```

**脚本功能**：
- 🔍 **自动检测**：当前目录、用户、虚拟环境
- ⚙️ **智能配置**：自动生成正确的服务配置
- 🛡️ **安全检查**：验证必要文件是否存在
- 📊 **详细反馈**：彩色输出和错误处理
- 🚀 **一键安装**：自动安装、启用、启动服务

**安装过程**：
1. 检测当前工作目录和用户
2. 验证虚拟环境和 app.py 文件
3. 生成正确的 systemd 服务配置
4. 安装服务到系统目录
5. 启用服务并启动
6. 显示服务管理命令

### 生产环境

#### 使用 Gunicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:5001 app:app > app.log 2>&1 &
```

#### 使用 Systemd 服务

**方法一：自动安装（推荐）**

使用提供的安装脚本自动配置和安装服务：

```bash
# 确保已运行 deploy.sh 创建虚拟环境
./deploy.sh

# 安装并启动服务
sudo ./install-service.sh
```

**方法二：手动安装**

1. **修改服务文件**
   ```bash
   # 编辑 nezha-api.service
   # 修改 User=your_username 为实际用户名
   # 修改路径为实际路径
   ```

2. **安装服务**
   ```bash
   sudo cp nezha-api.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable nezha-api
   sudo systemctl start nezha-api
   ```

3. **管理服务**
   ```bash
   sudo systemctl status nezha-api
   sudo systemctl restart nezha-api
   sudo systemctl stop nezha-api
   sudo journalctl -u nezha-api -f  # 查看日志
   ```

#### 配合 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📚 API 文档

### 基础信息

- **基础 URL**: `http://your-server:5001`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

### 接口列表

#### 1. 流量统计接口

**GET** `/api/v1/traffic-stats`

获取所有服务器的流量统计信息，按国家聚合。

**响应示例**:
```json
[
  {
    "countryNameEN": "United States of America",
    "countryNameEmojiCN": "🇺🇸 美国",
    "uplinkSpeed": 125.5,
    "downlinkSpeed": 89.2,
    "coords": [-95.71, 37.09]
  },
  {
    "countryNameEN": "Japan",
    "countryNameEmojiCN": "🇯🇵 日本",
    "uplinkSpeed": 67.8,
    "downlinkSpeed": 45.3,
    "coords": [138.25, 36.20]
  }
]
```

#### 2. 连接测试接口

**GET** `/api/v1/test-connection`

测试与哪吒监控面板的连接状态。

**响应示例**:
```json
{
  "status": "success",
  "message": "成功连接到哪吒监控，获取到 5 个服务器数据",
  "server_count": 5,
  "sample_data": {...}
}
```

#### 3. 诊断接口

**GET** `/api/v1/diagnose`

详细诊断连接问题，包括网络测试和认证测试。

**响应示例**:
```json
{
  "config": {
    "dashboard_url": "https://your-panel.com",
    "username": "admin",
    "password_set": true,
    "nginx_auth_configured": false
  },
  "network_tests": {
    "dns_resolution": {"status": "success", "ip": "192.168.1.1"},
    "port_connection": {"status": "success", "port": 443}
  },
  "auth_tests": {
    "login_without_nginx": {"status": "success", "status_code": 200}
  },
  "recommendations": []
}
```

## ❓ 常见问题

### Q1: API 返回速度为 0？

**A**: 这是正常现象，只有服务器有实时流量时才会显示非零速率。请确认：
- 哪吒面板中服务器有活跃流量
- 服务器状态正常
- 网络连接正常

### Q2: 新国家服务器未显示？

**A**: 需要补充国家映射表：
1. 查看日志中的警告信息
2. 在 `COUNTRY_CODE_TO_NAME_MAP` 中添加国家代码映射
3. 在 `COUNTRY_COORDS` 中添加坐标信息

### Q3: 连接失败？

**A**: 请检查：
1. 哪吒面板地址是否正确
2. 用户名密码是否正确
3. 网络连接是否正常
4. 防火墙设置是否允许连接

### Q4: 频繁请求压力大？

**A**: 建议：
1. 增加请求间隔（建议 5-10 秒）
2. 使用缓存机制
3. 考虑使用 CDN 加速

### Q5: 安装脚本运行失败？

**A**: 请检查：
1. 是否以 root 权限运行：`sudo ./install-service.sh`
2. 是否已运行 `./deploy.sh` 创建虚拟环境
3. 当前目录是否包含 `app.py` 文件
4. 查看错误信息并按照提示操作

### Q6: 服务启动失败？

**A**: 排查步骤：
1. 检查服务状态：`sudo systemctl status nezha-api`
2. 查看详细日志：`sudo journalctl -u nezha-api -f`
3. 验证配置文件：`sudo systemctl cat nezha-api`
4. 检查权限：确保用户有访问项目目录的权限

## 🔧 维护建议

### 日常维护

- 📊 **定期查看日志**：监控应用运行状态
- 🗺️ **更新国家映射**：及时补充新的国家服务器
- 🔄 **关注面板升级**：哪吒面板 API 变化时及时调整
- 💾 **备份配置**：定期备份 `.env` 配置文件

### 性能优化

- 🚀 **使用 Gunicorn**：生产环境推荐使用多进程
- 🔒 **配置 Nginx**：添加反向代理和 SSL 证书
- 📈 **监控指标**：添加应用性能监控
- 🗄️ **数据库缓存**：考虑使用 Redis 缓存热点数据

### 安全建议

- 🔐 **使用 HTTPS**：生产环境必须启用 SSL
- 🛡️ **防火墙配置**：只开放必要端口
- 🔑 **密钥管理**：使用环境变量或密钥管理服务
- 📝 **日志审计**：记录访问日志和安全事件

## 📖 参考命令

### 开发环境

```bash
# 配置环境
cp env.example .env
# 编辑 .env 文件填入实际配置

# 启动开发服务
source venv/bin/activate
python app.py

# 测试连接
curl http://localhost:5001/api/v1/test-connection

# 安装为系统服务
sudo ./install-service.sh
```

### 生产环境

```bash
# 启动生产服务
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:5001 app:app > app.log 2>&1 &

# 查看日志
tail -f app.log
```

### 服务管理

#### 基本命令

```bash
# 查看服务状态
sudo systemctl status nezha-api

# 启动服务
sudo systemctl start nezha-api

# 停止服务
sudo systemctl stop nezha-api

# 重启服务
sudo systemctl restart nezha-api

# 重新加载配置
sudo systemctl daemon-reload
```

#### 日志管理

```bash
# 查看实时日志
sudo journalctl -u nezha-api -f

# 查看最近的日志
sudo journalctl -u nezha-api -n 50

# 查看今天的日志
sudo journalctl -u nezha-api --since today

# 查看错误日志
sudo journalctl -u nezha-api -p err
```

#### 服务配置

```bash
# 查看服务配置
sudo systemctl cat nezha-api

# 编辑服务配置（不推荐）
sudo systemctl edit nezha-api

# 重新加载配置
sudo systemctl daemon-reload
sudo systemctl restart nezha-api
```

#### 故障排除

```bash
# 检查服务是否启用
sudo systemctl is-enabled nezha-api

# 检查服务是否运行
sudo systemctl is-active nezha-api

# 查看详细状态
sudo systemctl status nezha-api --no-pager -l

# 查看启动日志
sudo journalctl -u nezha-api --since "5 minutes ago"
```

## 📁 项目结构

```
api/
├── app.py                 # 主应用程序
├── readme.md             # 项目文档
├── .gitignore            # Git 忽略文件
├── deploy.sh             # 一键部署脚本
├── install-service.sh    # 自动服务安装脚本
├── nezha-api.service     # systemd 服务配置模板
├── env.example           # 环境变量配置示例
├── requirements.txt      # Python 依赖包列表
├── LICENSE              # MIT 许可证
└── static/               # 前端静态资源
    ├── index.html
    ├── css/
    ├── js/
    └── world.json
```

### 脚本说明

- **`deploy.sh`**: 一键部署脚本，创建虚拟环境并安装依赖
- **`install-service.sh`**: 智能服务安装脚本，自动配置 systemd 服务
- **`nezha-api.service`**: systemd 服务配置模板（安装时会自动修改）

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！ 