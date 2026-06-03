# Start LLM

大语言模型服务启动仓库，基于 vllm 提供 OpenAI 兼容 API。

## 技术栈

- Python 3.11
- [vllm](https://github.com/vllm-project/vllm) - 高性能 LLM 推理引擎
- [openai_router](https://github.com/shell-nlp/openai_router) - OpenAI API 路由/负载均衡服务
- Docker & Docker Compose
- OpenAI Python SDK

## 接手文档

- `docs/llm-start-项目全局梳理.md`：面向新接手同学的全局梳理、启动链路和运维注意事项
- `docs/最小化测试部署说明.md`：单模型 + 单路由的最小化安装测试说明

## 目录结构

```
.
├── docker-compose.yml              # 主配置：启动 vllm 模型服务
├── docker-compose-gpt-server.yml   # 启动 gpt_server 统一网关
├── docker-compose-openai-router.yml # 启动 openai-router 路由服务
├── gpt-server-config.yaml          # gpt_server 配置文件
├── pyproject.toml                  # Python 项目依赖
├── .python-version                 # Python 版本 (3.11)
├── AGENTS.md                       # 项目规范文档
├── assets/                         # 静态资源
│   ├── logo.png                    # 项目 logo
│   └── audio_data/                 # 音频数据（用于 TTS 角色参考）
│       └── roles/
│           ├── 新闻联播女声/        # 播音员角色音频
│           └── 余承东/              # 演示角色音频
├── tests/                          # API 测试脚本
│   ├── test_openai_chat.py         # 聊天补全测试
│   ├── test_openai_completion.py   # 文本补全测试
│   ├── test_openai_embedding.py    # Embedding 测试
│   ├── test_openai_embedding_vl.py  # 多模态 Embedding 测试
│   ├── test_openai_vl_chat.py      # 视觉语言聊天测试
│   ├── test_openai_tts_stream.py   # TTS 流式测试
│   ├── test_openai_transcriptions.py # 语音转文字测试
│   ├── test_openai_moderation.py   # 内容审核测试
│   ├── test_openai_completion_tool_calling.py # 工具调用测试
│   ├── test_openai_completion_response_format.py # 响应格式测试
│   ├── test_image_gen.py           # 图像生成测试
│   ├── test_image_edit.py          # 图像编辑测试
│   ├── test_rerank.py              # 重排序测试
│   ├── test_mteb.py                # MTEB 基准测试
│   ├── test_needle_haystack.py     # RAG 针尖测试
│   ├── test_perf.py                # 性能测试
│   ├── download_model.py           # 模型下载脚本
│   └── responses_api/              # Responses API 测试
│       ├── test_openai_responses.py
│       ├── test_openai_responses_tool_calling.py
│       ├── test_openai_responses_response_format.py
│       └── test_response_vl_chat.py
└── .gitignore                      # Git 忽略文件
```

## 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                      openai-router (8082)                    │
│                   OpenAI API 路由/负载均衡                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  qwen3.5      │    │ qwen3-embedding│  │ bge-reranker  │
│  (GPU 0)      │    │ (GPU 3)        │  │ (GPU 3)       │
│  :40000       │    │ :40001         │  │ :40003        │
└───────────────┘    └───────────────┘    └───────────────┘
```

## 模型配置

### docker-compose.yml

| 服务 | 模型 | 端口 | GPU | 说明 |
|------|------|------|-----|------|
| qwen3.5 | Qwen3-6-35B-A3B | 40000 | 0 | 聊天模型，支持 thinking/工具调用 |
| qwen3-embedding | Qwen3-Embedding-0-6B | 40001 | 3 | Embedding 模型 |
| Conan-embedding-v1 | Conan-embedding-v1 | 40004 | 3 | 另一个 Embedding 模型 |
| bge-reranker-base | bge-reranker-base | 40003 | 3 | 重排序模型 |

### gpt-server-config.yaml

| 模型类型 | 模型路径 | 说明 |
|----------|----------|------|
| spark_tts | Spark-TTS-0-5B | TTS 语音合成模型 |

## 快速开始

### 启动所有 vllm 模型服务

```bash
docker-compose up -d
```

### 启动 gpt_server 服务部署 tts

```bash
docker-compose -f docker-compose-gpt-server.yml up -d
```

### 启动 openai-router 路由

```bash
docker-compose -f docker-compose-openai-router.yml up -d
```

## API 使用示例

### 聊天补全

```python
from openai import OpenAI

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8082/v1")

response = client.chat.completions.create(
    model="qwen3.5",
    messages=[{"role": "user", "content": "你是谁"}]
)
print(response.choices[0].message.content)
```

### 流式聊天

```python
stream = True
output = client.chat.completions.create(
    model="qwen3.5",
    messages=[{"role": "user", "content": "你是谁"}],
    stream=stream,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}}
)
for chunk in output:
    print(chunk)
```

## 环境要求

- Docker & Docker Compose
- NVIDIA GPU (需安装 nvidia-container-toolkit)
- Python 3.11+
