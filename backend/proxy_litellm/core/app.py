from contextlib import asynccontextmanager
from fastapi import FastAPI
from ..config.logging_config import setup_logging
from ..config.app_config import load_config
from ..api.routes import router
from .handler import handler

# Set up logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    # Startup
    load_config()
    yield
    # Shutdown
    await handler.close()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    # Initialize FastAPI app with lifespan handler
    app = FastAPI(lifespan=lifespan)

    # Include API routes
    app.include_router(router)

    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", log_config="log_conf.yaml")
