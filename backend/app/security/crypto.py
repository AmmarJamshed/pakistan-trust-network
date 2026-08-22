from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from nacl.encoding import Base64Encoder
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from app.config import settings


def _fernet() -> Fernet:
    """Derive a Fernet key from ENCRYPTION_KEY (accepts raw Fernet or passphrase)."""
    raw = settings.encryption_key.encode("utf-8")
    try:
        return Fernet(raw)
    except (ValueError, Exception):
        digest = hashlib.sha256(raw).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_json(payload: Any) -> str:
    """Deterministic JSON serialization for hashing/signing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_credential_payload(payload: dict[str, Any]) -> str:
    return sha256_hex(canonical_json(payload))


def generate_ed25519_keypair() -> tuple[str, str]:
    """Return (public_key_b64, private_key_b64) as URL-safe-ish base64 strings."""
    signing_key = SigningKey.generate()
    private_b64 = signing_key.encode(encoder=Base64Encoder).decode("utf-8")
    public_b64 = signing_key.verify_key.encode(encoder=Base64Encoder).decode("utf-8")
    return public_b64, private_b64


def encrypt_private_key(private_key_b64: str) -> str:
    token = _fernet().encrypt(private_key_b64.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_private_key(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt private key") from exc


def sign_ed25519(message: bytes | str, private_key_b64: str) -> str:
    if isinstance(message, str):
        message = message.encode("utf-8")
    signing_key = SigningKey(private_key_b64.encode("utf-8"), encoder=Base64Encoder)
    signed = signing_key.sign(message, encoder=Base64Encoder)
    return signed.signature.decode("utf-8")


def verify_ed25519(message: bytes | str, signature_b64: str, public_key_b64: str) -> bool:
    if isinstance(message, str):
        message = message.encode("utf-8")
    try:
        verify_key = VerifyKey(public_key_b64.encode("utf-8"), encoder=Base64Encoder)
        verify_key.verify(message, Base64Encoder.decode(signature_b64.encode("utf-8")))
        return True
    except (BadSignatureError, Exception):
        return False


def merkle_root(leaves: list[str]) -> str:
    """Compute a simple binary Merkle root from hex leaf hashes."""
    if not leaves:
        return sha256_hex("empty")
    level = [sha256_hex(leaf) if len(leaf) != 64 else leaf for leaf in leaves]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [sha256_hex(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]
