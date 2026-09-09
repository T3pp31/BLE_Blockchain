"""Unit tests for transport selection and BLE transport delegation."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ble_blockchain.config.device_settings import DeviceSettings
from ble_blockchain.config.loader import TransportConfig
from ble_blockchain.transport import BleTransportService, FileTransportService, load_transport


def _make_settings(*, settings_path: Path | None = None) -> DeviceSettings:
    """Build a minimal DeviceSettings for transport selection (test helper)."""
    return DeviceSettings(
        profile="device1",
        tanmatsu_bt_addrs=["AA:BB:CC:DD:EE:FF"],
        signing_key_path="keys/device1_private.pem",
        public_key_pem="pem-self",
        trusted_peer_pems=frozenset({"pem-2"}),
        settings_path=settings_path or Path("settings1.json"),
    )


class TestLoadTransport:
    """load_transport(): 設定 mode と設定値のテスト。"""

    def test_ble_mode_returns_ble_transport(self) -> None:
        """正常系: config/transport.json の mode="ble" で BleTransportService が返る。"""
        # Given: 本物の config/transport.json（mode="ble"）を読む transport
        settings = _make_settings()

        # When: load_transport() を呼ぶ
        transport = load_transport(settings)

        # Then: BleTransportService が返る
        assert isinstance(transport, BleTransportService)

    def test_file_mode_returns_file_transport(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """正常系: mode="file" で FileTransportService が返る。"""
        # Given: mode="file" の設定を返すスタブへ差し替え
        monkeypatch.setattr(
            "ble_blockchain.transport.load_transport_config",
            lambda: TransportConfig(
                mode="file",
                file_inbox_dir="data/inbox",
                file_scan_csv="data/scan.csv",
                file_sender_id="device9",
                file_poll_interval_sec=0.25,
            ),
        )

        # When: load_transport() を呼ぶ
        transport = load_transport(_make_settings())

        # Then: FileTransportService が設定値で構築される
        assert isinstance(transport, FileTransportService)
        assert transport.sender_id == "device9"
        assert transport.poll_interval_sec == 0.25
        assert Path("data/inbox") == transport.inbox_dir
        assert Path("data/scan.csv") == transport.scan_csv

    def test_file_mode_empty_sender_id_falls_back_to_settings_stem(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """正常系(境界値): sender_id 空文字なら settings_path.stem が使われる。"""
        # Given: sender_id が空の file 設定と settings_path を持つ settings
        settings_path = tmp_path / "settings5.json"
        settings_path.touch()
        settings = _make_settings(settings_path=settings_path)
        monkeypatch.setattr(
            "ble_blockchain.transport.load_transport_config",
            lambda: TransportConfig(
                mode="file",
                file_inbox_dir="data/inbox",
                file_scan_csv="data/scan.csv",
                file_sender_id="",
                file_poll_interval_sec=0.5,
            ),
        )

        # When: load_transport() を呼ぶ
        transport = load_transport(settings)

        # Then: sender_id に settings5 が使われる
        assert isinstance(transport, FileTransportService)
        assert transport.sender_id == "settings5"

    def test_unknown_mode_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """異常系: 未知の mode では ValueError が投げられる。"""
        # Given: mode="udp" の設定を返すスタブ
        monkeypatch.setattr(
            "ble_blockchain.transport.load_transport_config",
            lambda: TransportConfig(
                mode="udp",
                file_inbox_dir="data/inbox",
                file_scan_csv="data/scan.csv",
                file_sender_id="device1",
                file_poll_interval_sec=0.5,
            ),
        )

        # When/Then: メッセージに mode 名が含まれる ValueError が投げられる
        with pytest.raises(ValueError, match="udp"):
            load_transport(_make_settings())


class TestBleTransportService:
    """BleTransportService: 各 ble/ 配下関数への委譲のテスト。"""

    def test_scan_delegates_to_discover_scan(self) -> None:
        """正常系: scan() は discover.scan の結果をそのまま返す。"""
        # Given: discover.scan がタプルを返す AsyncMock
        expected = (["AA:BB:CC:DD:EE:FF"], ["phone"])
        service = BleTransportService()

        # When: scan() を呼ぶ（内部で asyncio.run が使われるため二重実行しない）
        with patch(
            "ble_blockchain.ble.discover.scan",
            new=AsyncMock(return_value=expected),
        ):
            result = service.scan()

        # Then: タプルがそのまま返る
        assert result == expected

    def test_send_payload_delegates_to_send(
        self,
    ) -> None:
        """正常系: send_payload() は SEND(peers, payload) を呼ぶ。"""
        # Given: SEND を Mock へ差し替え
        with patch("ble_blockchain.pipeline.send_and_receive.SEND") as mock_send:
            service = BleTransportService()

            # When: send_payload() を呼ぶ
            services = service.send_payload(["AA:BB:CC:DD:EE:FF"], b"bytes")

        # Then: SEND が peers と payload で 1 回呼ばれる
        mock_send.assert_called_once_with(["AA:BB:CC:DD:EE:FF"], b"bytes")
        assert services is None

    def test_receive_payload_delegates_to_l2cap_server(self) -> None:
        """正常系: receive_payload() は l2cap_server() の戻り値を返す。"""
        # Given: l2cap_server が bytes を返す Mock
        with patch(
            "ble_blockchain.ble.l2cap_server.l2cap_server",
            return_value=b"received",
        ) as mock_server:
            service = BleTransportService()

            # When: receive_payload() を呼ぶ
            result = service.receive_payload()

        # Then: l2cap_server の戻り値がそのまま返る
        assert result == b"received"
        mock_server.assert_called_once_with()

    def test_start_discoverable_delegates_to_start_discoverable(self) -> None:
        """正常系: start_discoverable() は ble の関数へ委譲する。"""
        # Given: start_discoverable を Mock へ差し替え
        with patch(
            "ble_blockchain.ble.start_discoverable.start_discoverable",
        ) as mock_start:
            service = BleTransportService()

            # When: start_discoverable() を呼ぶ
            service.start_discoverable()

        # Then: 委譲先が 1 回呼ばれる
        mock_start.assert_called_once_with()
