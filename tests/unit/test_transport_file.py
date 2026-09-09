"""Unit tests for FileTransportService (shared-inbox file transport)."""

import os
import time
from pathlib import Path

import pytest

from ble_blockchain.transport_file import FileTransportService

class _PollingObserved(Exception):
    """receive_payload がポーリング（sleep）に達したことを示す番兵例外。"""


def _make_service(
    inbox_dir: Path,
    scan_csv: Path,
    *,
    sender_id: str = "device1",
    poll_interval_sec: float = 0.01,
) -> FileTransportService:
    """Build a FileTransportService with the given paths (test helper)."""
    return FileTransportService(
        inbox_dir=inbox_dir,
        scan_csv=scan_csv,
        sender_id=sender_id,
        poll_interval_sec=poll_interval_sec,
    )


def _write_scan_csv(path: Path, *, header: str = "bt_addrs,device_name") -> None:
    """Write a scan CSV with the given header and rows (test helper)."""
    path.write_text(
        f"{header}\n"
        "FC:66:CF:BE:10:BF,phone\n"
        "AA:BB:CC:DD:EE:FF,laptop\n",
        encoding="utf-8",
    )


def _assert_polls_then_returns(svc: FileTransportService) -> None:
    """sleep を番兵化して receive_payload のポーリング発生を安全に検証する。"""
    real_sleep = time.sleep
    try:
        time.sleep = lambda _seconds: (_ for _ in ()).throw(_PollingObserved())  # type: ignore[assignment]
        svc.receive_payload()
        pytest.fail("sleep (polling) should have been observed")
    except _PollingObserved:
        return  # ポーリングが観測された（以降のアサーションは呼び出し側で行う）
    finally:
        time.sleep = real_sleep  # type: ignore[assignment]


class TestScan:
    """scan(): CSV 読み取りのテスト。"""

    def test_scan_returns_addresses_and_names(self, tmp_path: Path) -> None:
        """正常系: bt_addrs / device_name の2列 CSV からタプルが返る。"""
        # Given: 有効な scan CSV を指定した transport
        csv_path = tmp_path / "scan.csv"
        _write_scan_csv(csv_path)
        svc = _make_service(tmp_path / "inbox", csv_path)

        # When: scan() を呼ぶ
        bt_addrs, device_name = svc.scan()

        # Then: アドレスと端末名のタプルが返る
        assert bt_addrs == ["FC:66:CF:BE:10:BF", "AA:BB:CC:DD:EE:FF"]
        assert device_name == ["phone", "laptop"]

    def test_scan_missing_csv_returns_empty(self, tmp_path: Path) -> None:
        """正常系(境界値): CSV が存在しないと空タプルが返る。"""
        # Given: 存在しない scan CSV を指定した transport
        svc = _make_service(tmp_path / "inbox", tmp_path / "nonexistent.csv")

        # When: scan() を呼ぶ
        bt_addrs, device_name = svc.scan()

        # Then: 空タプル（[]、[]）が返る
        assert bt_addrs == []
        assert device_name == []

    def test_scan_missing_bt_addrs_column_raises_key_error(
        self, tmp_path: Path,
    ) -> None:
        """異常系: bt_addrs 列が無い CSV では KeyError が発生する。"""
        # Given: bt_addrs 列が無い CSV を指定した transport
        csv_path = tmp_path / "bad.csv"
        csv_path.write_text("device_name\nphone\n", encoding="utf-8")
        svc = _make_service(tmp_path / "inbox", csv_path)

        # When/Then: scan() が KeyError を投げる
        with pytest.raises(KeyError):
            svc.scan()


class TestSendPayload:
    """send_payload(): inbox への書き込みのテスト。"""

    def test_send_payload_no_peers_creates_no_files(self, tmp_path: Path) -> None:
        """正常系(境界値): peers が 0 件ならファイルは生成されない。"""
        # Given: peers を渡さない transport
        inbox = tmp_path / "inbox"
        svc = _make_service(inbox, tmp_path / "scan.csv")

        # When: peers = [] で send_payload() を呼ぶ
        svc.send_payload([], b"payload")

        # Then: inbox ディレクトリは作成されるがファイルは無い
        assert inbox.is_dir()
        assert list(inbox.iterdir()) == []

    def test_send_payload_single_peer(self, tmp_path: Path) -> None:
        """正常系: peers 1 件で受信者プレフィックスのファイルが作られる。"""
        # Given: sender_id="device1" の transport
        inbox = tmp_path / "inbox"
        svc = _make_service(inbox, tmp_path / "scan.csv", sender_id="device1")

        # When: 1 件の peer へ送信する
        svc.send_payload(["device2"], b"hello")

        # Then: device2 プレフィックスのファイルが 1 つ生成され内容が一致する
        files = list(inbox.glob("*.bin"))
        assert len(files) == 1
        assert files[0].name.startswith("device2__device1-")
        assert files[0].read_bytes() == b"hello"

    def test_send_payload_multiple_peers(self, tmp_path: Path) -> None:
        """正常系: peers 複数件で受信者ごとにファイルが生成される。"""
        # Given: sender_id="device1" の transport
        inbox = tmp_path / "inbox"
        svc = _make_service(inbox, tmp_path / "scan.csv", sender_id="device1")

        # When: 2 件の peer（うち1件は ':' を含むアドレス）へ送信する
        svc.send_payload(["device2", "AA:BB:CC:DD:EE:FF"], b"data")

        # Then: 受信者プレフィックス付きファイルが 2 つ生成される
        files = sorted(path.name for path in inbox.glob("*.bin"))
        assert len(files) == 2
        assert any(name.startswith("device2__device1-") for name in files)
        # アドレスの ':' は '_' に置換される
        assert any(name.startswith("AA_BB_CC_DD_EE_FF__device1-") for name in files)
        assert all((inbox / name).read_bytes() == b"data" for name in files)


class TestReceivePayload:
    """receive_payload(): inbox からの読み取り・削除・ポーリングのテスト。"""

    def test_receive_returns_bytes_and_deletes_file(self, tmp_path: Path) -> None:
        """正常系: 自分宛ファイルがあれば bytes が返りファイルが削除される。"""
        # Given: device2 宛のファイルが inbox に 1 件ある
        inbox = tmp_path / "inbox"
        inbox.mkdir(parents=True)
        (inbox / "device2__device1-100.bin").write_bytes(b"hello")
        svc = _make_service(inbox, tmp_path / "scan.csv", sender_id="device2")

        # When: receive_payload() を呼ぶ
        result = svc.receive_payload()

        # Then: 内容が返り、ファイルは削除されている
        assert result == b"hello"
        assert list(inbox.glob("*.bin")) == []

    def test_receive_ignores_other_senders(self, tmp_path: Path) -> None:
        """異常系: 自分宛でないファイルは返さず、残される。"""
        # Given: device1 / device3 宛のファイルのみがある
        inbox = tmp_path / "inbox"
        inbox.mkdir(parents=True)
        other_a = inbox / "device1__x-1.bin"
        other_b = inbox / "device3__x-2.bin"
        other_a.write_bytes(b"for-device1")
        other_b.write_bytes(b"for-device3")
        svc = _make_service(inbox, tmp_path / "scan.csv", sender_id="device2")

        # When: sleep を番兵化して receive_payload() を回す（無限ループ回避）
        _assert_polls_then_returns(svc)

        # Then: 自分宛でないファイルは残っている
        assert other_a.exists()
        assert other_b.exists()

    def test_receive_polls_until_file_arrives(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """正常系(外部依存): 空の間はポーリングし、ファイル到着後に返す。"""
        # Given: 最初は空の inbox と、1 回目の sleep でファイルを注入する sleep
        inbox = tmp_path / "inbox"
        svc = _make_service(inbox, tmp_path / "scan.csv", sender_id="device1")
        sleep_calls: list[float] = []

        def fake_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)
            (inbox / "device1__peer-1.bin").write_bytes(b"late")

        monkeypatch.setattr("ble_blockchain.transport_file.time.sleep", fake_sleep)

        # When: receive_payload() を呼ぶ
        result = svc.receive_payload()

        # Then: ポーリング後に内容が返り、sleep は 1 回だけ呼ばれる
        assert result == b"late"
        assert len(sleep_calls) == 1

    def test_receive_returns_oldest_by_mtime(self, tmp_path: Path) -> None:
        """正常系: 2 件ある場合は最古の mtime のものが返される。"""
        # Given: device1 宛ファイルが 2 件（mtime が異なる）
        inbox = tmp_path / "inbox"
        inbox.mkdir(parents=True)
        recent = inbox / "device1__a-2.bin"
        oldest = inbox / "device1__a-1.bin"
        recent.write_bytes(b"recent")
        oldest.write_bytes(b"oldest")
        os.utime(recent, (2000, 2000))
        os.utime(oldest, (1000, 1000))
        svc = _make_service(inbox, tmp_path / "scan.csv", sender_id="device1")

        # When: receive_payload() を呼ぶ
        result = svc.receive_payload()

        # Then: 最古の内容が返り、新しい方は残る
        assert result == b"oldest"
        assert not oldest.exists()
        assert recent.exists()


class TestRoundtrip:
    """端末間ラウンドトリップのテスト。"""

    def test_roundtrip_device_a_to_device_b(self, tmp_path: Path) -> None:
        """正常系: device1 の送信を device2 が受信できる。"""
        # Given: 共有 inbox と scan CSV を共有する 2 台の transport
        inbox = tmp_path / "inbox"
        csv_path = tmp_path / "scan.csv"
        _write_scan_csv(csv_path)
        svc_a = _make_service(inbox, csv_path, sender_id="device1")
        svc_b = _make_service(inbox, csv_path, sender_id="device2")

        # When: device1 が device2 宛に送信し、device2 が受信する
        svc_a.send_payload(["device2"], b"hello")
        result = svc_b.receive_payload()

        # Then: ペイロードが一致し、scan も共有 CSV を返す
        assert result == b"hello"
        assert svc_b.scan() == (
            ["FC:66:CF:BE:10:BF", "AA:BB:CC:DD:EE:FF"],
            ["phone", "laptop"],
        )


class TestStartDiscoverable:
    """start_discoverable(): no-op のテスト。"""

    def test_start_discoverable_returns_none(self, tmp_path: Path) -> None:
        """正常系: no-op であり None が返る。"""
        # Given: file transport
        svc = _make_service(tmp_path / "inbox", tmp_path / "scan.csv")

        # When: start_discoverable() を呼ぶ
        result = svc.start_discoverable()

        # Then: None が返り、副作用がない
        assert result is None
        assert not (tmp_path / "inbox").exists()
