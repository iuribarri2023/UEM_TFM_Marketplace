from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def data_response(data: Any) -> dict[str, Any]:
    return {"data": data}


def error_response(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}

