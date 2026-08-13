from astrbot.api import logger
from astrbot.api.star import Context, Star

from .tool import QueryVideoTool

VERSION = "0.1.0"


class VideoSemanticSearchPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else {}
        self.enabled = bool(self.config.get("enabled", True))
        self.video_search_provider_id = str(
            self.config.get("video_search_provider_id") or ""
        ).strip()

        if self.enabled and self.video_search_provider_id:
            self.query_video_tool = QueryVideoTool(
                provider_id=self.video_search_provider_id,
                handler_module_path=__name__,
            )
            self.context.add_llm_tools(self.query_video_tool)
            logger.info(
                "[video-semantic-search] query_video registered version=%s",
                VERSION,
            )
        else:
            self.query_video_tool = None
            logger.info(
                "[video-semantic-search] tool not registered; enabled=%s provider_configured=%s",
                self.enabled,
                bool(self.video_search_provider_id),
            )
