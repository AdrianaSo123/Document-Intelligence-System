# --- BASE STAGE: Shared environment and dependencies ---
FROM python:3.9-slim as base

# Set working directory
WORKDIR /app

# Prevent python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app/src

# Install system dependencies (Poppler for PDF-to-Image, Tesseract for OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create a non-privileged user for security
RUN groupadd -g 1000 bdis && \
    useradd -u 1000 -g bdis -s /bin/sh bdis && \
    chown -R bdis:bdis /app

USER bdis

# --- API STAGE ---
FROM base as api
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "bdis.frameworks.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- WORKER STAGE ---
FROM base as worker
CMD ["celery", "-A", "bdis.frameworks.worker.celery_app", "worker", "--loglevel=info"]

# --- UI STAGE ---
FROM base as ui
EXPOSE 8501
CMD ["streamlit", "run", "src/bdis/frameworks/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
