from pb.ir.table.inference import poker_pb2, poker_pb2_grpc
from src.service.abstract_service import AbstractServicer


class PokerServicer(AbstractServicer, poker_pb2_grpc.PokerServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizePoker(self, request, context):
        self._grab_frame(context, "poker_poker")
        return poker_pb2.PokerRecognizePokerResponse()

    def RecognizeScene(self, request, context):
        self._grab_frame(context, "poker_scene")
        return poker_pb2.PokerRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        self._grab_frame(context, "poker_all")
        return poker_pb2.PokerRecognizeAllResponse()
