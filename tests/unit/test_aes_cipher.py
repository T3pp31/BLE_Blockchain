"""Unit tests for AES payload encryption and decryption."""

import pytest

from ble_blockchain.cipher.aes_cipher import decrypt_payload, encrypt_payload


def test_encrypt_decrypt_roundtrip() -> None:
    """正常系: encrypt then decrypt restores plaintext."""
    # Given: plaintext and fixed AES key
    plaintext = b"gakuseki,bt_addrs\n19G110001,FC:66:CF:BE:10:BF\n"
    key = bytes.fromhex(
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )

    # When: encrypt then decrypt
    ciphertext, nonce = encrypt_payload(plaintext, key=key)
    restored = decrypt_payload(ciphertext, nonce, key=key)

    # Then: plaintext is restored
    assert restored == plaintext
    assert ciphertext != plaintext


def test_decrypt_tampered_ciphertext_raises() -> None:
    """異常系: tampered ciphertext fails GCM authentication."""
    # Given: encrypted payload with tampered ciphertext
    key = bytes.fromhex(
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    ciphertext, nonce = encrypt_payload(b"secret", key=key)
    tampered = bytes([b ^ 0xFF for b in ciphertext])

    # When/Then: GCM authentication fails
    with pytest.raises(ValueError):
        decrypt_payload(tampered, nonce, key=key)


def test_load_aes_key_invalid_length(monkeypatch: pytest.MonkeyPatch) -> None:
    """異常系: invalid BLE_AES_KEY length raises ValueError."""
    # Given: env var with wrong key length
    monkeypatch.setenv("BLE_AES_KEY", "abcd")

    # When/Then: load fails via encrypt without explicit key
    with pytest.raises(ValueError, match="32 bytes"):
        encrypt_payload(b"data")
