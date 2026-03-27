from fastapi import FastAPI
from pydantic import BaseModel
import openai

app = FastAPI(title="翻译 API", version="1.0")

# 配置阿里云百炼
api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"  # 你的 API Key

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 定义请求格式
class TranslateRequest(BaseModel):
    text: str          # 要翻译的文本
    target_lang: str   # 目标语言，如 "英文"、"日文"、"法文"

# 定义响应格式
class TranslateResponse(BaseModel):
    original: str
    translated: str
    target_lang: str
    usage: dict  # 新增：存储 token 用量

@app.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    # 构建 Prompt
    prompt = f"请将以下文本翻译成{req.target_lang}，只返回翻译结果，不要加任何解释：\n{req.text}"
    
    # 调用 AI
    response = client.chat.completions.create(
        model="qwen-turbo",
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
        usage=usage_info  # 新增
    )

@app.get("/")
def root():
    return {"message": "翻译 API 已启动"}