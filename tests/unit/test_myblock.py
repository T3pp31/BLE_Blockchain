import hashlib
from typing import Optional

import pandas as pd
import pytest

from blockchain.myblock import (
    MyBlockChain,
    compute_majority_threshold,
    payload_content_hash,
    pubkey_fingerprint,
)
from config.loader import load_blockchain_config
from delete_excess_data import filter_registered_data
from pandas_d_encode import pandas_encode


def _content_hash_for_df(df: pd.DataFrame) -> str:
    filtered = filter_registered_data(df)
    return payload_content_hash(pandas_encode(filtered))


def _receive_item(
    gakuseki: str,
    bt_addrs: str,
    verified: bool = True,
    *,
    public_key_pem: str = "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
    content_hash: Optional[str] = None,
    device_name: str = "x",
) -> list:
    df = pd.DataFrame(
        {
            "gakuseki": [gakuseki],
            "bt_addrs": [bt_addrs],
            "device_name": [device_name],
        }
    )
    if content_hash is None:
        content_hash = _content_hash_for_df(df)
    return [df, None, b"sig", verified, public_key_pem, content_hash]


def test_build_from_receives_majority_threshold() -> None:
    # Given: 3 distinct reporters for same bt_addr with matching content hash
    chain = MyBlockChain()
    shared_hash = _content_hash_for_df(
        pd.DataFrame(
            {
                "gakuseki": ["19G110001"],
                "bt_addrs": ["FC:66:CF:BE:10:BF"],
                "device_name": ["x"],
            }
        )
    )
    receives = [
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-a",
            content_hash=shared_hash,
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-b",
            content_hash=shared_hash,
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-c",
            content_hash=shared_hash,
        ),
        _receive_item("19G110002", "AA:BB:CC:DD:EE:FF", public_key_pem="pem-d"),
    ]

    # When: building chain (threshold = 3 verified reporters)
    chain.build_from_receives(receives)

    # Then: only majority bt_addr becomes a block with reporter count
    assert len(chain.chain) == 1
    assert chain.chain[0]["tran_body"]["input"]["gakuseki"] == "19G110001"
    assert chain.chain[0]["tran_body"]["output"]["bt_addrs"] == "FC:66:CF:BE:10:BF"
    assert chain.chain[0]["tran_body"]["output"]["count"] == 3
    assert chain.chain[0]["tran_meta"]["content_hash"] == shared_hash
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
    # Given: 4 verified reporters split 2+2 across bt_addrs, threshold=3
    monkeypatch.setattr(
        "delete_excess_data._load_preliminary_data",
        lambda: pd.DataFrame(
            {
                "gakuseki": ["19G110001", "19G110002"],
                "bt_addrs": ["FC:66:CF:BE:10:BF", "BB:BB:BB:BB:BB:BB"],
            }
        ),
    )
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "FC:66:CF:BE:10:BF", public_key_pem="pem-a"),
        _receive_item("19G110001", "FC:66:CF:BE:10:BF", public_key_pem="pem-b"),
        _receive_item("19G110002", "BB:BB:BB:BB:BB:BB", public_key_pem="pem-c"),
        _receive_item("19G110002", "BB:BB:BB:BB:BB:BB", public_key_pem="pem-d"),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: no block because each bt_addr has only 2 reporters
    assert len(chain.chain) == 0


def test_build_from_receives_min_verified_receives_not_met(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: only 2 verified receives while min_verified_receives=3
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "FC:66:CF:BE:10:BF", public_key_pem="pem-a"),
        _receive_item("19G110001", "FC:66:CF:BE:10:BF", public_key_pem="pem-b"),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: chain empty
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
    first = chain.add_new_block(
        {"gakuseki": "19G110001"},
        {"bt_addrs": "A", "count": 1},
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
    second = chain.add_new_block(
        {"gakuseki": "19G110002"},
        {"bt_addrs": "B", "count": 1},
        tran_meta={
            "count": 1,
            "majority_threshold": 1,
            "content_hash": "b" * 64,
            "gakuseki_votes": {"19G110002": 1},
            "reporters": [
                {
                    "pubkey_fingerprint": "e" * 64,
                    "payload_content_hash": "b" * 64,
                }
            ],
        },
    )

    # Then: prev_hash links and validation passes
    assert first["block_index"] == 1
    assert second["block_header"]["prev_hash"] == first["block_header"]["tran_hash"]
    assert chain.validate_chain()
    assert chain.validate_tran_meta_verbose() == []


def test_validate_chain_detects_tampered_tran_hash() -> None:
    # Given: valid chain
    chain = MyBlockChain()
    chain.add_new_block({"gakuseki": "19G110001"}, {"bt_addrs": "A", "count": 1})
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
        _receive_item("19G110001", "00:00:00:00:00:00"),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: filtered out before counting
    assert len(chain.chain) == 0


def test_build_from_receives_includes_tran_meta_reporters() -> None:
    # Given: 3 reports with distinct reporter fingerprints and same content hash
    chain = MyBlockChain()
    shared_hash = _content_hash_for_df(
        pd.DataFrame(
            {
                "gakuseki": ["19G110001"],
                "bt_addrs": ["FC:66:CF:BE:10:BF"],
                "device_name": ["x"],
            }
        )
    )
    receives = [
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-a",
            content_hash=shared_hash,
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-b",
            content_hash=shared_hash,
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-c",
            content_hash=shared_hash,
        ),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: tran_meta contains reporter proofs
    assert len(chain.chain) == 1
    reporters = chain.chain[0]["tran_meta"]["reporters"]
    assert len(reporters) == 3
    assert reporters[0]["pubkey_fingerprint"] == pubkey_fingerprint("pem-a")


def test_gakuseki_tie_produces_no_block() -> None:
    # Given: same bt_addr with tied gakuseki votes (2 vs 2) among 4 reporters
    chain = MyBlockChain()
    receives = [
        _receive_item("19G110001", "FC:66:CF:BE:10:BF", public_key_pem="pem-a"),
        _receive_item("19G110001", "FC:66:CF:BE:10:BF", public_key_pem="pem-b"),
        _receive_item("19G110002", "FC:66:CF:BE:10:BF", public_key_pem="pem-c"),
        _receive_item("19G110002", "FC:66:CF:BE:10:BF", public_key_pem="pem-d"),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: no block due to gakuseki tie
    assert len(chain.chain) == 0


def test_row_inflation_same_reporter_does_not_satisfy_majority() -> None:
    # Given: one reporter duplicated in receive list with 3 identical rows each
    chain = MyBlockChain()
    df = pd.DataFrame(
        {
            "gakuseki": ["19G110001", "19G110001", "19G110001"],
            "bt_addrs": ["FC:66:CF:BE:10:BF"] * 3,
            "device_name": ["x"] * 3,
        }
    )
    content_hash = _content_hash_for_df(df)
    receives = [
        [df, None, b"sig", True, "pem-a", content_hash],
        [df, None, b"sig", True, "pem-a", content_hash],
        [df, None, b"sig", True, "pem-a", content_hash],
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: only one unique reporter; below min_verified_receives and threshold
    assert len(chain.chain) == 0


def test_content_hash_mismatch_blocks_adoption() -> None:
    # Given: 3 reporters but two different content hashes
    chain = MyBlockChain()
    hash_a = _content_hash_for_df(
        pd.DataFrame(
            {
                "gakuseki": ["19G110001"],
                "bt_addrs": ["FC:66:CF:BE:10:BF"],
                "device_name": ["x"],
            }
        )
    )
    receives = [
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-a",
            content_hash=hash_a,
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-b",
            content_hash=hash_a,
        ),
        _receive_item(
            "19G110001",
            "FC:66:CF:BE:10:BF",
            public_key_pem="pem-c",
            content_hash="b" * 64,
        ),
    ]

    # When: building chain
    chain.build_from_receives(receives)

    # Then: no block
    assert len(chain.chain) == 0


def test_validate_tran_meta_detects_tampered_count() -> None:
    # Given: block with inconsistent tran_meta.count
    chain = MyBlockChain()
    chain.add_new_block(
        {"gakuseki": "19G110001"},
        {"bt_addrs": "FC:66:CF:BE:10:BF", "count": 3},
        tran_meta={
            "count": 3,
            "majority_threshold": 2,
            "content_hash": "a" * 64,
            "gakuseki_votes": {"19G110001": 3},
            "reporters": [
                {
                    "pubkey_fingerprint": "f" * 64,
                    "payload_content_hash": "a" * 64,
                }
            ],
        },
    )

    # When/Then
    errors = chain.validate_tran_meta_verbose()
    assert len(errors) == 1
    assert "reporters length" in errors[0].reason
