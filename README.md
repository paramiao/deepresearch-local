# DeepResearch - 智能研究助手

一个基于AI的智能研究助手，能够自动生成研究计划、执行搜索查询并生成综合研究报告。DeepResearch结合了强大的搜索功能和AI分析能力，帮助用户进行深度、全面的研究工作。

## 核心功能

1. **智能研究计划生成**
   - 自动分析研究主题，生成结构化的研究计划
   - 识别核心研究问题，形成有针对性的研究方向
   - 提供用户审核和确认机制，确保研究方向符合期望

2. **问题导向的专门搜索**
   - 每个核心研究问题单独执行专门搜索
   - 优化的搜索算法，确保查询结果与研究问题高度相关
   - 智能提取网页内容中的关键信息，提高研究效率

3. **深度分析与报告生成**
   - 对每个研究问题生成深入、详细的分析
   - 完整保留研究过程，包括搜索查询、关键发现和数据来源
   - 生成结构化研究报告，含详细论证和数据支持

## 研究流程

DeepResearch遵循严格的研究流程，确保研究质量和用户参与：

1. **研究计划生成**: 分析用户提供的主题和要求，生成结构化研究计划
2. **用户确认**: 用户审核研究计划，可以确认或调整后再继续
3. **执行研究**: 对每个核心问题执行搜索、提取和分析
4. **生成研究报告**: 基于收集的数据和分析结果生成详细研究报告

## 环境配置和项目启动详细指南

### 环境要求

- Python 3.8+ 和虚拟环境
- Node.js 14+ 和npm
- 硅基流动API密钥（用于AI服务）
- SERPAPI密钥（用于搜索功能）

### 步骤 1: 克隆和准备项目

```bash
git clone https://github.com/paramiao/deepresearch-local.git
cd deepresearch-local
```

### 步骤 2: 后端设置

#### 创建并激活虚拟环境

```bash
cd backend
python -m venv venv  # 如果命令不可用，尝试使用 python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
# 或者 venv\Scripts\activate  # Windows
```

> **注意**：确保您的系统已安装Python虚拟环境模块。如果没有，可以通过以下命令安装：
> - Ubuntu/Debian: `sudo apt-get install python3-venv`
> - CentOS/RHEL: `sudo yum install python3-venv`
> - Windows: 通常已包含在Python安装中

#### 安装Python依赖

```bash
pip install -r requirements.txt
```

#### 配置环境变量

在`backend`目录下创建`.env`文件并添加以下内容：

```
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
PORT=8000
```

**重要提示**：必须配置有效的API密钥，否则AI和搜索功能将无法正常工作。

### 步骤 3: 前端设置

#### 安装Node.js依赖

```bash
cd frontend
npm install
```

> **注意**: 依赖安装过程可能需要几分钟时间，请耐心等待。如果出现警告消息，但没有错误，可以忽略并继续。

#### 修复前端配置

为确保前后端通信正常，**必须执行以下修改**，否则项目将无法正常运行：

1. **修改API URL配置**：

   打开 `frontend/src/services/api.js`，将：
   ```javascript
   const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
   ```
   修改为：
   ```javascript
   const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';
   ```

2. **修改研究服务配置**：

   打开 `frontend/src/services/researchService.js`（如果存在），将：
   ```javascript
   const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://10.108.43.112:8000/api';
   ```
   修改为：
   ```javascript
   const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';
   ```
   
3. **扫描其他可能的硬编码URL**：

   在前端项目中搜索所有可能的硬编码API URL（如localhost:8000或其他IP地址），并将它们也修改为相对路径。可以使用以下命令查找：
   
   ```bash
   cd frontend
   grep -r "http://localhost:8000" src --include="*.js"
   grep -r "http://10." src --include="*.js"
   ```

3. **添加代理配置**：

   在 `frontend/package.json` 文件末尾添加代理配置，确保在最后一个右花括号之前：
   ```json
   "proxy": "http://localhost:8000"
   ```
   完整示例：
   ```json
   {
     "name": "deepresearch-frontend",
     ...
     "browserslist": {
       ...
     },
     "proxy": "http://localhost:8000"
   }
   ```

4. **创建前端环境变量**：

   在 `frontend` 目录创建 `.env` 文件：
   ```
   REACT_APP_API_BASE_URL=/api
   ```

### 步骤 4: 启动应用

#### 启动后端

在一个终端中：

```bash
cd backend
source venv/bin/activate  # 如果尚未激活
python app.py  # 如果命令不可用，尝试 python3 app.py
```

后端服务将在 http://localhost:8000 上运行。

> **重要：** 确保后端服务启动在端口8000上，这与前端的代理配置置相匹配。如果要使用其他端口，需要同时修改前端的代理配置。

#### 启动前端

在另一个终端中：

```bash
cd frontend
npm start
```

前端将在 http://localhost:3000 上运行。

#### 验证安装

安装完成后，请执行以下检查：

1. 确认后端服务正在运行，通过访问 http://localhost:8000/api/status 显示服务正常
2. 确认前端可以访问，并在浏览器控制台中无API错误
3. 尝试启动一个研究过程，验证完整的研究流程

## 项目结构

- `/frontend`: React前端应用
  - `/src/components`: UI组件
  - `/src/services`: API服务和通信逻辑
  - `/src/styles`: CSS样式文件

- `/backend`: Flask后端API服务
  - `/app/services`: 核心服务逻辑
  - `/app/routes`: API路由
  - `/app/models`: 数据模型

## 最新优化

- **增强的问题导向研究**: 每个核心研究问题现在都有专门的搜索和分析流程
- **改进的搜索质量**: 优化了关键词匹配和内容提取算法，提高相关性
- **详细的研究报告**: 确保每个研究问题都有深入分析，不再是简单的一句话结论
- **保留完整研究过程**: 用户可以查看每个问题的搜索过程和关键发现

## 研究流程验证

成功部署项目后，请验证完整的研究流程是否正常工作。DeepResearch采用严格的四步骤研究流程：

1. **生成研究计划**: 在首页输入研究主题，等待AI生成结构化的研究计划
   - 验证点: 是否能看到生成的研究问题和方法

2. **用户确认**: 检查研究计划并确认（此步骤不得跳过）
   - 验证点: 点击“确认计划”按钮后是否正确转到研究过程页面

3. **执行研究**: 系统自动为每个核心问题执行搜索和分析
   - 验证点: 是否能看到实时的研究进度和中间结果

4. **生成研究报告**: 研究完成后自动生成详细报告
   - 验证点: 是否能看到完整的报告内容和数据来源

> **重要**: 确保研究流程的完整性，不要跳过任何步骤。特别是“用户确认”这一关键交互环节。

## 故障排除指南

### 404 错误 (API不可达)

**症状**: 前端控制台显示 "Request failed with status code 404"

**解决方案**:
1. 检查后端服务是否正在运行
2. 确认`package.json`中的代理配置正确 (`"proxy": "http://localhost:8000"`)
3. 确认所有前端服务文件中的API URL使用相对路径 (`/api`)
4. 检查api.js和researchService.js中的API基础URL配置是否已修改为相对路径
5. 重启前端服务

### API密钥错误

**症状**: 后端日志显示API密钥认证失败

**解决方案**:
1. 检查`.env`文件中的API密钥是否正确
2. 确认API密钥未过期或失效
3. 确保您的API密钥具有必要的权限

### package.json解析错误

**症状**: 启动前端时出现JSON语法错误

**解决方案**:
1. 确保package.json的JSON格式正确，特别是在添加代理配置后
2. 检查是否有多余或缺少的逗号、引号或大括号

## 版本历史

- **v1.0.0**: 初始版本，基础研究功能
- **v1.1.0**: 增强搜索和分析能力，提高研究报告质量
- **v1.2.0**: 实现问题导向的专门研究，优化用户界面和研究报告
- **v1.3.0**: 修复前后端通信问题，优化部署流程
