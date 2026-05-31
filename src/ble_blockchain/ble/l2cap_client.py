import bluetooth

from ble_blockchain.config.loader import load_l2cap_config


def l2cap_client(bt_addr: str, data: bytes) -> None:
    """Send serialized payload bytes to a peer over L2CAP."""
    config = load_l2cap_config()
    sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    sock.settimeout(config.connect_timeout_sec)

    print(f"trying to connect to {bt_addr} on PSM 0x{config.psm:x}")

    try:
        sock.connect((bt_addr, config.psm))
        offset = 0
        while offset < len(data):
            sent = sock.send(data[offset:])
            if sent == 0:
                raise RuntimeError("L2CAP send failed: connection closed")
            offset += sent
        print("送信完了")
    finally:
        sock.close()
