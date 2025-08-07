# Use an official slim Python base image (small + maintained)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for mysqlclient, cryptography, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
        libmysqlclient-dev \
        build-essential \
        curl \
        netcat && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code into the image
COPY . .

# Create logs directory if needed
RUN mkdir -p logs

# Expose default Flask/Django port (adjust if needed)
EXPOSE 5000

# Set entry point (update for Django if needed)
CMD ["python", "run.py"]

