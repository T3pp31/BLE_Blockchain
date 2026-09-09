"""File-based transport that exchanges payloads via local directories."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd


class FileTransportService:
    """Exchange payloads by writing/reading files under a shared inbox dir."""

    def __init__(
        self,
        *,
        inbox_dir: Path,
        scan_csv: Path,
        sender_id: str,
        poll_interval_sec: float = 0.5,
    ) -> None:
        self.inbox_dir = inbox_dir
        self.scan_csv = scan_csv
        self.sender_id = sender_id
        self.poll_interval_sec = poll_interval_sec

    def scan(self) -> tuple[list[str], list[str]]:
        """Read peer addresses and names from the configured scan CSV."""
        if not self.scan_csv.exists():
            return [], []

        df = pd.read_csv(self.scan_csv)
        return list(df["bt_addrs"]), list(df["device_name"])

    def start_discoverable(self) -> None:
        """No-op for file transport."""
        return None

    def send_payload(self, peers: list[str], payload_bytes: bytes) -> None:
        """Write payloads to the shared inbox dir, prefixed by recipient IDs."""
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time() * 1000)
        for peer in peers:
            safe_peer = peer.replace(":", "_")
            filename = f"{safe_peer}__{self.sender_id}-{timestamp}.bin"
            (self.inbox_dir / filename).write_bytes(payload_bytes)

    def receive_payload(self) -> bytes:
        """Read the oldest inbox file addressed to this sender, or poll."""
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        while True:
            candidates = sorted(
                self.inbox_dir.glob(f"{self.sender_id}*.bin"),
                key=lambda path: path.stat().st_mtime,
            )
            if candidates:
                path = candidates[0]
                payload = path.read_bytes()
                path.unlink()
                return payload
            time.sleep(self.poll_interval_sec)
