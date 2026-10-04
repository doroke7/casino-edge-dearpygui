from typing import Any, List

import numpy as np

from src.pipeline.abstract_pipeline import AbstractPipeline


class BarajaPipeline(AbstractPipeline):

    def run(self, frame_rgb: np.ndarray, cache_key: str) -> List[Any]:
        """Placeholder: finds nothing until the detector and classifier are wired in."""
        return []
