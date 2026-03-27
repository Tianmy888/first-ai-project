from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, AsyncGenerator
import openai
import uuid
import json

# ==================== 配置 ====================
app = FastAPI(title="AI 聊天 API", version="1.0")

# 配置阿里云百炼
api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"  # 你的 API Key

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 存储会话历史
sessions: Dict[str, List[Dict[str, str]]] = {}

# ==================== 数据模型 ====================
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    reply: str
    session_id: str

class NewSessionResponse(BaseModel):
    session_id: str

# ==================== API 接口 ====================
@app.get("/new_session", response_model=NewSessionResponse)
async def new_session():
    """创建新会话"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return NewSessionResponse(session_id=session_id)

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    """对话接口"""
    
    # 获取或创建会话
    session_id = chat_request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    
    # 构建消息历史
    messages = []
    messages.append({
        "role": "system", 
        "content": "你是一个幽默的AI助手，回答要带点搞笑。"
    })
    for msg in sessions[session_id]:
        messages.append(msg)
    messages.append({"role": "user", "content": chat_request.message})
    
    # 如果是流式输出
    if chat_request.stream:
        return StreamingResponse(
            stream_response(messages, session_id, chat_request.message),
            media_type="text/event-stream"
        )
    
    # 非流式输出
    try:
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        print(f"调用成功 - 输入:{response.usage.prompt_tokens} token，输出:{response.usage.completion_tokens} token，总计:{response.usage.total_tokens} token")
        reply = response.choices[0].message.content
        
        # 保存历史
        sessions[session_id].append({"role": "user", "content": chat_request.message})
        sessions[session_id].append({"role": "assistant", "content": reply})
        
        # 限制历史长度（最多保留20轮）
        if len(sessions[session_id]) > 40:
            sessions[session_id] = sessions[session_id][-40:]
        
        return ChatResponse(reply=reply, session_id=session_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI调用失败: {str(e)}")

async def stream_response(messages: List[Dict], session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """流式响应生成器"""
    try:
        full_reply = ""
        
        stream = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_reply += content
                # 修改这里：加上 ensure_ascii=False
                yield f"data: {json.dumps({'content': content, 'done': False}, ensure_ascii=False)}\n\n"
        
        # 保存历史
        sessions[session_id].append({"role": "user", "content": user_message})
        sessions[session_id].append({"role": "assistant", "content": full_reply})
        
        if len(sessions[session_id]) > 40:
            sessions[session_id] = sessions[session_id][-40:]
        
        # 修改这里：加上 ensure_ascii=False
        yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'done': True}, ensure_ascii=False)}\n\n"
    """流式响应生成器"""
    try:
        full_reply = ""
        
        stream = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_reply += content
                yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
        
        # 保存历史
        sessions[session_id].append({"role": "user", "content": user_message})
        sessions[session_id].append({"role": "assistant", "content": full_reply})
        
        if len(sessions[session_id]) > 40:
            sessions[session_id] = sessions[session_id][-40:]
        
        yield f"data: {json.dumps({'content': content, 'done': False}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话历史"""
    if session_id in sessions:
        sessions[session_id] = []
        return {"status": "cleared", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/")
async def root(request: Request):
    """根路径"""
    return {
        "message": "AI 聊天 API 已启动",
        "version": "1.0",
        "docs": "/docs",
        "endpoints": [
            "GET /new_session - 创建新会话",
            "POST /chat - 发送消息（支持 stream 参数）",
            "DELETE /session/{session_id} - 清除会话历史"
        ]
    }