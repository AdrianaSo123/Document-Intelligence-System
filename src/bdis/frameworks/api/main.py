import logging
from fastapi import FastAPI
from bdis.frameworks.api.routers import documents

# Configure structured logging for production observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

    # Wire up consolidated routers
    app.include_router(documents.router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

app = create_app()
