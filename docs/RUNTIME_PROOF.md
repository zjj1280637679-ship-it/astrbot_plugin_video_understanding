# 运行证据：CALL-SEAM-01 / ITERATIVE-LOOP-01

更新时间：2026-08-13。

## 结论

两个核心运行问题均已通过真实环境闭合：

1. **CALL-SEAM-01：CLOSED** — 视频查询工具能够沿 AstrBot 当前宿主视频契约把同一个 `Video` 交给已配置的视频模型卡并取得真实视频证据；
2. **ITERATIVE-LOOP-01：CLOSED** — AstrBot 自己的 `ToolLoopAgentRunner` 能驱动主模型先后产生两个不同的 `query_video` 查询，读取第一次工具结果后继续第二次查询，再综合证据形成最终回答。

当前已验证主链：

```text
用户任务 + AstrBot Video
→ AstrBot ToolLoopAgentRunner
→ 主模型调用 query_video(问题 A)
→ QueryVideoTool
→ AstrBot 当前视频附件宿主契约
→ 视频能力 Provider / 模型
→ 证据 A 返回 Tool Loop
→ 主模型生成不同的问题 B
→ query_video(问题 B)
→ 证据 B
→ 主模型最终回答
```

视频搜索插件自身不实现供应商 SDK、媒体上传器、Agent 循环或第二套视频会话。

## 当前宿主视频契约

AstrBot v4.27.3 与验证时的当前 master 运行探针均得到：

```text
PROVIDER_REQUEST_HAS_VIDEO_URLS=False
```

因此当前插件使用 AstrBot 已经存在的可信当前请求视频附件形态：

```text
[Video Attachment: name <name>, path <path>]
```

引用视频：

```text
[Video Attachment in quoted message: name <name>, path <path>]
```

这些内容由已经绑定的 AstrBot `Video` 组件生成，并通过 `extra_user_content_parts` 传递，不从普通用户文本中解析任意本地路径。

`transport.py` 只适配 AstrBot 宿主契约：

```text
宿主未来有 ProviderRequest.video_urls
→ 使用 video_urls

当前宿主没有
→ 使用 AstrBot 当前可信 Video Attachment 信封
```

它不判断 Google、火山、MiniMax 等供应商品牌。

## 上游未来方向

AstrBot PR #9424 提议把视频提升为统一 Provider 输入：

```text
Video
→ ProviderRequest.video_urls
→ video_url content block
→ Provider
```

截至本次验证该 PR 仍未合并，所以当前实现不能把该接口当成稳定宿主事实；但 `transport.py` 已为宿主未来出现原生字段保留自动切换。

## 真实 AstrBot 宿主矩阵

工作流：`Real AstrBot Runtime Matrix`。

S1 宿主传输隔离、S3 引用/多视频绑定测试完成后的运行：

```text
run #6 / 31708806935
result: success
```

| AstrBot ref | clone | uv sync | init | 插件安装 | compile/pytest | 接口探针 | AstrBot 启动/加载 | 结果 |
|---|---|---|---|---|---|---|---|---|
| `v4.27.3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | success |
| `master` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | success |

这证明当前开发分支在两个真实宿主中仍可安装、测试、启动和加载。

## 真实 Provider / 视频内容证据

火山方舟仓库临时证据分支：`test/video-semantic-search-e2e`。

Repository Secret `HUOSHANYINQINGAPI` 仅通过 GitHub Actions 环境变量注入，不写入代码或 artifact。

真实模型：

```text
doubao-seed-2-1-pro-260628
```

固定 6 秒测试视频：

```text
00:00-00:02  ALPHA
00:02-00:04  BETA
00:04-00:06  GAMMA
```

### L5：同一视频重复直接查询

工作流：`Live Video Semantic Search E2E`

```text
run #1 / 31705763398
result: success
```

同一 `Video` 的两次 `QueryVideoTool` 调用分别真实返回：

- 开头区间 → `ALPHA`；
- 中段区间 → `BETA`。

Provider 日志同时确认请求真实进入 Ark Chat Completions，并包含 `video_url` 视频块。

## L6：真实 AstrBot Tool Loop

工作流：`Live Video Semantic Search Tool Loop`

第一次运行 `31709376019` 在进入任何模型调用前因测试脚本缺少 sibling repo Python import path 失败；该失败只属于测试装载层。

修正 `PYTHONPATH` 后：

```text
run #2 / 31709608070
result: success
artifact: live-video-semantic-search-tool-loop
```

执行器：

```text
AstrBot ToolLoopAgentRunner
+ FunctionToolExecutor
+ QueryVideoTool
```

实际记录到的第一次工具调用：

```text
query: What large word is prominently displayed in the video around 00:00-00:02?
time_range: 00:00-00:02
```

工具结果：

```text
ALPHA
```

实际记录到的第二次工具调用：

```text
query: What large word is prominently displayed in the video around 00:02-00:04?
time_range: 00:02-00:04
```

工具结果：

```text
BETA
```

两次查询文本不同；第二次工具调用是在第一次工具结果已经返回 Tool Loop 后产生。

主模型最终回答：

```text
FIRST=ALPHA; SECOND=BETA
```

因此已经客观证明：

> 主模型可以把视频当作有界可搜索信息空间，在 AstrBot 原有 Agent Tool Loop 中通过“提出子问题 → 读取视频证据 → 继续提出不同子问题 → 综合回答”的循环完成任务。

## 当前通过项

- 插件不直接调用供应商 SDK：✅
- 插件不实现供应商请求体：✅
- 宿主传输契约独立于供应商品牌：✅
- 当前消息视频绑定：✅
- 多视频顺序绑定：✅
- 引用视频绑定与引用信封：✅
- 无视频/索引越界失败封闭：✅
- 同一视频多次直接查询：✅
- 真 `ToolLoopAgentRunner` 连续两次不同查询：✅
- 第一次证据 ALPHA：✅
- 第二次证据 BETA：✅
- 最终主模型综合两份证据：✅
- AstrBot v4.27.3 / master 真实安装与启动：✅

## 仍未外推的范围

本次证据不证明：

- 所有 Provider 已有视频通道；
- 所有火山模型都支持视频；
- Gemini/MiniMax 等其他 Provider 已做相同端到端验证；
- 长视频、复杂音轨、跨轮永久视频引用已验收；
- 当前模型能力未来永久不变。

这些必须分别通过对应运行证据建立，不能从本次成功外推。

## 脱敏要求

证据不得持久化 API Key、Authorization Header、用户隐私标识或真实私人视频。本次 L5/L6 使用的是工作流现场生成的合成 ALPHA/BETA/GAMMA 视频。