# 第一版最小实现蓝图

## 文件结构

```text
astrbot_plugin_video_understanding/
├── main.py
├── tool.py
├── video_binding.py
├── _conf_schema.json
├── metadata.yaml
├── README.md
└── docs/
```

第一版不引入额外视频处理依赖。

## `main.py`

职责：

1. 读取插件配置；
2. 在 LLM 请求阶段检查本轮是否存在可查询视频；
3. 根据 `activation_policy` 判断是否向当前 `ToolSet` 加入 `query_video`；
4. 把当前可查询视频列表绑定到本轮 Agent Context；
5. 不主动调用视频模型。

伪代码：

```python
@filter.on_llm_request()
async def expose_video_search(self, event, req):
    videos = await bind_videos_from_event(event)
    if not videos:
        return

    if not should_enable_tool(event, req, self.config):
        return

    event.set_extra("video_search_assets", videos)

    if req.func_tool is None:
        req.func_tool = ToolSet()

    req.func_tool.add_tool(self.query_video_tool)
    req.extra_user_content_parts.append(
        TextPart(text=build_video_search_notice(videos)).mark_as_temp()
    )
```

## `video_binding.py`

职责仅限把 AstrBot 已有 `Video` 组件映射为本轮索引。

规则：

```text
1. 当前消息中的 Video
2. Reply.chain 中的 Video
3. 按出现顺序编号 0..N-1
```

建议绑定对象：

```python
@dataclass
class BoundVideo:
    index: int
    component: Video
    source: Literal["current", "quoted"]
    display_name: str | None = None
```

不要在绑定阶段上传、抽帧或分析视频。

## `tool.py`

职责：

1. 读取 `query` / `video_index` / `time_range`；
2. 从当前 Agent Event 中取得绑定视频；
3. 将 AstrBot 视频引用按 `CALL-SEAM-01` 证明出的官方/既有入口传给管理员选择的视频模型卡；
4. 返回模型文本结果；
5. 不生成最终用户回答。

伪代码：

```python
@dataclass
class QueryVideoTool(FunctionTool[AstrAgentContext]):
    name: str = "query_video"
    ...

    async def call(self, context, **kwargs):
        event = context.context.event
        query = kwargs["query"]
        index = kwargs.get("video_index", 0)
        time_range = kwargs.get("time_range")

        videos = event.get_extra("video_search_assets") or []
        if not videos:
            return "VIDEO_QUERY_ERROR: no video is bound to this request"

        if index < 0 or index >= len(videos):
            return f"VIDEO_QUERY_ERROR: video_index {index} is out of range"

        provider_id = self.config.get("video_search_provider_id")
        if not provider_id:
            return "VIDEO_QUERY_ERROR: video search provider is not configured"

        prompt = build_video_search_prompt(query, time_range)
        return await call_video_provider_through_astrbot(...)
```

`call_video_provider_through_astrbot(...)` 的具体视频参数必须由 `RUNTIME_PROOF.md / CALL-SEAM-01` 确认后再填写，不提前猜测。

## `_conf_schema.json`

最低配置：

```json
{
  "enabled": {
    "type": "bool",
    "description": "启用视频语义搜索",
    "default": true
  },
  "video_search_provider_id": {
    "type": "string",
    "description": "视频搜索模型",
    "hint": "选择一张已经能够读取视频的现有模型卡。",
    "default": "",
    "_special": "select_provider"
  },
  "activation_policy": {
    "type": "string",
    "description": "工具启用策略",
    "options": ["fallback_only", "always_when_video"],
    "default": "fallback_only"
  }
}
```

## 主模型临时提示

仅在工具可用时加入：

```text
当前消息包含可查询视频。
当回答依赖视频内容时，可以调用 query_video；该工具可以重复调用。
如果第一次查询不足，请把仍然缺失的事实转化为新的、更具体的查询。
工具结果是视频观察证据，最终判断仍由你完成。
```

`fallback_only` 模式下，如果主模型不具备视频输入能力，则增加更强约束：

```text
在声称任何视频内事实之前，必须至少调用一次 query_video。
```

## 不在第一版实现

- 跨消息永久视频引用；
- 视频结果长期缓存；
- 视频模型多轮会话状态；
- 自动摘要；
- 分段长视频；
- 多模型投票；
- 抽帧/OCR/STT；
- Provider 自动切换；
- 自动能力探测。

## 开发顺序

```text
A. 完成 CALL-SEAM-01
B. 写 video_binding.py + 单测
C. 写 QueryVideoTool 的纯错误路径 + 单测
D. 接入已证明的视频 Provider 调用缝
E. 注入 Tool 到现有 Agent ToolSet
F. 完成双查询端到端测试
G. 再考虑 README、市场说明和版本发布
```
