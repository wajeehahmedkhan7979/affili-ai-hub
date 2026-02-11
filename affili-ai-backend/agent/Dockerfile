FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copy requirements from root
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# Copy entire app directory (needed for imports)
COPY app/ /app/app/
COPY scripts/ /app/scripts/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the worker
CMD ["python", "scripts/run_worker.py"]
