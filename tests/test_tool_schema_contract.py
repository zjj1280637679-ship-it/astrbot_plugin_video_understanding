from astrbot.core.agent.tool import ToolSet

from astrbot_plugin_video_understanding.media_tools import QueryAudioTool, QueryImageTool
from astrbot_plugin_video_understanding.tool import QueryVideoTool


def test_query_tools_support_full_and_skills_like_schema_projection():
    tools = ToolSet(
        [
            QueryImageTool(provider_id="image-provider"),
            QueryAudioTool(provider_id="audio-provider"),
            QueryVideoTool(provider_id="video-provider"),
        ]
    )
    light = tools.get_light_tool_set()
    param_only = tools.get_param_only_tool_set()

    for name in ("query_image", "query_audio", "query_video"):
        full_tool = tools.get_tool(name)
        light_tool = light.get_tool(name)
        param_tool = param_only.get_tool(name)
        assert full_tool is not None
        assert light_tool is not None
        assert param_tool is not None
        assert full_tool.description
        assert light_tool.description
        assert param_tool.parameters

    assert "missing information" in light.get_tool("query_image").description
    assert "existing audio relay" in light.get_tool("query_audio").description
