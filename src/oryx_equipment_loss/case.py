"""
Dataclass for representing cases of equipment loss.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Case:
    model_case_id: int
    asset_status: Tuple[str]
    confirmation_url: str

    # Are initialized later in the pipeline
    cause: Optional[Tuple[str]] = None
    asset_category: Optional[str] = None
    model: Optional[str] = None
    country_of_loss: Optional[str] = None
    country_of_production: Optional[str] = None
    attachment: Optional[str] = None
