import binascii
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.keywrap import aes_key_wrap, aes_key_unwrap
from django.conf import settings


class EncryptionError(Exception):
    """Raised when there is a cryptographic error or misconfiguration."""
    pass


def _get_ket_bytes() -> bytes:
    """
    Loads the Key Encryption Key (KEK) from settings.KMS_KEK_HEX.
    KEK is hex-encoded 32-byte value for 256-bit AES encryption.
    """
    hexadecimal_value = settings.KMS_KEK_HEX
    if not hexadecimal_value :
        raise EncryptionError("Key Encryption Key (KEK) not configured. Set KMS_KEK_HEX in environment.")
    try:
        return binascii.unhexlify(hexadecimal_value)
    except binascii.Error:
        raise EncryptionError("Invalid KMS_KEK_HEX (Must be hexadecimal),")


def encrypt_message(plaintext: bytes, aad: bytes) -> dict:
    """
    Encrypts a message using per-message DEK and AES-256-GCM.
    Returns dictionary with fields appropriate for Message model.
    """
    # 1. Data Encrypted Key (DEK) for each message (AES-256)
    dek = os.urandom(32)

    # 2. Encryption AES-GCM
    nonce = os.urandom(12)
    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(nonce,plaintext, aad)

    # 3. Wrap Data Encrypted Key (DEK) with Key Encrypted Key (KEK) for verification of Integrity
    kek = _get_ket_bytes()
    wrapped_dek = aes_key_wrap(kek,dek)

    return {
        "alg": "AES-256-GCM",
        "ciphertext": ciphertext,
        "nonce": nonce,
        "aad": aad,
        "wrapped_dek": wrapped_dek,
        "kek_id": settings.KEK_ID
    }


def decrypt_message(ciphertext: bytes, nonce: bytes, aad: bytes, wrapped_dek: bytes) -> bytes:
    """
    Returns a message (decrypted) that was encrypted with encrypt_message() function.
    If ciphertext, nonce, or aad are modified, AESGCM() will fail.
    If wrapped_dek or KEK have been altered, decryption will fail.
    """
    kek = _get_ket_bytes()
    dek = aes_key_unwrap(kek, wrapped_dek)
    aesgcm = AESGCM(dek)
    return aesgcm.decrypt(nonce, ciphertext, aad)