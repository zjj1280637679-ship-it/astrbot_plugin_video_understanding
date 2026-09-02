# GitHub Verification Environment

## Runtime matrix

Release baselines:

- `v4.27.4`
- `v4.28.0-beta.1`

Forward watch:

- `master` (allowed to fail without blocking a stable release)

Every real-runtime node clones the exact AstrBot ref, installs it with `uv sync`, initializes a clean data directory, installs this plugin into `data/plugins`, runs the plugin test suite, probes the host contracts actually used by the plugin, starts AstrBot, and uploads runtime evidence.

## Tool-schema contract

CI verifies that `query_image`, `query_audio`, and `query_video` survive AstrBot's full, light, and parameter-only ToolSet projections. It also runs AstrBot's own skills-like re-query context regression when available, because the first-pass `<modality_relay>` must remain visible in the second stage.

## Volcengine integration

A separate workflow installs both this Relay plugin and `zjj1280637679-ship-it/astrbot_plugin_volcengine_provider@main`. The combination must load without direct imports between the plugins and without live API credentials.

## Live provider smoke

Paid-provider smoke tests should be manual `workflow_dispatch` jobs with repository Secrets. Normal PR CI validates host/runtime contracts without consuming API quota.

## Architecture guard

Runtime Python files must not add vendor SDKs, OCR/STT/FFmpeg fallback trees, or imports of the Volcengine plugin. AstrBot remains the host and Provider owner.
