from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Meta(BaseModel):
    total: Optional[int] = None
    limit: Optional[int] = None
    has_more: Optional[bool] = None
    next_after_serial: Optional[int] = None
    content_version: Optional[int] = None


class Envelope(BaseModel, Generic[T]):
    data: T
    meta: Optional[Meta] = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
