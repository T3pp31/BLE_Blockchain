import pandas as pd

from blockchain.myblock import MyBlockChain


def _receive_item(
    gakuseki: str, bt_addrs: str, verified: bool = True
) -> list:
    df = pd.DataFrame(
        {"gakuseki": [gakuseki], "bt_addrs": [bt_addrs], "device_name": ["x"]}
    )
    return [df, None, b"sig", verified]


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
