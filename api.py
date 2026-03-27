from fastapi import FastAPI
from pydantic import BaseModel
import openai

# 创建 FastAPI 应用
app = FastAPI()

# 配置阿里云百炼
api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"  # 替换成你的真实 Key

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 定义请求的数据格式
class ChatRequest(BaseModel):
    message: str

# 定义响应的数据格式
class ChatResponse(BaseModel):
    reply: str

# 创建 API 接口
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[
            {"role": "user", "content": request.message}
        ]
    )
    reply = response.choices[0].message.content
    return ChatResponse(reply=reply)

# 根路径，测试用
@app.get("/")
def root():
    return {"message": "AI API 服务已启动"}