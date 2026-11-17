from abc import ABC, abstractmethod
from typing import Any


class ModuleContract(ABC):
    """Common contract for philosophy-driven SmartScreen modules."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def purpose(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def process(self, value: Any) -> Any:
        raise NotImplementedError
