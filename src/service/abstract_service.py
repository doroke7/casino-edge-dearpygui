from abc import ABC, abstractmethod


class AbstractServicer(ABC):
    """Interface shared by the Poker/Disk/Die servicers.

    The per-object RPC (RecognizePoker / RecognizeDisk / RecognizeDie) is named after
    its service, so only the RPCs common to all of them are declared here.
    """

    @abstractmethod
    def RecognizeScene(self, request, context):
        ...

    @abstractmethod
    def RecognizeAll(self, request, context):
        ...
