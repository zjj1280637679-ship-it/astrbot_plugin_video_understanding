import asyncio
import json
import re
from types import SimpleNamespace

import pytest

from astrbot.api.message_components import Video
from astrbot_plugin_video_understanding.tool import QueryVideoTool


def _tool_context(video, llm_generate):
    event = SimpleNamespace(message_obj=SimpleNamespace(message=[video]))
    host = SimpleNamespace(llm_generate=llm_generate)
    return SimpleNamespace(context=SimpleNamespace(event=event, context=host))


@pytest.mark.asyncio
async def test_same_tool_object_keeps_concurrent_video_queries_isolated(monkeypatch):
    first = Video.fromFileSystem("/tmp/concurrent-alpha.mp4")
    second = Video.fromFileSystem("/tmp/concurrent-beta.mp4")

    async def fake_convert(self):
        await asyncio.sleep(0)
        return str(self.file or self.path or self.url)

    monkeypatch.setattr(Video, "convert_to_file_path", fake_convert)
    seen = {}

    async def first_llm_generate(**kwargs):
        await asyncio.sleep(0.01)
        seen["first"] = kwargs
        return SimpleNamespace(completion_text="ALPHA_EVIDENCE")

    async def second_llm_generate(**kwargs):
        await asyncio.sleep(0)
        seen["second"] = kwargs
        return SimpleNamespace(completion_text="BETA_EVIDENCE")

    tool = QueryVideoTool(provider_id="video-provider")
    first_result, second_result = await asyncio.gather(
        tool.call(_tool_context(first, first_llm_generate), query="FIRST_QUERY", video_index=0),
        tool.call(_tool_context(second, second_llm_generate), query="SECOND_QUERY", video_index=0),
    )

    first_payload = json.loads(first_result)
    second_payload = json.loads(second_result)
    assert first_payload["query"] == "FIRST_QUERY"
    assert first_payload["evidence"] == "ALPHA_EVIDENCE"
    assert second_payload["query"] == "SECOND_QUERY"
    assert second_payload["evidence"] == "BETA_EVIDENCE"

    first_prompt = seen["first"]["prompt"]
    second_prompt = seen["second"]["prompt"]
    assert "FIRST_QUERY" in first_prompt and "SECOND_QUERY" not in first_prompt
    assert "SECOND_QUERY" in second_prompt and "FIRST_QUERY" not in second_prompt

    first_system = seen["first"]["system_prompt"]
    second_system = seen["second"]["system_prompt"]
    assert "FIRST_QUERY" not in first_system
    assert "SECOND_QUERY" not in second_system
    assert "your own video-understanding capability" in first_system
    assert "your own video-understanding capability" in second_system
    assert "read-only semantic search engine" not in first_system
    assert "read-only semantic search engine" not in second_system

    token_pattern = r"VIDEO_INPUT_UNAVAILABLE_[0-9a-f]{32}"
    first_token = re.search(token_pattern, first_system)
    second_token = re.search(token_pattern, second_system)
    assert first_token is not None and second_token is not None
    assert first_token.group(0) != second_token.group(0)
    assert first_token.group(0) not in first_prompt
    assert second_token.group(0) not in second_prompt

    def transport_text(call):
        if "video_urls" in call:
            return " ".join(call["video_urls"])
        return "\n".join(part.text for part in call["extra_user_content_parts"])

    assert "concurrent-alpha.mp4" in transport_text(seen["first"])
    assert "concurrent-beta.mp4" not in transport_text(seen["first"])
    assert "concurrent-beta.mp4" in transport_text(seen["second"])
    assert "concurrent-alpha.mp4" not in transport_text(seen["second"])
