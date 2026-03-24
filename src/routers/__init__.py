from dataclasses import dataclass

from src.routers.root.router import router as root_request_router
from src.routers.v1.router import router as v1_router


@dataclass(frozen=True)
class Router:
    routers = [
        (root_request_router, "/api/root", ["root"]),
        (v1_router, "/api/v1", ["v1"]),
    ]
