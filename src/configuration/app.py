import logging

from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware

from src.database.dependencies import DbSession
from src.routers import Router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)



class App:
    def __init__(self):
        self._app: FastAPI = FastAPI(
            title="Api microservice",
            description="Api microservice",
            version="1.0.0",
            docs_url=None,
            redoc_url=None,
            openapi_url="/api/openapi.json",
        )
        self._app.add_middleware(
            middleware_class=CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE", "PATCH", "PUT"],
            allow_headers=["*"]
        )

        @self._app.get("/health/live", tags=["health"])
        async def health_live() -> dict:
            return {"status": "ok"}

        @self._app.get("/health/ready", tags=["health"])
        async def health_ready(session: DbSession) -> dict:
            await session.execute(text("SELECT 1"))
            return {"status": "ready"}

        self._register_routers()

    def _register_routers(self) -> None:
        for router, prefix, tags in Router.routers:
            self._app.include_router(router=router, prefix=prefix, tags=tags)


    @property
    def app(self) -> FastAPI:
        return self._app
