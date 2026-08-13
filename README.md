# astrbot_plugin_video_understanding

AstrBot 视频语义搜索插件。

它不在收到视频后自动生成一次性摘要，而是把 AstrBot 已经取得的视频暴露为主模型可以反复查询的有界信息空间，并使用管理员选择的、已经具有视频读取能力的模型卡执行这些查询。

核心工作流：

```text
用户问题 + 视频
      ↓
主模型
      ↓
query_video("当前需要确认的一个视频子问题")
      ↓
视频能力模型卡读取视频并返回观察结果
      ↓
主模型根据结果继续追问或形成最终回答
```

## 设计原则

- 视频是被搜索的信息空间；
- 视频能力模型卡是语义搜索引擎；
- 主模型负责查询规划与最终回答；
- AstrBot 原有 Tool Loop 负责多轮工具调用；
- 本插件只负责视频绑定、`query_video` 工具暴露和查询转发。

本插件不重新实现 AstrBot 的视频消息、模型卡、Provider、会话或 Agent 循环，也不内置 FFmpeg、OCR、STT 或供应商专属 SDK。

## 当前阶段

当前仓库处于设计证据冻结阶段。正式编码前需要完成 `docs/RUNTIME_PROOF.md` 中的 `CALL-SEAM-01`，确认当前 AstrBot 环境中插件应复用的既有视频模型调用入口与参数形态。

## 设计文档

- `docs/ADR-001-video-as-search-space.md`：核心架构决策
- `docs/EVIDENCE.md`：上游能力与证据索引
- `docs/TOOL_CONTRACT.md`：`query_video` 工具契约
- `docs/IMPLEMENTATION_BLUEPRINT.md`：第一版最小实现蓝图
- `docs/RUNTIME_PROOF.md`：视频调用缝运行证据模板
- `docs/SECURITY_BOUNDARY.md`：安全与职责边界
- `docs/TEST_PLAN.md`：第一版测试与发布验收
