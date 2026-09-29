import threading
from datetime import datetime
from pathlib import Path

from PIL import Image


class SnapshotWriter:
    """Saves camera frames (BGR numpy arrays) as JPEG files into a directory.

    A frame is written once: callers that arrive with the frame that was saved last
    (for example many RPCs at the same moment) get that file back instead of a copy.
    """

    def __init__(self, directory, quality=90):
        self._directory = Path(directory)
        self._quality = quality
        self._lock = threading.Lock()
        self._last_frame = None
        self._last_path = None

    def save(self, frame, label):
        """Write `frame` to `<directory>/<label>_<timestamp>.jpg` and return the path.

        `label` is only used the first time a given frame is saved. Frames are compared
        by identity, which is enough because they are replaced as a whole and never
        modified.
        """
        with self._lock:
            if frame is self._last_frame:
                return self._last_path
            self._directory.mkdir(parents=True, exist_ok=True)
            path = self._directory / f"{label}_{datetime.now():%Y%m%d_%H%M%S_%f}.jpg"
            Image.fromarray(frame[:, :, ::-1]).save(path, quality=self._quality)  # BGR -> RGB
            self._last_frame = frame
            self._last_path = path
            return path
