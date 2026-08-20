# WasteDetectionGeo — Project Status

Living context doc — updated as things change. Local project root: `C:\dev\WasteDetectionGeo`
(moved here from `OneDrive\Desktop\...` because OneDrive's real-time sync was fighting Next.js
and Docker for disk access and causing severe slowdowns).

## What this app does

Civic-tech MVP: citizens anonymously upload a photo of illegally dumped waste + their GPS
location. An AI model verifies the photo actually shows waste, reports are deduped (perceptual
hash, ~50m/24h), and accepted reports feed an incrementally-clustered hotspot map so a municipal
body can see which areas have the most unresolved dumping.

## Live deployment

| Piece | Provider | URL | Status |
|---|---|---|---|
| Database | Supabase | `tstnmqzofazabwlkqynm.supabase.co` | ✅ Live |
| Backend | Render | https://wastedetectiongeo.onrender.com | ✅ Live (free tier) |
| Frontend | Netlify | https://lighthearted-sable-d7c85e.netlify.app | ✅ Live |

`CORS_ORIGIN` on Render is set to the Netlify URL above — confirmed working (verified the
`Access-Control-Allow-Origin` header matches).

Render free tier spins down after 15 min idle — first request after idle takes 30-60s to wake up.
This is expected, not a bug.

## Local dev

```bash
# Uses Supabase by default (DATABASE_URL in root .env, gitignored)
docker compose up -d backend

# OR use local Postgres+PostGIS instead of Supabase:
docker compose --profile local up -d

cd frontend && npm run dev   # localhost:3000
```

Backend is on host port **8001** (not 8000 — something unrelated on this machine already owns
8000). `frontend/.env.local` points `NEXT_PUBLIC_API_URL` at `http://localhost:8001`.

## Architecture decisions made this session (and why)

- **CV model**: not the model named in the original spec (`nonamelife/garbage-detection-model`
  — turned out to be a raw Keras model, incompatible with the `transformers` pipeline, 500'd on
  every request). Switched to CLIP-style zero-shot classification: compares the photo against two
  fixed captions ("a photo of illegally dumped garbage..." vs "a photo of a clean area...").
  Chosen over TrashNet-style fine-tuned classifiers because those have no "not garbage" class at
  all and are trained on cropped single-item photos, not real street scenes.
- **Model size**: full `openai/clip-vit-base-patch32` (605MB) blew past Render free tier's 512MB
  RAM cap. Swapped to `wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M` (~94MB), then went further.
- **ONNX Runtime rewrite (in progress as of last update)**: even TinyCLIP still needed ~450-460MB
  once PyTorch's own import overhead (~183MB, fixed regardless of model size) plus
  transformers/FastAPI/SQLAlchemy were all loaded — too close to the 512MB ceiling to be safe.
  Root cause isn't the model, it's PyTorch itself. Fix: `backend/scripts/export_model.py` exports
  just the vision encoder to ONNX **at Docker build time** (multi-stage build — torch/transformers
  only exist in the `exporter` stage) and precomputes text embeddings for the two fixed candidate
  captions, since they never change. The runtime image never imports torch or transformers at
  all — just `onnxruntime` + `numpy` + `Pillow`. Verified in isolation: correct classifications,
  peak RSS ~113MB (vs ~450MB with PyTorch). Full end-to-end verification against the real running
  server (not just the isolated test) was in progress when this doc was written — confirm actual
  `docker compose exec backend pip show transformers torch` fails (not installed) and check real
  memory via `/proc/<uvicorn-pid>/status` `VmRSS` before considering this done and pushing/
  redeploying to Render.
- **Supabase connection**: use the **connection pooler**, not the direct connection (direct is
  IPv6-only, breaks on many networks/hosts). Within the pooler, use **session mode (port 5432)**
  for anything running migrations (Alembic) — Supabase explicitly recommends this over transaction
  mode (port 6543) for migration tools. `DATABASE_URL` needs `sslmode=require` and
  `connect_timeout=10`. Password has special characters (`/ # & %`) that must be percent-encoded
  in the URL, or things break in confusing ways.
- **Alembic bug fix**: `alembic/env.py` originally routed the DB URL through
  `config.set_main_option()` → `configparser`, whose default interpolation chokes on literal `%`
  characters (from the percent-encoded password). Fixed by building the SQLAlchemy engine directly
  from `settings.database_url` instead, bypassing configparser's interpolation entirely.
- **`geom` NOT NULL bug**: `Report` rows were originally inserted with `geom` unset, then patched
  via a follow-up raw `UPDATE` — violated the NOT NULL constraint before the UPDATE ever ran.
  Fixed by setting `geom` via `WKTElement(...)` at construction time instead.
- **CPU-only PyTorch** (build-stage only now): always install the `+cpu` wheel via
  `--index-url https://download.pytorch.org/whl/cpu`, never the default (CUDA-enabled, ~2GB of
  unused GPU libs that previously destabilized local Docker builds badly enough to wedge WSL2).

## Known environment gotchas (this machine specifically)

- **Docker Desktop / WSL2 has repeatedly wedged** during this session (unresponsive `docker`
  CLI, hung builds) — root cause was originally the CUDA-torch download overwhelming memory; it's
  recurred since for unrelated transient reasons (corrupted downloads, buildkit connection
  hiccups). Fix when it happens: `taskkill //IM "Docker Desktop.exe" //F` +
  `taskkill //IM "com.docker.backend.exe" //F`, then `wsl --shutdown`, then relaunch Docker
  Desktop and wait for `docker info` to succeed before retrying.
- System RAM is limited (~15.7GB) and gets tight with Docker + PyCharm + browser all open at
  once — contributed to earlier slow builds/compiles.

## Credentials / secrets

- Supabase DB password and full connection string: in `C:\dev\WasteDetectionGeo\.env` (gitignored,
  not committed). Also set as `DATABASE_URL` in Render's environment variables.
- No other secrets in this project (no auth, anonymous reports by design).

## Outstanding / next steps

1. Finish verifying the ONNX rewrite locally (real server memory check), then commit, push, and
   let Render redeploy — this is what actually fixes the "ran out of memory" crash Render hit on
   the free tier.
2. Once redeployed, re-verify `/health`, a real report submission, and `/hotspots` against the
   live Render + Supabase + Netlify stack.
3. Nothing else currently blocking — deployment pipeline (GitHub → Render + Netlify) is otherwise
   working end-to-end.
