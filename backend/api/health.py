"""Database readiness endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db_session
from backend.api.schemas import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/api/health", response_model=HealthResponse)
def health_check(session: Annotated[Session, Depends(get_db_session)]) -> HealthResponse:
	session.execute(text("SELECT 1"))
	return HealthResponse(status="healthy", database="healthy")