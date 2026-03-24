"""Database session middleware for managing database connections per request."""

from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from src.database.core import async_session_maker
from src.database.logging import SessionTracker


async def db_session_middleware(request: Request, call_next):
    """
    Middleware for managing database sessions per request.

    Creates a new database session for each request, handles commits/rollbacks,
    and ensures proper cleanup of resources.

    Args:
        request: The incoming request
        call_next: The next middleware/endpoint in the stack

    Returns:
        Response from the next handler
    """
    session: AsyncSession | None = None

    try:
        session = async_session_maker()
        request.state.db = session

        session._chime_service_session_id = SessionTracker.track_session(
            session, context="api_request_chime_service"
        )

        response = await call_next(request)

        if session.is_active:
            await session.commit()

        return response

    except Exception as e:
        if session and session.is_active:
            await session.rollback()
        raise e
    finally:
        if session:
            if hasattr(session, "service_session_id"):
                SessionTracker.untrack_session(session.service_session_id)

            await session.close()
