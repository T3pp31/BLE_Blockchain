"""Unit tests for main.py behaviors reached through the transport layer."""

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from ble_blockchain.app.main import build_send_payload, run_communication_steps
from ble_blockchain.cipher.cipher import make_key, public_key_to_pem
from ble_blockchain.config.device_settings import DeviceSettings
from ble_blockchain.transport_file import FileTransportService


def _make_settings(*, signing_key_path: str, trusted_pems: frozenset[str]) -> DeviceSettings:
    """Build a DeviceSettings with the given key paths (test helper)."""
    return DeviceSettings(
        profile="device1",
        tanmatsu_bt_addrs=["AA:BB:CC:DD:EE:FF"],
        signing_key_path=signing_key_path,
        public_key_pem="pem-self",
        trusted_peer_pems=trusted_pems,
        settings_path=Path("settings1.json"),
    )


def _write_signing_key(path: Path) -> str:
    """Write an ECDSA signing key in PEM and return its peer public key PEM (test helper)."""
    secret_key, public_key = make_key()
    pem = public_key_to_pem(public_key)
    path.write_bytes(secret_key.to_pem())
    return pem


def _read_first_registered_bt_addr() -> str:
    """Read the first bt_addrs from the registered preliminary CSV (test helper)."""
    df = pd.read_csv("data_folder/事前取得データ.csv")
    return str(df["bt_addrs"].iloc[0])


class FakeScanTransport:
    """TransportService 実装: scan が固定タプルを返し、呼び出しを記録するフェイク。"""

    def __init__(self, bt_addrs: list[str], device_names: list[str]) -> None:
        self._bt_addrs = bt_addrs
        self._device_names = device_names
        self.send_calls: list[tuple[list[str], bytes]] = []
        self.discoverable_calls = 0
        self.receive_calls = 0

    def scan(self) -> tuple[list[str], list[str]]:
        return self._bt_addrs, self._device_names

    def start_discoverable(self) -> None:
        self.discoverable_calls += 1

    def send_payload(self, peers: list[str], payload_bytes: bytes) -> None:
        self.send_calls.append((peers, payload_bytes))

    def receive_payload(self) -> bytes:
        self.receive_calls += 1
        return b""


class TestBuildSendPayload:
    """build_send_payload(): scan → 署名・暗号化・pack のテスト。"""

    def test_returns_verifiable_payload(self, tmp_path: Path) -> None:
        """正常系: pack された bytes が返り、受信側 process_received_payload が検証できる。"""
        # Given: 事前登録 CSV に載っている bt_addrs と署名鍵
        registered_addr = _read_first_registered_bt_addr()
        signing_key_path = tmp_path / "signing.pem"
        key_pem = _write_signing_key(signing_key_path)
        settings = _make_settings(
            signing_key_path=str(signing_key_path),
            trusted_pems=frozenset({key_pem}),
        )
        fake = FakeScanTransport([registered_addr], ["phone"])

        # When: build_send_payload() を呼ぶ
        payload = build_send_payload(settings, fake)

        # Then: pack された bytes が返り、受信検証で verified=True になる
        from ble_blockchain.app.main import process_received_payload

        assert isinstance(payload, bytes)
        assert len(payload) > 0
        result = process_received_payload(payload, settings.trusted_peer_pems)
        assert result.verified is True
        assert result.df is not None
        assert registered_addr in result.df["bt_addrs"].values


class TestRunCommunicationSteps:
    """run_communication_steps(): 各 action の実行と委譲のテスト。"""

    def test_receive_appends_verified_payload(self, tmp_path: Path) -> None:
        """正常系: receive で検証可能な payload が 1 件追加される。"""
        # Given: 送信側 payload を検証可能な file transport と受信側 settings
        sender_pem = _write_signing_key(tmp_path / "sender.pem")
        receiver_settings = _make_settings(
            signing_key_path=str(tmp_path / "sender.pem"),
            trusted_pems=frozenset({sender_pem}),
        )
        inbox = tmp_path / "inbox"
        inbox.mkdir(parents=True)
        scan_csv = tmp_path / "scan.csv"
        scan_csv.write_text("bt_addrs,device_name\n", encoding="utf-8")
        transport = FileTransportService(
            inbox_dir=inbox,
            scan_csv=scan_csv,
            sender_id="device1",
            poll_interval_sec=0.0,
        )

        # When: 検証可能な payload を device1 宛に入れて receive を実行する
        payload_bytes = build_send_payload(receiver_settings, FakeScanTransport([], []))
        (inbox / "device1__peer-1.bin").write_bytes(payload_bytes)
        receive_data_list: list[Any] = []
        run_communication_steps(
            {"steps": [{"action": "receive"}]},
            receiver_settings,
            transport,
            receive_data_list,
        )

        # Then: 1 件検証済みで追加される
        assert len(receive_data_list) == 1
        assert receive_data_list[0].verified is True
        assert receive_data_list[0].df is not None

    def test_sleep_action_calls_time_sleep(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """正常系: sleep action は time.sleep を指定秒数で呼ぶ。"""
        # Given: settings と fake transport
        _write_signing_key(tmp_path / "signing.pem")
        settings = _make_settings(
            signing_key_path=str(tmp_path / "signing.pem"),
            trusted_pems=frozenset(),
        )
        fake = FakeScanTransport([], [])
        sleep_log: list[float] = []

        def record_sleep(seconds: float) -> None:
            sleep_log.append(seconds)

        monkeypatch.setattr("ble_blockchain.app.main.time.sleep", record_sleep)

        # When: sleep を含む steps を実行する
        run_communication_steps(
            {"steps": [{"action": "sleep", "seconds": 2.5}]},
            settings,
            fake,
            [],
        )

        # Then: time.sleep が指定秒数で呼ばれる
        assert sleep_log == [2.5]

    def test_discoverable_and_send_delegate_to_transport(self, tmp_path: Path) -> None:
        """正常系: discoverable / send が transport メソッドへ委譲される。"""
        # Given: 事前登録 bt_addr を返す fake transport と署名鍵
        registered_addr = _read_first_registered_bt_addr()
        signing_key_path = tmp_path / "signing.pem"
        _write_signing_key(signing_key_path)
        settings = _make_settings(
            signing_key_path=str(signing_key_path),
            trusted_pems=frozenset(),
        )
        fake = FakeScanTransport([registered_addr], ["phone"])

        # When: discoverable / send を含む steps を実行する
        run_communication_steps(
            {
                "steps": [
                    {"action": "discoverable"},
                    {"action": "send"},
                ]
            },
            settings,
            fake,
            [],
        )

        # Then: start_discoverable が 1 回、send が settings の bt_addrs で呼ばれる
        assert fake.discoverable_calls == 1
        assert len(fake.send_calls) == 1
        assert fake.send_calls[0][0] == settings.tanmatsu_bt_addrs
        assert isinstance(fake.send_calls[0][1], bytes)

    def test_unknown_action_raises_value_error(self, tmp_path: Path) -> None:
        """異常系: 未知の action では ValueError が投げられる。"""
        # Given: settings と fake transport
        signing_key_path = tmp_path / "signing.pem"
        _write_signing_key(signing_key_path)
        settings = _make_settings(
            signing_key_path=str(signing_key_path),
            trusted_pems=frozenset(),
        )
        fake = FakeScanTransport([], [])

        # When/Then: 未知 action で ValueError が投げられる
        with pytest.raises(ValueError, match="Unknown step action:"):
            run_communication_steps(
                {"steps": [{"action": "broadcast"}]}, settings, fake, []
            )
