import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from astrbot.api.message_components import Video
import astrbot_plugin_video_understanding.tool as tool_module
from astrbot_plugin_video_understanding.tool import QueryVideoTool
from astrbot_plugin_video_understanding.transport import (
    build_video_transport_kwargs,
    provider_accepts_native_video_urls,
)
from astrbot_plugin_video_understanding.video_binding import bind_videos_from_event


def _context(video, host):
    event = SimpleNamespace(message_obj=SimpleNamespace(message=[video]))
    return SimpleNamespace(context=SimpleNamespace(event=event, context=host))


class NativeProvider:
    async def text_chat(self, prompt=None, video_urls=None, **kwargs):
        return None


class LegacyProvider:
    async def text_chat(self, prompt=None, **kwargs):
        return None


def test_transport_negotiation_requires_explicit_provider_contract():
    video = Video.fromURL("https://example.com/video.mp4")
    bound = bind_videos_from_event(
        SimpleNamespace(message_obj=SimpleNamespace(message=[video]))
    )[0]

    assert provider_accepts_native_video_urls(NativeProvider()) is True
    assert build_video_transport_kwargs(
        bound,
        "/tmp/video.mp4",
        provider=NativeProvider(),
    ) == {"video_urls": ["/tmp/video.mp4"]}

    assert provider_accepts_native_video_urls(LegacyProvider()) is False
    legacy = build_video_transport_kwargs(
        bound,
        "/tmp/video.mp4",
        provider=LegacyProvider(),
    )
    assert "video_urls" not in legacy
    assert len(legacy["extra_user_content_parts"]) == 1

    conservative = build_video_transport_kwargs(bound, "/tmp/video.mp4", provider=None)
    assert "video_urls" not in conservative


@pytest.mark.asyncio
async def test_unavailable_token_at_response_start_fails_closed(monkeypatch):
    video = Video.fromURL("https://example.com/video.mp4")

    async def fake_convert(self):
        return "/tmp/video.mp4"

    token = "VIDEO_INPUT_UNAVAILABLE_TEST_NONCE"
    monkeypatch.setattr(Video, "convert_to_file_path", fake_convert)
    monkeypatch.setattr(tool_module, "build_video_unavailable_token", lambda: token)
    host = SimpleNamespace(
        llm_generate=AsyncMock(
            return_value=SimpleNamespace(
                completion_text=token + " because no usable video was attached"
            )
        )
    )

    result = await QueryVideoTool(provider_id="p").call(
        _context(video, host), query="What is visible?"
    )
    assert result.startswith("VIDEO_QUERY_ERROR:")
    assert "did not receive a usable video" in result


@pytest.mark.asyncio
async def test_token_mentioned_later_in_normal_evidence_is_not_false_failure(monkeypatch):
    video = Video.fromURL("https://example.com/video.mp4")

    async def fake_convert(self):
        return "/tmp/video.mp4"

    token = "VIDEO_INPUT_UNAVAILABLE_TEST_NONCE"
    evidence = f"The screen is normal. Diagnostic text later mentions {token}."
    monkeypatch.setattr(Video, "convert_to_file_path", fake_convert)
    monkeypatch.setattr(tool_module, "build_video_unavailable_token", lambda: token)
    host = SimpleNamespace(
        llm_generate=AsyncMock(
            return_value=SimpleNamespace(completion_text=evidence)
        )
    )

    result = await QueryVideoTool(provider_id="p").call(
        _context(video, host), query="Read the diagnostic text"
    )
    payload = json.loads(result)
    assert payload["type"] == "video_search_result"
    assert payload["evidence"] == evidence
