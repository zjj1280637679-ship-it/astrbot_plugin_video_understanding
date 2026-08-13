from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star

from .tool import QueryVideoTool
from .video_binding import bind_videos_from_event

VERSION = "0.1.0"
PLUGIN_PACKAGE = "astrbot_plugin_video_understanding"


def _belongs_to_this_plugin(tool) -> bool:
    if isinstance(tool, QueryVideoTool):
        return True
    module_path = str(getattr(tool, "handler_module_path", "") or "")
    return PLUGIN_PACKAGE in module_path.split(".")


class VideoSemanticSearchPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else {}
        self.enabled = bool(self.config.get("enabled", True))
        self.video_search_provider_id = str(
            self.config.get("video_search_provider_id") or ""
        ).strip()
        self.query_video_tool = None

        if not self.enabled or not self.video_search_provider_id:
            logger.info(
                "[video-semantic-search] tool unavailable; enabled=%s provider_configured=%s",
                self.enabled,
                bool(self.video_search_provider_id),
            )
            return

        tool_manager = self.context.get_llm_tool_manager()
        existing = tool_manager.get_func("query_video")
        if existing is not None and not _belongs_to_this_plugin(existing):
            logger.error(
                "[video-semantic-search] query_video name collision; existing tool kept"
            )
            return

        self.query_video_tool = QueryVideoTool(
            provider_id=self.video_search_provider_id,
            handler_module_path=__name__,
        )
        self.context.add_llm_tools(self.query_video_tool)
        logger.info(
            "[video-semantic-search] query_video registered version=%s; "
            "AstrBot tool policy is authoritative and video-less requests hide it",
            VERSION,
        )

    @filter.on_llm_request()
    async def scope_query_video(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
    ) -> None:
        tool = self.query_video_tool
        if tool is None or req.func_tool is None:
            return

        request_tool = req.func_tool.get_tool(tool.name)
        if request_tool is None or not _belongs_to_this_plugin(request_tool):
            return
        if bind_videos_from_event(event):
            return
        req.func_tool.remove_tool(tool.name)
