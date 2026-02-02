FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip list

# Copy application code and migrations
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Create storage directory for logs/screenshots
RUN mkdir -p /app/storage

# Run the application
# Note: DATABASE_URL should be provided via environment variables in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
