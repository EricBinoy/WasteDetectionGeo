# ---- Stage 1: export the vision model to ONNX ----------------------------------------
# torch + transformers only ever exist in this build stage; the runtime stage below never
# installs them, so their ~250MB combined import overhead is never paid at request time.
FROM python:3.11-slim AS exporter
WORKDIR /export

RUN pip install --no-cache-dir torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir transformers==4.44.2 onnx==1.16.2 numpy==1.26.4 Pillow==10.4.0

COPY scripts/export_model.py .
RUN EXPORT_OUT_DIR=/export/model_assets python export_model.py

# ---- Stage 2: runtime -------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=exporter /export/model_assets /app/model_assets

COPY . .

RUN mkdir -p uploads

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
