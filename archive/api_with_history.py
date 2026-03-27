from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import openai
import uuid

app = FastAPI(title="AI 聊天 API", description="支持多轮对话的AI服务", version="2.0")

# 配置阿里云百炼
api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"  # 替换成你的真实 Key

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 存储会话历史（生产环境应该用 Redis）
sessions: Dict[str, List[Dict[str, str]]] = {}

# 定义请求格式
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # 可选，不传就创建新会话

class ChatResponse(BaseModel):
    reply: str
    session_id: str  # 返回会话ID，前端保存

# 创建新会话
@app.get("/new_session")
def new_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return {"session_id": session_id}

# 对话接口（支持历史）
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # 获取或创建会话
    session_id = request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    
    # 构建消息历史
    messages = []
    
    # 添加系统提示（可选）
    messages.append({
        "role": "system", 
        "content": "你是一个友好的AI助手，回答要简洁、有帮助。"
    })
    
    # 添加历史消息
    for msg in sessions[session_id]:
        messages.append(msg)
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": request.message})
    
    # 调用AI
    try:
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        reply = response.choices[0].message.content
        
        # 保存历史
        sessions[session_id].append({"role": "user", "content": request.message})
        sessions[session_id].append({"role": "assistant", "content": reply})
        
        # 限制历史长度（最多保留20轮）
        if len(sessions[session_id]) > 40:
            sessions[session_id] = sessions[session_id][-40:]
        
        return ChatResponse(reply=reply, session_id=session_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 清除会话历史
@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    if session_id in sessions:
        sessions[session_id] = []
        return {"status": "cleared"}
    raise HTTPException(status_code=404, detail="Session not found")

# 根路径
@app.get("/")
def root():
    return {
        "message": "AI 聊天 API 已启动",
        "docs": "/docs",
        "endpoints": [
            "GET /new_session - 创建新会话",
            "POST /chat - 发送消息",
            "DELETE /session/{session_id} - 清除会话历史"
        ]
    }