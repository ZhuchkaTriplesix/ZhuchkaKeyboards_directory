"""Pydantic schemas for root router endpoints."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(StrEnum):
    """Health status enum."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class ServiceStatus(StrEnum):
    """Individual service status enum."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "database": "connected",
                "redis": "connected",
            }
        }
    )

    status: HealthStatus = Field(..., description="Overall health status of the application")
    database: str = Field(..., description="Database connection status")
    redis: str = Field(..., description="Redis connection status")
