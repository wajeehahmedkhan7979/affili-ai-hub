FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install

# Copy agent code
COPY agent/ .
COPY app/ /app/app

# Copy .env config
COPY agent/agent_config.env .env

# Run agent
CMD ["python", "main.py"]
