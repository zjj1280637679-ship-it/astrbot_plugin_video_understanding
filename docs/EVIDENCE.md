# 设计证据索引

基线：AstrBot v4.27.3 / 2026-08-13。

本文件只记录决定插件架构所需的上游事实，不把运行假设写成已证实事实；同时明确区分“视频消息/模型能力已经存在”与“插件调用视频模型时应复用的统一请求接口是否已经进入当前公开稳定主干”这两个不同问题。

## EVD-01：AstrBot 已有正式 Video 消息组件

AstrBot 核心已经把视频作为正式消息组件处理，并可将视频转换为可用本地路径。

设计含义：插件不得重新实现平台视频下载、路径解析、Base64 解码或文件服务。

证据位置：

- `astrbot/core/message/components.py`
- `astrbot/core/astr_main_agent.py::_append_video_attachment`

## EVD-02：当前消息和引用消息均已有视频附件处理

主 Agent 会遍历当前消息中的 `Video`，也会遍历 `Reply.chain` 中的 `Video`。

设计含义：第一版可直接绑定当前视频与引用视频，不解析 QQ/NapCat 原始事件。

证据位置：

- `astrbot/core/astr_main_agent.py::build_main_agent`

## EVD-03：模型元数据已定义 video 模态

`LLMModalities` 的 input/output 支持 `text`、`image`、`audio`、`video`。

设计含义：视频能力属于 AstrBot 现有模型卡/能力体系，本插件不建立独立能力数据库。

证据位置：

- `astrbot/core/utils/llm_metadata.py`

## EVD-04：AstrBot 已有模态能力判断

核心通过 Provider 配置中的 `modalities` 判断输入模态支持情况。

设计含义：插件可复用已有能力元数据决定是否以 fallback 方式暴露工具，但不再次测试被选视频模型卡“能不能看视频”。

证据位置：

- `astrbot/core/astr_main_agent.py::_provider_supports_modality`

## EVD-05：插件可以注册 LLM Tool

AstrBot 官方插件开发接口支持 `FunctionTool` + `add_llm_tools()`，也支持在请求构造阶段动态向 `ToolSet` 加入工具。

设计含义：`query_video` 应是真正的主模型工具，而不是隐藏的预处理钩子。

证据位置：

- `docs/zh/dev/star/guides/ai.md`
- `astrbot/core/astr_main_agent.py`

## EVD-06：AstrBot 已有 Tool Loop

`tool_loop_agent()` 和主 Agent Runner 已经负责“大模型 → 工具 → 工具结果 → 大模型”的循环。

设计含义：多轮视频查询的循环由 AstrBot 承担，本插件不写独立 Agent 编排器。

证据位置：

- `astrbot/core/star/context.py::tool_loop_agent`
- `astrbot/core/agent/runners/tool_loop_agent_runner.py`

## EVD-07：插件配置可以选择已有 Provider

`_conf_schema.json` 支持 `_special: "select_provider"`。

设计含义：插件只保存视频搜索模型卡 ID，不保存供应商 API Key、Base URL 或供应商类型。

证据位置：

- `docs/zh/dev/star/guides/plugin-config.md`

## EVD-08：图片 Caption 是反例而非直接模板

AstrBot 图片转述当前属于一次性 Caption：选专用 Provider → 描述图片 → 注入 `<image_caption>`。

设计含义：视频插件可以借鉴模型卡选择和错误边界，但不能复制“一次性预描述”的核心行为。

证据位置：

- `astrbot/core/astr_main_agent.py::_request_img_caption`
- `astrbot/core/astr_main_agent.py::_ensure_img_caption`

## EVD-09：上游已经提出统一的视频请求接口 `video_urls`

AstrBot PR #9424（`feat: wire up video input modality for MiniMax providers`）明确指出，在该 PR 所针对的公开主干状态下，`Video` 附件虽然已经被 AstrBot 识别，但主 Agent 只向模型请求留下文字占位，并没有把视频模态实际送入对应 Provider；该 PR 因此新增了统一的视频输入链：

```text
Video
→ convert_to_file_path()
→ ProviderRequest.video_urls
→ assemble_context()
→ video_url content block
→ Provider
```

同时新增：

- `ProviderRequest.video_urls`；
- `VideoURLPart`；
- `video_url` 内容块；
- Tool Loop 的 video 模态保留/降级逻辑；
- OpenAI-compatible Provider 的 `video_urls` 参数与媒体物化；
- Anthropic Provider 的 `video_url` → `video` 转换；
- 对应 `tests/test_video_input_modality.py` 回归测试。

设计含义：`video_urls=[video_path]` 是目前最有直接上游证据支持、并且与 `image_urls` / `audio_urls` 同构的统一插件调用缝候选；本插件不应自行发明另一套视频参数命名。

证据位置：

- AstrBot PR #9424
- `tests/test_video_input_modality.py`（PR 分支）

## EVD-10：PR #9424 截至 2026-08-13 仍未合并，且没有修改 Gemini Provider

截至本证据记录日期，PR #9424 状态为 `open`、`merged=false`。其变更文件覆盖通用请求实体、主 Agent、Tool Loop、OpenAI-compatible Provider 与 Anthropic Provider，但不包含 `astrbot/core/provider/sources/gemini_source.py`，也不修改插件侧 `Context.llm_generate()` 的显式参数列表。

设计含义：

1. 可以把 `video_urls` 记录为**上游正在收敛的公共契约候选**；
2. 不能把“当前公开稳定版的所有 Provider 都已经消费 `video_urls`”写成事实；
3. 更不能据此否定某个实际运行环境中的 Google/Gemini 模型卡已经具备视频读取能力——那属于运行环境/Provider 实现事实；
4. 在为本插件正式接入某张视频模型卡之前，只需要确认该运行环境怎样把已有 Video 传入该卡，而不需要重新验证模型理论能力。

## CALL-SEAM-01：已从“未知接口”缩小为“统一候选 + 运行确认”

现在已经有两层结论：

### 已确认的上游候选

```python
video_path = await video.convert_to_file_path()

response = await context.llm_generate(
    chat_provider_id=video_search_provider_id,
    prompt=query_prompt,
    video_urls=[video_path],
)
```

其中 `Context.llm_generate()` 本身会把未显式列出的 `**kwargs` 继续传给目标 Provider，因此当运行环境中的 Provider 已实现 `video_urls` 时，插件无需感知供应商类型即可复用该契约。

### 仍需运行确认的部分

需要在实际部署环境确认：管理员准备选择的视频模型卡（例如某张 Google/Gemini 视频模型卡）是否已经通过 `video_urls`，或通过当前 AstrBot 版本提供的等价统一入口，消费同一个 Video。

该确认只验证**调用缝**，不是重新验证模型能力。

见：`RUNTIME_PROOF.md`。

## 禁止把以下内容误写成证据

- “PR #9424 已经进入当前公开稳定主干”；
- “所有 Provider 都已经支持统一 `video_urls` 参数”；
- “Gemini Provider 当前公开主干已经按 #9424 的 `video_urls` 实现接收视频”；
- “所有视频模型都支持时间范围参数”；
- “视频上传一定由插件完成”。

这些只有在实际运行链或正式合并后的公开契约中得到确认后才能进入实现。
