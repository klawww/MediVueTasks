from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.tasks import router as tasks_router
from app.core.database import get_engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Task Management API",
    description="A robust Task Management API that supports advanced filtering, tagging, and deadlines.",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with consistent error format."""
    details = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details[field] = error["msg"]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation Failed", "details": details},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "details": {"message": str(exc)}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    # If detail is already in our format, use it directly
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    # Otherwise, wrap it in our standard format
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, str) else "Error", "details": None},
    )


# Include routers
app.include_router(tasks_router)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
