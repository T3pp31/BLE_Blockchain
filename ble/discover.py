# addressを探すためのコード
import asyncio

from bleak import BleakScanner


async def scan() -> tuple[list[str], list[str]]:
    """
    周囲のデバイスをスキャンし，端末名とアドレスを返す

    Return
    ----------
    bt_addrs, device_name : lists of BLE address and device name
    """
    bt_addrs: list[str] = []
    device_name: list[str] = []

    devices = await BleakScanner.discover()
    for device in devices:
        bt_addrs.append(device.address)
        device_name.append(device.name or "")

    return bt_addrs, device_name
