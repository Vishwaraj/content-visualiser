import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.llm_service import (
    check_gemini_connection,
    list_models,
    generate_visualization, # Updated import
    get_supported_visualization_types, # New import
)
from app.services.visualizations.visualization_strategy import VisualizationOptions, VisualizationResult # New import
from google.genai import errors as genai_errors

# Configure logging to show INFO level logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

# CORS is vital for React <-> FastAPI communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class VisualizationRequest(BaseModel):
    """Request body for creating a visualization job."""
    question: str
    visualization_type: str = Field(
        "flowchart", description="Type of visualization to generate (e.g., 'flowchart', 'mindmap')"
    )
    options: VisualizationOptions = Field(
        default_factory=VisualizationOptions, description="Options for visualization generation"
    )


class VisualizationJobCreateResponse(BaseModel):
    """Response body containing job ID and status upon job creation."""
    job_id: str
    status: JobStatus


class VisualizationJob(BaseModel):
    id: str
    status: JobStatus
    visualization_type: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field({})
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime # New field for job expiry
    attempts: int = 0


class VisualizationJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    visualization_type: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field({})
    error: Optional[str] = None
    
_jobs: Dict[str, VisualizationJob] = {} # Updated type hint

@app.get("/health")
async def health_check():
    """K8s style health check."""
    return {"status": "healthy", "env": settings.ENVIRONMENT}

@app.get("/test-ai")
async def test_ai_connection():
    """Verifies Gemini connection."""
    result = await check_gemini_connection()
    return {"ai_status": result}

@app.get("/list-models")
async def get_models():
    """Lists available Gemini models."""
    result = await list_models()
    return {"models": result}

@app.get("/supported-visualizations")
async def get_supported_types_endpoint():
    """Returns a list of supported visualization types."""
    return {"supported_types": get_supported_visualization_types()}



async def _run_visualization_job(
    job_id: str,
    question: str,
    visualization_type: str,
    options: VisualizationOptions,
) -> None:
    """Background task that calls Gemini with retry and updates job state."""
    logger.info(f"[JOB {job_id}] Starting background task for visualization type: {visualization_type}")
    job = _jobs.get(job_id)
    if not job:
        logger.warning(f"[JOB {job_id}] Attempted to run non-existent job")
        return

    max_attempts = 3
    base_delay_seconds = 1.5

    for attempt in range(1, max_attempts + 1):
        logger.info(f"[JOB {job_id}] Attempt {attempt}/{max_attempts}")
        job.status = JobStatus.RUNNING
        job.attempts = attempt
        job.updated_at = datetime.utcnow()
        _jobs[job_id] = job

        try:
            logger.info(f"[JOB {job_id}] Calling generate_visualization...")
            result: VisualizationResult = await generate_visualization(
                question, visualization_type, options
            )
            logger.info(f"[JOB {job_id}] Visualization generated successfully!")
            job.content = result.content
            job.metadata = result.metadata
            job.status = JobStatus.SUCCEEDED
            job.updated_at = datetime.utcnow()
            _jobs[job_id] = job
            logger.info(f"[JOB {job_id}] Job completed successfully")
            return
        except (ValueError, RuntimeError) as exc:
            # Catch specific errors from visualization strategies or LLM service
            logger.exception(
                f"[JOB {job_id}] Visualization generation failed "
                f"(type={visualization_type}, attempt={attempt}/{max_attempts}): {exc}"
            )
            job.status = JobStatus.FAILED
            job.error = str(exc)
            job.updated_at = datetime.utcnow()
            _jobs[job_id] = job
            return
        except genai_errors.ServerError as exc:
            # Try to robustly determine the HTTP status code from the exception.
            status_code = getattr(exc, "status_code", None)
            if status_code is None:
                resp = getattr(exc, "response", None)
                if resp is not None:
                    status_code = getattr(resp, "status_code", None) or getattr(
                        resp, "status", None
                    )
            if status_code is None:
                text = str(exc).lower()
                if "503" in text or "unavailable" in text or "overloaded" in text:
                    status_code = 503
                elif (
                    "429" in text
                    or "too many requests" in text
                    or "rate limit" in text
                ):
                    status_code = 429
            logger.exception(
                f"[JOB {job_id}] Gemini ServerError "
                f"(attempt={attempt}/{max_attempts}, status_code={status_code}): {exc}"
            )

            # Retry on transient service or throttling errors only, with backoff.
            if status_code in (503, 429) and attempt < max_attempts:
                delay = base_delay_seconds * (2 ** (attempt - 1))
                logger.warning(f"[JOB {job_id}] Retrying after {delay:.1f}s due to status {status_code}")
                job.status = JobStatus.PENDING # Temporarily set to PENDING for retry
                job.error = f"Transient Gemini error (status={status_code}). Retrying in {delay:.1f}s."
                job.updated_at = datetime.utcnow()
                _jobs[job_id] = job
                await asyncio.sleep(delay)
                continue

            job.status = JobStatus.FAILED
            # User-friendly error message while still logging the raw exception above.
            if status_code == 503:
                job.error = (
                    "The Gemini model is still overloaded after multiple attempts. "
                    "Please wait a bit and try again."
                )
            elif status_code == 429:
                job.error = (
                    "Gemini rate limit was hit several times in a row. "
                    "Please slow down and try again shortly."
                )
            else:
                job.error = f"Gemini returned an error while generating the diagram: {exc}"
            job.updated_at = datetime.utcnow()
            _jobs[job_id] = job
            return
        except Exception as exc:  # pragma: no cover - defensive guardrail
            logger.exception(
                f"[JOB {job_id}] Unexpected error "
                f"(attempt={attempt}/{max_attempts}): {exc}"
            )
            job.status = JobStatus.FAILED
            job.error = f"Unexpected error: {exc}"
            job.updated_at = datetime.utcnow()
            _jobs[job_id] = job
            return


@app.post("/visualize", response_model=VisualizationJobCreateResponse)
async def visualize(request: VisualizationRequest) -> VisualizationJobCreateResponse:
    """Create an asynchronous visualization job.

    The frontend should poll `/visualize/{job_id}` to retrieve the final diagram
    or any error that occurred.
    """
    logger.info(f"Received visualization request: type={request.visualization_type}, question='{request.question[:100]}...'")
    # Validate requested visualization type
    supported_types = get_supported_visualization_types()
    if request.visualization_type.lower() not in supported_types:
        logger.warning(f"Unsupported visualization type requested: {request.visualization_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported visualization type: '{request.visualization_type}'. "
                   f"Supported types are: {', '.join(supported_types)}."
        )

    job_id = str(uuid.uuid4())
    logger.info(f"Created job {job_id} for {request.visualization_type} visualization")
    now = datetime.utcnow()
    # Jobs expire after 1 hour (settings.JOB_EXPIRY_SECONDS could be used)
    expires_at = now + timedelta(seconds=3600) 

    job = VisualizationJob(
        id=job_id,
        status=JobStatus.PENDING,
        visualization_type=request.visualization_type.lower(),
        content=None,
        metadata={},
        error=None,
        created_at=now,
        updated_at=now,
        expires_at=expires_at,
        attempts=0,
    )
    _jobs[job_id] = job

    # Fire-and-forget background task
    asyncio.create_task(
        _run_visualization_job(
            job_id,
            request.question,
            request.visualization_type,
            request.options,
        )
    )

    return VisualizationJobCreateResponse(job_id=job_id, status=JobStatus.PENDING)


@app.get("/visualize/{job_id}", response_model=VisualizationJobStatusResponse)
async def get_visualization_job(job_id: str) -> VisualizationJobStatusResponse:
    """Retrieve the status and result (if ready) of a visualization job."""
    job = _jobs.get(job_id)
    if not job:
        logger.debug(f"[JOB {job_id}] Job not found in memory")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Visualization job '{job_id}' not found or expired."},
        )
    
    # Log current status for debugging (only on status changes or errors)
    if job.status in [JobStatus.SUCCEEDED, JobStatus.FAILED]:
        logger.info(f"[JOB {job_id}] Returning final status: {job.status}")
    
    # Optional: Clean up expired jobs (could be a separate background task)
    if job.expires_at < datetime.utcnow():
        logger.warning(f"[JOB {job_id}] Job has expired")
        del _jobs[job_id]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Visualization job '{job_id}' has expired and was removed."},
        )

    return VisualizationJobStatusResponse(
        job_id=job.id,
        status=job.status,
        visualization_type=job.visualization_type,
        content=job.content,
        metadata=job.metadata,
        error=job.error,
    )