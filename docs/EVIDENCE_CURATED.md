# 证据策展与结论边界

更新时间：2026-08-13。

本文件明确每份证据允许支持什么结论、禁止支持什么结论。README、发布说明和代码注释不得超过这里定义的证据边界。

## L1：源码结构证据

来源：AstrBot 官方源码、火山方舟供应商插件源码。

已证实：

- AstrBot 有正式 `Video` 组件与 `convert_to_file_path()`；
- 当前消息和 `Reply.chain` 都有视频附件结构；
- AstrBot 有 `FunctionTool`、`ToolSet`、`ToolLoopAgentRunner`；
- v4.27.3 的 `ProviderRequest` 尚无 `video_urls`；
- 火山方舟 Provider 会消费 AstrBot 当前可信 `Video Attachment` 临时内容块并转换为 Ark `video_url`。

这一级不能证明具体模型能力或真实请求成功。

## L2：单元测试证据

来源：`tests/test_video_semantic_search.py`。

已证实：

- 当前视频优先、引用视频随后，多视频按出现顺序编号；
- 无视频和索引越界均失败封闭；
- 当前宿主信封与未来原生 `video_urls` 两种宿主契约可以确定性选择；
- `QueryVideoTool` 只执行一次“查询 → 证据”调用；
- 视频模型返回失败哨兵时不会伪装成空搜索结果。

这一级不能证明真实 AstrBot 安装或真实 Provider 传输。

## L3：真实 AstrBot 宿主运行证据

来源：视频插件仓库 `Real AstrBot Runtime Matrix`。

已在 AstrBot `v4.27.3` 与当日当前 `master` 上真实执行：

```text
clone AstrBot
→ uv sync
→ astrbot init
→ 安装插件
→ compile
→ pytest
→ 宿主接口探针
→ astrbot run
→ 插件加载
```

S1/S3 重构后的 run `31708806935` 仍为 success。

允许结论：插件在这两个宿主中能够真实安装、测试、启动和加载。

## L4：真实 Provider 传输证据

来源：火山方舟仓库 `Live Video Semantic Search E2E`，run `31705763398`。

已确认：

- Secret 只由 GitHub Actions 注入；
- 请求实际到达 Ark Chat Completions；
- Provider 实际生成 `video_url` 视频块；
- 上游返回 HTTP 200。

允许结论：

```text
QueryVideoTool
→ AstrBot 当前请求视频附件信封
→ 火山方舟 Provider
→ Ark video_url
```

这条传输链在该次运行中真实成立。

## L5：真实视频内容问答证据

固定测试视频：

```text
00:00-00:02  ALPHA
00:02-00:04  BETA
00:04-00:06  GAMMA
```

真实模型：`doubao-seed-2-1-pro-260628`。

同一 `Video` 的两次直接 `QueryVideoTool` 查询分别返回：

- 开头：`ALPHA`；
- 中段：`BETA`。

允许结论：同一视频能够通过同一查询工具被重复、针对性检索，而不是只能产生一次固定摘要。

## L6：真实 AstrBot Agent Tool Loop 证据

状态：**完成**。

来源：火山方舟仓库 `Live Video Semantic Search Tool Loop`，run `31709608070`，artifact `live-video-semantic-search-tool-loop`。

执行器：AstrBot `ToolLoopAgentRunner` + `FunctionToolExecutor`。

实际工具调用记录：

### 第一次

```text
query: What large word is prominently displayed in the video around 00:00-00:02?
time_range: 00:00-00:02
```

工具证据：`ALPHA`。

### 第二次

```text
query: What large word is prominently displayed in the video around 00:02-00:04?
time_range: 00:02-00:04
```

工具证据：`BETA`。

两次 query 不同，且第二次调用发生在第一次工具结果已经进入 Tool Loop 之后。

主模型最终回答：

```text
FIRST=ALPHA; SECOND=BETA
```

因此现在允许支持：

> 本插件已经客观实现“主模型把视频作为可反复查询的信息空间，在 AstrBot 原有 Agent Tool Loop 中逐步取得视频证据，再由主模型综合回答”的目标架构。

## 仍然禁止外推的结论

以上证据不等于：

- 所有 Provider 都已经支持视频；
- 所有火山模型都支持视频；
- Google/MiniMax 等其他 Provider 已完成同样端到端验证；
- 长视频、复杂音轨、OCR、跨轮视频记忆已经验证；
- 当前模型能力会永久不变。

## 当前允许发布的核心表述

> 插件把当前或引用消息中的视频作为可查询的信息空间暴露给主模型。主模型可以通过 `query_video` 在 AstrBot 原有 Tool Loop 中连续提出不同的视频子问题、读取局部证据并继续追问；这一多轮搜索闭环已经通过真实 AstrBot + 火山方舟视频模型端到端验证。