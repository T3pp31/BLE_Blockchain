import json
from pathlib import Path

import pytest

from blockchain.validator import validate_export_file


def test_validate_export_file_success(tmp_path: Path) -> None:
    # Given: minimal valid export
    from blockchain.myblock import MyBlockChain
    from blockchain.persistence import save_chain_export

    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A"})
    export_path = tmp_path / "ok.json"
    save_chain_export(chain, export_path, device_id="device1")

    # When/Then
    assert validate_export_file(export_path) == 0


def test_validate_export_file_failure(tmp_path: Path) -> None:
    # Given: invalid JSON
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not json", encoding="utf-8")

    # When/Then
    assert validate_export_file(bad_path) == 1
