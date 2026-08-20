# Changelog

All notable changes to Audience Mirror will be documented here.

## [0.2.0-alpha.2] - 2026-08-20

### Added

- link-first Media Source Resolver for public direct video URLs and rights-confirmed YouTube, Bilibili and Douyin pages;
- public direct-link connections pinned to the IP validated at every redirect, plus platform input and selected-endpoint public-address checks;
- a shared platform download/remux workspace budget, 30-minute download/remux deadline, declared-duration four-hour limit, live/unknown-duration rejection and failed-staging cleanup;
- redacted source receipts that do not persist signed URL parameters, generic URL paths, cookies or credentials;
- workbench source switcher with URL as the default path and file upload as fallback.
- evidence-preserving semantic Timeline reconstruction that separates dense local frame samples from at most 16 decision-relevant Agent events and leaves Provider coverage gaps explicit;
- Codex CLI structured Reasoner alongside Claude Code, per-run remote-processing confirmation, terminal `abandon` semantics and a reproducible sequential Run Manifest;
- restart-safe local experiment recovery, a recent-experiment index and deep links reconstructed from redacted workbench artifacts;
- a governed Codex evidence-frame video adapter that sends at most 12 timestamped decoded images while keeping the original video and audio local;
- wheel-packaged schemas, public fixtures and workbench assets, plus a writable workspace resolver and standalone wheel smoke test in CI;
- a fixed-viewport three-pane evidence workbench with independent mobile panes, keyboard-operable Timeline, deep-linked cue seeking and source-ratio-preserving video playback;
- a public, synthetic-only workbench screenshot that can be redistributed without bundling third-party media;

### Verified

- local tests cover URL classification, query/path redaction, private-network rejection, shared platform budgets, failed-ingest cleanup, bounded format selection and the workbench receipt path;
- a public 177.96-second Qwen-hosted MP4 direct link produced 12 local Timeline events from 36,698,404 downloaded bytes;
- a public 635-second Blender Foundation YouTube page produced a 161,192,038-byte MP4 with one video and one audio stream through the new shared-budget split download plus PyAV remux;
- desktop and 390 px mobile URL-first views have no console errors or horizontal overflow.
- real 16:9 H.264 playback preserves the source ratio with centered `contain` rendering; decorative aperture overlays are removed whenever native video controls are present, preventing evidence and controls from being covered;
- GPT-5.6 Sol at xhigh completed a real 1-Persona × 4-Event structured Session over the public synthetic Timeline in 68,719 ms aggregate model latency; all four hash-chained Trace events validate. This does not validate native video understanding or human prediction.
- after an actual service restart, seven local experiments were recovered with video, Timeline, Trace and calibration artifacts; a 414.2-second experiment restored 155 events, 6 Persona sessions and 657 Trace events;
- the Codex evidence-frame baseline analyzed two real decoded frames from a public synthetic H.264 fixture in 26,693 ms, then GPT-5.6 Sol/xhigh completed 1 Persona × 2 semantic events in 34,571 ms aggregate model latency. Both contracts validate; this is a fixed-frame visual baseline without audio, native full-video understanding or human calibration;
- the official 888-second Sintel film was imported from YouTube, decoded locally into 148 retained evidence frames, and reduced by temporally stratified 12-frame Codex analysis into 12 semantic events in 127,779 ms. One GPT-5.6 Sol/xhigh Persona then completed all 12 events in 252,507 ms aggregate model latency; all hash-chained traces validate. This remains a single uncalibrated synthetic trajectory, not a population estimate;
- optional manual WebVTT retrieval for platform links, with a 5 MiB bound, path-free evidence references and time-overlap fusion into semantic events; a real Sintel smoke selected the 1,556-byte Simplified Chinese manual track and parsed 26 cues without invoking automatic translation;
- 48 local tests pass, including time-stratified frame-budget coverage that prevents scene-dense openings from consuming a long-video evidence budget, plus subtitle selection, parsing and evidence-fusion coverage;
- a non-editable wheel installed into a clean runtime validates the long-video Timeline and Trace artifacts and runs the zero-cost Demo from outside the source checkout;
- real-browser desktop and 390 px mobile checks cover pane switching, all four Inspector views, deep-link seek, original-aspect video rendering and zero console errors;

## [0.2.0-alpha.1] - 2026-08-20

Public developer preview published as a GitHub pre-release.

### Added

- real local MP4 decoding, metadata, SHA-256, frame evidence, scene-change sampling, and WAV extraction;
- model-independent Environment Contract with a stateful Media Timeline adapter;
- native Gemini full-video adapter with explicit remote-consent and classification gates;
- future-blind model sequential runtime and Claude Code structured JSON reasoner;
- Human Anchor validation and calibration diagnostics;
- interactive FastAPI workbench with real upload, Timeline, evidence, Persona Trace, and calibration views;
- hard model-call and budget controls;
- deep 2026 landscape review covering Douyin/Volcengine, LibTV, MiniMax Design, native video APIs, and open long-video agents.

### Verified

- 20 local tests with media and web extras, including actual MP4 video/AAC encoding, decode, mono WAV extraction, and Human Anchor version-alignment rejection;
- browser flow for real upload, H.264/AAC playback, time-slice seeking, local ingest, deterministic sequential run, evidence down-drill, and per-call remote-processing governance;
- desktop and mobile responsive layouts without console errors.

### Remaining

- native Gemini execution awaits a configured key and asset-specific authorization;
- Claude Code model execution awaits renewed local OAuth;
- ASR, OCR, diarization, agentic high-FPS verification, Social Lab, and production persistence are not yet implemented;
- no human dataset has calibrated behavioral proxy outputs.

## [0.1.0-alpha] - 2026-08-20

First public research and engineering preview.

### Included

- deterministic, zero-key local demo with a 10,000-record synthetic Persona pool;
- separate Deep Trace, Broad Sweep, and zero-LLM Population Projection layers;
- hash-chained event traces with Timeline evidence references;
- self-contained HTML evidence report and reproducibility manifest;
- Timeline, Trace, and Human Anchor JSON Schemas;
- contract-only MatrAIx adapter inspection without downloading third-party data;
- product thesis, evidence register, architecture, validation plan, and open-source strategy;
- nine deterministic contract and end-to-end tests.

### Known limitations

- no real video ingestion, ASR, VLM, or model-provider execution;
- no human calibration dataset or claim of human representativeness;
- current runnable environment is Media-specific while the general Environment Contract is planned;
- no hosted product, authentication, collaboration, or production security controls.

[0.2.0-alpha.1]: https://github.com/YunyueLi/audience-mirror/releases/tag/v0.2.0-alpha.1
[0.2.0-alpha.2]: https://github.com/YunyueLi/audience-mirror/releases/tag/v0.2.0-alpha.2
[0.1.0-alpha]: https://github.com/YunyueLi/audience-mirror/releases/tag/v0.1.0-alpha
