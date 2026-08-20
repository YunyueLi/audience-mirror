# Third-party boundary

The repository bundles no third-party source code, model weights, Persona
dataset or media asset. Optional packages and providers are installed or called
at runtime under their own terms.

## Current optional dependencies and providers

| Component | Use | Boundary |
| --- | --- | --- |
| PyAV／FFmpeg libraries | Local video decode and audio extraction | Python dependency; no media is redistributed |
| Pillow | Local frame conversion and scene-difference samples | Python dependency |
| FastAPI／Uvicorn | Local prototype workbench | Binds to `127.0.0.1` by default; not a production security boundary |
| Google Gemini Files API | Optional native full-video analysis | Explicit per-experiment remote consent; public/internal only in the current adapter; provider terms apply |
| Claude Code CLI | Optional structured Persona event reasoning | External local executable and authentication; no credentials are stored here |

## Intended adapters

| Project | Intended use | Boundary |
| --- | --- | --- |
| MatrAIx | Persona retrieval, Cohort and Trial contracts | External checkout only; code and datasets reviewed separately |
| TinyTroupe | Small-panel experiment comparison | Future optional adapter; not bundled |
| Foreworld／GAIA | World memory and later social simulation | Versioned API adapter; not bundled |
| MiroFish | Research reference or separately licensed service | AGPL code is not copied or linked into this repository |
| LongVideoAgent／DVD／AVP／LensWalk | Architecture and benchmark references for agentic video verification | No source copied; future reuse requires fixed-version license review |

Before adding a dependency, record its exact version, license, files used, data
terms, model-weight terms and any notice or source-offer obligations.
