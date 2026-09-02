# v0.2 Architecture

## Mathematical model

Ideal native multimodal response:

\[
Z_1 = F(X,Y)
\]

Relay path begins with a generic first pass:

\[
T_0 = G(Y)
\]

Let the current question require evidence \(E=\Psi(X)\). The remaining information residual is:

\[
R_k = E - Info(T_0,\ldots,T_k)
\]

If that residual can still change the final answer, the main model compiles it into a focused media query \(q_{k+1}=\Gamma(R_k)\), and the matching `query_*` tool re-reads the original media.

## Lifecycle boundary

Three systems remain separate:

1. Ambient ingestion: group-history captioning or archive indexing.
2. Request relay: this plugin.
3. Native transport: AstrBot plus the selected Provider.

Request Relay acts only after AstrBot has created a real Agent request. Ordinary group media that never enters the Agent request is untouched.

## Relay gate

`provider.provider_config["modalities"]` is treated as an input-route declaration, not a permanent capability truth table.

States: `ENABLED`, `DISABLED`, `UNKNOWN`.

Modes: `always`, `adaptive`.

`UNKNOWN` is resolved by user policy (`relay` by default).

## First pass and active query

The automatic first pass is intentionally generic and is injected as a `<modality_relay>` block. Query tools always re-open the original media; they do not answer from bootstrap text alone.

Successful bootstrap Q/A is added to the event-scoped media-model history so later focused questions can resolve references naturally. No permanent media database is created.

## AstrBot ownership

The plugin deliberately does not own Provider routing, fallback selection, AgentRunner, Tool Loop, generic media infrastructure, or a model capability database.

## Provider neutrality

No vendor-specific import is allowed in runtime code. The Volcengine dual-channel plugin is an integration target, not a dependency.

## Full / Skills-like contract

Tool descriptions must be sufficient for first-stage selection. Parameter schemas must be sufficient for second-stage execution. The plugin never branches on AstrBot's internal `tool_schema_mode` value.
