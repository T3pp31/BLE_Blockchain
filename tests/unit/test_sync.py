import json
from pathlib import Path

import pytest

from ble_blockchain.blockchain.aggregator import aggregate_chains
from ble_blockchain.blockchain.myblock import MyBlockChain
from ble_blockchain.blockchain.persistence import save_chain_export
from ble_blockchain.blockchain.sync import (
    collect_export_paths,
    merge_exports,
    select_canonical,
)
from tests.conftest import valid_tran_meta


def _write_export(tmp_path: Path, name: str, blocks: int) -> Path:
    chain = MyBlockChain()
    for index in range(blocks):
        chain.add_new_block(
            {"gakuseki": f"19G11000{index}"},
            {"bt_addrs": f"ADDR-{index}", "count": 1},
            tran_meta=valid_tran_meta(),
        )
    export_path = tmp_path / name
    save_chain_export(chain, export_path, device_id=name.replace(".json", ""))
    return export_path


def test_select_canonical_prefers_longer_chain(tmp_path: Path) -> None:
    # Given: two exports with different lengths
    short_path = _write_export(tmp_path, "short.json", blocks=1)
    long_path = _write_export(tmp_path, "long.json", blocks=3)
    candidates = merge_exports([short_path, long_path])

    # When: selecting canonical
    canonical = select_canonical(candidates)

    # Then: longer chain wins
    assert len(canonical["chain"]) == 3


def test_aggregate_chains_writes_output(tmp_path: Path) -> None:
    # Given: export files
    _write_export(tmp_path, "a.json", blocks=2)
    _write_export(tmp_path, "b.json", blocks=1)
    output_path = tmp_path / "canonical.json"

    # When: aggregating
    result = aggregate_chains(tmp_path, output_path)

    # Then: canonical file written
    assert output_path.exists()
    assert len(result["chain"]) == 2


def test_collect_export_paths_excludes_output_file(tmp_path: Path) -> None:
    # Given: device exports and an existing canonical output in the same directory
    _write_export(tmp_path, "a.json", blocks=2)
    _write_export(tmp_path, "b.json", blocks=1)
    output_path = tmp_path / "canonical.json"
    aggregate_chains(tmp_path, output_path)

    # When: collecting paths while excluding the output filename
    paths = collect_export_paths(tmp_path, exclude_names=frozenset({"canonical.json"}))

    # Then: canonical.json is not included
    assert output_path.exists()
    assert output_path not in paths
    assert len(paths) == 2


def test_aggregate_chains_ignores_existing_canonical(tmp_path: Path) -> None:
    # Given: exports and a prior canonical.json in the input directory
    _write_export(tmp_path, "short.json", blocks=1)
    long_path = _write_export(tmp_path, "long.json", blocks=3)
    output_path = tmp_path / "canonical.json"
    aggregate_chains(tmp_path, output_path)

    # When: aggregating again into the same output path
    result = aggregate_chains(tmp_path, output_path)

    # Then: longest device export wins (not stale canonical)
    assert len(result["chain"]) == 3
    assert long_path.exists()


def test_collect_export_paths_empty_dir_raises(tmp_path: Path) -> None:
    # Given: empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # When/Then: aggregation fails clearly
    with pytest.raises(Exception):
        aggregate_chains(empty_dir, empty_dir / "out.json")
