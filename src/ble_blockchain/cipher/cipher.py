"""ECDSA signing, verification, and PEM key helpers."""

from pathlib import Path
from typing import Union

from ecdsa import SECP256k1, BadSignatureError, SigningKey, VerifyingKey


def load_signing_key_from_pem(path: Union[str, Path]) -> SigningKey:
    """Load an ECDSA signing key from a PEM file."""
    key_path = Path(path)
    with open(key_path, "rb") as key_file:
        return SigningKey.from_pem(key_file.read())


def make_key() -> tuple[SigningKey, VerifyingKey]:
    """Generate a new SECP256k1 signing key pair."""
    secret_key = SigningKey.generate(curve=SECP256k1)
    public_key = secret_key.verifying_key
    return secret_key, public_key


def public_key_to_pem(public_key: VerifyingKey) -> str:
    """Encode a verifying key as an ASCII PEM string."""
    return public_key.to_pem().decode("ascii")


def public_key_from_pem(pem: str) -> VerifyingKey:
    """Parse a verifying key from an ASCII PEM string."""
    return VerifyingKey.from_pem(pem.encode("ascii"))


def make_signature(secret_key: SigningKey, plaintext: bytes) -> bytes:
    """Sign plaintext bytes with the given secret key."""
    return secret_key.sign(plaintext)


def judge_signature(
    signature: bytes, plaintext: bytes, public_key: VerifyingKey
) -> bool:
    """Return True when the signature verifies for the plaintext and public key."""
    try:
        return public_key.verify(signature, plaintext)
    except BadSignatureError:
        return False
