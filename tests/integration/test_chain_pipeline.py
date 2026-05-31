import json
from pathlib import Path

from blockchain.export import export_chain
from blockchain.myblock import MyBlockChain
from blockchain.persistence import load_chain
from blockchain.validator import validate_export_file


def test_export_validate_integration(tmp_path: Path, monkeypatch) -> None:
    # Given: built chain and export path
    monkeypatch.setattr(
        "blockchain.export.load_paths_config",
        lambda: type("Paths", (), {"chain_export_dir": str(tmp_path)})(),
    )
    chain = MyBlockChain()
    chain.add_new_block(
        {"gakuseki": "19G110001"},
        {"bt_addrs": "FC:66:CF:BE:10:BF", "count": 1},
    )
    export_path = export_chain(chain, "settings1")

    # When: validating export
    exit_code = validate_export_file(export_path)

    # Then: validation succeeds
    assert exit_code == 0
    loaded = load_chain(export_path)
    assert loaded.validate_chain()
