"""Unit tests for chain export validation."""

import json
from pathlib import Path

from conftest_helpers import make_chain_with_block
from ble_blockchain.blockchain.myblock import MyBlockChain
from ble_blockchain.blockchain.persistence import save_chain_export
from ble_blockchain.blockchain.validator import validate_export_file


def test_validate_export_file_success(tmp_path: Path) -> None:
    """正常系: valid export file returns exit code 0."""
    # Given: minimal valid export with consistent tran_meta
    chain = make_chain_with_block(bt_addrs="FC:66:CF:BE:10:BF")
    export_path = tmp_path / "ok.json"
    save_chain_export(chain, export_path, device_id="device1")

    # When/Then
    assert validate_export_file(export_path) == 0


def test_validate_export_file_failure(tmp_path: Path) -> None:
    """異常系: invalid JSON returns exit code 1."""
    # Given: invalid JSON
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not json", encoding="utf-8")

    # When/Then
    assert validate_export_file(bad_path) == 1


def test_validate_export_file_rejects_wrong_chain_hash_version(
    tmp_path: Path,
) -> None:
    """異常系: unsupported chain_hash_version returns exit code 1."""
    # Given: export with unsupported chain_hash_version
    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A", "count": 1})
    export_path = tmp_path / "old.json"
    save_chain_export(chain, export_path, device_id="device1")
    data = json.loads(export_path.read_text(encoding="utf-8"))
    data["chain_hash_version"] = 1
    export_path.write_text(json.dumps(data), encoding="utf-8")

    # When/Then
    assert validate_export_file(export_path) == 1
