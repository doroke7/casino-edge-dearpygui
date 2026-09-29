from abc import ABC, abstractmethod

import grpc


class AbstractServicer(ABC):
    """Interface shared by the Poker/Disk/Die servicers.

    The per-object RPC (RecognizePoker / RecognizeDisk / RecognizeDie) is named after
    its service, so only the RPCs common to all of them are declared here.
    """

    def __init__(self, frames):
        self._frames = frames

    def _grab_frame(self, context):
        """The latest camera frame, or abort the RPC with UNAVAILABLE when there is none."""
        frame = self._frames.latest()
        if frame is None:
            context.abort(grpc.StatusCode.UNAVAILABLE, "camera is off")
        return frame

    @abstractmethod
    def RecognizeScene(self, request, context):
        ...

    @abstractmethod
    def RecognizeAll(self, request, context):
        ...
