# ZebraFetch

A FastAPI-based application for scanning and processing documents.

## Features

- Document scanning and processing
- RESTful API endpoints
- Docker containerization
- Health check monitoring
- API key authentication
- Background task processing
- File cleanup management

## Prerequisites

- Python 3.11 or higher
- Docker (for containerized deployment)
- curl (for health checks)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ZebraFetch.git
cd ZebraFetch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Local Development

1. Start the application:
```bash
uvicorn app.main:app --reload
```

2. The API will be available at `http://localhost:8000`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t zebrafetch .
```

2. Run the container:
```bash
docker run -p 8000:8000 zebrafetch
```

The application includes a health check endpoint at `/health` that is monitored by Docker.

## API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

- `POST /v1/scan`: Upload and scan documents
- `GET /v1/jobs/{job_id}`: Get job status
- `GET /health`: Health check endpoint

## Development

### Running Tests

```bash
pytest
```

### Code Quality

The project uses several tools to maintain code quality:

- Black for code formatting
- Flake8 for linting
- MyPy for type checking
- Pytest for testing

Run all checks:
```bash
# Format code
black .

# Run linter
flake8

# Type checking
mypy .

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
