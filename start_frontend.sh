#!/bin/bash

# 进入前端目录
cd "$(dirname "$0")/frontend"

# 检查是否安装了依赖
if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install
fi

# 检查是否存在.env文件
if [ ! -f ".env" ]; then
    echo "创建.env文件..."
    echo "REACT_APP_API_BASE_URL=http://localhost:8000/api" > .env
else
    # 更新现有.env文件中的API地址
    sed -i 's|http://localhost:5000/api|http://localhost:8000/api|g' .env
    echo "已更新.env文件中的API地址为端口8000"
fi

# 启动前端服务
echo "启动前端服务..."
npm start
