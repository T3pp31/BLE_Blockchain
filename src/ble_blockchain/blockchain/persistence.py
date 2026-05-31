from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ble_blockchain.blockchain.myblock import CHAIN_HASH_VERSION, MyBlockChain


class ChainPersistenceError(ValueError):
    """Raised when chain export cannot be loaded or validated."""


def load_chain_from_dict(data: dict[str, Any]) -> MyBlockChain:
    """Load a chain from export JSON data and validate it."""
    version = data.get("chain_hash_version")
    if version != CHAIN_HASH_VERSION:
        raise ChainPersistenceError(
            f"unsupported chain_hash_version: {version!r} "
            f"(expected {CHAIN_HASH_VERSION})"
        )

    chain_data = data.get("chain")
    if not isinstance(chain_data, list):
        raise ChainPersistenceError("export JSON must contain a 'chain' list")

    chain = MyBlockChain()
    chain.chain = chain_data
    if not chain.validate_chain():
        errors = chain.validate_chain_verbose()
        first = errors[0]
        raise ChainPersistenceError(
            f"invalid chain at block {first.block_index}: {first.reason}"
        )
    meta_errors = chain.validate_tran_meta_verbose()
    if meta_errors:
        first = meta_errors[0]
        raise ChainPersistenceError(
            f"invalid tran_meta at block {first.block_index}: {first.reason}"
        )
    return chain


def load_chain(path: Path) -> MyBlockChain:
    """Load and validate a chain export file."""
    with open(path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    return load_chain_from_dict(data)


def chain_to_export_dict(
    chain: MyBlockChain,
    *,
    device_id: str,
    schema_version: int = 1,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "chain_hash_version": CHAIN_HASH_VERSION,
        "device_id": device_id,
        "created_at": _current_timestamp(),
        "majority_threshold": chain.last_majority_threshold,
        "verified_receive_count": chain.last_verified_receive_count,
        "chain": chain.chain,
    }


def save_chain_export(
    chain: MyBlockChain,
    export_path: Path,
    *,
    device_id: str,
) -> Path:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    payload = chain_to_export_dict(chain, device_id=device_id)
    with open(export_path, "w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, sort_keys=False, indent=2)
    return export_path


def _current_timestamp() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
