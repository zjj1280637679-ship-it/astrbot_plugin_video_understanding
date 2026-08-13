# 下一阶段设计规划

更新时间：2026-08-13。

当前已经完成两类核心证据：

1. AstrBot `v4.27.3` 与当前 `master` 的真实安装、单测、启动和插件加载均成功；
2. `QueryVideoTool` 通过 AstrBot 当前视频附件信封与火山方舟 Provider，连续两次查询同一个视频，分别正确取得 `ALPHA` 与 `BETA`。

下一阶段不继续扩张功能面，而是把“已经跑通的实验闭环”收束成可发布、可维护、可升级的插件。

## S1：宿主视频传输契约隔离

目标：让 `QueryVideoTool` 只负责“一个查询 → 一个证据结果”，不直接知道 AstrBot 当前或未来如何表示视频输入。

实施：

- 新建 `transport.py`；
- 当前 AstrBot 没有 `ProviderRequest.video_urls` 时，生成 AstrBot 自己的可信 `Video Attachment` 临时内容块；
- 未来宿主提供原生 `video_urls` 时自动切换到原生字段；
- 不出现任何 `provider == google/volcengine/minimax` 分支；
- `tool.py` 不承担供应商协议或媒体转码。

验收：

- v4.27.3 单测通过；
- master 单测通过；
- 火山方舟真实视频 E2E 仍通过。

## S2：真实 AstrBot Tool Loop

目标：证明不是测试脚本直接调用工具，而是 AstrBot 的 `ToolLoopAgentRunner` 驱动主模型完成：

```text
用户任务
→ 主模型调用 query_video(问题 A)
→ 得到证据 A
→ 主模型基于证据 A 再调用 query_video(问题 B)
→ 得到证据 B
→ 主模型最终回答
```

验收证据必须记录：

- 实际工具调用次数 >= 2；
- 两次 `query` 参数不同；
- 第一次命中 `ALPHA`，第二次命中 `BETA`；
- 最终主模型回答包含二者；
- 循环由 AstrBot `ToolLoopAgentRunner` 执行，而非插件自己的 while/for 编排器。

## S3：视频绑定边界

目标：确认搜索空间绑定正确，不把“能读一个当前视频”误当成全部消息结构都成立。

必须覆盖：

1. 当前消息单视频；
2. 当前消息多视频，按出现顺序编号；
3. `Reply.chain` 中的引用视频；
4. 当前视频优先于引用视频；
5. `video_index` 越界失败封闭；
6. 无视频时失败封闭。

第一版不要求跨下一条用户消息永久保存视频对象；那属于独立的会话引用能力。

## S4：发布门禁

发布前必须同时满足：

- `python -m compileall` 通过；
- pytest 通过；
- AstrBot v4.27.3 真实启动加载通过；
- AstrBot master 真实启动加载通过；
- 真 Tool Loop E2E 通过；
- 火山方舟真实视频 E2E 通过；
- README 与 metadata 不再描述成一次性“视频转述”；
- 不含 Google/火山/MiniMax SDK；
- 不含 ffmpeg/OCR/STT 业务实现；
- 不建立独立 Agent Loop、视频数据库或供应商路由器。

## 暂不进入第一版的能力

- 跨轮永久视频资产绑定；
- 视频语义索引库；
- 自动分段长视频；
- OCR/STT/抽帧降级；
- Provider 自动探测和自动切换；
- 多视频联合推理专用编排器。

这些能力即便理论上可做，也不能在没有明确收益证据前扩大插件职责。