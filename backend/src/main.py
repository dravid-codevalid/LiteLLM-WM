# File: main.py. Description: Main FastAPI application entry point. Consists of: app factory, middleware wiring, router includes, and Temporal worker lifespan.
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client
from temporalio.worker import Worker

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.shared.config.settings import settings
from src.shared.middleware.error_handler import (
    ErrorHandlerMiddleware,
    http_exception_handler,
    validation_exception_handler,
)

from src.modules.auth.router import router as auth_router
from src.modules.workspaces.router import router as workspaces_router
from src.modules.admin.router import router as admin_router
from src.modules.conversations.router import router as conversations_router
from src.modules.usage.router import router as usage_router

from src.modules.usage.workflows import BillingWorkflow
from src.modules.usage.activities import record_usage_activity

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Temporal worker in background
    worker_task = None
    try:
        temporal_client = await Client.connect(settings.TEMPORAL_HOST)
        worker = Worker(
            temporal_client,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
            workflows=[BillingWorkflow],
            activities=[record_usage_activity],
        )
        worker_task = asyncio.create_task(worker.run())
        logger.info("Temporal worker started")
    except Exception as e:
        logger.warning(f"Temporal worker failed to start (non-fatal): {e}")

    yield

    if worker_task:
        worker_task.cancel()


def create_app() -> FastAPI:
    app = FastAPI(title="Multi-Tenant AI Research Assistant", lifespan=lifespan)

    app.add_middleware(ErrorHandlerMiddleware)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.1.9:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(workspaces_router)
    app.include_router(admin_router)
    app.include_router(conversations_router)
    app.include_router(usage_router)

    return app


app = create_app()
