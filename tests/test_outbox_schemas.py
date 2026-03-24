"""Outbox payload schemas (JSON-serializable)."""

from uuid import uuid4

from src.events.schemas import (
    DIRECTORY_CONSENT_CHANGED,
    DIRECTORY_CUSTOMER_CREATED,
    DIRECTORY_CUSTOMER_UPDATED,
    ConsentChangedPayload,
    CustomerCreatedPayload,
    CustomerUpdatedPayload,
    payload_to_json,
)


def test_event_type_constants():
    assert DIRECTORY_CUSTOMER_CREATED == "directory.customer.created"
    assert DIRECTORY_CUSTOMER_UPDATED == "directory.customer.updated"
    assert DIRECTORY_CONSENT_CHANGED == "directory.consent.changed"


def test_payload_to_json_roundtrip_keys():
    cid = uuid4()
    sub = uuid4()
    p = CustomerCreatedPayload(customer_id=cid, subject=sub)
    d = payload_to_json(p)
    assert d["customer_id"] == str(cid)
    assert d["subject"] == str(sub)
    assert "occurred_at" in d

    p2 = CustomerUpdatedPayload(customer_id=cid, subject=sub)
    d2 = payload_to_json(p2)
    assert d2["customer_id"] == str(cid)

    p3 = ConsentChangedPayload(
        customer_id=cid,
        consent_type="privacy",
        document_version="v1",
        granted=True,
    )
    d3 = payload_to_json(p3)
    assert d3["consent_type"] == "privacy"
    assert d3["granted"] is True
