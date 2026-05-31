import hashlib
from typing import Optional

import pandas as pd
import pytest

from blockchain.myblock import (
    MyBlockChain,
    compute_majority_threshold,
    pubkey_fingerprint,
)
from config.loader import load_blockchain_config


def _receive_item(
    gakuseki: str,
    bt_addrs: str,
    verified: bool = True,
    *,
    public_key_pem: str = "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
    content_hash: Optional[str] = None,
) -> list:
    df = pd.DataFrame(
        {"gakuseki": [gakuseki], "bt_addrs": [bt_addrs], "device_name": ["x"]}
    )
    if content_hash is None:
        content_hash = hashlib.sha256(b"plaintext").hexdigest()
    return [df, None, b"sig", verified, public_key_pem, content_hash]


def test_build_from_receives_majority_threshold() -> None:
    # Given: 3 verified reports for same bt_addr out of 4 slots
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110001", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110001", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110002", "AA:BB:CC:DD:EE:FF"),
    ]

    # When: building chain (threshold = 4//2+1 = 3)
    chain.build_from_receives(receives)

    # Then: only majority bt_addr becomes a block
    assert len(chain.chain) == 1
    assert chain.chain[0]["tran_body"]["input"]["gakuseki"] == "19G110001"
    assert chain.chain[0]["tran_body"]["output"]["bt_addrs"] == "FC:66:CF:BE:10:BF"
    assert chain.chain[0]["tran_body"]["output"]["count"] == 3
    assert chain.validate_chain()


def test_build_from_receives_skips_unverified() -> None:
    # Given: unverified entries only
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "FC:66:CF:BE:10:BF", verified=False),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: no blocks added
    assert len(chain.chain) == 0


def test_build_from_receives_empty() -> None:
    # Given: empty receive list
    chain = MyBlockChain()

    # When: building chain
    chain.build_from_receives([])

    # Then: chain stays empty
    assert len(chain.chain) == 0


def test_build_from_receives_below_threshold_no_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: 4 verified receives split 2+2, threshold=3
    monkeypatch.setattr(
        "delete_excess_data._load_registered_bt_addrs",
        lambda: {"FC:66:CF:BE:10:BF", "BB:BB:BB:BB:BB:BB"},
    )
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110001", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110002", "BB:BB:BB:BB:BB:BB"),
        _receive_item("19G110002", "BB:BB:BB:BB:BB:BB"),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: no block because each bt_addr count < threshold
    assert len(chain.chain) == 0


@pytest.mark.parametrize(
    ("verified_count", "expected"),
    [
        (1, 1),
        (2, 2),
        (3, 2),
        (4, 3),
    ],
)
def test_compute_majority_threshold_default_ratio(
    verified_count: int, expected: int
) -> None:
    # Given/When: ratio is 0.5 (strict majority)
    config = load_blockchain_config()
    assert config.majority_ratio == 0.5

    # Then
    assert compute_majority_threshold(verified_count, config.majority_ratio) == expected


def test_add_new_block_chain_links_and_validates() -> None:
    # Given: empty chain
    chain = MyBlockChain()

    # When: adding two blocks
    first = chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A"})
    second = chain.add_new_block({"gakuseki": "19G110002"}, {"bt_addrs": "B"})

    # Then: prev_hash links and validation passes
    assert first["block_index"] == 1
    assert second["block_header"]["prev_hash"] == first["block_header"]["tran_hash"]
    assert chain.validate_chain()


def test_validate_chain_detects_tampered_tran_hash() -> None:
    # Given: valid chain
    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A"})
    chain.chain[0]["block_header"]["tran_hash"] = "0" * 64

    # When/Then: validation fails with reason
    errors = chain.validate_chain_verbose()
    assert len(errors) == 1
    assert errors[0].block_index == 1
    assert "tran_hash" in errors[0].reason


def test_build_from_receives_filters_unregistered_bt_addr() -> None:
    # Given: only unregistered bt_addr reports
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "00:00:00:00:00:00"),
        _receive_item("19G110001", "00:00:00:00:00:00"),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: filtered out before counting
    assert len(chain.chain) == 0


def test_build_from_receives_includes_tran_meta_reporters() -> None:
    # Given: 3 reports with distinct reporter fingerprints
    chain = MyBlockChain()
    receives = [
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-a",
            content_hash="hash-a",
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-b",
            content_hash="hash-b",
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-c",
            content_hash="hash-c",
        ),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: tran_meta contains reporter proofs
    assert len(chain.chain) == 1
    reporters = chain.chain[0]["tran_meta"]["reporters"]
    assert len(reporters) == 3
    assert reporters[0]["pubkey_fingerprint"] == pubkey_fingerprint("pem-a")


def test_one_block_per_bt_addr_deduplicates_gakuseki_rows() -> None:
    # Given: same bt_addr reported for two gakuseki with majority
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110001", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110002", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110002", "FC:66:CF:BE:10:BF"),
        _receive_item("19G110002", "FC:66:CF:BE:10:BF"),
    ]

    # When: building chain with one_block_per_bt_addr enabled
    chain.build_from_receives(receives)

    # Then: only one block for the bt_addr
    assert len(chain.chain) == 1
