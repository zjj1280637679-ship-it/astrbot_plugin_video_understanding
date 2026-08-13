from __future__ import annotations

import inspect

from astrbot.core.agent.message import TextPart

from .video_binding import BoundVideo


def provider_accepts_native_video_urls(provider: object | None) -> bool:
    """Check the selected Provider transport contract, not model capability."""
    if provider is None:
        return False
    text_chat = getattr(provider, "text_chat", None)
    if not callable(text_chat):
        return False
    try:
        return "video_urls" in inspect.signature(text_chat).parameters
    except (TypeError, ValueError):
        return False


def _safe_marker_name(bound: BoundVideo) -> str:
    name = str(bound.display_name or f"video_{bound.index}")
    name = name.replace("\r", " ").replace("\n", " ")
    name = name.replace(", path ", "_path_").replace(", ref ", "_ref_")
    name = " ".join(name.split())
    return name[:160] or f"video_{bound.index}"


def build_video_attachment_marker(bound: BoundVideo, video_path: str) -> str:
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


def build_video_transport_kwargs(
    bound: BoundVideo,
    video_path: str,
    *,
    provider: object | None = None,
) -> dict:
    """Use native video only when the selected Provider explicitly exposes it."""
    if provider_accepts_native_video_urls(provider):
        return {"video_urls": [video_path]}

    return {
        "extra_user_content_parts": [
            TextPart(text=build_video_attachment_marker(bound, video_path))
        ]
    }
