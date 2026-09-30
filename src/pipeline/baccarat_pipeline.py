from typing import Any, List

import numpy as np

from lib.cache.main import cacheable
from src.pipeline.abstract_pipeline import AbstractPipeline


class BaccaratPipeline(AbstractPipeline):

    @cacheable(prefix="baccarat_pipeline", value="", ttl=1)
    def run(self, frame_rgb: np.ndarray) -> List[Any]:
        """Placeholder: finds nothing until the detector and classifier are wired in."""
        return []
