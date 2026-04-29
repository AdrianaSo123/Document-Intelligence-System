import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bdis.frameworks.api.routers import documents, jobs, workspaces
from bdis.core.logging_config import setup_json_logging

# Configure structured JSON logging
setup_json_logging()
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Humble Object Pattern: The main app only wires up the infrastructure.
    All business logic and routing is delegated to routers and use cases.
    """
    app = FastAPI(
        title="Business Document Intelligence System (BDIS)",
        description="Clean Architecture AI-Powered Document Ingestion",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Wire up consolidated routers
    app.include_router(documents.router)
    app.include_router(jobs.router)
    app.include_router(workspaces.router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

app = create_app()
