# AstrBot 上游视频输入兼容性矩阵

记录日期：2026-08-13。

本文件只描述公开上游源码和 PR 证据；实际部署环境可以具有额外或更早落地的视频能力，运行事实以 `RUNTIME_PROOF.md` 为准。

| 层级 | AstrBot v4.27.3 公开主干 | PR #9424 | 本插件结论 |
|---|---|---|---|
| `Video` 消息组件 | 已有 | 保留 | 直接复用 |
| 当前/引用视频绑定 | 已有 | 保留 | 直接复用 |
| 模型 `video` 模态元数据 | 已有 | 进一步进入请求清洗 | 不自建能力库 |
| `ProviderRequest.video_urls` | 未见于当前公开主干 | 新增 | 首选统一契约候选 |
| `VideoURLPart` / `video_url` | 未见于当前公开主干 | 新增 | 首选统一内容块候选 |
| Tool Loop 保留视频模态 | 当前公开主干未形成完整 video request 路径 | 新增 | 由 AstrBot 承担循环 |
| OpenAI-compatible Provider 视频传输 | 当前公开主干不能按 #9424 契约假定 | #9424 新增 | 插件不实现私有请求体 |
| Anthropic Provider 视频传输 | 当前公开主干不能按 #9424 契约假定 | #9424 新增 | 插件不实现私有请求体 |
| Gemini Provider `video_urls` 接入 | 本次公开源码检查未确认 | #9424 未修改 `gemini_source.py` | 必须以实际部署环境为准 |

## PR #9424 的关键意义

PR #9424 的标题为 `feat: wire up video input modality for MiniMax providers`。其说明明确指出：在该 PR 针对的基线中，AstrBot 已能识别视频附件，但只向主模型请求留下文字占位，视频模态本身没有沿 Provider 请求链传下去。

该 PR 选择的修复方向不是新增独立视频框架，而是把视频提升为与图片、音频同级的统一 Provider 输入：

```text
ProviderRequest.video_urls
        ↓
video_url content block
        ↓
具体 Provider 消费统一块
```

这与本插件的职责边界一致：插件只提交“视频 + 查询”，供应商传输由 AstrBot/Provider 负责。

## 当前状态

截至记录日期，PR #9424：

- state: open
- merged: false
- head: `476576302f23945e8d7b6c3bfe856ba8b04813b5`

因此本插件不能把该 PR 尚未合并的接口当作所有稳定环境必然存在的事实；但可以把 `video_urls` 作为优先验证的统一契约，因为这是目前最直接、与上游方向一致、并已有测试覆盖的接口形态。

## 对第一版的约束

第一版只接受两种情况：

1. 当前部署环境已经支持 `Context/Provider` 统一视频输入，优先验证 `video_urls`；
2. 当前部署环境存在另一条 AstrBot 已有的、供应商无关的等价统一入口。

如果两者都不存在，第一版应明确报告 AstrBot/Provider 版本依赖，而不是在插件内部加入 Google、MiniMax、火山等供应商专用适配。
