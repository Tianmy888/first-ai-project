from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, AsyncGenerator
import openai
import uuid
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# ==================== 配置 ====================
app = FastAPI(title="AI 聊天 API", description="支持多轮对话、流式输出、限流保护的AI服务", version="2.0")

# 配置阿里云百炼
api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"  # 替换成你的真实 Key

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 存储会话历史
sessions: Dict[str, List[Dict[str, str]]] = {}

# ==================== 限流配置（第5步）====================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# ==================== 数据模型 ====================
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = False  # 是否使用流式输出

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    estimated_tokens: Optional[int] = None  # 预估消耗token

class NewSessionResponse(BaseModel):
    session_id: str

# ==================== 辅助函数 ====================
def estimate_cost(messages: List[Dict]) -> int:
    """第3步：粗略估算 token 数（中文字数 * 2，英文单词数 * 1.5）"""
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        # 粗略估算：中文按2，英文按1.5
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        other_chars = len(content) - chinese_chars
        total_chars += chinese_chars * 2 + other_chars * 1.5
    return int(total_chars)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_ai_with_retry(messages):
    """第4步：带重试的 AI 调用"""
    return client.chat.completions.create(
        model="qwen-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )

# ==================== API 接口 ====================
@app.get("/new_session", response_model=NewSessionResponse)
@limiter.limit("100/minute")  # 第5步：限流
async def new_session(request: Request):
    """创建新会话"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return NewSessionResponse(session_id=session_id)

@app.post("/chat")
@limiter.limit("10/minute")  # 第5步：限流，每分钟最多10次
async def chat(request: ChatRequest, request_obj: Request):
    """对话接口，支持多轮对话和流式输出"""
    
    # 获取或创建会话
    session_id = request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    
    # 构建消息历史
    messages = []
    messages.append({
        "role": "system", 
        "content": "你是一个友好的AI助手，回答要简洁、有帮助。"
    })
    for msg in sessions[session_id]:
        messages.append(msg)
    messages.append({"role": "user", "content": request.message})
    
    # 第3步：估算token
    estimated_tokens = estimate_cost(messages)
    print(f"[会话 {session_id[:8]}] 预估消耗 {estimated_tokens} tokens")
    
    # 如果是流式输出
    if request.stream:
        return StreamingResponse(
            stream_response(messages, session_id, request.message),
            media_type="text/event-stream"
        )
    
    # 非流式输出，第4步：带重试
    try:
        response = call_ai_with_retry(messages)
        reply = response.choices[0].message.content
        
        # 保存历史
        sessions[session_id].append({"role": "user", "content": request.message})
        sessions[session_id].append({"role": "assistant", "content": reply})
        
        # 限制历史长度（最多保留20轮）
        if len(sessions[session_id]) > 40:
            sessions[session_id] = sessions[session_id][-40:]
        
        return ChatResponse(
            reply=reply, 
            session_id=session_id,
            estimated_tokens=estimated_tokens
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI调用失败: {str(e)}")

async def stream_response(messages: List[Dict], session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """流式响应生成器"""
    try:
        full_reply = ""
        
        # 调用流式API
        stream = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            stream=True
        )
        
        # 逐块返回
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_reply += content
                yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
        
        # 保存历史
        sessions[session_id].append({"role": "user", "content": user_message})
        sessions[session_id].append({"role": "assistant", "content": full_reply})
        
        # 限制历史长度
        if len(sessions[session_id]) > 40:
            sessions[session_id] = sessions[session_id][-40:]
        
        # 发送完成信号
        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

@app.delete("/session/{session_id}")
@limiter.limit("20/minute")
async def clear_session(session_id: str, request: Request):
    """清除会话历史"""
    if session_id in sessions:
        sessions[session_id] = []
        return {"status": "cleared", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    """根路径"""
    return {
        "message": "AI 聊天 API 已启动",
        "version": "2.0",
        "docs": "/docs",
        "endpoints": [
            "GET /new_session - 创建新会话",
            "POST /chat - 发送消息（支持 stream 参数）",
            "DELETE /session/{session_id} - 清除会话历史",
            "GET / - 服务信息"
        ]
    }

# 启动时打印信息
if __name__ == "__main__":
    import uvicorn
    print("启动 AI 聊天 API 服务...")
    print("访问 http://127.0.0.1:8000/docs 查看 API 文档")
    uvicorn.run(app, host="0.0.0.0", port=8000)