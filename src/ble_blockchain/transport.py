"""Transport abstraction for payload exchange (BLE or file based)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ble_blockchain.config.device_settings import DeviceSettings
from ble_blockchain.config.loader import load_transport_config
from ble_blockchain.transport_file import FileTransportService


class TransportService(Protocol):
    """Common interface for exchanging payloads with peers."""

    # pylint: disable=missing-function-docstring
    def scan(self) -> tuple[list[str], list[str]]:
        ...

    def start_discoverable(self) -> None:
        ...

    def send_payload(self, peers: list[str], payload_bytes: bytes) -> None:
        ...

    def receive_payload(self) -> bytes:
        ...

    # pylint: enable=missing-function-docstring


class BleTransportService:
    """Transport over BLE. 依存ライブラリは実行時 import で解決する。"""

    def scan(self) -> tuple[list[str], list[str]]:
        """Scan BLE devices via the discover module."""
        # bleak をモジュール import 時に解決しないため実行時 import する
        from ble_blockchain.ble.discover import (  # pylint: disable=import-outside-toplevel
            scan,
        )

        import asyncio  # pylint: disable=import-outside-toplevel

        return asyncio.run(scan())

    def start_discoverable(self) -> None:
        """Make the device discoverable via bluetoothctl."""
        from ble_blockchain.ble.start_discoverable import (  # pylint: disable=import-outside-toplevel
            start_discoverable,
        )

        start_discoverable()

    def send_payload(self, peers: list[str], payload_bytes: bytes) -> None:
        """Send the packed payload to each peer over L2CAP."""
        from ble_blockchain.pipeline.send_and_receive import (  # pylint: disable=import-outside-toplevel
            SEND,
        )

        SEND(peers, payload_bytes)

    def receive_payload(self) -> bytes:
        """Receive one packed payload over L2CAP."""
        from ble_blockchain.ble.l2cap_server import (  # pylint: disable=import-outside-toplevel
            l2cap_server,
        )

        return l2cap_server()


def load_transport(settings: DeviceSettings) -> TransportService:
    """Build a transport service from config/transport.json mode."""
    config = load_transport_config()
    if config.mode == "ble":
        return BleTransportService()
    if config.mode == "file":
        sender_id = config.file_sender_id
        if not sender_id:
            sender_id = settings.settings_path.stem
        return FileTransportService(
            inbox_dir=Path(config.file_inbox_dir),
            scan_csv=Path(config.file_scan_csv),
            sender_id=sender_id,
            poll_interval_sec=config.file_poll_interval_sec,
        )
    raise ValueError(f"Unknown transport mode: {config.mode}")
