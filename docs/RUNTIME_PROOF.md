# 运行证据：CALL-SEAM-01

目标：确认本插件在实际部署环境中应复用的 AstrBot → 视频模型卡调用缝。

这不是视频能力测试；前提已经是“被选模型卡具备视频读取能力”。本记录只回答：插件应该通过哪个已有 AstrBot 入口，把当前 `Video` 与一次自然语言子查询交给该模型卡。

## 上游静态证据结论

AstrBot PR #9424 已经给出了目前最明确的统一视频请求契约候选：

```text
Video
→ convert_to_file_path()
→ ProviderRequest.video_urls
→ video_url content block
→ Provider
```

其中 OpenAI-compatible Provider 在该 PR 中显式新增 `video_urls` 参数，并将其物化成 `data:video/...;base64,...`；Anthropic Provider 则把统一 `video_url` 内容块转换为 Anthropic 的 `video` block。

但是，截至 2026-08-13：

- PR #9424 仍是 open；
- `merged=false`；
- 公开稳定主干尚不能据此假定所有 Provider 都实现了 `video_urls`；
- 该 PR 不修改 `gemini_source.py`。

因此，本项目采用下列证据等级：

```text
上游统一契约候选：video_urls       已确认
当前公开稳定版全 Provider 可用：     未确认
实际部署中的所选视频模型卡可用：     待端到端运行确认
```

## 真实 AstrBot 安装与加载证据（2026-08-13）

已在 GitHub Actions `Real AstrBot Runtime Matrix` 中沿用火山方舟供应商插件已验证的真实运行时安装方式：

```text
git clone AstrBot 指定 ref
→ Python 3.12
→ setup-uv
→ uv sync --directory AstrBot
→ astrbot init
→ 将当前插件复制到 AstrBot/data/plugins
→ 在该 AstrBot 环境执行 pytest
→ 启动 astrbot run --port 6185
```

运行：`#1 / 31704222379`。

矩阵结果：

| AstrBot ref | clone | uv sync | init | 插件安装 | pytest | 接口探针 | AstrBot 启动/插件加载 | 结果 |
|---|---|---|---|---|---|---|---|---|
| `v4.27.3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | success |
| `master` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | success |

真实启动日志均出现：

```text
Loading plugin astrbot_plugin_video_understanding ...
Plugin astrbot_plugin_video_understanding (0.1.0) by 羊膜大人
[video-semantic-search] tool not registered; enabled=True provider_configured=False
```

这证明插件在未配置视频搜索模型时能够在真实 AstrBot 中安全加载，并且不会错误注册一个不可执行的工具。

### 实际宿主接口探针

`v4.27.3`：

```text
PROVIDER_REQUEST_HAS_VIDEO_URLS=False
CONTEXT_LLM_GENERATE_SIGNATURE=(..., image_urls=None, audio_urls=None, ..., **kwargs)
GEMINI_TEXT_CHAT_SIGNATURE=(..., image_urls=None, audio_urls=None, ..., **kwargs)
GEMINI_ASSEMBLE_CONTEXT_SIGNATURE=(self, text, image_urls=None, audio_urls=None, extra_user_content_parts=None)
```

同一次运行对当前 `master` 的探针结果相同：

```text
PROVIDER_REQUEST_HAS_VIDEO_URLS=False
CONTEXT_LLM_GENERATE_SIGNATURE=(..., image_urls=None, audio_urls=None, ..., **kwargs)
GEMINI_TEXT_CHAT_SIGNATURE=(..., image_urls=None, audio_urls=None, ..., **kwargs)
GEMINI_ASSEMBLE_CONTEXT_SIGNATURE=(self, text, image_urls=None, audio_urls=None, extra_user_content_parts=None)
```

因此已经得到两个彼此独立的事实：

1. **插件运行时兼容性成立**：v4.27.3 和当前 master 都能真实安装、执行单测、启动并加载插件。
2. **统一视频传输缝尚未在这两个宿主中成立**：`ProviderRequest.video_urls` 不存在，内置 Gemini 的公开 `assemble_context` 也没有视频参数。

后者不能被解释成“Gemini 模型没有视频能力”，只能说明这两个 AstrBot 宿主版本没有通过当前候选统一字段把视频送入该 Provider。

## 当前插件调用形式

开发分支当前保留上游方向一致的候选调用：

```python
video_path = await bound_video.component.convert_to_file_path()

response = await context.llm_generate(
    chat_provider_id=video_search_provider_id,
    prompt=video_query_prompt,
    video_urls=[video_path],
)
```

真实 AstrBot 环境中的单元测试已经证明 `QueryVideoTool` 会把解析后的本地视频路径作为 `video_urls=[...]` 传给 `Context.llm_generate`；但由于当前 v4.27.3/master 的宿主 Provider 请求链尚未消费这一字段，这一测试只能证明**插件侧契约实现正确**，不能伪装成“视频已经真实到达 Gemini”。

如果实际部署中的某个已有 Provider 已消费 `video_urls`，这条调用即可直接形成端到端链路；如果实际环境使用另一条供应商无关的 AstrBot 统一入口，则应只替换这里的宿主接口，不在插件中新增供应商私有实现。

## 固定端到端测试素材

待统一视频输入宿主成立后，使用 5～8 秒、无隐私内容的固定样本：

```text
0-2 秒：ALPHA
2-4 秒：BETA
4-6 秒：GAMMA
音轨：ONE / TWO / THREE
```

查询 A：

```text
画面依次出现了哪三个单词？
```

查询 B：

```text
第二个出现的单词是什么？
```

完整 CALL-SEAM-01 只有在真实视频模型分别回答 `ALPHA → BETA → GAMMA` 和 `BETA` 后才算闭合。

## 成功标准

最终端到端成功必须同时满足：

1. 不直接调用 Google/Gemini、MiniMax、火山或其他供应商 SDK；
2. 不由本插件实现上传器或媒体转码；
3. 通过 AstrBot 已有 Provider/Context 调用链完成；
4. 视频模型正确回答测试视频中的事实；
5. 同一入口可以只替换查询文本再次调用；
6. 插件没有保存另一套视频对话状态；
7. 主模型的 Tool Loop 可以使用第一次工具结果决定第二次查询。

## 如果 `video_urls` 在当前环境失败

只允许得到以下结论：

> 当前所选 AstrBot/Provider 版本没有通过该统一候选字段消费视频，需确认实际环境已经存在的等价视频入口或等待上游统一契约落地。

禁止自动采取：

- 直接调用供应商 SDK；
- 在插件里写 Google/MiniMax/火山分支；
- 自动抽帧代替视频输入；
- 因此断言“模型没有视频能力”。

## 脱敏要求

提交运行结果前删除：

- API Key；
- Authorization Header；
- 带签名的临时 URL；
- 本地用户名路径；
- QQ/群聊/用户隐私标识；
- 真实私人视频内容。
