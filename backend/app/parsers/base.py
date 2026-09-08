from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.network import NetworkModel


class BaseParser(ABC):
    """Every vendor parser converts a raw exported config into a NetworkModel."""

    vendor: str = "generic"

    @classmethod
    @abstractmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        """Return True if this parser can likely handle the given export."""

    @abstractmethod
    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        """Parse the raw export text into the normalized NetworkModel."""
