"""Main entry point for the AsterDEX Trading API server."""

import uvicorn
from src.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "src.app:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,  # Set to True for development
        log_level=settings.log_level.lower()
    )
