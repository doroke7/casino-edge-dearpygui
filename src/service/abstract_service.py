from abc import ABC

import grpc


class AbstractServicer(ABC):
    """Shared plumbing for the recognition servicers: the frame buffer, snapshots and pipeline."""

    def __init__(self, frames, snapshots, pipeline):
        self._frames = frames
        self._snapshots = snapshots
        self._pipeline = pipeline

    def _grab_frame(self, context, label):
        """The latest camera frame, saved as a JPEG named after `label`.

        Aborts the RPC with UNAVAILABLE when there is no frame.
        """
        frame = self._frames.latest()
        if frame is None:
            context.abort(grpc.StatusCode.UNAVAILABLE, "camera is off")
        self._snapshots.save(frame, label)
        return frame
