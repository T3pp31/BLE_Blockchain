"""Send packed payloads to peers over L2CAP."""

from ble_blockchain.ble.l2cap_client import l2cap_client


def SEND(bt_addrs: list[str], payload_bytes: bytes) -> None:  # pylint: disable=invalid-name
    """Send payload to each peer address sequentially."""
    for bt_addr in bt_addrs:
        l2cap_client(bt_addr, payload_bytes)
