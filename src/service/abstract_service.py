from abc import ABC, abstractmethod

import grpc


class AbstractServicer(ABC):
    """Interface shared by the Poker/Disk/Die servicers.

    The per-object RPC (RecognizePoker / RecognizeDisk / RecognizeDie) is named after
    its service, so only the RPCs common to all of them are declared here.
    """

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

    @abstractmethod
    def RecognizeScene(self, request, context):
        ...

    @abstractmethod
    def RecognizeAll(self, request, context):
        ...
