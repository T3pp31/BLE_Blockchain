"""Shared typed data structures for the BLE blockchain pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ReceivedPayload:
    """One received payload entry used for chain building.

    Replaces the former positional 6-element list contract so the
    blockchain layer can read fields by name.
    """

    df: pd.DataFrame | None
    public_key: Any
    signature: bytes
    verified: bool
    public_key_pem: str | None
    payload_content_hash: str | None
