import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from astrbot.api.message_components import Image, Record, Reply
from astrbot.core.agent.tool import ToolSet
from astrbot.core.provider.entities import ProviderRequest

from astrbot_plugin_video_understanding.main import VideoSemanticSearchPlugin as ModalityRelayPlugin
from astrbot_plugin_video_understanding.media_binding import bind_audio_from_event, bind_images_from_event
from astrbot_plugin_video_understanding.media_tools import QueryAudioTool, QueryImageTool
from astrbot_plugin_video_understanding.policy import NativeRouteState, get_native_route_state, should_relay


def event_with(*components):
    return SimpleNamespace(
        message_obj=SimpleNamespace(message=list(components)),
        unified_msg_origin="test:umo",
    )


def tool_context(event, host):
    return SimpleNamespace(context=SimpleNamespace(event=event, context=host))


def make_context():
    context = MagicMock()
    manager = MagicMock()
    manager.get_func.return_value = None
    context.get_llm_tool_manager.return_value = manager
    context.get_config.return_value = {}
    context.get_using_provider_async = AsyncMock(
        return_value=SimpleNamespace(provider_config={"modalities": ["text"]})
    )
    context.llm_generate = AsyncMock(
        return_value=SimpleNamespace(completion_text="bootstrap")
    )
    return context


def test_native_route_state_is_three_state_and_provider_neutral():
    provider = SimpleNamespace(provider_config={"modalities": ["text", "image"]})
    assert get_native_route_state(provider, "image") is NativeRouteState.ENABLED
    assert get_native_route_state(provider, "audio") is NativeRouteState.DISABLED
    assert get_native_route_state(
        SimpleNamespace(provider_config={"modalities": []}), "image"
    ) is NativeRouteState.UNKNOWN
    assert get_native_route_state(None, "video") is NativeRouteState.UNKNOWN


def test_adaptive_and_always_policy():
    assert not should_relay("adaptive", NativeRouteState.ENABLED)
    assert should_relay("adaptive", NativeRouteState.DISABLED)
    assert should_relay("adaptive", NativeRouteState.UNKNOWN, unknown_policy="relay")
    assert not should_relay("adaptive", NativeRouteState.UNKNOWN, unknown_policy="native")
    assert should_relay("always", NativeRouteState.ENABLED)


def test_images_and_audio_bind_current_before_quoted():
    current_image = Image.fromURL("https://example.com/current.png")
    quoted_image = Image.fromURL("https://example.com/quoted.png")
    current_audio = Record.fromURL("https://example.com/current.wav")
    quoted_audio = Record.fromURL("https://example.com/quoted.wav")
    event = event_with(
        Reply(id="r1", chain=[quoted_image, quoted_audio]),
        current_image,
        current_audio,
    )
    images = bind_images_from_event(event)
    audio = bind_audio_from_event(event)
    assert [item.source for item in images] == ["current", "quoted"]
    assert [item.index for item in images] == [0, 1]
    assert [item.source for item in audio] == ["current", "quoted"]
    assert [item.index for item in audio] == [0, 1]


@pytest.mark.asyncio
async def test_query_image_rechecks_original_media(monkeypatch):
    image = Image.fromURL("https://example.com/hand.png")

    async def resolve(self):
        return "/tmp/hand.png"

    monkeypatch.setattr(Image, "convert_to_file_path", resolve)
    host = MagicMock()
    host.llm_generate = AsyncMock(
        return_value=SimpleNamespace(completion_text="Six visible fingers.")
    )
    result = await QueryImageTool(provider_id="vision-provider").call(
        tool_context(event_with(image), host),
        query="How many visible fingers are on this hand?",
    )
    call = host.llm_generate.await_args.kwargs
    assert call["image_urls"] == ["/tmp/hand.png"]
    payload = json.loads(result)
    assert payload["modality"] == "image"
    assert payload["evidence"] == "Six visible fingers."


@pytest.mark.asyncio
async def test_query_audio_rechecks_original_media(monkeypatch):
    audio = Record.fromURL("https://example.com/a.wav")

    async def resolve(self):
        return "/tmp/a.wav"

    monkeypatch.setattr(Record, "convert_to_file_path", resolve)
    host = MagicMock()
    host.llm_generate = AsyncMock(
        return_value=SimpleNamespace(completion_text="The speaker says beta.")
    )
    result = await QueryAudioTool(provider_id="audio-provider").call(
        tool_context(event_with(audio), host),
        query="What exact word does the speaker say?",
        time_range="00:01-00:03",
    )
    call = host.llm_generate.await_args.kwargs
    assert call["audio_urls"] == ["/tmp/a.wav"]
    assert "00:01-00:03" in call["prompt"]
    assert json.loads(result)["modality"] == "audio"


@pytest.mark.asyncio
async def test_adaptive_bootstrap_runs_only_when_main_route_lacks_image(monkeypatch):
    image = Image.fromURL("https://example.com/hand.png")

    async def resolve(self):
        return "/tmp/hand.png"

    monkeypatch.setattr(Image, "convert_to_file_path", resolve)
    context = make_context()
    plugin = ModalityRelayPlugin(
        context,
        {
            "enabled": True,
            "relay_mode": "adaptive",
            "image_relay_provider_id": "vision-provider",
            "enable_query_tools": True,
        },
    )
    request = ProviderRequest(
        image_urls=["/tmp/hand.png"],
        func_tool=ToolSet([plugin.query_tools["image"]]),
    )
    await plugin.scope_and_relay(event_with(image), request)
    assert context.llm_generate.await_count == 1
    assert request.image_urls == []
    assert any(
        "<modality_relay" in getattr(part, "text", "")
        for part in request.extra_user_content_parts
    )

    context.llm_generate.reset_mock()
    context.get_using_provider_async = AsyncMock(
        return_value=SimpleNamespace(provider_config={"modalities": ["text", "image"]})
    )
    request2 = ProviderRequest(
        image_urls=["/tmp/hand.png"],
        func_tool=ToolSet([plugin.query_tools["image"]]),
    )
    await plugin.scope_and_relay(event_with(image), request2)
    assert context.llm_generate.await_count == 0
    assert request2.image_urls == ["/tmp/hand.png"]


@pytest.mark.asyncio
async def test_query_tools_are_request_scoped():
    context = make_context()
    plugin = ModalityRelayPlugin(
        context,
        {
            "enabled": True,
            "image_relay_provider_id": "vision-provider",
            "audio_relay_provider_id": "audio-provider",
            "video_relay_provider_id": "video-provider",
        },
    )
    request = ProviderRequest(func_tool=ToolSet(list(plugin.query_tools.values())))
    await plugin.scope_and_relay(event_with(), request)
    assert request.func_tool.get_tool("query_image") is None
    assert request.func_tool.get_tool("query_audio") is None
    assert request.func_tool.get_tool("query_video") is None
