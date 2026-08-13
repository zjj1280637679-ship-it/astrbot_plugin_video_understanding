import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from astrbot.api.message_components import Video
import astrbot_plugin_video_understanding.tool as tool_module
from astrbot_plugin_video_understanding.tool import QueryVideoTool, build_video_query_prompt


class Event:
    def __init__(self, *components):
        self.message_obj = SimpleNamespace(message=list(components))
        self._extras = {}

    def get_extra(self, key=None, default=None):
        if key is None:
            return self._extras
        return self._extras.get(key, default)

    def set_extra(self, key, value):
        self._extras[key] = value


def tool_context(event, host):
    return SimpleNamespace(context=SimpleNamespace(event=event, context=host))


@pytest.mark.asyncio
async def test_same_video_replays_raw_qa_as_context(monkeypatch):
    video = Video.fromFileSystem("/tmp/context-alpha.mp4")
    event = Event(video)
    calls = []

    async def fake_resolve_path(event, bound):
        return "/tmp/context-alpha.mp4"

    async def fake_resolve_provider(context, provider_id):
        return None

    async def fake_generate(**kwargs):
        calls.append(kwargs)
        answer = "GAMMA" if len(calls) == 1 else "BETA"
        return SimpleNamespace(completion_text=answer)

    monkeypatch.setattr(tool_module, "resolve_bound_video_path", fake_resolve_path)
    monkeypatch.setattr(tool_module, "resolve_transport_provider", fake_resolve_provider)
    host = SimpleNamespace(llm_generate=AsyncMock(side_effect=fake_generate))
    tool = QueryVideoTool(provider_id="video-provider")

    first_query = "Which displayed word contains the letter M?"
    second_query = "What word appeared immediately before it?"

    await tool.call(tool_context(event, host), query=first_query, video_index=0)
    second_raw = await tool.call(
        tool_context(event, host),
        query=second_query,
        video_index=0,
    )

    assert calls[0]["contexts"] == []
    assert calls[1]["contexts"] == [
        {"role": "user", "content": build_video_query_prompt(first_query, "")},
        {"role": "assistant", "content": "GAMMA"},
    ]
    assert "GAMMA" not in calls[1]["prompt"]
    payload = json.loads(second_raw)
    assert payload["evidence"] == "BETA"


@pytest.mark.asyncio
async def test_video_indexes_keep_independent_histories(monkeypatch):
    first = Video.fromFileSystem("/tmp/context-first.mp4")
    second = Video.fromFileSystem("/tmp/context-second.mp4")
    event = Event(first, second)
    calls = []

    async def fake_resolve_path(event, bound):
        return f"/tmp/context-{bound.index}.mp4"

    async def fake_resolve_provider(context, provider_id):
        return None

    async def fake_generate(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(completion_text="OK")

    monkeypatch.setattr(tool_module, "resolve_bound_video_path", fake_resolve_path)
    monkeypatch.setattr(tool_module, "resolve_transport_provider", fake_resolve_provider)
    host = SimpleNamespace(llm_generate=AsyncMock(side_effect=fake_generate))
    tool = QueryVideoTool(provider_id="video-provider")

    await tool.call(tool_context(event, host), query="Question for video zero", video_index=0)
    await tool.call(tool_context(event, host), query="Question for video one", video_index=1)

    assert calls[0]["contexts"] == []
    assert calls[1]["contexts"] == []


@pytest.mark.asyncio
async def test_failed_video_query_does_not_enter_follow_up_context(monkeypatch):
    video = Video.fromFileSystem("/tmp/context-failure.mp4")
    event = Event(video)
    calls = []
    token = "VIDEO_INPUT_UNAVAILABLE_CONTEXT_TEST"

    async def fake_resolve_path(event, bound):
        return "/tmp/context-failure.mp4"

    async def fake_resolve_provider(context, provider_id):
        return None

    async def fake_generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return SimpleNamespace(completion_text=token)
        return SimpleNamespace(completion_text="RECOVERED")

    monkeypatch.setattr(tool_module, "resolve_bound_video_path", fake_resolve_path)
    monkeypatch.setattr(tool_module, "resolve_transport_provider", fake_resolve_provider)
    monkeypatch.setattr(tool_module, "build_video_unavailable_token", lambda: token)
    host = SimpleNamespace(llm_generate=AsyncMock(side_effect=fake_generate))
    tool = QueryVideoTool(provider_id="video-provider")

    first = await tool.call(tool_context(event, host), query="First attempt", video_index=0)
    second = await tool.call(tool_context(event, host), query="Try again", video_index=0)

    assert first.startswith("VIDEO_QUERY_ERROR:")
    assert calls[1]["contexts"] == []
    assert json.loads(second)["evidence"] == "RECOVERED"
