"""Integration tests for chain export, validation, and aggregation."""

from pathlib import Path

import pytest

from conftest import valid_tran_meta
from conftest_helpers import make_chain_with_block, patch_chain_export_dir
from ble_blockchain.blockchain.aggregator import aggregate_chains
from ble_blockchain.blockchain.export import export_chain
from ble_blockchain.blockchain.myblock import MyBlockChain
from ble_blockchain.blockchain.persistence import (
    ChainPersistenceError,
    load_chain,
    save_chain_export,
)
from ble_blockchain.blockchain.validator import validate_export_file


def test_export_validate_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """正常系: exported chain passes validation and reload."""
    # Given: built chain and export path
    patch_chain_export_dir(monkeypatch, tmp_path)
    chain = MyBlockChain()
    chain.add_new_block(
        {"gakuseki": "19G110001"},
        {"bt_addrs": "FC:66:CF:BE:10:BF", "count": 1},
        tran_meta=valid_tran_meta(),
    )
    export_path = export_chain(chain, "settings1")

    # When: validating export
    exit_code = validate_export_file(export_path)

    # Then: validation succeeds
    assert exit_code == 0
    loaded = load_chain(export_path)
    assert loaded.validate_chain()


def test_aggregate_strict_requires_multiple_devices(tmp_path: Path) -> None:
    """異常系: strict aggregation requires multiple device exports."""
    # Given: single-device exports only
    chain = make_chain_with_block()
    save_chain_export(chain, tmp_path / "only.json", device_id="settings1")
    output_path = tmp_path / "canonical.json"

    # When/Then: strict aggregation fails
    with pytest.raises(ChainPersistenceError, match="distinct device_id"):
        aggregate_chains(tmp_path, output_path, strict=True)
