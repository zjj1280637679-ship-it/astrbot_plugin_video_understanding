# 上机实测清单 — v0.1.0

测试分支：`manual-test/v0.1.0`

本分支用于真实 AstrBot / QQ 环境手测。不要用默认 `main`；当前默认分支还没有运行时代码。

## 1. 安装前提

- AstrBot `>= 4.27.3`
- AstrBot 中已经存在一个你确认可以读取视频的模型卡
- 插件只选择该模型卡，不填写第二份 API Key / Base URL

## 2. 配置

安装插件后在配置页：

```text
启用视频语义搜索工具 = 开
视频搜索模型 = 选择已有视频能力模型卡
```

保存后重载插件或重启 AstrBot。

启动日志应至少能看到：

```text
[video-semantic-search] query_video registered version=0.1.0
```

如果看到 `tool unavailable`，优先检查插件是否启用、是否已经选择视频模型卡。

## 3. 第一轮：当前消息视频

先发一个内容简单、6~15 秒的视频，然后在同一条消息或紧接着明确询问视频内容，例如：

```text
先告诉我视频最后出现的文字是什么，再确认它前一个出现的文字是什么。
```

理想行为：

```text
主模型 → query_video(Q1) → 视频模型 A1
主模型 → query_video(Q2，允许用“它/刚才那个”等追问) → 视频模型 A2
主模型 → 最终回答
```

重点不是固定必须调用两次，而是：需要继续取证时，后续查询能够继承同一视频此前成功 Q/A。

## 4. 第二轮：引用视频

引用/回复一条包含视频的历史消息，再问：

```text
这个视频里人物最后做了什么？
```

应能够绑定 `Reply.chain` 中的视频，而不是提示“本轮没有视频”。

## 5. 第三轮：无视频消息

单独发普通文字，例如：

```text
你好
```

这轮不应因为本插件产生 `query_video` 视频查询；没有视频时工具会从本轮请求中隐藏。

## 6. 如果失败，请保留这四样

1. AstrBot 版本号；
2. 插件配置页截图（模型卡名字即可，不要暴露 API Key）；
3. QQ 对话截图，包含视频与问题；
4. 相关日志片段，优先搜索：

```text
[video-semantic-search]
VIDEO_QUERY_ERROR
query_video
```

不要发送 Authorization Header、API Key、完整视频 Base64 或签名临时 URL。

## 7. 失败位置快速判断

```text
插件列表里都看不到
→ 安装/目录/metadata 层

看到 tool unavailable
→ 插件配置层

query_video: no video
→ QQ / AstrBot Video 绑定层

could not resolve selected video
→ AstrBot 媒体解析层

configured model could not consume current AstrBot video input contract
→ Provider 视频传输层

工具有结果但主模型答错
→ Tool Loop / 主模型综合层
```

第一次上机只需要把真实平台链路跑通；暂时不要用长视频、多视频、复杂 OCR 或高速 UI 作为首测样本。