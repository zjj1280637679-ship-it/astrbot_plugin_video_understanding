# astrbot_plugin_video_understanding

AstrBot 对话式视频搜索插件。

`query_video` 不是自动视频摘要器，也不增强视频模型的智能。它只把当前/引用视频与主模型整理出的自然语言问题交给管理员选择的已有视频能力模型卡，再把答案返回主模型。

```text
用户问题 + 视频
→ 主模型整理查询
→ query_video
→ 视频模型回答
→ 主模型判断是否还要问
→ 必要时继续 query_video
→ 视频模型保留此前同视频 Q/A
→ 主模型最终回答
```

视频理解深度由“用户问题所需深度 × 视频模型自身能力”决定。插件不规定只能直接观察、不能做因果分析、必须窄查询或固定分析步骤。

## 连续查询

同一次 AstrBot event / Agent run 中，同一 `provider_id + video_index` 的成功 Q/A 会原样作为后续视频模型调用的 `contexts`：

```text
Q1 → A1
Q2 + Q1/A1 → A2
Q3 + Q1/A1/Q2/A2 → A3
```

历史不摘要、不改写；不同视频/Provider 隔离；event 结束自然失效；失败调用不进入历史。插件不建立永久视频数据库。

因此可以自然追问：

```text
Q1: 哪个大字包含字母 M？
A1: GAMMA
Q2: 它之前是什么？
A2: BETA
```

第二问不需要重新把 `GAMMA` 写进 prompt。

## 工具参数

```text
query       必填：交给视频模型的问题或提示词
video_index 可选：视频编号，默认 0
time_range  可选：时间范围注意力提示
```

`time_range` 不会裁剪视频，也不保证降低 Provider 成本。

当前消息视频先编号，然后加入 `Reply.chain` 中的引用视频。无视频、索引越界、视频解析失败或 Provider 调用失败都会明确失败。

## 职责边界

`query_video` 服从 AstrBot Tool Manager、工具启停和人格白名单。插件只消费 AstrBot / Provider 已有的视频传输能力，不增加：

- 供应商专属 SDK 或品牌路由；
- 视频能力重复探测；
- 自建上传器；
- OCR / STT / 抽帧 / FFmpeg 业务降级；
- 自动摘要或自动问题分解；
- 独立 Agent Loop；
- 永久视频资产库。

## 当前验证

当前业务 runtime：

```text
d5f4742e114771669a7e969a8eb6e62d3bffa883
```

真实火山方舟 + AstrBot ToolLoop 验证已经证明：视频模型第一次回答 `GAMMA` 后，主模型第二次只用“that word / 它”进行追问；第二次视频模型调用实际收到此前 `user + assistant(GAMMA)` contexts，返回 `BETA`，最终主模型回答：

```text
REFERENT=GAMMA; BEFORE=BETA
```

当前权威验证基线：`docs/FINAL_VALIDATION_BASELINE_2026-08-14.md`。

## 配置

只需在 AstrBot 中选择已经配置好的视频能力模型卡。插件不保存 API Key、Base URL，也不维护自己的 Provider 数据库。
