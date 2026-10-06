"""Safe exception translation for the HTTP API."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def register_error_handlers(app: FastAPI) -> None:
	"""Register generic error responses that do not expose internal details."""
	@app.exception_handler(RequestValidationError)
	async def validation_error_handler(
		request: Request,
		exc: RequestValidationError,
	) -> JSONResponse:
		return JSONResponse(
			status_code=422,
			content={"detail": "Request validation failed"},
		)

	@app.exception_handler(SQLAlchemyError)
	async def database_error_handler(
		request: Request,
		exc: SQLAlchemyError,
	) -> JSONResponse:
		logger.error("database_request_failed")
		return JSONResponse(
			status_code=503,
			content={"detail": "A required data service is unavailable"},
		)

	@app.exception_handler(Exception)
	async def unexpected_error_handler(
		request: Request,
		exc: Exception,
	) -> JSONResponse:
		logger.error("unhandled_api_request_failure")
		return JSONResponse(
			status_code=500,
			content={"detail": "An internal error occurred"},
		)