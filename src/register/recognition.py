from container.recognition import RecognitionContainer
from pb.ir.table.inference.equipment import die_pb2_grpc, disk_pb2_grpc, poker_pb2_grpc
from pb.ir.table.inference.game import baccarat_pb2_grpc, sicbo_pb2_grpc


def register(o_server, o_container: RecognitionContainer) -> None:
    """Register every recognition servicer provided by the container on the gRPC server."""
    baccarat_pb2_grpc.add_BaccaratServiceServicer_to_server(o_container.baccarat_servicer(), o_server)
    sicbo_pb2_grpc.add_SicboServiceServicer_to_server(o_container.sicbo_servicer(), o_server)
    die_pb2_grpc.add_DieServiceServicer_to_server(o_container.die_servicer(), o_server)
    disk_pb2_grpc.add_DiskServiceServicer_to_server(o_container.disk_servicer(), o_server)
    poker_pb2_grpc.add_PokerServiceServicer_to_server(o_container.poker_servicer(), o_server)
