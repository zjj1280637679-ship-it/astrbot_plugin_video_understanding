from unittest.mock import MagicMock

import pytest

from astrbot.api.message_components import Video
from astrbot.core.agent.tool import FunctionTool, ToolSet
from astrbot.core.provider.entities import ProviderRequest
from astrbot_plugin_video_understanding.main import VideoSemanticSearchPlugin


def _event():
    event = MagicMock()
    event.message_obj = MagicMock()
    event.message_obj.message = [Video.fromURL("https://example.com/video.mp4")]
    return event


def _plugin(existing=None):
    context = MagicMock()
    manager = MagicMock()
    manager.get_func.return_value = existing
    context.get_llm_tool_manager.return_value = manager
    plugin = VideoSemanticSearchPlugin(
        context,
        {"enabled": True, "video_search_provider_id": "video-provider"},
    )
    return plugin, context


@pytest.mark.asyncio
async def test_request_scoping_is_idempotent_for_authorized_tool():
    plugin, _ = _plugin()
    request = ProviderRequest(func_tool=ToolSet([plugin.query_video_tool]))
    event = _event()
    await plugin.scope_query_video(event, request)
    await plugin.scope_query_video(event, request)
    assert request.func_tool is not None
    assert len(request.func_tool.tools) == 1
    assert request.func_tool.get_tool("query_video") is plugin.query_video_tool


def test_existing_third_party_query_video_is_not_overwritten():
    existing = FunctionTool(
        name="query_video",
        description="third party",
        parameters={"type": "object", "properties": {}},
    )
    existing.handler_module_path = "plugins.other_video_plugin.main"
    plugin, context = _plugin(existing=existing)
    assert plugin.query_video_tool is None
    context.add_llm_tools.assert_not_called()
