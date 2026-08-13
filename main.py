from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star
from astrbot.core.agent.tool import ToolSet

from .tool import QueryVideoTool
from .video_binding import bind_videos_from_event

VERSION = "0.1.0"


class VideoSemanticSearchPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else {}
        self.enabled = bool(self.config.get("enabled", True))
        self.video_search_provider_id = str(
            self.config.get("video_search_provider_id") or ""
        ).strip()
        self.query_video_tool = None
        if self.enabled and self.video_search_provider_id:
            self.query_video_tool = QueryVideoTool(
                provider_id=self.video_search_provider_id,
                handler_module_path=__name__,
            )
            logger.info(
                "[video-semantic-search] query_video prepared version=%s; injected only for requests containing video",
                VERSION,
            )
        else:
            logger.info(
                "[video-semantic-search] tool unavailable; enabled=%s provider_configured=%s",
                self.enabled,
                bool(self.video_search_provider_id),
            )

    @filter.on_llm_request()
    async def inject_query_video(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
    ) -> None:
        tool = self.query_video_tool
        if tool is None or not bind_videos_from_event(event):
            return
        if req.func_tool is None:
            req.func_tool = ToolSet()
        existing = req.func_tool.get_tool(tool.name)
        if existing is tool:
            return
        if existing is not None:
            logger.warning(
                "[video-semantic-search] query_video name collision; existing tool kept"
            )
            return
        req.func_tool.add_tool(tool)
