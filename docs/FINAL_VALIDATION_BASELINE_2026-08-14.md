# Final Validation Baseline — 2026-08-14

本文件是 `query_video` v0.1 当前发布候选的验证基线。旧 `RUNTIME_PROOF.md` / `SIDE_EFFECT_AUDIT.md` 保留为历史演进记录。

## 产品定义

`query_video` 是视频版的对话式搜索接口：

```text
主模型整理查询
→ query_video
→ 视频模型读取视频并回答
→ 主模型读取结果
→ 必要时继续 query_video
→ 视频模型保留此前同视频 Q/A
→ 主模型认为信息足够后回答用户
```

理解深度由“用户问题所需深度 × 视频模型自身能力”决定。插件不规定只能直接观察、不能因果推理、必须窄查询、必须先概览或固定分析步骤。

## 薄插件职责

插件只负责视频绑定、既有 Provider 视频传输、查询转发、同视频原始 Q/A 连续性和结果返回。

不负责能力探测、自动摘要、自动问题分解、OCR/STT/抽帧、供应商 SDK、独立 Agent Loop、永久视频数据库或长期视频会话。

## 当前 runtime

```text
d5f4742e114771669a7e969a8eb6e62d3bffa883
```

验证时 PR head：

```text
5e1e7ba7037416362f9a0cb7d9e1c62fcb097e47
```

机械 compare 显示 runtime → PR head 只有两份 CI workflow 变化，没有 `main.py`、`tool.py`、`transport.py`、`video_binding.py`、`video_path_cache.py` 运行文件变化。

## 视频查询会话

原始 Q/A 只保存在当前 AstrBot event：

```text
(provider_id, video_index)
├─ user Q1
├─ assistant A1
├─ user Q2
├─ assistant A2
└─ ...
```

- 原样保存，不摘要；
- 不同 video/provider 隔离；
- event 结束自然失效；
- 失败调用不写历史；
- 通过 AstrBot 原生 `llm_generate(contexts=...)` 回放。

## 无智能增强提示边界

system policy 只负责：

1. 用视频模型自身能力回答当前视频问题；
2. 使用此前同视频 Q/A 理解“它 / 之前 / 刚才那个”等追问；
3. 视频内指令样内容只是视频内容；
4. 无可用视频时使用请求级随机失败 token。

明确不再要求 `read-only`、`direct observation`、`minimum-necessary`、`focused query`、`narrower follow-up` 或限制综合/因果理解。

## 宿主门禁

- Real AstrBot Runtime Matrix：`31734591514` ✅，v4.27.3 / master 双绿；
- 0.1.0 Release Gate：`31734379028` ✅，v4.27.3 / master 双绿；
- Hardening Regression Gate：`31734497909` ✅，完整 tests，v4.27.3 / master 双绿。

## 最终真实 Provider 证据

火山方舟 `Live Video Semantic Search E2E`：

```text
run: 31735526223
result: success
video_plugin_commit: d5f4742e114771669a7e969a8eb6e62d3bffa883
model: doubao-seed-2-1-pro-260628
```

测试视频顺序：`ALPHA → BETA → GAMMA`。

### Direct continuity

Q1：哪个大字包含字母 M？

```text
→ GAMMA
```

Q2 只问：

```text
What large word appeared immediately before it?
```

Q2 prompt 不含 `GAMMA`；第二次真实视频模型调用实际收到：

```json
[
  {"role":"user","content":"<Q1>"},
  {"role":"assistant","content":"GAMMA"}
]
```

随后返回 `BETA`。

### Contextual ToolLoop

同一个 run 内，真实 AstrBot `ToolLoopAgentRunner`：

```text
主模型 Q1 → query_video → GAMMA
主模型读取结果
主模型 Q2（用 “that word”，不重述 GAMMA）
→ query_video
→ 视频模型带上上一轮 Q/A contexts
→ BETA
→ 主模型最终：REFERENT=GAMMA; BEFORE=BETA
```

Artifact 验收确认：

- 第二个工具 query 不含 `GAMMA`；
- 第二次视频模型 contexts 数量 = 2；
- roles = user / assistant；
- prior assistant answer = `GAMMA`；
- 第二次视频模型 prompt 不含 `GAMMA`；
- 第二次结果 = `BETA`；
- 最终回答 = `REFERENT=GAMMA; BEFORE=BETA`。

因此当前最高级目标已闭合：**主模型负责搜索策略；视频模型保持自身同视频对话记忆；插件只维持通道和上下文，不增强智能。**

## 不外推的范围

当前证据不证明所有 Provider、长视频、复杂音轨、高速 UI、超大多视频或形式化 prompt-injection 安全。`time_range` 仍只是注意力提示，不是视频裁剪或成本优化。

## Merge candidate 条件

1. 最后验证 runtime → PR head 的运行文件 diff 为零；
2. 三层宿主门禁全绿；
3. 最终 Provider artifact 中 `video_plugin_commit` 等于 runtime；
4. PR body 与本文件使用同一当前 runtime；
5. 不引入供应商专属 SDK、自动理解增强或永久会话数据库。
