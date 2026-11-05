# Cherry Studio / NextChat / 任意 OpenAI 兼容客户端配置

在「添加模型服务 → OpenAI 提供商」里按下表填，API 密钥填你自己申请的 Key：

| 平台 | 接口地址 (Base URL) | 模型名（示例） | 密钥环境变量 |
|---|---|---|---|
| Groq | https://api.groq.com/openai/v1 | qwen/qwen3.8-27b | GROQ_API_KEY |
| Google Gemini | https://generativelanguage.googleapis.com/v1beta/openai | gemini-flash-lite-latest | GEMINI_API_KEY |
| NVIDIA NIM | https://integrate.api.nvidia.com/v1 | nvidia/nemotron-3.5-bolt-e4b | NVIDIA_API_KEY |
| OpenRouter | https://openrouter.ai/api/v1 | cohere/north-mini-code:free | OPENROUTER_API_KEY |

填好后点「检查」，连通即可聊。多个平台各加一个服务商，某个限流就手动切另一个。
