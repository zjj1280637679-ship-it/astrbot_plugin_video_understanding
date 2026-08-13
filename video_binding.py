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
    ref = str(video.path or video.url or video.file or "").strip()
    if not ref:
        return fallback
    name = os.path.basename(ref.split("?", 1)[0].rstrip("/"))
    return name or fallback


def bind_videos_from_event(event: AstrMessageEvent) -> list[BoundVideo]:
    """Bind current videos first, then videos embedded in replies."""

    bound: list[BoundVideo] = []

    for component in event.message_obj.message:
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

    for component in event.message_obj.message:
        if not isinstance(component, Reply) or not component.chain:
            continue
        for reply_component in component.chain:
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
