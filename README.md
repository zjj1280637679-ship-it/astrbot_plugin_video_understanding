# AstrBot 多模态转述桥

> v0.2 development branch: `feat/modality-relay-v0.2`

这个仓库从原来的 `query_video` 视频语义搜索器扩展为 **AstrBot 请求态多模态转述桥**。它不接管群聊环境中的全量媒体归档，只处理已经进入当前 Agent Request 的图片、语音、视频。

## 核心行为

### 两档首报策略

- `adaptive`：仅当当前实际主模型卡没有启用对应 `modalities` 原生输入路径时，调用专用转述模型生成第一次通用首报。
- `always`：当前请求存在该媒体时始终生成首报。

能力未知保持三态：`enabled / disabled / unknown`。`unknown` 默认保守走转述，但不会被写成永久“模型不支持”事实。

### 三个主动查询工具

- `query_image`
- `query_audio`
- `query_video`

第一次首报只是通用观察。主模型通过内置 Skill 判断：

```text
回答当前问题所需的证据
-
已有首报与查询结果已经覆盖的证据
=
仍需补充的信息残差
```

只有残差可能改变最终答案时才调用对应 `query_*`，重新读取原始媒体。

例如：

```text
用户：这只手有几根手指？
首报：图片中是一只张开的手。
残差：手指数未知。
query_image：仔细检查这只手，准确统计所有可见手指。
```

## 与 AstrBot 的边界

AstrBot 继续拥有 Event / Message Chain、Provider / ProviderRequest、媒体基础设施、Tool Manager / Tool Loop、Full / Skills-like 两段式工具调度，以及主模型和 fallback 路由。

本插件只拥有 Request 媒体绑定、`always / adaptive` Relay Gate、通用首报、当前 Agent Run 内查询历史、`query_image / query_audio / query_video` 和 Residual Query Skill。

原则：**深度依赖 AstrBot 的抽象，浅度依赖 AstrBot 的内部实现。**

## 与 AstrBot 原生图片转述 / STT 的关系

如果本插件负责当前请求图片，建议留空：

```text
provider_settings.default_image_caption_provider_id
```

如果本插件负责当前请求音频，建议关闭：

```text
provider_stt_settings.enable
```

AstrBot 预处理 STT 会把 `Record` 替换为 `Plain`，使后续 `query_audio` 无法重新访问原始语音。

`provider_ltm_settings.image_caption` 属于群聊环境历史文本化，不属于本插件职责，可以独立保留。

## 火山方舟双通道

`astrbot_plugin_volcengine_provider` 是受支持的集成对象，但不是本插件运行依赖。

本插件不 import 火山插件、不根据 Provider 品牌或 model ID 猜能力、不复制 Ark 音频/视频传输，只读取 AstrBot 模型卡的 canonical `modalities` 和公共 Provider/媒体契约。

因此火山模型卡开启 `audio` / `video` 时，`adaptive` 会自然保留原生路径；关闭时才进入 Relay。

## Skills-like 两段式工具调用

插件不自行实现两段式 Tool Loop。

在 AstrBot `skills-like` 模式下：

1. 第一阶段只依赖工具名称和 Description，决定是否选择 `query_image / query_audio / query_video`；
2. 第二阶段由 AstrBot 下发所选工具参数 Schema，主模型把残差编译为具体 `query`；
3. 第一次 `<modality_relay>` 通过 `extra_user_content_parts` 注入并应在 re-query 中保留。

工具参数保持最小：

```text
query_image(query, image_index=0)
query_audio(query, audio_index=0, time_range="")
query_video(query, video_index=0, time_range="")
```

## GitHub 验证

仓库内 CI 使用真实 AstrBot Runtime，而不是只做 Mock：

- AstrBot `v4.27.4`
- AstrBot `v4.28.0-beta.1`
- AstrBot `master`（前瞻预警）
- Full / Skills-like Tool Schema 合同
- 未安装火山插件
- 安装火山双通道 `main`

`master` 是兼容雷达，不是发布地基。

详见：

- `docs/ARCHITECTURE_V0.2.md`
- `docs/VERIFICATION_ENVIRONMENT.md`
- `skills/modality-residual-query/SKILL.md`
