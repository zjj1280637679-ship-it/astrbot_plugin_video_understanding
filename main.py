from astrbot.api.star import Context, Star


class VideoSemanticSearchPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else {}
