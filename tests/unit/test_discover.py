"""Unit tests for BLE device discovery."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from ble_blockchain.ble.discover import scan


def test_scan_uses_bleak_device_fields() -> None:
    """正常系: scan extracts address and name from bleak devices."""
    # Given: bleak devices with address and name
    device_a = MagicMock()
    device_a.address = "AA:BB:CC:DD:EE:FF"
    device_a.name = "Phone: with colon"

    device_b = MagicMock()
    device_b.address = "11:22:33:44:55:66"
    device_b.name = None

    mock_discover = AsyncMock(return_value=[device_a, device_b])

    # When: scanning
    async def run_scan():
        with patch(
            "ble_blockchain.ble.discover.BleakScanner.discover", mock_discover
        ):
            return await scan()

    bt_addrs, device_names = asyncio.run(run_scan())

    # Then: address and name extracted without str().split
    assert bt_addrs == ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]
    assert device_names == ["Phone: with colon", ""]
