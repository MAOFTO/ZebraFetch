# ZebraFetch Deployment Guide

This guide explains how to deploy ZebraFetch in various environments.

## Prerequisites

- Docker and Docker Compose installed
- (Optional) Portainer for stack deployment
- (Optional) Prometheus for metrics collection

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/zebrafetch.git
   cd zebrafetch
   ```

2. Copy the example config:
   ```bash
   cp backend/config.yaml.example backend/config.yaml
   ```

3. Start the service:
   ```bash
   docker-compose up -d
   ```

4. Access the API at `http://localhost:8000`

## Portainer Stack Deployment

1. In Portainer, create a new stack named `zebrafetch`

2. Use the following stack configuration:
   ```yaml
   version: '3.8'
   
   services:
     zebrafetch:
       image: zebrafetch/zebrafetch:1.0.0
       container_name: zebrafetch
       ports:
         - "8000:8000"
       volumes:
         - zebrafetch_data:/app/data
       environment:
         - ZF_CONFIG=/app/config.yaml
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
         interval: 30s
         timeout: 10s
         retries: 3
       restart: unless-stopped
   
   volumes:
     zebrafetch_data:
   ```

3. Deploy the stack

## Prometheus Integration

Add the following to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'zebrafetch'
    static_configs:
      - targets: ['zebrafetch:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## API Authentication

By default, authentication is disabled. To enable API key authentication:

1. Edit `config.yaml`:
   ```yaml
   auth:
     enabled: true
     api_keys:
       - "your-secure-api-key"
   ```

2. Restart the service

3. Include the API key in requests:
   ```
   X-API-Key: your-secure-api-key
   ```

## Health Checks

The service exposes a health check endpoint at `/healthz`. Use this for container orchestration:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Metrics

Prometheus metrics are available at `/metrics`. Key metrics include:

- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `job_duration_seconds`: Time taken to process jobs
- `active_jobs`: Number of currently running jobs

## Troubleshooting

1. Check container logs:
   ```bash
   docker logs zebrafetch
   ```

2. Verify configuration:
   ```bash
   docker exec zebrafetch cat /app/config.yaml
   ```

3. Test API endpoints:
   ```bash
   curl http://localhost:8000/healthz
   curl http://localhost:8000/metrics
   ```

## Security Considerations

1. Always run behind a reverse proxy with TLS
2. Enable API key authentication for production
3. Restrict CORS origins to trusted domains
4. Monitor rate limits and adjust as needed
5. Regularly update the container image

## Backup and Recovery

1. The SQLite database is stored in the `zebrafetch_data` volume
2. To backup:
   ```bash
   docker run --rm -v zebrafetch_data:/data -v $(pwd):/backup alpine tar czf /backup/zebrafetch-data.tar.gz /data
   ```

3. To restore:
   ```bash
   docker run --rm -v zebrafetch_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/zebrafetch-data.tar.gz"
   ``` 