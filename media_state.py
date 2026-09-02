from __future__ import annotations

import os

from astrbot.api.event import AstrMessageEvent

from .media_binding import BoundMedia

_PATH_CACHE_KEY = "modality_relay_resolved_paths"
_HISTORY_KEY = "modality_relay_query_history"
_HISTORY_FALLBACK_ATTR = "_modality_relay_query_history"


def _component_ref(bound: BoundMedia) -> str:
    for attr in ("path", "url", "file"):
        value = getattr(bound.component, attr, None)
        if value:
            ref = str(value).strip()
            if ref:
                return ref
    return ""


def _event_dict(event: object, key: str, fallback_attr: str | None = None) -> dict:
    getter = getattr(event, "get_extra", None)
    setter = getattr(event, "set_extra", None)
    if callable(getter) and callable(setter):
        try:
            value = getter(key)
            if isinstance(value, dict):
                return value
            value = {}
            setter(key, value)
            return value
        except Exception:
            pass
    if fallback_attr:
        value = getattr(event, fallback_attr, None)
        if isinstance(value, dict):
            return value
        value = {}
        try:
            setattr(event, fallback_attr, value)
        except Exception:
            return {}
        return value
    return {}


def get_media_query_contexts(
    event: object, modality: str, provider_id: str, media_index: int
) -> list[dict]:
    store = _event_dict(event, _HISTORY_KEY, _HISTORY_FALLBACK_ATTR)
    key = (str(modality), str(provider_id), int(media_index))
    history = store.get(key, [])
    return [dict(item) for item in history if isinstance(item, dict)]


def append_media_query_turn(
    event: object,
    modality: str,
    provider_id: str,
    media_index: int,
    user_prompt: str,
    assistant_answer: str,
) -> None:
    store = _event_dict(event, _HISTORY_KEY, _HISTORY_FALLBACK_ATTR)
    key = (str(modality), str(provider_id), int(media_index))
    history = store.setdefault(key, [])
    history.extend(
        [
            {"role": "user", "content": str(user_prompt)},
            {"role": "assistant", "content": str(assistant_answer)},
        ]
    )


def _path_key(bound: BoundMedia) -> str:
    return f"{bound.modality}:{bound.source}:{bound.index}:{id(bound.component)}"


async def resolve_bound_media_path(event: AstrMessageEvent, bound: BoundMedia) -> str:
    cache = _event_dict(event, _PATH_CACHE_KEY)
    key = _path_key(bound)
    path = cache.get(key)
    if path and os.path.exists(path):
        return path
    cache.pop(key, None)

    resolver = getattr(bound.component, "convert_to_file_path", None)
    if not callable(resolver):
        raise ValueError(f"{bound.modality} component has no media resolver")
    path = await resolver()
    if not path:
        raise ValueError(f"{bound.modality} resolver returned an empty path")
    cache[key] = path

    ref = _component_ref(bound).lower()
    if ref.startswith(("http://", "https://", "data:", "base64://")):
        tracker = getattr(event, "track_temporary_local_file", None)
        if callable(tracker):
            try:
                tracker(path)
            except Exception:
                pass
    return path
