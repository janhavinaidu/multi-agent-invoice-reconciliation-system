# Backend Folder Structure

Complete, production-ready folder structure for the Invoice Reconciliation FastAPI backend.

```
backend/
│
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application entry point
│   │
│   ├── api/                     # API layer
│   │   ├── __init__.py
│   │   ├── routes.py            # API endpoints/routes
│   │   └── utils.py             # API utility functions
│   │
│   ├── core/                    # Core configuration
│   │   ├── __init__.py
│   │   └── config.py            # Settings and configuration
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models for validation
│   │
│   └── services/                # Business logic layer
│       ├── __init__.py
│       ├── agent_service.py     # Agent system integration
│       └── processing_service.py # Job management
│
├── uploads/                     # Temporary uploaded files
│   ├── {file_id}.pdf           # Uploaded invoices
│   └── po_{file_id}.json       # Uploaded POs
│
├── outputs/                     # Processing results
│   └── {job_id}_result.json    # Job results
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_api.py             # API endpoint tests
│   ├── test_agents.py          # Agent integration tests
│   └── test_services.py        # Service layer tests
│
├── .env.example                 # Environment variables template
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Docker container definition
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── README.md                   # Backend documentation
├── QUICKSTART.md               # Quick setup guide
└── FOLDER_STRUCTURE.md         # This file
```

## Detailed Structure

### `/app` - Main Application

The core application code, organized by responsibility:

#### `/app/main.py`
- FastAPI application initialization
- CORS middleware configuration
- Route inclusion
- Startup/shutdown events
- Entry point for uvicorn

#### `/app/api/` - API Layer
- **routes.py**: All API endpoints
  - Upload endpoints (`/upload/invoice`, `/upload/po`)
  - Processing endpoints (`/process`, `/status/{id}`)
  - Result endpoints (`/result/{id}`, `/download/{id}`)
  - Management endpoints (`/jobs`, `/job/{id}`)
  - PO endpoints (`/po/list`, `/po/{number}`)
  - Statistics (`/stats`, `/health`)
  
- **utils.py**: API utilities
  - `process_invoice_background()` - Background processing
  - `format_result_for_frontend()` - Response formatting

#### `/app/core/` - Configuration
- **config.py**: Centralized configuration
  - Settings class (extends Pydantic BaseSettings)
  - Environment variable management
  - Default values
  - Validation

#### `/app/models/` - Data Models
- **schemas.py**: Pydantic models
  - Request models (ProcessRequest, etc.)
  - Response models (JobResponse, StatusResponse, etc.)
  - Data models (LineItem, MatchingData, etc.)
  - Enums (JobStatus, AgentName, etc.)

#### `/app/services/` - Business Logic
- **agent_service.py**: Agent system integration
  - LLM initialization
  - Agent initialization
  - Invoice processing orchestration
  - PO database management
  
- **processing_service.py**: Job management
  - Job creation and tracking
  - Status updates
  - Statistics calculation
  - Job cleanup

### `/uploads` - Temporary Storage
- Uploaded invoice files
- Uploaded PO files
- Automatically cleaned based on retention policy
- Not tracked in git

### `/outputs` - Results Storage
- Processing results in JSON format
- One file per job
- Can be downloaded via API
- Not tracked in git

### `/tests` - Test Suite
- Unit tests for services
- Integration tests for API
- Agent system tests
- Test fixtures and utilities

## File Purposes

### Configuration Files

**`.env.example`**
- Template for environment variables
- Copy to `.env` and fill in values
- Never commit `.env` to git

**`requirements.txt`**
- Python package dependencies
- Install with `pip install -r requirements.txt`

**`Dockerfile`**
- Container image definition
- Multi-stage build for optimization
- Includes Tesseract OCR

**`docker-compose.yml`**
- Multi-container setup
- Backend + frontend (optional)
- Volume mounts for persistence

### Documentation Files

**`README.md`**
- Complete API documentation
- Endpoint reference
- Setup instructions
- Integration examples

**`QUICKSTART.md`**
- 3-minute setup guide
- Quick testing examples
- Troubleshooting tips

**`FOLDER_STRUCTURE.md`** (this file)
- Architecture overview
- File organization
- Purpose of each component

## Running the Application

### Development Mode

```bash
# From project root
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="gsk_..."

# Run with auto-reload
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# Or using Docker
docker-compose up -d
```

## Import Paths

Due to the structure, imports work as follows:

```python
# From within app/
from app.core.config import settings
from app.models.schemas import ProcessRequest
from app.services.agent_service import get_agent_service

# API routes in app/api/routes.py
from app.models.schemas import *
from app.services.agent_service import get_agent_service
```

## Adding New Features

### New API Endpoint
1. Add route function in `app/api/routes.py`
2. Define request/response models in `app/models/schemas.py`
3. Add business logic in appropriate service

### New Service
1. Create new file in `app/services/`
2. Implement service class
3. Create singleton getter function
4. Import in routes as needed

### New Model
1. Add Pydantic model in `app/models/schemas.py`
2. Use in route type hints
3. FastAPI auto-validates

## Environment Variables

Required in `.env`:
```bash
GROQ_API_KEY=gsk_...           # Required
API_HOST=0.0.0.0               # Optional, default: 0.0.0.0
API_PORT=8000                  # Optional, default: 8000
DEBUG=True                     # Optional, default: True
CORS_ORIGINS=http://localhost:3000  # Optional
```

## Best Practices

1. **Services** - Business logic goes in services
2. **Routes** - Keep routes thin, delegate to services
3. **Models** - Use Pydantic for validation
4. **Config** - Centralize all configuration
5. **Logging** - Log at appropriate levels
6. **Errors** - Use HTTPException with proper status codes
7. **Async** - Use async/await for I/O operations
8. **Testing** - Write tests for services and routes

## Scalability

This structure supports:
- ✅ Horizontal scaling (multiple workers)
- ✅ Service isolation (easy to extract microservices)
- ✅ Testing (clear boundaries)
- ✅ Maintenance (organized by responsibility)
- ✅ Documentation (auto-generated with FastAPI)

## Next Steps

1. Add caching layer (Redis)
2. Add database (PostgreSQL for jobs/results)
3. Add WebSocket for real-time updates
4. Add authentication/authorization
5. Add rate limiting
6. Add monitoring (Prometheus/Grafana)