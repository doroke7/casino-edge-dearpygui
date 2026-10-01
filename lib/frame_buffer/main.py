class FrameBuffer:
    """Holds only the latest frame; safe to share between a capture thread and readers.

    No lock: the whole state is one reference, and storing or loading a single
    attribute is atomic in CPython (GIL, and per-object locking on free-threaded
    builds). That only holds because a frame is replaced as a whole and never mutated:
    it is a BGR numpy array (height, width, 3) that must not be modified.
    """

    def __init__(self):
        self._frame = None

    def put(self, frame):
        """Store `frame` and make it read-only, since every reader shares the same array."""
        frame.flags.writeable = False
        self._frame = frame

    def latest(self):
        """The most recent frame, or None when no camera is feeding the buffer."""
        return self._frame

    def clear(self):
        self._frame = None
