#!/bin/bash

# 删除旧的虚拟环境（如果存在）
if [ -d "venv" ]; then
    rm -rf venv
fi

# 创建虚拟环境（使用 Python 3.12）
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

echo "虚拟环境已设置完成，并已安装所有依赖。"
echo "使用 'source venv/bin/activate' 激活环境。"
echo "使用 'python3 intraday.py' 启动服务。"