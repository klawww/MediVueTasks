# Task Management API

A robust Task Management API built with FastAPI that supports advanced filtering, tagging, and deadlines.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed

### Run with Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd task-management-api

# Start the application
docker-compose up --build

# The API will be available at http://localhost:8000
# Swagger documentation at http://localhost:8000/docs
```

### Run Locally (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set database URL (requires PostgreSQL running)
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/taskdb

# Run the application
uvicorn app.main:app --reload
```

### Running Tests

```bash
# With Docker
docker-compose run app pytest tests/ -v

# Locally
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks` | Create a new task |
| GET | `/tasks` | List tasks with filtering and pagination |
| GET | `/tasks/{id}` | Get a specific task |
| PATCH | `/tasks/{id}` | Partially update a task |
| DELETE | `/tasks/{id}` | Soft delete a task |
| GET | `/health` | Health check endpoint |

### Create Task (POST /tasks)

```json
{
  "title": "Complete project",
  "description": "Finish the backend assessment",
  "priority": 5,
  "due_date": "2024-12-31",
  "tags": ["work", "urgent"]
}
```

### List Tasks (GET /tasks)

Query parameters:
- `completed` (bool): Filter by completion status
- `priority` (int, 1-5): Filter by priority level
- `tags` (string): Comma-separated tags (e.g., `?tags=work,urgent`)
- `limit` (int, default 10): Number of results per page
- `offset` (int, default 0): Number of results to skip

### Update Task (PATCH /tasks/{id})

Only include fields you want to update:

```json
{
  "completed": true,
  "priority": 4
}
```

## Design Decisions

### Soft Delete vs Hard Delete

**Decision: Soft Delete**

Rationale:
- **Data Recovery**: Allows recovery of accidentally deleted tasks
- **Audit Trail**: Maintains history for compliance and debugging
- **Referential Integrity**: Prevents cascading issues with related data
- **User Experience**: Enables "trash" or "undo" functionality

Trade-offs:
- Requires filtering `is_deleted=False` in all queries
- Database size grows over time (mitigated with periodic cleanup jobs)

### Tagging Implementation: Join Table

**Decision: Normalized join table approach**

```
Tasks <---> task_tags <---> Tags
```

**Advantages:**
- **Query Efficiency**: Proper indexing on the join table enables fast lookups
- **Data Integrity**: Foreign key constraints ensure referential integrity
- **Flexibility**: Easy to add tag metadata (color, description) later
- **Standard SQL**: Works with any SQL database, not just PostgreSQL
- **Deduplication**: Tags are stored once and reused across tasks

**Trade-offs vs JSONB/ARRAY:**

| Aspect | Join Table | JSONB/ARRAY |
|--------|-----------|-------------|
| Query Performance | Better for filtering | Better for reading |
| Schema Flexibility | Requires migration | Very flexible |
| Data Integrity | Strong (FK constraints) | Application-enforced |
| Portability | Database-agnostic | PostgreSQL-specific |
| Tag Reuse | Automatic deduplication | Manual deduplication |

The join table was chosen because:
1. Filtering by tags is a primary use case
2. Tag integrity and consistency are important
3. Future extensibility (tag metadata, permissions) is supported

### Database Indexing Strategy

Indexes applied to frequently filtered columns:
- `tasks.priority` - For priority-based filtering
- `tasks.completed` - For completion status filtering
- `tasks.is_deleted` - For soft delete filtering
- `tasks.due_date` - For date-based queries
- `tags.name` - For tag lookups

## Production Readiness Improvements

### Security
- [ ] Add authentication/authorization (JWT, OAuth2)
- [ ] HTTPS enforcement
- [ ] CORS configuration

### Performance
- [ ] Connection pooling configuration
- [ ] Redis caching for frequently accessed data
- [ ] Database read replicas for scaling reads

### Reliability
- [ ] Database migrations with Alembic versioning
- [ ] Health checks with database connectivity verification
- [ ] Structured logging (JSON format)
- [ ] Error tracking (Sentry integration)
- [ ] Graceful shutdown handling

### Observability
- [ ] Prometheus/GCP metrics
- [ ] Request/response logging

### DevOps
- [ ] CI/CD pipeline configuration
- [ ] Environment-specific configurations
- [ ] Database backup automation

### Testing
- [ ] Integration tests with real PostgreSQL
- [ ] Load/performance testing
- [ ] Contract testing for API compatibility
- [ ] End-to-end testing

## Project Structure

```
task-management-api/
├── app/
│   ├── api/
│   │   └── tasks.py        # API endpoints
│   ├── core/
│   │   ├── config.py       # Settings/configuration
│   │   └── database.py     # Database connection
│   ├── models/
│   │   └── task.py         # SQLAlchemy models
│   ├── schemas/
│   │   └── task.py         # Pydantic schemas
│   └── main.py             # FastAPI application
├── tests/
│   ├── conftest.py         # Test configuration
│   └── test_tasks.py       # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Error Response Format

All errors follow a consistent structure:

```json
{
  "error": "Validation Failed",
  "details": {
    "priority": "Must be between 1 and 5"
  }
}
```
