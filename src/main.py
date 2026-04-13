import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import get_settings

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import src.tools  # noqa: F401 — registers all tools via @register_tool decorators
    logger.info("Tools registered: startup complete")
    yield


app = FastAPI(title="ML Traductores Agent", lifespan=lifespan)

from src.api import webhooks  # noqa: E402

app.include_router(webhooks.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
