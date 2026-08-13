# 设计证据索引

基线：AstrBot v4.27.3 / 2026-08-13。

本文件只记录决定插件架构所需的上游事实，不把运行假设写成已证实事实。

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

## 未闭合证据：CALL-SEAM-01

仍需从实际可用的视频模型卡链路中记录：

> 插件通过哪一个 AstrBot 已有公开调用入口，以什么现有参数或内容块形式，把 `Video` 与一次自然语言查询交给已选视频模型卡。

这不是在验证模型是否支持视频，而是在确认插件应复用的现有调用缝。

见：`RUNTIME_PROOF.md`。

## 禁止把以下内容误写成证据

- “所有 Provider 都支持统一 `video_urls` 参数”；
- “Gemini Provider 当前公开 Python 接口一定以某个固定字段接收视频”；
- “所有视频模型都支持时间范围参数”；
- “视频上传一定由插件完成”。

这些只有在实际调用链或正式公开契约中得到确认后才能进入实现。
