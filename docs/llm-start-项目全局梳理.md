# llm-start 项目全局梳理

## 1. 先用一句话理解这个仓库

这个仓库本质上不是“业务应用代码仓库”，而是一个 **大模型服务部署与联调仓库**。  
它的核心作用是把几类模型服务启动起来，再通过统一的 OpenAI 兼容接口暴露给上层系统使用。

从当前仓库内容看，主线是这 3 层：

1. `vllm`：承载聊天、Embedding、Rerank 等模型。
2. `gpt_server`：承载 TTS 这类不直接走当前 `vllm` 编排的能力。
3. `openai-router`：把多个后端模型聚合成一个统一入口，方便上层只对接一个 API 地址。

如果你刚接手，这个项目最重要的认知不是“从哪写业务代码”，而是：

- 哪些模型服务已经部署。
- 统一入口在哪。
- 模型名最终会路由到哪个后端地址。
- 当前哪些能力是仓库内自包含的，哪些能力依赖外部环境。

## 2. 当前仓库的整体架构

### 2.1 逻辑链路

```text
客户端 / 上层应用
        |
        v
openai-router  :8082
        |
        +-----------------> qwen3.5               :40000
        |
        +-----------------> qwen3-embedding       :40001
        |
        +-----------------> bge-reranker-base     :40003
        |
        +-----------------> Conan-embedding-v1    :40004
        |
        +-----------------> gpt_server(tts)       :28082
```

### 2.2 你应该怎么理解它

- `docker-compose.yml` 负责起多个 `vllm` 容器。
- `docker-compose-gpt-server.yml` 负责起 `gpt_server`，目前主要用于 `tts`。
- `docker-compose-openai-router.yml` 负责起统一路由层 `openai-router`。
- `data/routes.db` 是路由层的持久化状态，里面保存了模型路由和别名。

也就是说，**真正决定“请求发到哪里”的，不只是一份 compose 文件，还有 `data/routes.db` 里的映射关系。**

## 3. 仓库结构与职责

### 3.1 关键文件

| 路径 | 作用 | 你接手时重点关注什么 |
|---|---|---|
| `README.md` | 项目简要说明 | 可快速了解目标，但信息比实际环境更理想化 |
| `docker-compose.yml` | 主模型服务编排 | 聊天、Embedding、Rerank 模型怎么起、占哪张 GPU、暴露什么端口 |
| `docker-compose-gpt-server.yml` | `gpt_server` 编排 | TTS 服务如何启动 |
| `docker-compose-openai-router.yml` | `openai-router` 编排 | 统一 API 入口如何暴露 |
| `gpt-server-config.yaml` | `gpt_server` 配置 | TTS 模型路径、控制器地址、工作 GPU |
| `data/routes.db` | 路由数据库 | 模型名、别名、后端 URL 的真实映射 |
| `tests/` | 联调脚本集合 | 这些更像“接口样例/冒烟脚本”，不是严格 CI 测试 |
| `assets/` | 静态资源 | TTS 参考音频、图片样例等 |
| `pyproject.toml` | Python 依赖 | 仓库几乎不含应用代码，依赖主要给测试与压测脚本使用 |

### 3.2 当前不是重点的部分

- 这个仓库里几乎没有完整的后端业务代码。
- 也没有完整的前端项目代码。
- 所以它更像是“模型服务启动仓库 + 联调样例仓库”。

## 4. 当前部署了什么能力

### 4.1 `vllm` 主服务

来自 [docker-compose.yml](/home/dev/bxc/start_llm/docker-compose.yml)：

| 服务名 | 对外端口 | GPU | 模型路径 | 主要能力 |
|---|---|---:|---|---|
| `qwen3.5` | `40000` | `0` | `/home/dev/model/Qwen/Qwen3___6-35B-A3B/` | 聊天、推理、工具调用 |
| `qwen2.5-0.5b-instruct` | `40002` | `3` | `/home/dev/model/Qwen/Qwen2.5-0.5B-Instruct/` | 轻量聊天、最小化测试 |
| `qwen3-embedding` | `40001` | `3` | `/home/dev/model/Qwen/Qwen3-Embedding-0___6B/` | Embedding |
| `Conan-embedding-v1` | `40004` | `3` | `/home/dev/model/TencentBAC/Conan-embedding-v1/` | Embedding |
| `bge-reranker-base` | `40003` | `3` | `/home/dev/model/Xorbits/bge-reranker-base/` | Rerank |

`qwen3.5` 这一项还额外开了这些能力：

- `--reasoning-parser qwen3`
- `--tool-call-parser qwen3_coder`
- `--enable-auto-tool-choice`
- `--default-chat-template-kwargs '{"enable_thinking": false}'`

这说明它不是单纯聊天模型，而是被当作带推理和工具调用能力的统一大模型来用。

### 4.2 `gpt_server` 服务

来自 [docker-compose-gpt-server.yml](/home/dev/bxc/start_llm/docker-compose-gpt-server.yml) 和 [gpt-server-config.yaml](/home/dev/bxc/start_llm/gpt-server-config.yaml)：

| 服务名 | 对外端口 | 模型 | GPU | 主要能力 |
|---|---|---|---:|---|
| `gpt_server` | `28082` / `21001` | `Spark-TTS-0.5B` | `2` | TTS |

其中：

- `8082` 是 `gpt_server` 内部 API 端口，映射到宿主机 `28082`
- `21001` 是 controller 端口
- 配置里 `model_type: spark_tts`

### 4.3 `openai-router` 统一入口

来自 [docker-compose-openai-router.yml](/home/dev/bxc/start_llm/docker-compose-openai-router.yml)：

- 服务名：`openai-router`
- 对外端口：`8082`
- 数据目录：`./data:/app/data`

它的作用是把上面的多个模型服务汇总成一个统一入口，供客户端使用：

```text
http://<host>:8082/v1
```

## 5. 路由层当前的真实模型映射

我直接查看了 [data/routes.db](/home/dev/bxc/start_llm/data/routes.db) 里的内容，当前有效路由如下：

| 模型名 | 实际后端 |
|---|---|
| `bge-reranker-base` | `http://192.168.102.19:40003` |
| `Conan-embedding-v1` | `http://192.168.102.19:40004` |
| `qwen3-embedding` | `http://192.168.102.19:40001` |
| `qwen3.5` | `http://192.168.102.19:40000` |
| `tts` | `http://192.168.102.19:28082` |

当前别名如下：

| 别名 | 实际模型 |
|---|---|
| `qwq` | `qwen3.5` |
| `qwen` | `qwen3.5` |
| `qwen32b` | `qwen3.5` |
| `qwen3` | `qwen3.5` |
| `text-embedding-ada-003` | `qwen3-embedding` |

这部分非常重要，因为它解释了为什么有些脚本写的是 `model="qwq"`，但实际跑的是 `qwen3.5`。

## 6. 启动顺序与运行方式

### 6.1 环境前提

你在接手前至少要确认这几件事：

1. 机器装了 NVIDIA 驱动和容器运行环境。
2. 宿主机存在 `/home/dev/model/`，并且模型已经下载好。
3. 端口 `40000`、`40001`、`40003`、`40004`、`8082`、`28082`、`21001` 没被占用。
4. 当前宿主机 IP 是否还是 `192.168.102.19`。

### 6.2 推荐启动顺序

```bash
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose-gpt-server.yml up -d
docker-compose -f docker-compose-openai-router.yml up -d
```

### 6.3 为什么按这个顺序

- 先起模型后端，否则路由层启动后可能找不到后端。
- `tts` 走的是 `gpt_server`，它不在主 `vllm` compose 里。
- `openai-router` 最后起，便于它接管完整的后端集合。

### 6.4 我已经做过的校验

我用下面的命令做过 compose 配置语法校验，三份文件都能正常解析：

```bash
docker-compose -f docker-compose.yml config
docker-compose -f docker-compose-gpt-server.yml config
docker-compose -f docker-compose-openai-router.yml config
```

## 7. 测试脚本应该怎么理解

### 7.1 它们更像“样例脚本”而不是“自动化测试”

当前 `tests/` 下的大多数文件特点是：

- 直接 `python xxx.py` 运行。
- 没有统一测试框架组织。
- 部分脚本依赖人工观察输出。
- 部分脚本带硬编码地址和模型名。
- 个别脚本甚至有刻意中断逻辑，例如 `tests/test_openai_embedding.py` 里存在 `assert 0`。

所以你不要把它们当成“这个仓库已经有完善测试体系”，更准确的理解是：

**这是服务联调脚本集合。**

### 7.2 已覆盖的能力类别

| 类别 | 代表脚本 |
|---|---|
| Chat Completions | `tests/test_openai_chat.py` |
| Completion Tool Calling | `tests/test_openai_completion_tool_calling.py` |
| Embedding | `tests/test_openai_embedding.py` |
| Rerank | `tests/test_rerank.py` |
| TTS | `tests/test_openai_tts_stream.py` |
| ASR / Transcriptions | `tests/test_openai_transcriptions.py` |
| Responses API | `tests/responses_api/test_openai_responses.py` |
| 图片生成 | `tests/test_image_gen.py` |
| 多模态 VL | `tests/test_openai_vl_chat.py` |
| 压测 | `tests/test_perf.py` |

### 7.3 当前脚本存在的入口不一致问题

仓库里出现了多套不同的地址：

- `http://localhost:8082/v1`
- `http://192.168.102.19:8082/v1`
- `http://localhost:28000/v1`
- `http://localhost:58082/v1`

这说明：

1. 当前仓库保存的是某个历史环境的联调痕迹。
2. 不是所有脚本都能直接在当前环境运行。
3. 接手后第一件事之一，就是统一这些脚本的目标地址和模型名。

## 8. 当前仓库“已自包含”和“依赖外部环境”的边界

### 8.1 仓库内相对自包含的能力

从 compose 和路由库看，这几项是当前仓库最明确、最完整的主线：

- `qwen3.5` 聊天
- `qwen3-embedding`
- `Conan-embedding-v1`
- `bge-reranker-base`
- `tts`

### 8.2 明显依赖外部环境或缺少本仓库定义的能力

这些能力在测试脚本中出现了，但当前仓库并没有完整给出对应部署：

- `Responses API` 使用了 `http://localhost:58082/v1`
- `VL` 脚本使用了 `http://localhost:28000/v1`
- 图片生成脚本使用了 `model="z_image"`
- 审核脚本使用了 `model="injection"`
- 语音识别脚本使用了 `model="asr"`
- 多模态 Embedding 脚本中出现了 `bge-vl`

这意味着你在接手时不能默认这些能力已经由当前仓库完整托管。  
更合理的判断是：**这套仓库是更大部署环境中的一个子集。**

## 9. 作为初级开发/运维，建议你先掌握这 5 件事

### 9.1 先把“OpenAI 兼容接口”概念吃透

你需要知道这些接口大致对应什么：

- `/v1/chat/completions`
- `/v1/embeddings`
- `/v1/audio/speech`
- `/v1/audio/transcriptions`
- `/v1/rerank`
- `/v1/responses`

因为这个项目几乎所有能力，都是围绕“对外伪装成 OpenAI 风格 API”来组织的。

### 9.2 理解模型服务和路由服务的区别

- `vllm` / `gpt_server`：真正执行推理的后端。
- `openai-router`：面向上层的统一入口。

如果上层报错，你要先判断问题是在：

- 模型容器没起来
- 路由没配对
- 模型名写错
- 目标地址写错

### 9.3 学会从 3 个地方排查问题

1. compose 文件：看服务应该怎么起。
2. `data/routes.db`：看模型实际被路由到哪。
3. 测试脚本：看调用方期望怎么使用。

### 9.4 学会区分“直连模型端口”和“走统一网关”

当前环境里至少有两类访问方式：

- 直连模型，例如 `40000`
- 走统一入口，例如 `8082`

一般来说：

- 联调单模型问题，优先直连。
- 给业务系统接入，优先走统一入口。

### 9.5 对硬编码保持警惕

这个仓库当前最明显的运维风险之一就是硬编码较多：

- 模型目录硬编码为 `/home/dev/model/`
- 测试脚本里硬编码 IP
- 路由库里硬编码 IP
- 个别脚本里硬编码本地文件路径

只要换机器、换目录、换 IP，这些点都可能出问题。

## 10. 你接手后的第一周建议

### 10.1 第 1 天

先做静态确认：

1. 确认宿主机 GPU 情况。
2. 确认 `/home/dev/model/` 下模型是否齐全。
3. 确认当前真实 IP。
4. 确认三份 compose 文件能否成功启动。

### 10.2 第 2 到 3 天

先打通主链路：

1. 直连 `qwen3.5` 验证聊天接口。
2. 通过 `openai-router:8082` 再验证一次聊天接口。
3. 验证 Embedding。
4. 验证 Rerank。
5. 验证 TTS。

### 10.3 第 4 到 5 天

开始做治理：

1. 统一 `tests/` 中的 `base_url` 配置方式。
2. 把硬编码 IP 改成环境变量或集中配置。
3. 把“样例脚本”和“真正测试脚本”分开。
4. 补一份服务启动后的健康检查文档。

## 11. 当前我认为最值得优先补齐的地方

如果后面你要继续维护这个仓库，我建议优先做这几件事：

1. 把 `tests/` 改成可配置的脚本，至少统一 `BASE_URL`。
2. 给 `data/routes.db` 的初始化方式补文档，避免大家手改 SQLite。
3. 在仓库里补一份“哪些能力已部署，哪些能力依赖外部环境”的清单。
4. 给每个模型能力补一条最小可运行的验证命令。
5. 如果这是长期项目，建议补监控、日志查看和故障排查手册。

## 12. 一个适合你现在的理解框架

你可以先把这个项目记成下面这句话：

> 这是一个把多个大模型服务封装成统一 OpenAI 接口的部署仓库，`compose` 负责拉起服务，`routes.db` 负责模型路由，`tests/` 负责联调验证。

只要你先把这句话吃透，后面再看每个模型、每个端口、每个脚本，就不会乱。

## 13. 附：常用命令

### 13.1 安装 Python 依赖

```bash
uv sync
```

### 13.2 启动服务

```bash
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose-gpt-server.yml up -d
docker-compose -f docker-compose-openai-router.yml up -d
```

### 13.3 查看路由库中的模型映射

```bash
sqlite3 data/routes.db 'select id, model_name, model_url from modelroute order by id;'
sqlite3 data/routes.db 'select alias_name, model_name from modelalias order by id;'
```

### 13.4 运行一个最基本的聊天脚本

```bash
uv run python tests/test_openai_chat.py
```

运行前记得先确认脚本里的 `base_url` 是否符合当前机器环境。
