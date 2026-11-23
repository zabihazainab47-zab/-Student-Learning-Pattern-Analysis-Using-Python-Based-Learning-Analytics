# Dockerfile for Student Learning Pattern Analysis
# Multi-platform deployment (Render, Railway, Hugging Face Spaces, Fly.io)

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY . .

# Initialize SQLite database with demonstration records
RUN python scripts/create_demo_data.py

# Expose container port
EXPOSE 8000

# Start FastAPI application
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
