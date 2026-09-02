from __future__ import annotations

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star

from .media_binding import bind_audio_from_event, bind_images_from_event
from .media_tools import QueryAudioTool, QueryImageTool
from .policy import get_native_route_state, should_relay
from .relay import build_relay_block, safe_bootstrap
from .tool import QueryVideoTool
from .video_binding import bind_videos_from_event

VERSION = "0.2.0"
PLUGIN_PACKAGE = "astrbot_plugin_video_understanding"


def _belongs_to_this_plugin(tool) -> bool:
    if isinstance(tool, (QueryImageTool, QueryAudioTool, QueryVideoTool)):
        return True
    module_path = str(getattr(tool, "handler_module_path", "") or "")
    if PLUGIN_PACKAGE in module_path.split("."):
        return True
    return PLUGIN_PACKAGE in str(getattr(tool.__class__, "__module__", "") or "")


class VideoSemanticSearchPlugin(Star):
    """Request-scoped multimodal relay for AstrBot."""

    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else {}
        self.enabled = bool(self.config.get("enabled", True))
        self.relay_mode = str(self.config.get("relay_mode") or "adaptive").strip().lower()
        self.unknown_native_route = str(
            self.config.get("unknown_native_route") or "relay"
        ).strip().lower()
        self.enable_query_tools = bool(self.config.get("enable_query_tools", True))
        self.provider_ids = {
            "image": str(self.config.get("image_relay_provider_id") or "").strip(),
            "audio": str(self.config.get("audio_relay_provider_id") or "").strip(),
            "video": str(
                self.config.get("video_relay_provider_id")
                or self.config.get("video_search_provider_id")
                or ""
            ).strip(),
        }
        # Backward-compatible public handles from the original video-only plugin.
        self.provider_id = self.provider_ids["video"]
        self.query_video_tool: QueryVideoTool | None = None

        self.bootstrap_prompts = {
            "image": str(self.config.get("image_bootstrap_prompt") or "").strip(),
            "audio": str(self.config.get("audio_bootstrap_prompt") or "").strip(),
            "video": str(self.config.get("video_bootstrap_prompt") or "").strip(),
        }
        self.query_tools: dict[str, object] = {}
        self._warned_conflicts: set[str] = set()

        if not self.enabled:
            logger.info("[modality-relay] disabled")
            return

        if self.enable_query_tools:
            self._register_query_tools()
        self.query_video_tool = self.query_tools.get("video")

        logger.info(
            "[modality-relay] loaded version=%s mode=%s query_tools=%s "
            "providers(image=%s,audio=%s,video=%s)",
            VERSION,
            self.relay_mode,
            self.enable_query_tools,
            bool(self.provider_ids["image"]),
            bool(self.provider_ids["audio"]),
            bool(self.provider_ids["video"]),
        )

    def _register_query_tools(self) -> None:
        candidates = {
            "image": QueryImageTool(
                provider_id=self.provider_ids["image"], handler_module_path=__name__
            ),
            "audio": QueryAudioTool(
                provider_id=self.provider_ids["audio"], handler_module_path=__name__
            ),
            "video": QueryVideoTool(
                provider_id=self.provider_ids["video"], handler_module_path=__name__
            ),
        }
        manager = self.context.get_llm_tool_manager()
        to_add = []
        for modality, tool in candidates.items():
            if not self.provider_ids[modality]:
                continue
            existing = manager.get_func(tool.name)
            if existing is not None and not _belongs_to_this_plugin(existing):
                logger.error(
                    "[modality-relay] %s name collision; existing tool kept", tool.name
                )
                continue
            self.query_tools[modality] = tool
            to_add.append(tool)
        if to_add:
            self.context.add_llm_tools(*to_add)

    async def _resolve_current_provider(self, event: AstrMessageEvent):
        selected = None
        getter = getattr(event, "get_extra", None)
        if callable(getter):
            try:
                selected = getter("selected_provider")
            except Exception:
                selected = None
        if isinstance(selected, str) and selected.strip():
            provider_getter = getattr(self.context, "get_provider_by_id", None)
            if callable(provider_getter):
                try:
                    provider = provider_getter(selected.strip())
                    if hasattr(provider, "__await__"):
                        provider = await provider
                    if provider is not None:
                        return provider
                except Exception:
                    pass

        async_getter = getattr(self.context, "get_using_provider_async", None)
        if callable(async_getter):
            try:
                return await async_getter(umo=getattr(event, "unified_msg_origin", None))
            except TypeError:
                try:
                    return await async_getter()
                except Exception:
                    pass
            except Exception:
                pass
        return None

    def _bindings(self, event: AstrMessageEvent) -> dict[str, list]:
        return {
            "image": bind_images_from_event(event),
            "audio": bind_audio_from_event(event),
            "video": bind_videos_from_event(event),
        }

    def _scope_query_tools(self, req: ProviderRequest, bindings: dict[str, list]) -> None:
        if req.func_tool is None:
            return
        for modality, tool in self.query_tools.items():
            request_tool = req.func_tool.get_tool(tool.name)
            if request_tool is None or not _belongs_to_this_plugin(request_tool):
                continue
            if not bindings.get(modality):
                req.func_tool.remove_tool(tool.name)

    async def scope_query_video(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """Compatibility shim for v0.1 tests and integrations.

        This keeps the old public request-scoping handle without registering a
        second AstrBot hook or running the v0.2 passive relay twice.
        """
        self._scope_query_tools(
            req,
            {"image": [], "audio": [], "video": bind_videos_from_event(event)},
        )

    def _read_host_config(self, event: AstrMessageEvent) -> dict:
        getter = getattr(self.context, "get_config", None)
        if not callable(getter):
            return {}
        try:
            cfg = getter(umo=getattr(event, "unified_msg_origin", None))
        except TypeError:
            try:
                cfg = getter()
            except Exception:
                return {}
        except Exception:
            return {}
        return cfg if isinstance(cfg, dict) else {}

    def _warn_builtin_conflicts(self, event: AstrMessageEvent) -> None:
        cfg = self._read_host_config(event)
        provider_settings = cfg.get("provider_settings", {})
        if (
            isinstance(provider_settings, dict)
            and provider_settings.get("default_image_caption_provider_id")
            and "image_caption" not in self._warned_conflicts
        ):
            self._warned_conflicts.add("image_caption")
            logger.warning(
                "[modality-relay] AstrBot request image caption is still configured. "
                "Leave provider_settings.default_image_caption_provider_id empty when "
                "Relay owns request images."
            )

        stt_settings = cfg.get("provider_stt_settings", {})
        if (
            isinstance(stt_settings, dict)
            and stt_settings.get("enable", False)
            and "stt" not in self._warned_conflicts
        ):
            self._warned_conflicts.add("stt")
            logger.warning(
                "[modality-relay] AstrBot preprocessing STT is enabled and can replace "
                "Record components before query_audio sees them. Disable it when Relay "
                "owns request audio."
            )

    async def _relay_one_modality(
        self,
        *,
        modality: str,
        event: AstrMessageEvent,
        req: ProviderRequest,
        bindings: list,
        main_provider,
    ) -> None:
        if not bindings:
            return

        native_state = get_native_route_state(main_provider, modality)
        if not should_relay(
            self.relay_mode,
            native_state,
            unknown_policy=self.unknown_native_route,
        ):
            logger.debug(
                "[modality-relay] native route kept modality=%s state=%s",
                modality,
                native_state.value,
            )
            return

        relay_provider_id = self.provider_ids.get(modality, "")
        if not relay_provider_id:
            logger.warning(
                "[modality-relay] relay required but no %s relay provider is configured",
                modality,
            )
            return

        successes = 0
        for bound in bindings:
            text = await safe_bootstrap(
                modality=modality,
                event=event,
                astrbot_context=self.context,
                provider_id=relay_provider_id,
                bound=bound,
                prompt=self.bootstrap_prompts.get(modality, ""),
            )
            if not text:
                continue
            req.extra_user_content_parts.append(
                build_relay_block(
                    modality=modality,
                    index=bound.index,
                    source=bound.source,
                    text=text,
                )
            )
            successes += 1

        if successes == len(bindings):
            if modality == "image":
                req.image_urls = []
            elif modality == "audio":
                req.audio_urls = []

    @filter.on_llm_request()
    async def scope_and_relay(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        if not self.enabled:
            return

        self._warn_builtin_conflicts(event)
        bindings = self._bindings(event)
        self._scope_query_tools(req, bindings)
        if not any(bindings.values()):
            return

        main_provider = await self._resolve_current_provider(event)
        for modality in ("image", "audio", "video"):
            await self._relay_one_modality(
                modality=modality,
                event=event,
                req=req,
                bindings=bindings[modality],
                main_provider=main_provider,
            )
