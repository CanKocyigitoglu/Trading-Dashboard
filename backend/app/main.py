"""FastAPI application entry point.

Wires the API router, CORS for the dev frontend, and exception handlers that
translate expected failures into stable machine-readable error codes without
leaking stack traces or internal details.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .adapters.positions_source import PositionsSourceError
from .api.v1 import router
from .config import get_settings
from .domain.portfolio import CurrencyAggregationError
from .services.dashboard import EmptySelectionError


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Trading Risk Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(PositionsSourceError)
    async def _source_error(_: Request, exc: PositionsSourceError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "code": "positions_source_error",
                "message": "The positions source could not be read or is malformed.",
            },
        )

    @app.exception_handler(CurrencyAggregationError)
    async def _currency_error(_: Request, exc: CurrencyAggregationError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "code": "currency_aggregation_unsupported",
                "message": "Positions span multiple currencies; aggregation needs an FX rate.",
            },
        )

    @app.exception_handler(EmptySelectionError)
    async def _empty_selection(_: Request, exc: EmptySelectionError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "no_positions_for_filter",
                "message": "No positions match the selected filters.",
            },
        )

    app.include_router(router)
    return app


app = create_app()
