"""Root logging: include request id from context when present."""

from __future__ import annotations

import logging

from src.middlewares.request_id import get_request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def configure_request_id_logging() -> None:
    root = logging.getLogger()
    if not any(isinstance(f, RequestIdFilter) for f in root.filters):
        root.addFilter(RequestIdFilter())
