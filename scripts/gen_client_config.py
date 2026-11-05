#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_client_config.py — 一键生成常见客户端的免费模型接入配置
读 keys.env（自己的 Key），输出：
  - clients/openai_sdk.example.py   任意 OpenAI 兼容 SDK 调用示例
  - clients/cherry_studio.md        Cherry Studio / NextChat 手动配置说明
  - clients/litellm.example.yaml    自建聚合网关配置（429 自动切换）
Key 不写进示例文件，全部用环境变量占位，可安全提交。
"""
import os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "clients")
os.makedirs(OUT, exist_ok=True)

def load_env():
    env = {}
    p = os.path.join(BASE, "keys.env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

env = load_env()
have = [k for k in ("GROQ_API_KEY","GEMINI_API_KEY","NVIDIA_API_KEY","OPENROUTER_API_KEY","CF_API_TOKEN") if env.get(k)]

# 1) OpenAI SDK 示例
sdk = '''# 免费大模型 OpenAI 兼容调用示例（pip install openai）
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
'''
open(os.path.join(OUT, "openai_sdk.example.py"), "w").write(sdk)

# 2) Cherry Studio 说明
cherry = '''# Cherry Studio / NextChat / 任意 OpenAI 兼容客户端配置

在「添加模型服务 → OpenAI 提供商」里按下表填，API 密钥填你自己申请的 Key：

| 平台 | 接口地址 (Base URL) | 模型名（示例） | 密钥环境变量 |
|---|---|---|---|
| Groq | https://api.groq.com/openai/v1 | qwen/qwen3.8-27b | GROQ_API_KEY |
| Google Gemini | https://generativelanguage.googleapis.com/v1beta/openai | gemini-flash-lite-latest | GEMINI_API_KEY |
| NVIDIA NIM | https://integrate.api.nvidia.com/v1 | nvidia/nemotron-3.5-bolt-e4b | NVIDIA_API_KEY |
| OpenRouter | https://openrouter.ai/api/v1 | cohere/north-mini-code:free | OPENROUTER_API_KEY |

填好后点「检查」，连通即可聊。多个平台各加一个服务商，某个限流就手动切另一个。
'''
open(os.path.join(OUT, "cherry_studio.md"), "w").write(cherry)

# 3) LiteLLM 聚合网关示例（自动故障转移）
litellm = '''# 一键自建免费聚合网关：pip install 'litellm[proxy]'
# litellm --config litellm.example.yaml --port 4199
# 之后所有客户端统一连 http://127.0.0.1:4199，模型名 free-chat，某家挂了自动切下一家
model_list:
  - model_name: free-chat
    litellm_params:
      model: openai/gemini-flash-lite-latest
      api_base: https://generativelanguage.googleapis.com/v1beta/openai
      api_key: os.environ/GEMINI_API_KEY
  - model_name: free-chat
    litellm_params:
      model: groq/qwen/qwen3.8-27b
      api_key: os.environ/GROQ_API_KEY
  - model_name: free-chat
    litellm_params:
      model: openai/nvidia/nemotron-3.5-bolt-e4b
      api_base: https://integrate.api.nvidia.com/v1
      api_key: os.environ/NVIDIA_API_KEY
  - model_name: free-chat
    litellm_params:
      model: openrouter/cohere/north-mini-code:free
      api_key: os.environ/OPENROUTER_API_KEY
litellm_settings:
  drop_params: true
  num_retries: 3
  request_timeout: 30
router_settings:
  routing_strategy: latency-based-routing
  num_retries: 3
  timeout: 30
  allowed_fails: 2
  cooldown_time: 120
general_settings:
  dangerously_permit_weak_or_unset_master_key: true
  disable_spend_logs: true
'''
open(os.path.join(OUT, "litellm.example.yaml"), "w").write(litellm)

print(f"已生成客户端配置到 {OUT}")
print("当前检测到已配置的 Key:", have or "（先运行 bash setup.sh 填 Key）")
