# Waste Dumping Detection & Hotspot Mapper

A civic-tech MVP for Mumbai: citizens anonymously upload a photo of illegally dumped waste plus
their location. A computer-vision model verifies the photo actually shows waste, and reports are
aggregated into geo-clusters ("hotspots") so the municipal body can see which areas have the most
unresolved dumping, prioritized by report count and severity.

No accounts, no login — fully anonymous and public.

## Architecture

- **Backend**: FastAPI (Python) + PostgreSQL/PostGIS, SQLAlchemy + Alembic migrations. CV inference
  via the Hugging Face `transformers` pipeline (`nonamelife/garbage-detection-model`). Near-duplicate
  detection via perceptual hashing (`imagehash`).
- **Frontend**: Next.js (App Router) + Tailwind, deployed on Netlify. Map view uses Leaflet +
  OpenStreetMap tiles (no API key needed).
- **Storage**: uploaded images are written to local disk under `backend/uploads` for this MVP. When
  this needs to scale beyond a single instance, swap `UPLOAD_DIR`-based storage in
  `backend/app/routes/reports.py` for S3 (or another object store) — the write/URL-building code is
  isolated there.

## Repository layout

```
/backend   FastAPI app, Alembic migrations, Dockerfile, render.yaml
/frontend  Next.js app (upload page + map page), netlify.toml
docker-compose.yml   local Postgres+PostGIS + backend for development
```

## Local development

Requirements: Docker + Docker Compose, Node 18+.

1. Start Postgres/PostGIS + backend:
   ```bash
   docker compose up --build
   ```
   This runs migrations automatically on container start (see `backend/Dockerfile`'s `CMD`) and
   serves the API at `http://localhost:8000`. The first request that triggers CV classification
   will download model weights from Hugging Face Hub (a few hundred MB) — this can take a minute.

2. In another terminal, run the frontend:
   ```bash
   cd frontend
   cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
   npm install
   npm run dev
   ```
   Visit `http://localhost:3000` to upload a report, and `http://localhost:3000/map` to see hotspots.

## API summary

- `POST /reports` — multipart form: `image` (file), `latitude`, `longitude`. Rate-limited to
  10 requests/hour/IP. Returns `409` on a near-duplicate (same phash within ~50m in the last 24h),
  `429` when rate-limited, otherwise a JSON body with `status: "accepted" | "rejected"`.
- `GET /hotspots` — returns all hotspots as a GeoJSON `FeatureCollection`, each feature carrying
  `report_count`, `avg_severity`, and `priority_score`.
- `GET /reports/{id}` — single report detail.

## Manual steps you still need to do (deployment)

Nothing above deploys itself — here's exactly what to set up, in order. I'll walk you through each
one if you want; just say which step you're on.

### 1. Backend + database on Render

1. Create a free account at [render.com](https://render.com) and connect your GitHub account.
2. In the Render dashboard, choose **New > Blueprint**, point it at this repo, and it should pick up
   `backend/render.yaml` automatically (it defines both the web service and the Postgres database).
   - If Blueprint deploy isn't available on your plan, create the two resources manually instead:
     - **New > PostgreSQL** — enable the PostGIS extension (Render's Postgres supports it; if using
       a different host, run `CREATE EXTENSION postgis;` yourself once connected).
     - **New > Web Service** — root directory `backend`, environment "Docker", it will pick up the
       `Dockerfile`.
3. Set these environment variables on the web service (Render dashboard > your service > Environment):
   - `DATABASE_URL` — the internal connection string Render gives you for the Postgres instance
     (Render fills this automatically if you used the Blueprint).
   - `CORS_ORIGIN` — your Netlify site URL once you have it (step 2), e.g. `https://your-site.netlify.app`.
   - `PUBLIC_BASE_URL` — the public URL Render assigns your backend, e.g. `https://waste-detection-backend.onrender.com`.
4. **Important — persistent uploads**: Render's free plan does not include persistent disks (only
   paid plans do). On the free plan, anything written to `/app/uploads` is wiped on every deploy/restart.
   For a real deployment, either upgrade to a paid Render plan with a disk attached (already wired up
   in `render.yaml`), or swap to S3-compatible storage before going live with real users — this is the
   one shortcut this MVP intentionally takes.
5. Once deployed, confirm `https://<your-backend>.onrender.com/health` returns `{"status": "ok"}`
   and migrations ran (check the deploy logs for `alembic upgrade head`).

### 2. Frontend on Netlify

1. Create a free account at [netlify.com](https://netlify.com) and connect GitHub.
2. **Add new site > Import an existing project**, pick this repo, set the base directory to `frontend`.
3. Netlify should detect Next.js and use `netlify.toml` (build command `npm run build`, the
   `@netlify/plugin-nextjs` plugin is configured for you).
4. Set the environment variable on the Netlify site (Site configuration > Environment variables):
   - `NEXT_PUBLIC_API_URL` — your Render backend URL from step 1, e.g. `https://waste-detection-backend.onrender.com`.
5. Deploy. Once it's live, go back to Render and set `CORS_ORIGIN` to this Netlify URL (step 1.3),
   then redeploy the backend so it takes effect.

### 3. Verify end-to-end

1. Open your Netlify site, submit a test report with a photo and location.
2. Check `/map` shows a marker after a report is accepted.
3. If uploads/CORS fail, double check `CORS_ORIGIN` (backend) and `NEXT_PUBLIC_API_URL` (frontend)
   exactly match each other's deployed URLs (no trailing slash mismatches).

## Notes / known MVP shortcuts

- Severity score is currently `confidence * 100` from the classifier — the code has a `TODO` comment
  marking where this should factor in bounding-box coverage once a real object-detection model
  (not just classification) replaces the current one.
- Hotspot clustering is a simple incremental "join nearest hotspot within 100m, else create new"
  approach, not a full re-clustering algorithm. Good enough for MVP density, not for large-scale
  production use.
- No authentication anywhere by design — reports are anonymous. `ip_hash` is stored only to support
  the rate limiter, never displayed or linked to reports publicly.
