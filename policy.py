from __future__ import annotations

from enum import Enum
from typing import Mapping


class NativeRouteState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class RelayMode(str, Enum):
    ALWAYS = "always"
    ADAPTIVE = "adaptive"


def get_native_route_state(provider: object | None, modality: str) -> NativeRouteState:
    """Read AstrBot's canonical model-card modalities without guessing capability."""
    if provider is None:
        return NativeRouteState.UNKNOWN
    provider_config = getattr(provider, "provider_config", None)
    if not isinstance(provider_config, Mapping):
        return NativeRouteState.UNKNOWN
    modalities = provider_config.get("modalities")
    if not isinstance(modalities, list) or not modalities:
        return NativeRouteState.UNKNOWN
    normalized = {
        str(value).strip().lower() for value in modalities if str(value).strip()
    }
    return (
        NativeRouteState.ENABLED
        if str(modality).strip().lower() in normalized
        else NativeRouteState.DISABLED
    )


def should_relay(
    mode: str,
    native_state: NativeRouteState,
    *,
    unknown_policy: str = "relay",
) -> bool:
    normalized_mode = str(mode or RelayMode.ADAPTIVE.value).strip().lower()
    if normalized_mode == RelayMode.ALWAYS.value:
        return True
    if native_state is NativeRouteState.ENABLED:
        return False
    if native_state is NativeRouteState.DISABLED:
        return True
    return str(unknown_policy or "relay").strip().lower() != "native"
