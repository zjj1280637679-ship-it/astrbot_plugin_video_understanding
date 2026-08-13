from __future__ import annotations

from dataclasses import fields as dataclass_fields

from astrbot.core.agent.message import TextPart
from astrbot.core.provider.entities import ProviderRequest

from .video_binding import BoundVideo


def provider_request_has_native_video_urls() -> bool:
    """Return whether the running AstrBot host exposes native video_urls.

    This probes only the host request contract. It does not infer model or
    provider capability.
    """

    try:
        return any(field.name == "video_urls" for field in dataclass_fields(ProviderRequest))
    except TypeError:
        return "video_urls" in getattr(ProviderRequest, "__annotations__", {})


def build_video_attachment_marker(bound: BoundVideo, video_path: str) -> str:
    """Mirror AstrBot's current trusted video attachment envelope."""

    quoted = " in quoted message" if bound.source == "quoted" else ""
    return (
        f"[Video Attachment{quoted}: name {bound.display_name}, "
        f"path {video_path}]"
    )


def build_video_transport_kwargs(bound: BoundVideo, video_path: str) -> dict:
    """Build the thinnest video input accepted by the running AstrBot host.

    Newer hosts with a native ``ProviderRequest.video_urls`` field receive that
    field directly. Current v4.27.x hosts receive the framework's own trusted
    current-request video attachment envelope through ``extra_user_content_parts``.

    Provider-specific serialization remains the selected Provider's job.
    """

    if provider_request_has_native_video_urls():
        return {"video_urls": [video_path]}

    return {
        "extra_user_content_parts": [
            TextPart(text=build_video_attachment_marker(bound, video_path))
        ]
    }
