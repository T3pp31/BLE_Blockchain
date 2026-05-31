"""Unit tests for BLE message codec pack/unpack."""

import pytest

from ble_blockchain.ble.message_codec import MessagePayload, pack, unpack

_INVALID_VERSION_RAW = (
    b'{"version":99,"ciphertext_b64":"","nonce_b64":"",'
    b'"public_key_pem":"","signature_b64":""}'
)


def test_pack_unpack_roundtrip() -> None:
    """正常系: pack then unpack restores all fields."""
    # Given: a message payload with binary fields
    payload = MessagePayload(
        ciphertext=b"cipher",
        nonce=b"123456789012",
        public_key_pem="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
        signature=b"sigbytes",
    )

    # When: packing and unpacking
    raw = pack(payload)
    restored = unpack(raw)

    # Then: all fields match
    assert restored.ciphertext == payload.ciphertext
    assert restored.nonce == payload.nonce
    assert restored.public_key_pem == payload.public_key_pem
    assert restored.signature == payload.signature


def test_unpack_invalid_version() -> None:
    """異常系: unsupported version raises ValueError."""
    # Given: JSON with unsupported version
    raw = _INVALID_VERSION_RAW

    # When/Then: unpack raises ValueError
    with pytest.raises(ValueError, match="Unsupported message version"):
        unpack(raw)


def test_unpack_invalid_json() -> None:
    """異常系: malformed JSON raises an exception."""
    # Given: malformed JSON bytes
    raw = b"not-json"

    # When/Then: json.loads fails
    with pytest.raises(Exception):
        unpack(raw)
