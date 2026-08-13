# astrbot_plugin_video_understanding

AstrBot 视频语义搜索插件。

它不是“收到视频就先生成一份摘要”的转述器，而是把当前或引用消息中的视频作为一个**可反复查询的有界信息空间**交给主模型：主模型在 AstrBot 原有 Tool Loop 中调用 `query_video`，读取局部视频证据，再决定是否继续提出新的、更具体的问题。

## 工作方式

```text
用户问题 + 视频
      ↓
AstrBot 主模型
      ↓
query_video("当前需要确认的一个视频子问题")
      ↓
管理员选择的视频能力模型卡
      ↓
返回局部视频证据
      ↓
主模型读取证据
      ├─ 信息不足 → 再次 query_video(新的子问题)
      └─ 证据充分 → 主模型最终回答
```

视频是被搜索的信息空间；视频能力模型卡是语义搜索引擎；主模型负责查询规划、证据综合和最终回答。

## 已验证闭环

2026-08-13 已完成真实运行验证：

- AstrBot `v4.27.3`：安装、pytest、启动和插件加载通过；
- 当日 AstrBot `master`：安装、pytest、启动和插件加载通过；
- 真实火山方舟视频模型 `doubao-seed-2-1-pro-260628`：同一测试视频连续查询成功；
- AstrBot `ToolLoopAgentRunner`：主模型真实产生两次不同的 `query_video` 调用，第一次取得 `ALPHA`，第二次取得 `BETA`，最终回答 `FIRST=ALPHA; SECOND=BETA`。

详细运行证据见 `docs/RUNTIME_PROOF.md` 和 `docs/EVIDENCE_CURATED.md`。

## 配置

插件只需要选择 AstrBot 中**已经配置好的视频能力模型卡**：

```text
启用视频语义搜索工具：开启
视频搜索模型：选择已有模型卡
```

配置项通过 AstrBot `_special: select_provider` 选择现有模型卡。本插件不保存 API Key、Base URL，也不建立自己的 Provider 数据库。

## query_video

核心工具参数：

```text
query       必填：这一次需要从视频中确认的一个明确问题
video_index 可选：本轮视频编号，默认 0
time_range  可选：例如 00:12-00:25
```

一次调用只负责回答当前查询。主模型可以根据工具结果再次调用，而不是要求视频模型一次完成整个用户任务。

示例：

```text
query_video("用户什么时候点击保存，点击后界面发生了什么？")
→ 返回时间与界面变化证据

query_video("刚才出现的失败提示具体写了什么？")
→ 返回更窄的文字证据

主模型结合两次结果与其他上下文给出最终判断
```

## 视频绑定

第一版规则：

1. 当前消息中的视频优先；
2. 多个当前视频按出现顺序编号；
3. 然后加入 `Reply.chain` 中的引用视频；
4. `video_index` 从 `0` 开始；
5. 无视频或索引越界时失败封闭，不猜测目标。

第一版不建立跨后续消息的永久视频资产库。

## AstrBot / Provider 职责边界

插件只消费 AstrBot 和所选 Provider 已经提供的视频传输能力。

当前 AstrBot v4.27.3 尚没有统一的 `ProviderRequest.video_urls` 字段，因此插件会复用 AstrBot 当前请求已经使用的可信 `Video Attachment` 内容形态；未来宿主出现原生 `video_urls` 后，传输层可直接切换到宿主统一字段。

具体 Provider 如何把 AstrBot 视频输入转换成供应商请求体，属于该 Provider 的职责。本插件不会增加：

- Google / Gemini SDK；
- 火山方舟 SDK；
- MiniMax 专用分支；
- 自建视频上传器；
- FFmpeg / OCR / STT 降级流水线；
- 独立 Agent Loop；
- 独立视频数据库。

目前真实端到端验证覆盖了火山方舟 Provider；这不能外推为所有 Provider 已经完成同样验证。

## 安全边界

视频模型的输出被作为**证据材料**返回，而不是高优先级指令。视频里的字幕、对白、代码或“忽略之前规则”等内容仍然只是被搜索的视频内容。

传输失败、模型没有真正收到视频、无视频或索引错误都会返回明确失败状态，主模型不得把失败解释为“视频中不存在该内容”。

## 设计与证据文档

- `docs/ADR-001-video-as-search-space.md`：核心架构决策
- `docs/NEXT_STAGE_PLAN.md`：阶段闸门与验收目标
- `docs/EVIDENCE_CURATED.md`：证据等级与可支持结论
- `docs/RUNTIME_PROOF.md`：真实 AstrBot / Provider / Tool Loop 运行证据
- `docs/TOOL_CONTRACT.md`：`query_video` 工具契约
- `docs/UPSTREAM_COMPATIBILITY.md`：AstrBot 上游视频接口状态
- `docs/SECURITY_BOUNDARY.md`：安全与职责边界
- `docs/TEST_PLAN.md`：测试与发布验收
