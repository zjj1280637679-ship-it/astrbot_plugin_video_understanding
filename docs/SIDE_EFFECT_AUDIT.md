# 副作用与漏洞排查记录

更新时间：2026-08-14。

本文件用于区分：

1. 插件自身应修的副作用；
2. AstrBot 已负责、插件不应重复实现的控制；
3. Provider 已负责、插件不应越界接管的传输行为；
4. 仍需真实运行证据才能支持的结论。

## 已修复

### SE-01 无视频会话仍暴露 `query_video`

风险：无视频消息也携带工具 schema，增加上下文噪声，并让模型产生必然失败的工具调用。

修复：`query_video` 先注册到 AstrBot Tool Manager；`on_llm_request` 只在本轮没有当前/引用视频时从 `req.func_tool` 删除本插件工具。

验收：无视频时 `query_video` 被移除；其他工具保持不变。

### SE-02 动态挂载绕过 AstrBot 工具授权

风险：直接在 `on_llm_request` 新建 `ToolSet()` 或重新加入工具，会绕过 AstrBot 已经完成的人格工具白名单、工具停用状态与插件作用域过滤。

修复：插件不再在请求阶段新增工具，只允许“保留 AstrBot 已经允许的 query_video”或“无视频时删除”。

验收：

- `req.func_tool is None` 时插件不创建 ToolSet；
- 人格/宿主没有包含 `query_video` 时插件不加回；
- 有视频且 AstrBot 已允许时才保留。

### SE-03 同名工具覆盖第三方插件

风险：`Context.add_llm_tools()` 对同名工具可以替换已有对象，可能破坏另一个插件。

修复：注册前查询 Tool Manager；如果 `query_video` 已由其他插件占用，则失败封闭并保留现有工具。

### SE-04 视频模型输出破坏结果结构

风险：XML 包裹结果时，恶意/异常视频模型输出可以包含 `</video_search_result>`、伪 `SYSTEM:` 等文本，使边界难以解析。

修复：结果改为 `json.dumps()` 序列化对象，模型文本只进入 `evidence` 字符串字段，并标记：

```json
{
  "trust": "untrusted_external_video_evidence",
  "instruction_authority": "none"
}
```

测试包含伪关闭标签、引号和换行。

### SE-05 固定传输失败哨兵与真实视频内容碰撞

风险：若视频画面真的显示 `VIDEO_INPUT_UNAVAILABLE`，固定字符串会被误判为“模型没收到视频”。

修复：每次查询生成独立随机哨兵；仅当返回值与当次随机哨兵完全一致时判定传输失败。

测试同时证明普通字符串 `VIDEO_INPUT_UNAVAILABLE` 可以作为合法视频证据返回。

### SE-06 异常工具参数放大请求成本

风险：模型产生异常长的 `query` / `time_range` 时，会无意义扩大视频模型提示成本。

修复：Schema 与运行时双重限制：

- `query <= 8000` 字符；
- `time_range <= 256` 字符。

这些上限只限制异常参数，不改变正常自然语言查询能力。

### SE-07 视频附件信封字段注入

风险：显示文件名包含换行或 `, path ` / `, ref ` 等分隔符时，可能破坏当前 AstrBot 附件信封。

修复：显示名移除 CR/LF 并替换保留分隔符；视频路径出现 CR/LF 时直接拒绝。

火山 Provider 端只解析 `extra_user_content_parts` 中的当前请求可信信封，不从普通 prompt/history 中读取相似文本。

## 已排除 / 由 AstrBot 负责

### SE-08 `query_video` 递归调用自身

排除理由：工具内部调用 `Context.llm_generate()`，不传 `tools`，也不启动 `tool_loop_agent()`。因此视频模型是一次性观察调用，无法在这一层递归调用 AstrBot 工具。

### SE-09 主 Agent 无限视频搜索 / 重复收费

责任边界：AstrBot `ToolLoopAgentRunner` 已负责最大 Agent 步数、工具调用超时和重复工具调用提醒。本插件不再建立第二套循环计数器。

注意：不同自然语言查询本来就是本插件的目标行为，会产生多次视频模型请求。管理员应按所选 Provider 的计费方式评估成本。

### SE-10 视频上传复用、压缩和缓存

责任边界：属于 AstrBot / Provider 的媒体传输实现。本插件只提交当前宿主视频契约，不建立供应商上传缓存或转码流水线。

### SE-11 视频来源 URL / 本地路径解析安全

责任边界：`Video.convert_to_file_path()` 与 AstrBot `MediaResolver` 负责平台媒体引用解析。本插件不重新实现下载器、路径权限或 SSRF 规则。

## 数据与隐私副作用

### SE-12 远程视频模型数据外发

事实：收到视频不会自动调用第二个模型；只有主模型实际调用 `query_video` 时，本次视频和子查询才会发送到管理员选择的视频模型卡所属 Provider。

控制：README 与安全文档明确披露；插件不长期保存视频，不复制 API Key，不记录 Base64/完整临时 URL。

### SE-13 主模型与视频搜索模型相同

允许：管理员可以选择同一 Provider/同一模型卡作为视频搜索模型。

副作用：仍会产生一个独立的 `llm_generate` 视频查询请求，因此可能产生额外费用；但不会产生递归 Tool Loop。插件不自动改模型或跳过该调用，因为“是否使用专门的视频搜索步骤”属于管理员配置选择。

## 当前仍需回归验证

以下修复必须重新通过：

1. AstrBot v4.27.3 单测 + 启动加载；
2. 当前 AstrBot master 单测 + 启动加载；
3. 0.1.0 Release Gate 双矩阵；
4. 真实火山方舟 L5：同一视频 ALPHA/BETA 两次查询；
5. 真实 AstrBot L6：ToolLoopAgentRunner 连续两次 `query_video` 并最终综合 ALPHA/BETA。

在 4/5 完成前，不把结构安全修改自动外推为“真实端到端未受影响”。
