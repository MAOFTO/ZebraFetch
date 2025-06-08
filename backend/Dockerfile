# Build stage
FROM python:3.12-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies
#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfontconfig1 \
    libcurl4 \
    libgl1 \
    libxcb1 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application code and resources
COPY app ./app
COPY schemas ./schemas
COPY config.yaml ./config.yaml

# Set environment variables
ENV PYTHONPATH=/app
ENV ZF_CONFIG=/app/config.yaml

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 