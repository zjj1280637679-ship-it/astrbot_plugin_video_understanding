from __future__ import annotations

from dataclasses import fields as dataclass_fields

from astrbot.core.agent.message import TextPart
from astrbot.core.provider.entities import ProviderRequest

from .video_binding import BoundVideo


def provider_request_has_native_video_urls() -> bool:
    """Return whether the running AstrBot host exposes native video_urls."""

    try:
        return any(
            field.name == "video_urls" for field in dataclass_fields(ProviderRequest)
        )
    except TypeError:
        return "video_urls" in getattr(ProviderRequest, "__annotations__", {})


def _safe_marker_name(bound: BoundVideo) -> str:
    name = str(bound.display_name or f"video_{bound.index}")
    name = name.replace("\r", " ").replace("\n", " ")
    name = name.replace(", path ", "_path_").replace(", ref ", "_ref_")
    name = " ".join(name.split())
    return name[:160] or f"video_{bound.index}"


def build_video_attachment_marker(bound: BoundVideo, video_path: str) -> str:
    """Mirror AstrBot's current trusted video attachment envelope."""

    path = str(video_path or "")
    if not path:
        raise ValueError("video path is empty")
    if "\r" in path or "\n" in path:
        raise ValueError("video path contains unsupported control characters")

    quoted = " in quoted message" if bound.source == "quoted" else ""
    return (
        f"[Video Attachment{quoted}: name {_safe_marker_name(bound)}, "
        f"path {path}]"
    )


def build_video_transport_kwargs(bound: BoundVideo, video_path: str) -> dict:
    """Build the thinnest video input accepted by the running AstrBot host."""

    if provider_request_has_native_video_urls():
        return {"video_urls": [video_path]}

    return {
        "extra_user_content_parts": [
            TextPart(text=build_video_attachment_marker(bound, video_path))
        ]
    }
