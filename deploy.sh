#!/bin/bash

cd "$(dirname "$0")"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 启动 app.py（开发模式，后台运行，日志输出到 app.log）
nohup python app.py > app.log 2>&1 &
echo "app.py 已在后台启动，日志见 app.log"