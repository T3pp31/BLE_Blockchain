import os

import pandas as pd
import pytest

TEST_AES_KEY_HEX = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)


@pytest.fixture(autouse=True)
def aes_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLE_AES_KEY", TEST_AES_KEY_HEX)


@pytest.fixture
def sample_scan_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "bt_addrs": ["FC:66:CF:BE:10:BF", "AA:BB:CC:DD:EE:FF"],
            "device_name": ["phone", "laptop"],
        }
    )


@pytest.fixture
def sample_plaintext_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "gakuseki": ["19G110001"],
            "bt_addrs": ["FC:66:CF:BE:10:BF"],
            "device_name": ["phone"],
        }
    )
