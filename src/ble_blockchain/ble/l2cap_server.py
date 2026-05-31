"""L2CAP server for receiving BLE payload bytes (Linux / PyBluez)."""

import bluetooth

from ble_blockchain.config.loader import load_l2cap_config


def l2cap_server() -> bytes:
    """Receive one serialized payload over L2CAP and return raw bytes."""
    config = load_l2cap_config()
    server_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    server_sock.bind(("", config.psm))
    server_sock.listen(1)

    try:
        print("送信されてくるデータを待ってます")
        client_sock, address = server_sock.accept()
        print(f"接続を確認{address}")

        chunks: list[bytes] = []
        total = 0
        while True:
            try:
                chunk = client_sock.recv(config.recv_bufsize)
            except bluetooth.BluetoothError:
                break

            if not chunk:
                break

            chunks.append(chunk)
            total += len(chunk)
            print(f"total byte read:{total}")

        client_sock.close()
        payload = b"".join(chunks)
        print(f"データを受信しました: {len(payload)} bytes")
        print("connection closed")
        return payload
    finally:
        server_sock.close()
