"""Domain event types and payloads (outbox)."""

from src.events.outbox import enqueue_outbox
from src.events.schemas import (
    DIRECTORY_CONSENT_CHANGED,
    DIRECTORY_CUSTOMER_CREATED,
    DIRECTORY_CUSTOMER_UPDATED,
    ConsentChangedPayload,
    CustomerCreatedPayload,
    CustomerUpdatedPayload,
    payload_to_json,
)

__all__ = [
    "CONSENT_CHANGED",
    "CUSTOMER_CREATED",
    "CUSTOMER_UPDATED",
    "ConsentChangedPayload",
    "CustomerCreatedPayload",
    "CustomerUpdatedPayload",
    "enqueue_outbox",
    "payload_to_json",
]

CUSTOMER_CREATED = DIRECTORY_CUSTOMER_CREATED
CUSTOMER_UPDATED = DIRECTORY_CUSTOMER_UPDATED
CONSENT_CHANGED = DIRECTORY_CONSENT_CHANGED
