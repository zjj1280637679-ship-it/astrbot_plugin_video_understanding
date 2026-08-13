from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from astrbot.api.message_components import Video
from astrbot_plugin_video_understanding.video_binding import bind_videos_from_event
from astrbot_plugin_video_understanding.video_path_cache import resolve_bound_video_path


class EventStub:
    def __init__(self, video):
        self.message_obj = SimpleNamespace(message=[video])
        self.extras = {}
        self.tracked = []

    def get_extra(self, key):
        return self.extras.get(key)

    def set_extra(self, key, value):
        self.extras[key] = value

    def track_temporary_local_file(self, path):
        self.tracked.append(path)


@pytest.mark.asyncio
async def test_remote_video_is_resolved_once_per_event(monkeypatch, tmp_path: Path):
    video = Video.fromURL("https://example.com/video.mp4")
    local = tmp_path / "video.mp4"
    local.write_bytes(b"video")
    resolver = AsyncMock(return_value=str(local))
    monkeypatch.setattr(Video, "convert_to_file_path", resolver)
    event = EventStub(video)
    bound = bind_videos_from_event(event)[0]
    assert await resolve_bound_video_path(event, bound) == str(local)
    assert await resolve_bound_video_path(event, bound) == str(local)
    assert resolver.await_count == 1
    assert event.tracked == [str(local)]


@pytest.mark.asyncio
async def test_missing_cached_path_is_resolved_again(monkeypatch, tmp_path: Path):
    video = Video.fromURL("https://example.com/video.mp4")
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    first.write_bytes(b"one")
    second.write_bytes(b"two")
    resolver = AsyncMock(side_effect=[str(first), str(second)])
    monkeypatch.setattr(Video, "convert_to_file_path", resolver)
    event = EventStub(video)
    bound = bind_videos_from_event(event)[0]
    assert await resolve_bound_video_path(event, bound) == str(first)
    first.unlink()
    assert await resolve_bound_video_path(event, bound) == str(second)
    assert resolver.await_count == 2
