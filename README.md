# AI 对话与翻译服务

> 一个轻量级的 AI 服务底座，提供对话与翻译能力，支持流式输出、多轮记忆、成本可控。

## ✨ 特性

- 🚀 **一键启动**：提供 Docker Compose，5 分钟快速部署
- 💬 **智能对话**：支持多用户会话隔离，保留最近 20 轮记忆
- 🌍 **多语言翻译**：支持中、英、日、韩、法、德、西等 7+ 语言互译
- 📡 **流式输出**：SSE 实时响应，提升用户体验
- 📊 **成本透明**：每次请求返回 token 消耗，便于成本控制
- 📝 **完整文档**：自动生成 Swagger API 文档

## 🚀 快速开始

### 前置要求
- Docker 和 Docker Compose
- OpenAI API Key

### 5 分钟部署
```bash
# 1. 克隆项目
git clone https://github.com/Tianmy888/first-ai-project.git
cd first-ai-project

# 2. 设置 API Key
export OPENAI_API_KEY="your-api-key"

# 3. 一键启动
docker-compose up -d

# 4. 访问 API 文档
open http://localhost:8000/docs