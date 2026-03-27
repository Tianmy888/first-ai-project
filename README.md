# AI API 项目

离职期间自学 AI 应用开发的个人项目，从 Python 零基础到完成两个可运行的 API 服务。

## 项目列表

### 1. AI 翻译 API (`translate_api.py`)
- 支持中、英、日、韩、法、德、西等 7+ 种语言互译
- 集成 token 用量监控，每次请求返回成本数据
- 启动：`uvicorn translate_api:app --reload --port 8001`

### 2. AI 对话 API (`api_working.py`)
- 支持多轮对话，通过 session_id 管理会话
- 实现 SSE 流式输出，文字逐字返回
- 对话历史记忆，保留最近 20 轮
- 启动：`uvicorn api_working:app --reload --port 8000`

## 技术栈
- Python 3.13
- FastAPI
- 阿里云百炼（通义千问）

## 快速开始

```bash
# 克隆项目
git clone https://github.com/Tianmy888/first-ai-project.git

# 进入目录
cd first-ai-project

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install fastapi uvicorn openai

# 启动翻译 API
uvicorn translate_api:app --reload --port 8001

# 启动对话 API
uvicorn api_working:app --reload --port 8000