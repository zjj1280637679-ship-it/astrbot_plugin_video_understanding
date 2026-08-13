# 证据策展与结论边界

更新时间：2026-08-13。

本文件的目的不是堆链接，而是明确每份证据**允许支持什么结论、禁止支持什么结论**。后续 README、发布说明和代码注释均不得超过这里定义的证据边界。

## 证据等级

### L1：源码结构证据

来源：AstrBot 官方源码、火山方舟供应商插件源码。

可支持：

- AstrBot 存在 `Video` 消息组件和 `convert_to_file_path()`；
- 当前/引用消息中存在视频附件处理；
- AstrBot 有 `ToolSet`、`FunctionTool`、`ToolLoopAgentRunner`；
- 当前 v4.27.3 的 `ProviderRequest` 没有 `video_urls`；
- 火山方舟 Provider 当前会消费 AstrBot 生成的可信 `Video Attachment` 临时内容块并转换为 Ark `video_url`。

不可支持：

- 某个具体模型在当前账号下一定能读视频；
- 所有 Provider 都支持该视频路径；
- 真正的多轮工具循环已经发生。

## L2：单元测试证据

来源：`tests/test_video_semantic_search.py`。

可支持：

- 视频绑定顺序、索引和错误边界符合代码契约；
- `QueryVideoTool` 会把一次自然语言查询转交给所选模型卡；
- 当前宿主信封与未来原生 `video_urls` 两种分支可被确定性选择；
- 视频模型返回失败哨兵时工具不会伪装成“没有内容”。

不可支持：

- 真实 AstrBot 能安装插件；
- 真实 Provider 收到视频；
- 模型确实理解视频。

## L3：真实 AstrBot 宿主运行证据

来源：视频插件仓库 GitHub Actions `Real AstrBot Runtime Matrix`。

已验证环境：

- AstrBot `v4.27.3`；
- 当日当前 `master`。

实际步骤：

```text
clone AstrBot
→ uv sync
→ astrbot init
→ 安装插件
→ compile
→ pytest
→ 接口探针
→ astrbot run
→ 插件加载
```

可支持：

- 插件在这两个真实宿主中能够安装、导入、测试并启动；
- 当前宿主接口形态已被运行时探针确认。

不可支持：

- 视频已经到达具体 Provider；
- 任何具体视频模型能力结论。

## L4：真实 Provider 传输证据

来源：火山方舟仓库 `Live Video Semantic Search E2E` 的 HTTP/Provider 运行日志。

运行 `31705763398` 已确认：

- Secret 由 GitHub Actions 注入且未打印；
- 请求实际发送到 Ark Chat Completions；
- 请求体中实际包含 `video_url` 视频块；
- 上游返回 HTTP 200。

可支持：

- `QueryVideoTool → AstrBot 视频附件信封 → 火山方舟 Provider → Ark video_url` 的传输链在该次运行中真实成立。

不可支持：

- 所有火山模型都支持视频；
- Google/MiniMax/其他 Provider 同样成立；
- 主模型已经自主做了多轮查询规划。

## L5：真实视频内容问答证据

来源：artifact `live-video-semantic-search-e2e`。

固定测试视频：

```text
00:00-00:02  ALPHA
00:02-00:04  BETA
00:04-00:06  GAMMA
```

真实模型：`doubao-seed-2-1-pro-260628`。

结果：

- 查询开头词语 → 返回 `ALPHA`，`observed=true`；
- 对同一视频再次查询中间词语 → 返回 `BETA`，`observed=true`。

可支持：

- 同一个视频对象可以通过同一个 `QueryVideoTool` 被重复自然语言查询；
- 视频模型返回了与视频内容相符的局部证据；
- 插件不是只能生成一次固定摘要。

不可支持：

- 主模型自己决定了第二次查询；
- 复杂长视频、音频、OCR、因果分析都已经验证；
- 该模型能力在未来永久不变。

## L6：真实 Agent Tool Loop 证据

当前状态：**待完成**。

只有当 AstrBot `ToolLoopAgentRunner` 驱动主模型实际产生至少两次不同的 `query_video` 调用，并在读取第一次工具结果后生成第二次查询，才能升级为 L6。

完成后允许支持：

> 本插件已经客观实现“主模型把视频作为可反复查询的信息空间，在 AstrBot 原有 Agent Tool Loop 中逐步检索视频证据”的目标架构。

在 L6 完成前，README 不得声称“已验证主模型自主多轮视频搜索”。

## 当前允许发布的核心表述

可以说：

> 插件把当前或引用消息中的视频暴露为 `query_video` 工具；该工具可被重复调用，并已在真实 AstrBot + 火山方舟视频模型链路中验证同一视频的多次针对性查询。

暂时不能说：

> 主模型已经被端到端验证会自主连续搜索视频直到证据充分。

后一句必须等待 L6。