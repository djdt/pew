import numpy as np
import copy

from .config import LaserConfig
from .data import LaserData

from typing import Any, Dict, List, Tuple


class Laser(object):
    def __init__(
        self,
        data: Dict[str, LaserData] = None,
        config: LaserConfig = None,
        name: str = "",
        path: str = "",
    ):
        self.data = data if data is not None else {}
        self.layers = 1
        self.config = copy.copy(config) if config is not None else LaserConfig()

        self.name = name
        self.path = path

    @property
    def extent(self) -> Tuple[float, float, float, float]:
        if len(self.data) == 0:
            return (0, 0, 0, 0)
        return self.config.data_extent(self.get(self.isotopes[0]))

    @property
    def isotopes(self) -> List[str]:
        return list(self.data.keys())

    def add(self, isotope: str, data: np.ndarray) -> None:
        self.data[isotope] = LaserData(data)

    def get(self, isotope: str, **kwargs: Any) -> np.ndarray:
        """Valid kwargs are calibrate, extent, flat."""
        return self.data[isotope].get(self.config, **kwargs)

    def get_structured(self, **kwargs: Any) -> np.ndarray:
        dtype = [(isotope, float) for isotope in self.data]
        structured = np.empty(next(iter(self.data.values())).data.shape, dtype)
        for isotope, _ in dtype:
            structured[isotope] = self.data[isotope].get(self.config, **kwargs)
        return structured

    @classmethod
    def from_structured(
        cls,
        data: np.ndarray,
        config: LaserConfig = None,
        name: str = "",
        filepath: str = "",
    ):  # type: ignore
        data = {k: LaserData(data[k]) for k in data.dtype.names}
        return cls(data=data, config=config, name=name, filepath=filepath)
