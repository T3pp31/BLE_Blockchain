from __future__ import annotations

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from ble_blockchain.config.loader import load_aes_key

NONCE_SIZE = 12
TAG_SIZE = 16


def encrypt_payload(plaintext: bytes, key: bytes | None = None) -> tuple[bytes, bytes]:
    aes_key = key if key is not None else load_aes_key()
    nonce = get_random_bytes(NONCE_SIZE)
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return ciphertext + tag, nonce


def decrypt_payload(
    ciphertext_with_tag: bytes, nonce: bytes, key: bytes | None = None
) -> bytes:
    aes_key = key if key is not None else load_aes_key()
    ciphertext = ciphertext_with_tag[:-TAG_SIZE]
    tag = ciphertext_with_tag[-TAG_SIZE:]
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
