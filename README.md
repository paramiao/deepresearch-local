# DeepResearch 深度研究助手

DeepResearch是一个基于Gemini API的研究助手应用，可以通过聊天界面提出研究需求，获取研究规划方案，并最终生成研究报告。应用支持全中文交互，界面类似ChatGPT。

## 功能特点

- 基于用户需求生成详细的研究计划
- 根据研究计划和发现生成完整的研究报告
- 提供研究相关问题的专业解答
- 简洁直观的聊天界面
- 全中文交互体验

## 技术栈

### 前端
- React 18
- React Router
- Axios
- React Markdown
- Styled Components

### 后端
- Flask
- Google Generative AI (Gemini API)
- Flask-CORS

## 快速开始

### 环境要求
- Node.js 16+
- Python 3.8+
- Gemini API 密钥

### 后端设置

1. 进入后端目录:
```bash
cd deepresearch/backend
```

2. 创建虚拟环境并激活:
```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用: venv\Scripts\activate
```

3. 安装依赖:
```bash
pip install -r requirements.txt
```

4. 设置环境变量:
```bash
export GEMINI_API_KEY="your_gemini_api_key"  # 在Windows上使用: set GEMINI_API_KEY=your_gemini_api_key
```

5. 启动服务器:
```bash
python app.py
```

### 前端设置

1. 进入前端目录:
```bash
cd deepresearch/frontend
```

2. 安装依赖:
```bash
npm install
```

3. 创建`.env`文件并设置API地址:
```
REACT_APP_API_BASE_URL=http://localhost:5000/api
```

4. 启动开发服务器:
```bash
npm start
```

5. 在浏览器中访问: http://localhost:3000

## 使用指南

1. 访问应用后，您会看到一个类似ChatGPT的聊天界面
2. 输入您的研究主题和需求，例如: "中国新能源汽车市场发展，需要包含近五年的市场数据和未来三年预测"
3. 系统会生成一个研究计划，包含研究背景、目标、方法等
4. 您可以继续提问获取更多信息，或者提供研究发现，请求生成最终的研究报告

## 项目结构

```
deepresearch/
├── backend/             # 后端代码
│   ├── app/             # Flask应用
│   │   ├── models/      # 数据模型
│   │   ├── routes/      # API路由
│   │   └── services/    # 业务逻辑
│   ├── config/          # 配置文件
│   ├── utils/           # 工具函数
│   └── app.py           # 应用入口
├── frontend/            # 前端代码
│   ├── public/          # 静态资源
│   └── src/             # React源代码
│       ├── components/  # UI组件
│       ├── pages/       # 页面组件
│       ├── services/    # API服务
│       └── styles/      # CSS样式
└── docs/                # 文档
    ├── 需求文档.md       # 项目需求文档
    └── 版本规划.md       # 版本迭代计划
```

## 许可
MIT
