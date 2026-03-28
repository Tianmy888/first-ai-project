# main.py - 统一的API入口

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import time
import random
from datetime import datetime

# ========== 配置部分 ==========
# Mock模式开关（无需API Key即可演示）
USE_MOCK = True  # 改成False就是真实调用模式

# 支持的语言
SUPPORTED_LANGS = {
    "zh": "中文",
    "en": "英文", 
    "ja": "日文",
    "ko": "韩文",
    "fr": "法文",
    "de": "德文",
    "es": "西班牙文"
}

# Mock翻译数据
MOCK_TRANSLATIONS = {
    ("你好世界", "en"): "Hello World",
    ("你好世界", "ja"): "こんにちは世界",
    ("你好世界", "ko"): "안녕하세요 세계",
    ("深度学习", "en"): "Deep Learning",
    ("人工智能", "en"): "Artificial Intelligence",
    ("吃土", "en"): "spend all one's money",
    ("锦鲤", "en"): "lucky charm",
    ("早上好", "en"): "Good morning",
    ("晚上好", "en"): "Good evening",
}

# Mock对话数据
MOCK_CHAT_RESPONSES = {
    "你好": "你好！我是AI助手，有什么可以帮你的吗？",
    "翻译": "我可以帮你翻译多种语言，支持中、英、日、韩、法、德、西等语言。",
    "默认": "这是演示模式下的回复。设置真实API Key后可以获得更智能的回答。"
}

# 会话存储（简单内存存储，演示用）
sessions = {}

# ========== 数据模型 ==========
class TranslateRequest(BaseModel):
    text: str
    target_lang: str
    source_lang: Optional[str] = "auto"

class TranslateResponse(BaseModel):
    source_text: str
    source_lang: str
    target_lang: str
    translation: str
    tokens_used: int
    mock: bool = False

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tokens_used: int
    mock: bool = False

# ========== 创建FastAPI应用 ==========
app = FastAPI(
    title="AI对话与翻译服务",
    description="一个轻量级的AI服务底座，提供对话与翻译能力",
    version="1.2.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== API接口 ==========
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "AI对话与翻译服务",
        "version": "1.2.0",
        "status": "running",
        "mock_mode": USE_MOCK,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": "1.2.0",
        "timestamp": datetime.now().isoformat(),
        "mock_mode": USE_MOCK
    }

@app.get("/languages")
async def get_languages():
    """获取支持的语言列表"""
    return {
        "supported_langs": SUPPORTED_LANGS,
        "count": len(SUPPORTED_LANGS)
    }

@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """翻译接口"""
    start_time = time.time()
    
    # 参数校验
    if not request.text:
        raise HTTPException(status_code=400, detail="text字段不能为空")
    
    if request.target_lang not in SUPPORTED_LANGS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的语言: {request.target_lang}，支持: {', '.join(SUPPORTED_LANGS.keys())}"
        )
    
    # Mock模式
    if USE_MOCK:
        key = (request.text, request.target_lang)
        if key in MOCK_TRANSLATIONS:
            translation = MOCK_TRANSLATIONS[key]
        else:
            # 生成通用Mock翻译
            translation = f"[演示模式] {request.text} → {SUPPORTED_LANGS[request.target_lang]}"
        
        return TranslateResponse(
            source_text=request.text,
            source_lang=request.source_lang or "auto",
            target_lang=request.target_lang,
            translation=translation,
            tokens_used=50,
            mock=True
        )
    
    # TODO: 真实调用OpenAI API
    # 这里可以导入你已有的translate_api.py中的函数
    # from translate_api import call_translation
    # result = call_translation(request.text, request.target_lang)
    
    return TranslateResponse(
        source_text=request.text,
        source_lang="zh",
        target_lang=request.target_lang,
        translation="[真实模式] 需要配置OpenAI API Key",
        tokens_used=0,
        mock=False
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """对话接口"""
    
    # 生成或获取session_id
    session_id = request.session_id or f"session_{int(time.time())}"
    
    # 初始化会话
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "created_at": datetime.now().isoformat()
        }
    
    # Mock模式
    if USE_MOCK:
        # 简单的关键词匹配
        response_text = MOCK_CHAT_RESPONSES.get(
            request.message, 
            f"收到消息：「{request.message}」\n\n这是演示模式下的回复。设置真实API Key后可以获得更智能的回答。"
        )
        
        # 记录历史
        sessions[session_id]["history"].append({
            "user": request.message,
            "assistant": response_text,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            tokens_used=100,
            mock=True
        )
    
    # TODO: 真实调用OpenAI API
    return ChatResponse(
        response="[真实模式] 需要配置OpenAI API Key",
        session_id=session_id,
        tokens_used=0,
        mock=False
    )

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话历史"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "session_id": session_id,
        "history": sessions[session_id]["history"],
        "created_at": sessions[session_id]["created_at"],
        "total_messages": len(sessions[session_id]["history"])
    }

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    if session_id in sessions:
        del sessions[session_id]
    
    return {"message": f"会话 {session_id} 已清除"}

# ========== 启动配置 ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)