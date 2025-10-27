from typing import Optional

from apps.users.utils.encryption import decrypt_token, encrypt_token
from django.db import models
from utils.base_models import BaseModel


class ProviderAccount(BaseModel):
    class ProviderChoices(models.TextChoices):
        INSTAGRAM = "INSTAGRAM", "Instagram"
        FACEBOOK = "FACEBOOK", "Facebook"
        YOUTUBE = "YOUTUBE", "Youtube"
        X = "X", "X"

    profile = models.ForeignKey(
        to="EditorProfile",
        on_delete=models.CASCADE,
        related_name="provider_accounts",
    )
    provider = models.CharField(choices=ProviderChoices.choices)
    _access_token = models.BinaryField(db_column="access_token", editable=False)
    _refresh_token = models.BinaryField(
        db_column="refresh_token", editable=False, null=True, blank=True
    )
    _expires_at = models.DateTimeField(null=True, blank=True)
    _key_version = models.PositiveIntegerField(default=1)

    @property
    def access_token(self) -> str:
        return decrypt_token(self._access_token, self._key_version)

    @access_token.setter
    def access_token(self, value: str):
        self._access_token, self._key_version = encrypt_token(value)

    @property
    def refresh_token(self) -> Optional[str]:
        if not self._refresh_token:
            return None
        return decrypt_token(self._refresh_token, self._key_version)

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]):
        if value:
            self._refresh_token, self._key_version = encrypt_token(value)
        else:
            self._refresh_token = None
