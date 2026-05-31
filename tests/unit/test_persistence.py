import json
from pathlib import Path

import pytest

from blockchain.export import export_chain
from blockchain.myblock import MyBlockChain
from blockchain.persistence import ChainPersistenceError, load_chain, save_chain_export


def test_save_and_load_chain_roundtrip(tmp_path: Path) -> None:
    # Given: a valid chain
    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "FC:66:CF:BE:10:BF"})
    export_path = tmp_path / "settings1_test.json"

    # When: saving and loading
    save_chain_export(chain, export_path, device_id="settings1")
    loaded = load_chain(export_path)

    # Then: chain matches and validates
    assert len(loaded.chain) == 1
    assert loaded.validate_chain()
    with open(export_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    assert data["device_id"] == "settings1"
    assert data["chain_hash_version"] == 2


def test_load_chain_rejects_tampered_export(tmp_path: Path) -> None:
    # Given: tampered export file
    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A"})
    export_path = tmp_path / "bad.json"
    save_chain_export(chain, export_path, device_id="device1")
    with open(export_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    data["chain"][0]["block_header"]["tran_hash"] = "0" * 64
    with open(export_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file)

    # When/Then: load fails
    with pytest.raises(ChainPersistenceError):
        load_chain(export_path)


def test_export_chain_writes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: chain and custom export dir
    monkeypatch.setattr(
        "blockchain.export.load_paths_config",
        lambda: type("Paths", (), {"chain_export_dir": str(tmp_path)})(),
    )
    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A"})

    # When: exporting
    path = export_chain(chain, "settings1")

    # Then: file exists
    assert path.exists()
    assert path.name.startswith("settings1_")
