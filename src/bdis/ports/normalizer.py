from abc import ABC, abstractmethod
from typing import Dict, Any

class INormalizer(ABC):
    """
    Port for performing deterministic data normalization and correction.
    """
    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw extracted data and returns a normalized version.
        """
        pass
