import json
from pathlib import Path

from ble_blockchain.blockchain.export import export_chain
from ble_blockchain.blockchain.myblock import MyBlockChain
from ble_blockchain.blockchain.persistence import load_chain
from ble_blockchain.blockchain.validator import validate_export_file


def _valid_tran_meta(count: int = 1) -> dict:
    content_hash = "a" * 64
    return {
        "count": count,
        "majority_threshold": count,
        "content_hash": content_hash,
        "gakuseki_votes": {"19G110001": count},
        "reporters": [
            {
                "pubkey_fingerprint": "f" * 64,
                "payload_content_hash": content_hash,
            }
        ]
        * count,
    }


def test_export_validate_integration(tmp_path: Path, monkeypatch) -> None:
    # Given: built chain and export path
    monkeypatch.setattr(
        "ble_blockchain.blockchain.export.load_paths_config",
        lambda: type("Paths", (), {"chain_export_dir": str(tmp_path)})(),
    )
    chain = MyBlockChain()
    chain.add_new_block(
        {"gakuseki": "19G110001"},
        {"bt_addrs": "FC:66:CF:BE:10:BF", "count": 1},
        tran_meta=_valid_tran_meta(),
    )
    export_path = export_chain(chain, "settings1")

    # When: validating export
    exit_code = validate_export_file(export_path)

    # Then: validation succeeds
    assert exit_code == 0
    loaded = load_chain(export_path)
    assert loaded.validate_chain()


def test_aggregate_strict_requires_multiple_devices(
    tmp_path: Path, monkeypatch
) -> None:
    # Given: single-device exports only
    from ble_blockchain.blockchain.aggregator import aggregate_chains
    from ble_blockchain.blockchain.persistence import save_chain_export

    chain = MyBlockChain()
    chain.add_new_block(
        {"gakuseki": "19G110001"},
        {"bt_addrs": "A", "count": 1},
        tran_meta=_valid_tran_meta(),
    )
    save_chain_export(chain, tmp_path / "only.json", device_id="settings1")
    output_path = tmp_path / "canonical.json"

    # When/Then: strict aggregation fails
    import pytest
    from ble_blockchain.blockchain.persistence import ChainPersistenceError

    with pytest.raises(ChainPersistenceError, match="distinct device_id"):
        aggregate_chains(tmp_path, output_path, strict=True)
