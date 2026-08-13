# 运行证据：CALL-SEAM-01

目标：确认本插件在实际部署环境中应复用的 AstrBot → 视频模型卡调用缝。

这不是视频能力测试；前提已经是“被选模型卡具备视频读取能力”。本记录只回答：插件应该通过哪个已有 AstrBot 入口，把当前 `Video` 与一次自然语言子查询交给该模型卡。

## 结论

**CALL-SEAM-01 已在 2026-08-13 通过真实火山方舟端到端测试闭合。**

当前 AstrBot v4.27.3 / master 仍没有 `ProviderRequest.video_urls`，因此本插件现在使用 AstrBot 已经存在的当前请求视频附件信封；当未来宿主正式提供 `video_urls` 时，代码会自动切换到统一字段。

当前已验证路径：

```text
AstrBot Video
→ Video.convert_to_file_path()
→ QueryVideoTool
→ AstrBot 当前请求 TextPart 视频附件信封
→ Context.llm_generate(..., extra_user_content_parts=[TextPart(...)])
→ 已配置的视频模型卡
→ Provider 消费 AstrBot 当前视频附件信封
→ 真实视频模型回答
→ 工具结果返回主模型
```

这条路径只依赖 AstrBot 当前宿主契约，不在视频搜索插件里判断或适配 Google、火山、MiniMax 等供应商品牌。

## 上游统一契约方向

AstrBot PR #9424 给出了未来更直接的统一视频请求方向：

```text
Video
→ convert_to_file_path()
→ ProviderRequest.video_urls
→ video_url content block
→ Provider
```

截至本次验证：

- PR #9424 仍是 open；
- `merged=false`；
- v4.27.3 与当前 master 的 `ProviderRequest` 均没有 `video_urls`；
- 因此插件不能把尚未进入宿主的接口当成当前事实。

插件现在按宿主能力自动选择：

```text
ProviderRequest 有 video_urls
→ video_urls=[video_path]

ProviderRequest 没有 video_urls
→ 使用 AstrBot 当前请求 TextPart 视频附件信封
```

## 真实 AstrBot 安装与加载证据

GitHub Actions：`Real AstrBot Runtime Matrix`。

最新验证运行：`#3 / 31705567880`。

矩阵：

| AstrBot ref | clone | uv sync | init | 插件安装 | pytest | 接口探针 | AstrBot 启动/插件加载 | 结果 |
|---|---|---|---|---|---|---|---|---|
| `v4.27.3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | success |
| `master` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | success |

这证明当前开发分支在两个真实 AstrBot 宿主中都可以安装、编译、执行单测并启动加载。

### 宿主接口探针

`v4.27.3` 与本次测试时的 `master` 均得到：

```text
PROVIDER_REQUEST_HAS_VIDEO_URLS=False
CONTEXT_LLM_GENERATE_SIGNATURE=(..., image_urls=None, audio_urls=None, ..., **kwargs)
GEMINI_TEXT_CHAT_SIGNATURE=(..., image_urls=None, audio_urls=None, ..., **kwargs)
GEMINI_ASSEMBLE_CONTEXT_SIGNATURE=(self, text, image_urls=None, audio_urls=None, extra_user_content_parts=None)
```

因此 `video_urls` 只能作为未来统一契约方向；当前运行时应复用 AstrBot 已存在的视频附件信封。

## 当前 AstrBot 视频附件信封

当前 AstrBot 会把本次视频作为框架生成的 `TextPart` 放进 `extra_user_content_parts`。本插件生成与宿主相同的当前请求形态，例如：

```text
[Video Attachment: name alpha-beta-gamma.mp4, path /tmp/.../alpha-beta-gamma.mp4]
```

引用视频对应：

```text
[Video Attachment in quoted message: name ..., path ...]
```

该内容不是从普通聊天文本中解析出来的，而是由工具从已经绑定的 AstrBot `Video` 组件生成，因此普通用户输入一个长得相似的字符串不能使插件读取任意本地文件。

## 火山方舟 Provider 对照证据

`astrbot_plugin_volcengine_provider/adapters/video.py` 明确把当前 AstrBot 视频契约定义为：

```text
trusted current-request TextPart envelope
→ MediaResolver
→ Ark video_url block
```

它只接受 `extra_user_content_parts` 中由当前请求携带的精确视频附件信封；普通 prompt / 历史文本中的相似字符串不足以触发视频文件读取。

因此本插件不需要知道 Ark 请求体，也不需要调用火山 SDK；它只提交 AstrBot 当前宿主认识的视频附件形态。

## 真实火山方舟端到端视频查询

测试工作流临时放在火山方舟仓库分支 `test/video-semantic-search-e2e`，以便安全使用该仓库已有的 `HUOSHANYINQINGAPI` Repository Secret。

运行：

```text
Live Video Semantic Search E2E
run #1 / 31705763398
result: success
```

环境：

```text
AstrBot: v4.27.3
Provider: astrbot_plugin_volcengine_provider / Volcengine Ark ordinary API
Model: doubao-seed-2-1-pro-260628
Video transport: AstrBot current-request attachment envelope
Secret: GitHub Actions environment only; not printed or persisted
```

### 固定测试视频

工作流现场生成一个约 6 秒 MP4：

```text
00:00-00:02  ALPHA
00:02-00:04  BETA
00:04-00:06  GAMMA
```

文件大小：`10757 bytes`。

### 查询 1

主模型工具调用等价于：

```text
query_video(
  "What large word is shown at the beginning of the video, approximately 00:00-00:02?",
  time_range="00:00-00:02"
)
```

真实工具结果：

```text
ALPHA
At 00:00-00:01.8 ... the large bold black text ... reads ALPHA.
```

判定：`ALPHA observed = true`。

### 查询 2

同一个 `Video` 对象再次调用：

```text
query_video(
  "What large word is shown in the middle of the video, approximately 00:02-00:04?",
  time_range="00:02-00:04"
)
```

真实工具结果：

```text
BETA
This ... word is displayed between approximately 00:02 and 00:04 ...
```

判定：`BETA observed = true`。

两次查询均经过真实 `QueryVideoTool`、真实火山方舟 Provider 和真实 Ark 模型；同一视频可以只替换查询文本反复搜索，不需要插件维护第二套视频会话状态。

## 当前成功标准状态

1. 不直接调用 Google/Gemini、MiniMax、火山或其他供应商 SDK：✅
2. 不由本插件实现供应商上传器或请求体：✅
3. 通过 AstrBot 已有视频附件/Provider 调用链完成：✅
4. 视频模型正确回答测试视频中的事实：✅
5. 同一视频可以替换查询文本再次调用：✅
6. 插件没有保存第二套视频对话状态：✅
7. QueryVideoTool 返回结果继续作为主模型证据：✅
8. v4.27.3 / master 真实安装、pytest、启动加载：✅

**CALL-SEAM-01：CLOSED。**

## 仍未声称的范围

本次证据不等于：

- 所有视频模型卡都已支持 AstrBot 当前附件信封；
- Gemini 内置 Provider 已经接通视频；
- 所有平台的 QQ/Telegram/WebChat 视频来源都已经做了端到端测试；
- 长视频、音轨、多视频、跨消息持续引用已经验收。

这些仍应分别通过实际 Provider / 平台运行证据确认，而不能从本次 Ark 成功外推。

## 脱敏要求

运行证据和 artifact 不得包含：

- API Key；
- Authorization Header；
- 带签名的临时 URL；
- 本地用户名路径；
- QQ/群聊/用户隐私标识；
- 真实私人视频内容。
