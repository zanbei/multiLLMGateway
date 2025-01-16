from fastapi import FastAPI
from ..config.logging_config import setup_logging
from ..config.app_config import load_config
from ..api.routes import router

# Set up logging
logger = setup_logging()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    # Initialize FastAPI app
    app = FastAPI()

    # Load litellm config
    load_config()

    # Include API routes
    app.include_router(router)

    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", log_config="log_conf.yaml")
