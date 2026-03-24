import logging

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from src.database.dependencies import DbSession
from src.misc.logging_config import configure_request_id_logging
from src.routers import Router
from src.routers.v1.router import TAG_SELF, TAG_STAFF

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [req=%(request_id)s] %(message)s",
)
configure_request_id_logging()
logger = logging.getLogger(__name__)


class App:
    def __init__(self):
        self._app: FastAPI = FastAPI(
            title="Api microservice",
            description="Api microservice",
            version="1.0.0",
            docs_url=None,
            redoc_url=None,
            openapi_url=None,
            openapi_tags=[
                {
                    "name": TAG_SELF,
                    "description": "Profile, addresses, consents, B2B links for the Bearer token subject.",
                },
                {
                    "name": TAG_STAFF,
                    "description": "Operational customer tools; JWT with staff scope (e.g. `admin`).",
                },
            ],
        )
        self._app.add_middleware(
            middleware_class=CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE", "PATCH", "PUT"],
            allow_headers=["*"],
        )

        @self._app.get("/health/live", tags=["health"])
        async def health_live() -> dict:
            return {"status": "ok"}

        @self._app.get("/health/ready", tags=["health"])
        async def health_ready(session: DbSession) -> dict:
            await session.execute(text("SELECT 1"))
            return {"status": "ready"}

        @self._app.get(
            "/metrics",
            tags=["health"],
            include_in_schema=False,
            summary="Prometheus metrics",
        )
        async def prometheus_metrics() -> Response:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

        self._register_routers()

    def _register_routers(self) -> None:
        for router, prefix, tags in Router.routers:
            self._app.include_router(router=router, prefix=prefix, tags=tags)

    @property
    def app(self) -> FastAPI:
        return self._app
