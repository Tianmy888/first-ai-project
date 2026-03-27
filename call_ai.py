import openai

# 替换成你的阿里云百炼 API Key
api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-turbo",  # 免费模型，足够用
    messages=[
        {"role": "user", "content": "请用一句话介绍你自己"}
    ]
)

print(response.choices[0].message.content)