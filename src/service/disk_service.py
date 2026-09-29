from pb.ir.table.inference.equipment import disk_pb2, disk_pb2_grpc
from src.service.abstract_service import AbstractServicer


class DiskServicer(AbstractServicer, disk_pb2_grpc.DiskServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizeDisk(self, request, context):
        self._grab_frame(context, "disk")
        return disk_pb2.RecognizeDiskResponse()
