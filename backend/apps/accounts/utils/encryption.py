from typing import Optional

from cryptography.fernet import Fernet
from django.conf import settings


def get_fernet_for_version(key_version: int) -> Fernet:
    key = settings.ENCRYPTION_KEYS[key_version]
    return Fernet(key)


def encrypt_token(token: str, key_version: Optional[int] = None) -> tuple[bytes, int]:
    key_version = key_version or settings.CURRENT_KEY_VERSION
    f = get_fernet_for_version(key_version)
    return f.encrypt(token.encode()), key_version


def decrypt_token(encrypted: bytes, key_version: int) -> str:
    f = get_fernet_for_version(key_version)
    return f.decrypt(encrypted).decode()


def rotate_encrypted_field(instance, field_name: str):
    old_value = getattr(instance, field_name)
    if not old_value:
        return
    decrypted = decrypt_token(old_value, instance.key_version)
    encrypted, new_version = encrypt_token(decrypted)
    setattr(instance, field_name, encrypted)
    instance.key_version = new_version
