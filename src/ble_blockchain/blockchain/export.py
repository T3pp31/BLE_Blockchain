from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ble_blockchain.blockchain.myblock import MyBlockChain
from ble_blockchain.blockchain.persistence import save_chain_export
from ble_blockchain.config.loader import load_paths_config


def build_export_path(device_id: str, export_dir: Path | None = None) -> Path:
    base_dir = export_dir if export_dir is not None else Path(
        load_paths_config().chain_export_dir
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{device_id}_{timestamp}.json"
    return base_dir / filename


def export_chain(chain: MyBlockChain, device_id: str) -> Path:
    export_path = build_export_path(device_id)
    return save_chain_export(chain, export_path, device_id=device_id)
