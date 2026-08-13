# Changelog

## 0.1.0 - 2026-08-13

### Added

- 新增 `query_video` 视频语义搜索工具；主模型可围绕当前问题反复查询同一个视频，而不是依赖一次性通用摘要。
- 支持当前消息中的多个视频，按出现顺序使用 `video_index` 编号。
- 支持 `Reply.chain` 中的引用视频；当前消息视频优先于引用视频。
- 新增 `time_range` 可选参数，用于让主模型聚焦特定视频区间。
- 新增 AstrBot 宿主视频传输适配层：当前 v4.27.x 使用可信 `Video Attachment` 内容形态，未来宿主提供原生 `ProviderRequest.video_urls` 时可切换到统一字段。
- 视频查询结果明确标记为证据材料，视频中的字幕、对白、代码和命令不提升为主模型指令。
- 对无视频、索引越界、视频解析失败、Provider 调用失败、空响应和视频未实际到达模型等情况实行失败封闭。

### Verified

- AstrBot `v4.27.3` 真实安装、pytest、启动和插件加载通过。
- 验证时 AstrBot `master` 真实安装、pytest、启动和插件加载通过。
- 真实火山方舟视频链路中，同一个 6 秒视频两次查询分别正确返回 `ALPHA` 与 `BETA`。
- AstrBot `ToolLoopAgentRunner` 真实驱动主模型先后发出两个不同的 `query_video` 查询，并最终输出 `FIRST=ALPHA; SECOND=BETA`。

### Scope

- 0.1.0 不包含跨后续消息的永久视频资产绑定、长视频自动分段、OCR/STT/抽帧降级、独立 Agent 循环或供应商专属 SDK。
- 当前真实端到端 Provider 验证覆盖火山方舟；其他视频 Provider 需要各自运行证据，不能从该结果外推。
