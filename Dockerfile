FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils && rm -rf /var/lib/apt/lists/*
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "bdis.frameworks.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
