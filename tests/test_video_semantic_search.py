from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from astrbot.api.message_components import Video

from ..tool import QueryVideoTool, VIDEO_INPUT_UNAVAILABLE, build_video_query_prompt
from ..video_binding import bind_videos_from_event


def _event_with(*components):
    event = MagicMock()
    event.message_obj = MagicMock()
    event.message_obj.message = list(components)
    return event


def _tool_context(event, astrbot_context=None):
    return SimpleNamespace(
        context=SimpleNamespace(
            event=event,
            context=astrbot_context or MagicMock(),
        )
    )


def test_bind_current_videos_preserves_order():
    first = Video.fromURL("https://example.com/alpha.mp4")
    second = Video.fromURL("https://example.com/beta.mp4")

    bound = bind_videos_from_event(_event_with(first, second))

    assert [item.index for item in bound] == [0, 1]
    assert [item.source for item in bound] == ["current", "current"]
    assert [item.display_name for item in bound] == ["alpha.mp4", "beta.mp4"]
    assert [item.component for item in bound] == [first, second]


def test_video_query_prompt_is_query_scoped():
    prompt = build_video_query_prompt(
        "When does BETA first appear?", "00:01-00:05"
    )

    assert "When does BETA first appear?" in prompt
    assert "00:01-00:05" in prompt
    assert VIDEO_INPUT_UNAVAILABLE in prompt
    assert "general summary" in prompt


@pytest.mark.asyncio
async def test_query_video_fails_closed_without_video():
    tool = QueryVideoTool(provider_id="video-provider")

    result = await tool.call(
        _tool_context(_event_with()),
        query="What happens?",
    )

    assert result == (
        "VIDEO_QUERY_ERROR: no video exists in the current or quoted message"
    )


@pytest.mark.asyncio
async def test_query_video_passes_video_urls_to_astrbot(monkeypatch):
    video = Video.fromURL("https://example.com/alpha.mp4")

    async def fake_convert_to_file_path(self):
        return "/tmp/alpha.mp4"

    monkeypatch.setattr(Video, "convert_to_file_path", fake_convert_to_file_path)

    astrbot_context = MagicMock()
    astrbot_context.llm_generate = AsyncMock(
        return_value=SimpleNamespace(
            completion_text="BETA first appears at about 00:02."
        )
    )
    tool = QueryVideoTool(provider_id="video-provider")

    result = await tool.call(
        _tool_context(_event_with(video), astrbot_context),
        query="When does BETA first appear?",
        video_index=0,
        time_range="00:00-00:05",
    )

    call = astrbot_context.llm_generate.await_args.kwargs
    assert call["chat_provider_id"] == "video-provider"
    assert call["video_urls"] == ["/tmp/alpha.mp4"]
    assert "When does BETA first appear?" in call["prompt"]
    assert "00:00-00:05" in call["prompt"]
    assert "BETA first appears" in result


@pytest.mark.asyncio
async def test_query_video_rejects_transport_sentinel(monkeypatch):
    video = Video.fromURL("https://example.com/alpha.mp4")

    async def fake_convert_to_file_path(self):
        return "/tmp/alpha.mp4"

    monkeypatch.setattr(Video, "convert_to_file_path", fake_convert_to_file_path)

    astrbot_context = MagicMock()
    astrbot_context.llm_generate = AsyncMock(
        return_value=SimpleNamespace(completion_text=VIDEO_INPUT_UNAVAILABLE)
    )
    tool = QueryVideoTool(provider_id="video-provider")

    result = await tool.call(
        _tool_context(_event_with(video), astrbot_context),
        query="What is on screen?",
    )

    assert result.startswith("VIDEO_QUERY_ERROR:")
    assert "did not receive a usable video" in result
