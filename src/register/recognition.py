from pb.ir.table.inference import die_pb2_grpc, disk_pb2_grpc, poker_pb2_grpc
from src.service.die import DieServicer
from src.service.disk import DiskServicer
from src.service.poker import PokerServicer


def register(o_server) -> None:
    """Register every recognition servicer on the given gRPC server."""
    poker_pb2_grpc.add_PokerServiceServicer_to_server(PokerServicer(), o_server)
    disk_pb2_grpc.add_DiskServiceServicer_to_server(DiskServicer(), o_server)
    die_pb2_grpc.add_DieServiceServicer_to_server(DieServicer(), o_server)
