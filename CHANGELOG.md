# Changelog

## 0.1.0 - 2026-08-14

### Added

- 新增 `query_video` 对话式视频搜索工具；主模型可反复向管理员选择的已有视频能力模型卡提问。
- 同一次 AstrBot event / Agent run 中，同一 `provider_id + video_index` 保留原始成功 Q/A，并通过 AstrBot 原生 `contexts` 回放给视频模型。
- 后续查询可自然使用“它 / 之前 / 刚才那个”等指代；历史不摘要、不改写，不同视频/Provider 隔离，event 结束后自然失效。
- 支持当前消息多个视频与 `Reply.chain` 引用视频；`time_range` 仅作为注意力提示。
- 复用 AstrBot / Provider 已有视频传输，并在同一 event 中复用已解析视频路径。

### Design

- 插件不做视频智能增强。理解深度由用户问题与视频模型自身能力决定。
- 不限制直接观察/因果/综合分析，不自动摘要、不自动分解问题、不替主模型规划下一问。
- 主模型决定问什么、问多深、是否继续；视频模型负责理解视频；插件只维持通道和上下文连续性。

### Verified

- 当前业务 runtime：`d5f4742e114771669a7e969a8eb6e62d3bffa883`。
- AstrBot `v4.27.3` 与验证时 `master`：真实安装、完整 tests、启动和插件加载通过。
- 真实火山方舟模型 `doubao-seed-2-1-pro-260628`：第一问得到 `GAMMA`，第二问只用指代且不重述 `GAMMA`，视频模型通过此前 Q/A contexts 返回 `BETA`。
- 真实 AstrBot `ToolLoopAgentRunner` 中，主模型自主产生上述依赖视频模型记忆的第二问，最终回答 `REFERENT=GAMMA; BEFORE=BETA`。
- 最终上下文 E2E：run `31735526223`。

### Scope

- 不包含永久视频会话数据库、自动理解增强、OCR/STT/抽帧降级、独立 Agent Loop 或供应商专属 SDK。
- 当前真实 Provider E2E 只覆盖火山方舟，其他 Provider 需要独立运行证据。
