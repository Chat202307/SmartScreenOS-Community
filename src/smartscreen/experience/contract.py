from typing import Iterable, List

from src.smartscreen.contracts.base import ModuleContract
from src.smartscreen.contracts.types import Experience
from src.smartscreen.home_event import HomeEvent


class ExperienceContract(ModuleContract):
    """Contract: HomeEvent(s) to explainable Experience(s)."""

    @property
    def name(self) -> str:
        return "experience"

    @property
    def purpose(self) -> str:
        return (
            "Translate verified home facts into human-readable, "
            "explainable household experience."
        )

    def process(self, value: Iterable[HomeEvent]) -> List[Experience]:
        raise NotImplementedError(
            "M031 will provide the Experience Engine implementation."
        )
