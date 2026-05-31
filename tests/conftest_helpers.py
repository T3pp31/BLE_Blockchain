"""Test helpers that depend on ble_blockchain (loaded after bluetooth stub)."""

from pathlib import Path

import pytest

from conftest import valid_tran_meta
from ble_blockchain.blockchain.myblock import MyBlockChain


def patch_chain_export_dir(
    monkeypatch: pytest.MonkeyPatch, export_dir: Path
) -> None:
    """Redirect chain export directory for tests."""
    dir_str = str(export_dir)
    fake_config = type("Paths", (), {"chain_export_dir": dir_str})()

    def load_paths_config() -> object:
        return fake_config

    monkeypatch.setattr(
        "ble_blockchain.blockchain.export.load_paths_config",
        load_paths_config,
    )


def make_chain_with_block(
    *,
    gakuseki: str = "19G110001",
    bt_addrs: str = "A",
    count: int = 1,
) -> MyBlockChain:
    """Create a chain containing one block with valid tran_meta."""
    chain = MyBlockChain()
    chain.add_new_block(
        {"gakuseki": gakuseki},
        {"bt_addrs": bt_addrs, "count": count},
        tran_meta=valid_tran_meta(count=count, gakuseki=gakuseki),
    )
    return chain
