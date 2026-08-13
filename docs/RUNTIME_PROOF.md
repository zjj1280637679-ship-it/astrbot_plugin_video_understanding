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

其中 OpenAI-compatible Provider 在该 PR 中显式新增 `video_urls` 参数，并将其物化成 `data:video/...;base64,...`；Anthropic Provider则把统一 `video_url` 内容块转换为 Anthropic 的 `video` block。

但是，截至 2026-08-13：

- PR #9424 仍是 open；
- `merged=false`；
- 公开稳定主干尚不能据此假定所有 Provider 都实现了 `video_urls`；
- 该 PR 不修改 `gemini_source.py`。

因此，本项目采用下列证据等级：

```text
上游统一契约候选：video_urls       已确认
当前公开稳定版全 Provider 可用：     未确认
实际部署中的所选视频模型卡可用：     待运行确认
```

## 首选插件调用形式

若实际部署中的所选 Provider 已消费 `video_urls`，第一版应优先使用下面这条薄调用链：

```python
video_path = await bound_video.component.convert_to_file_path()

response = await context.llm_generate(
    chat_provider_id=video_search_provider_id,
    prompt=video_query_prompt,
    video_urls=[video_path],
)
```

理由：

1. `Context.llm_generate()` 已经是 AstrBot 给插件调用已有模型卡的公共入口；
2. 它会把额外的 `**kwargs` 继续转发给目标 Provider；
3. `video_urls` 是上游 PR #9424 已经提出并测试的统一请求字段；
4. 插件因此无需知道 Google、MiniMax、火山或其他 Provider 的私有请求体。

如果实际环境不是通过 `video_urls` 工作，则只记录 AstrBot/Provider 已经提供的**等价统一入口**；不得在本插件内新增供应商特判。

## 环境记录

- AstrBot 版本/commit：
- 插件版本：
- 平台：
- 视频搜索模型卡 ID：
- Provider 类型：
- 模型名：

## 测试视频

使用 5～8 秒、无隐私内容的固定样本：

```text
0-2 秒：ALPHA
2-4 秒：BETA
4-6 秒：GAMMA
音轨：ONE / TWO / THREE
```

## 查询 A：视觉顺序

```text
画面依次出现了哪三个单词？
```

预期：模型能够回答 `ALPHA → BETA → GAMMA`。

## 查询 B：第二次独立查询

在同一个视频对象上再次调用同一接口：

```text
第二个出现的单词是什么？
```

预期：模型回答 `BETA`。

这里的核心验收不是内容难度，而是证明“同一 Video 可以被主模型通过同一个 query_video 工具反复提问”。

## 需要记录的调用缝

### 1. AstrBot 提供给插件的视频对象

```text
组件类型：Video
组件关键字段：
convert_to_file_path() 结果形态：
```

### 2. 插件调用的 AstrBot 公共入口

```text
方法名：
所属对象：
关键参数：
```

首选候选：

```text
Context.llm_generate(..., video_urls=[...])
```

### 3. 视频参数的实际形态

只记录结构，不记录密钥或敏感 URL：

```text
参数名/内容块类型：
值是本地路径 / URL / file id / 其他：
```

### 4. Provider 侧观察

```text
Provider 是否成功接收视频：
是否发生上传/转换：
该动作由 AstrBot/Provider 哪一层执行：
本插件是否保持供应商无关：是 / 否
```

### 5. 返回结果

```text
查询 A 返回：
查询 B 返回：
```

## 判定

成功标准：

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
