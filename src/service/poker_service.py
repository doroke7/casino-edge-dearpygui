from pb.ir.table.inference import poker_pb2, poker_pb2_grpc
from src.service.abstract_service import AbstractServicer


class PokerServicer(AbstractServicer, poker_pb2_grpc.PokerServiceServicer):
    """Placeholder: every RPC returns an empty result until recognition is wired in."""

    def RecognizePoker(self, request, context):
        return poker_pb2.PokerRecognizePokerResponse()

    def RecognizeScene(self, request, context):
        return poker_pb2.PokerRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        return poker_pb2.PokerRecognizeAllResponse()
