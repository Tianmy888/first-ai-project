from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, AsyncGenerator
import openai
import uuid
import json

app = FastAPI(title="AI 聊天 API - 支持流式输出")

# 配置 API（同上）
api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"
client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

sessions: Dict[str, List[Dict[str, str]]] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = False  # 是否使用流式输出

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.post("/chat")
async def chat(request: ChatRequest):
    # 获取会话（同之前的代码）
    session_id = request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    
    messages = [{"role": "system", "content": "你是一个友好的AI助手，回答要简洁、有帮助。"}]
    for msg in sessions[session_id]:
        messages.append(msg)
    messages.append({"role": "user", "content": request.message})
    
    # 如果是流式输出
    if request.stream:
        return StreamingResponse(
            stream_response(client, messages, session_id, request.message),
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
        reply = response.choices[0].message.content
        
        sessions[session_id].append({"role": "user", "content": request.message})
        sessions[session_id].append({"role": "assistant", "content": reply})
        
        return ChatResponse(reply=reply, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 流式响应生成器
async def stream_response(client, messages, session_id, user_message):
    try:
        # 存储完整回复
        full_reply = ""
        
        # 调用流式API
        stream = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            stream=True  # 开启流式
        )
        
        # 逐块返回
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_reply += content
                # 以 SSE 格式发送
                yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
        
        # 保存历史
        sessions[session_id].append({"role": "user", "content": user_message})
        sessions[session_id].append({"role": "assistant", "content": full_reply})
        
        # 发送完成信号
        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

# 其他接口（new_session, clear_session, root）同之前