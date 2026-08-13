from unittest.mock import MagicMock

import pytest

from astrbot.api.message_components import Video
from astrbot.core.agent.tool import ToolSet
from astrbot.core.provider.entities import ProviderRequest
from astrbot_plugin_video_understanding.main import VideoSemanticSearchPlugin
from astrbot_plugin_video_understanding.tool import QueryVideoTool


def _event():
    event = MagicMock()
    event.message_obj = MagicMock()
    event.message_obj.message = [Video.fromURL("https://example.com/video.mp4")]
    return event


def _plugin():
    return VideoSemanticSearchPlugin(
        MagicMock(),
        {"enabled": True, "video_search_provider_id": "video-provider"},
    )


@pytest.mark.asyncio
async def test_request_scoped_injection_is_idempotent():
    plugin = _plugin()
    request = ProviderRequest()
    event = _event()
    await plugin.inject_query_video(event, request)
    await plugin.inject_query_video(event, request)
    assert request.func_tool is not None
    assert len(request.func_tool.tools) == 1
    assert request.func_tool.get_tool("query_video") is plugin.query_video_tool


@pytest.mark.asyncio
async def test_existing_query_video_tool_is_not_overwritten():
    plugin = _plugin()
    existing = QueryVideoTool(provider_id="other-provider")
    request = ProviderRequest(func_tool=ToolSet([existing]))
    await plugin.inject_query_video(_event(), request)
    assert request.func_tool is not None
    assert request.func_tool.get_tool("query_video") is existing
