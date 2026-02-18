from abc import ABC, abstractmethod

from django.core.files.storage import Storage


class BaseMediaStorage(Storage, ABC):
    "Base contract for any media backend"

    @abstractmethod
    def get_backend_name(self) -> str:
        pass

    def generate_url(self, name: str) -> str:
        return self.url(name)

    def health_check(self) -> bool:
        return True
