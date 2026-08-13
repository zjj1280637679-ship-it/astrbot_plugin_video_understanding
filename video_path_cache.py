from __future__ import annotations

import os

from astrbot.api.event import AstrMessageEvent

from .video_binding import BoundVideo

_CACHE_KEY = "video_semantic_search_resolved_paths"


def _video_ref(bound: BoundVideo) -> str:
    video = bound.component
    for attr in ("path", "url", "file"):
        value = getattr(video, attr, None)
        if value:
            ref = str(value).strip()
            if ref:
                return ref
    return ""


def _cache(event: AstrMessageEvent) -> dict[str, str] | None:
    getter = getattr(event, "get_extra", None)
    setter = getattr(event, "set_extra", None)
    if not callable(getter) or not callable(setter):
        return None
    try:
        value = getter(_CACHE_KEY)
    except Exception:
        return None
    if isinstance(value, dict):
        return value
    value = {}
    try:
        setter(_CACHE_KEY, value)
    except Exception:
        return None
    return value


def _key(bound: BoundVideo) -> str:
    return f"{bound.source}:{bound.index}:{id(bound.component)}"


def _materialized_source(bound: BoundVideo) -> bool:
    return _video_ref(bound).lower().startswith(
        ("http://", "https://", "data:", "base64://")
    )


async def resolve_bound_video_path(
    event: AstrMessageEvent,
    bound: BoundVideo,
) -> str:
    """Memoize only AstrBot's resolved path for this one message event."""
    cache = _cache(event)
    key = _key(bound)
    if cache is not None:
        path = cache.get(key)
        if path and os.path.exists(path):
            return path
        cache.pop(key, None)

    path = await bound.component.convert_to_file_path()
    if not path:
        return path
    if cache is not None:
        cache[key] = path

    if _materialized_source(bound):
        tracker = getattr(event, "track_temporary_local_file", None)
        if callable(tracker):
            try:
                tracker(path)
            except Exception:
                pass
    return path
