# main.py - 整合真实API + 演示模式

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import openai
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========== 配置 ==========
# 演示模式开关：true=用假数据，false=调用真实API
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# 阿里云百炼配置（真实模式用）
ALIYUN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-22f64e3fb1044781bb8daf2ac36afdad")
ALIYUN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ALIYUN_MODEL = "qwen-turbo"

# 初始化真实API客户端
real_client = openai.OpenAI(
    api_key=ALIYUN_API_KEY,
    base_url=ALIYUN_BASE_URL
)

# 支持的语言
SUPPORTED_LANGS = ["中文", "英文", "日文", "韩文", "法文", "德文", "西班牙文"]

# ========== 数据模型 ==========
class TranslateRequest(BaseModel):
    text: str
    target_lang: str

class TranslateResponse(BaseModel):
    original: str
    translated: str
    target_lang: str
    usage: Dict
    mock: bool = False

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    mock: bool = False

# ========== 创建应用 ==========
app = FastAPI(
    title="AI对话与翻译服务",
    description="支持演示模式和阿里云百炼真实模式",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话存储（简单内存存储）
sessions = {}

# ========== 翻译接口（整合你的真实代码） ==========
@app.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    """翻译接口 - 支持演示模式和真实模式"""
    
    # 参数校验
    if not req.text:
        raise HTTPException(status_code=400, detail="text不能为空")
    if req.target_lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail=f"不支持的语言，支持：{SUPPORTED_LANGS}")
    
    # ========== 演示模式 ==========
    if MOCK_MODE:
        return TranslateResponse(
            original=req.text,
            translated=f"[演示模式] {req.text} → {req.target_lang}",
            target_lang=req.target_lang,
            usage={"total_tokens": 50, "mock": True},
            mock=True
        )
    
    # ========== 真实模式（你的代码） ==========
    try:
        # 构建 Prompt（和你的原代码一致）
        prompt = f"请将以下文本翻译成{req.target_lang}，只返回翻译结果，不要加任何解释：\n{req.text}"
        
        # 调用阿里云百炼
        response = real_client.chat.completions.create(
            model=ALIYUN_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        translated = response.choices[0].message.content
        
        # 提取 token 用量
        usage_info = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return TranslateResponse(
            original=req.text,
            translated=translated,
            target_lang=req.target_lang,
            usage=usage_info,
            mock=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")

# ========== 对话接口 ==========
@app.post("/chat")
async def chat(req: ChatRequest):
    """对话接口 - 支持演示模式"""
    
    session_id = req.session_id or f"session_{int(time.time())}"
    
    if MOCK_MODE:
        # 演示模式
        mock_responses = {
            "你好": "你好！我是AI助手，有什么可以帮你的吗？",
            "翻译": "我可以帮你翻译多种语言，支持中、英、日、韩、法、德、西等语言。"
        }
        reply = mock_responses.get(req.message, f"[演示模式] 收到：{req.message}")
        
        return ChatResponse(
            response=reply,
            session_id=session_id,
            mock=True
        )
    
    # TODO: 真实对话模式（可以后续从 api_working.py 整合）
    return ChatResponse(
        response="真实对话模式开发中，请先使用演示模式",
        session_id=session_id,
        mock=False
    )

# ========== 辅助接口 ==========
@app.get("/")
def root():
    return {
        "service": "AI对话与翻译服务",
        "version": "2.0.0",
        "mock_mode": MOCK_MODE,
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/languages")
def get_languages():
    return {"supported_langs": SUPPORTED_LANGS, "count": len(SUPPORTED_LANGS)}

# ========== 启动 ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)