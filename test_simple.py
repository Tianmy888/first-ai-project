import openai

api_key = "sk-22f64e3fb1044781bb8daf2ac36afdad"  # 换成你的 Key

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

try:
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": "你好"}]
    )
    print("成功！回复：", response.choices[0].message.content)
except Exception as e:
    print("错误：", e)