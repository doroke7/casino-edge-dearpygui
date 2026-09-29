"""Abstract base class for IR pipelines.

Each concrete pipeline wraps model inference and returns plain tuple results.
The service layer converts those tuples into gRPC/protobuf messages.
"""

from __future__ import annotations

import abc
from typing import List, Any

import numpy as np


class AbstractPipeline(abc.ABC):
    """Interface every pipeline must implement."""

    @abc.abstractmethod
    def run(self, frame_rgb: np.ndarray) -> List[Any]:
        """Run the pipeline on *frame* and return the results."""

