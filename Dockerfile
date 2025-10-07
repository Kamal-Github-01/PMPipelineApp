FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/data_simulator /app/data_ingestion /app/model_training /app/edge_inference /app/dashboard /app/data /app/models

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["bash"]