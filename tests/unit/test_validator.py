import json
from pathlib import Path

import pytest

from blockchain.validator import validate_export_file


def test_validate_export_file_success(tmp_path: Path) -> None:
    # Given: minimal valid export with consistent tran_meta
    from blockchain.myblock import MyBlockChain
    from blockchain.persistence import save_chain_export

    chain = MyBlockChain()
    chain.add_new_block(
        {"gakuseki": "19G110001"},
        {"bt_addrs": "FC:66:CF:BE:10:BF", "count": 1},
        tran_meta={
            "count": 1,
            "majority_threshold": 1,
            "content_hash": "a" * 64,
            "gakuseki_votes": {"19G110001": 1},
            "reporters": [
                {
                    "pubkey_fingerprint": "f" * 64,
                    "payload_content_hash": "a" * 64,
                }
            ],
        },
    )
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


def test_validate_export_file_rejects_wrong_chain_hash_version(
    tmp_path: Path,
) -> None:
    # Given: export with unsupported chain_hash_version
    from blockchain.persistence import save_chain_export
    from blockchain.myblock import MyBlockChain

    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A", "count": 1})
    export_path = tmp_path / "old.json"
    save_chain_export(chain, export_path, device_id="device1")
    data = json.loads(export_path.read_text(encoding="utf-8"))
    data["chain_hash_version"] = 1
    export_path.write_text(json.dumps(data), encoding="utf-8")

    # When/Then
    assert validate_export_file(export_path) == 1
