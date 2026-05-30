import pytest

from ble.message_codec import MessagePayload, pack, unpack


def test_pack_unpack_roundtrip() -> None:
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
    # Given: JSON with unsupported version
    raw = b'{"version":99,"ciphertext_b64":"","nonce_b64":"","public_key_pem":"","signature_b64":""}'

    # When/Then: unpack raises ValueError
    with pytest.raises(ValueError, match="Unsupported message version"):
        unpack(raw)


def test_unpack_invalid_json() -> None:
    # Given: malformed JSON bytes
    raw = b"not-json"

    # When/Then: json.loads fails
    with pytest.raises(Exception):
        unpack(raw)
