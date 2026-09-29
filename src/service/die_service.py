from pb.ir.table.inference.equipment import die_pb2, die_pb2_grpc
from src.service.abstract_service import AbstractServicer


class DieServicer(AbstractServicer, die_pb2_grpc.DieServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizeDie(self, request, context):
        self._grab_frame(context, "die")
        return die_pb2.RecognizeDieResponse()
