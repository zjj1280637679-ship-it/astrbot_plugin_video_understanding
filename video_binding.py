from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Reply, Video


@dataclass(slots=True)
class BoundVideo:
    index: int
    component: Video
    source: Literal["current", "quoted"]
    display_name: str


def _display_name(video: Video, fallback: str) -> str:
    ref = ""
    for attr in ("path", "url", "file"):
        value = getattr(video, attr, None)
        if value:
            ref = str(value).strip()
            if ref:
                break
    if not ref:
        return fallback
    name = os.path.basename(ref.split("?", 1)[0].rstrip("/"))
    return name or fallback


def _message_components(event: AstrMessageEvent) -> list:
    message_obj = getattr(event, "message_obj", None)
    message = getattr(message_obj, "message", None)
    if not isinstance(message, (list, tuple)):
        return []
    return list(message)


def bind_videos_from_event(event: AstrMessageEvent) -> list[BoundVideo]:
    components = _message_components(event)
    if not components:
        return []

    bound: list[BoundVideo] = []

    for component in components:
        if isinstance(component, Video):
            index = len(bound)
            bound.append(
                BoundVideo(
                    index=index,
                    component=component,
                    source="current",
                    display_name=_display_name(component, f"video_{index}"),
                )
            )

    for component in components:
        if not isinstance(component, Reply):
            continue
        chain = getattr(component, "chain", None)
        if not isinstance(chain, (list, tuple)):
            continue
        for reply_component in chain:
            if isinstance(reply_component, Video):
                index = len(bound)
                bound.append(
                    BoundVideo(
                        index=index,
                        component=reply_component,
                        source="quoted",
                        display_name=_display_name(reply_component, f"video_{index}"),
                    )
                )

    return bound
