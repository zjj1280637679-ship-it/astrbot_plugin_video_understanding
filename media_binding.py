from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Image, Record, Reply


@dataclass(slots=True)
class BoundMedia:
    modality: Literal["image", "audio"]
    index: int
    component: object
    source: Literal["current", "quoted"]
    display_name: str


def _message_components(event: AstrMessageEvent) -> list:
    message_obj = getattr(event, "message_obj", None)
    message = getattr(message_obj, "message", None)
    if not isinstance(message, (list, tuple)):
        return []
    return list(message)


def _display_name(component: object, fallback: str) -> str:
    ref = ""
    for attr in ("path", "url", "file"):
        value = getattr(component, attr, None)
        if value:
            ref = str(value).strip()
            if ref:
                break
    if not ref:
        return fallback
    name = os.path.basename(ref.split("?", 1)[0].rstrip("/"))
    return name or fallback


def _bind(event: AstrMessageEvent, *, modality: str, cls: type) -> list[BoundMedia]:
    components = _message_components(event)
    if not components:
        return []
    bound: list[BoundMedia] = []
    for component in components:
        if isinstance(component, cls):
            index = len(bound)
            bound.append(
                BoundMedia(
                    modality=modality,
                    index=index,
                    component=component,
                    source="current",
                    display_name=_display_name(component, f"{modality}_{index}"),
                )
            )
    for component in components:
        if not isinstance(component, Reply):
            continue
        chain = getattr(component, "chain", None)
        if not isinstance(chain, (list, tuple)):
            continue
        for reply_component in chain:
            if isinstance(reply_component, cls):
                index = len(bound)
                bound.append(
                    BoundMedia(
                        modality=modality,
                        index=index,
                        component=reply_component,
                        source="quoted",
                        display_name=_display_name(
                            reply_component, f"{modality}_{index}"
                        ),
                    )
                )
    return bound


def bind_images_from_event(event: AstrMessageEvent) -> list[BoundMedia]:
    return _bind(event, modality="image", cls=Image)


def bind_audio_from_event(event: AstrMessageEvent) -> list[BoundMedia]:
    return _bind(event, modality="audio", cls=Record)
