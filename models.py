from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TripRecord(BaseModel):
    destination: str
    budget: float
    travelers: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    output_path: str
