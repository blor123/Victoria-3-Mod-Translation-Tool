from abc import ABC, abstractmethod

from app.mod_sources.models import ModEntry


class ModSourceProvider(ABC):
    """Read-only discovery boundary used by future v1.7/v1.8 providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @abstractmethod
    def discover(self) -> list[ModEntry]: ...
