# 免费大模型 OpenAI 兼容调用示例（pip install openai）
# Key 从环境变量读，不要硬编码
import os
from openai import OpenAI

# 例1：Groq（最快，免手机注册）
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
)
r = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[{"role": "user", "content": "你好"}],
)
print(r.choices[0].message.content)

# 例2：Google Gemini（额度最大，OpenAI 兼容端点）
gem = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    api_key=os.environ["GEMINI_API_KEY"],
)
print(gem.chat.completions.create(
    model="gemini-flash-lite-latest",
    messages=[{"role": "user", "content": "你好"}]
).choices[0].message.content)

# 例3：NVIDIA NIM（45 个免费端点）
nv = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"],
)
print(nv.chat.completions.create(
    model="nvidia/nemotron-3.5-bolt-e4b",
    messages=[{"role": "user", "content": "你好"}]
).choices[0].message.content)
