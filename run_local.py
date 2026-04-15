"""Script de arranque local — usa SelectorEventLoop (requerido por psycopg en Windows)."""
import asyncio
import selectors
import sys

import uvicorn


async def serve():
    config = uvicorn.Config(
        "src.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if sys.platform == "win32":
        # psycopg async requiere SelectorEventLoop en Windows
        asyncio.run(
            serve(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    else:
        asyncio.run(serve())
