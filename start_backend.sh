#!/bin/bash

# 进入后端目录
cd "$(dirname "$0")/backend"

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 检查是否设置了API密钥
if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo "警告: 未设置SILICONFLOW_API_KEY环境变量。"
    echo "请设置SILICONFLOW_API_KEY环境变量后再启动服务。"
    echo "例如: export SILICONFLOW_API_KEY=your_api_key_here"
    
    # 设置用户提供的硬基流动API密钥
    export SILICONFLOW_API_KEY="sk-jydepycxtbgohburuphpummkqjhussdfkwjlappjywequsbv"
    echo "已设置用户提供的硬基流动API密钥。"
fi

# 检查是否设置了API基地址
if [ -z "$SILICONFLOW_API_BASE_URL" ]; then
    export SILICONFLOW_API_BASE_URL="https://api.siliconflow.cn/v1"
    echo "已设置默认API基地址: $SILICONFLOW_API_BASE_URL"
fi

# 检查是否设置了SERPAPI_API_KEY
if [ -z "$SERPAPI_API_KEY" ]; then
    echo "警告: 未设置SERPAPI_API_KEY环境变量。"
    echo "请设置SERPAPI_API_KEY环境变量以启用真实搜索功能。"
    
    # 使用用户提供的SerAPI密钥
    export SERPAPI_API_KEY="22364bddedce6755e022ee9e20264269a9859ab008c6c7052e62c07c328731be"
    echo "已设置用户提供的SERPAPI_API_KEY。"
fi

# 启动后端服务
echo "启动后端服务..."
python app.py
