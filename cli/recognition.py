"""Recognition gRPC server."""

import logging
import signal
import sys
import threading
from concurrent import futures

import click
import grpc

import bootstrap
from pb.ir.table.inference import (
    die_pb2, die_pb2_grpc,
    disk_pb2, disk_pb2_grpc,
    poker_pb2, poker_pb2_grpc,
)

logger = logging.getLogger(__name__)


class PokerServicer(poker_pb2_grpc.PokerServiceServicer):
    """Placeholder: every RPC returns an empty result until recognition is wired in."""

    def RecognizePoker(self, request, context):
        return poker_pb2.PokerRecognizePokerResponse()

    def RecognizeScene(self, request, context):
        return poker_pb2.PokerRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        return poker_pb2.PokerRecognizeAllResponse()


class DiskServicer(disk_pb2_grpc.DiskServiceServicer):
    """Placeholder: every RPC returns an empty result until recognition is wired in."""

    def RecognizeDisk(self, request, context):
        return disk_pb2.DiskRecognizeDiskResponse()

    def RecognizeScene(self, request, context):
        return disk_pb2.DiskRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        return disk_pb2.DiskRecognizeAllResponse()


class DieServicer(die_pb2_grpc.DieServiceServicer):
    """Placeholder: every RPC returns an empty result until recognition is wired in."""

    def RecognizeDie(self, request, context):
        return die_pb2.DieRecognizeDieResponse()

    def RecognizeScene(self, request, context):
        return die_pb2.DieRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        return die_pb2.DieRecognizeAllResponse()


@click.command(name="recognition", help="Recognition gRPC server")
@click.option("-p", "--port", type=int, default=lambda: bootstrap.config("recognition.port"), show_default="config recognition.port")
@click.option("-w", "--max_workers", type=int, default=lambda: bootstrap.config("recognition.max_workers"), show_default="config recognition.max_workers")
@click.option("-v", "--verbose", is_flag=True)
def main(port: int, max_workers: int, verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        stream=sys.stderr,
    )
    serve(port=int(port), max_workers=int(max_workers))


def serve(port: int, max_workers: int) -> None:
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    poker_pb2_grpc.add_PokerServiceServicer_to_server(PokerServicer(), server)
    disk_pb2_grpc.add_DiskServiceServicer_to_server(DiskServicer(), server)
    die_pb2_grpc.add_DieServiceServicer_to_server(DieServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("Recognition gRPC server listening on [::]:%d (workers=%d)", port, max_workers)

    stop_event = threading.Event()

    def _shutdown(signum, _frame):
        logger.info("Received %s, shutting down...", signal.Signals(signum).name)
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    stop_event.wait()
    server.stop(grace=5).wait()
    logger.info("Server stopped.")
