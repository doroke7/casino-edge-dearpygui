"""Recognition gRPC server."""

import logging
import signal
import sys
import threading
from concurrent import futures

import click
import grpc

import bootstrap
from container.recognition import RecognitionContainer
from src.register import recognition as register_recognition

logger = logging.getLogger(__name__)


@click.command(name="recognition", help="Recognition gRPC server")
@click.option("-p", "--port", "i_port", type=int, default=lambda: bootstrap.config("services.recognition.port"), show_default="config services.recognition.port")
@click.option("-w", "--max_workers", "i_max_workers", type=int, default=lambda: bootstrap.config("services.recognition.max_workers"), show_default="config services.recognition.max_workers")
@click.option("-v", "--verbose", "b_verbose", is_flag=True)
def main(i_port: int, i_max_workers: int, b_verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if b_verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        stream=sys.stderr,
    )
    serve(i_port=int(i_port), i_max_workers=int(i_max_workers))


def serve(i_port: int, i_max_workers: int) -> None:

    o_server = grpc.server(futures.ThreadPoolExecutor(max_workers=i_max_workers))

    o_container = RecognitionContainer()
    register_recognition.register(o_server, o_container)
    o_server.add_insecure_port(f"[::]:{i_port}")
    o_server.start()
    
    logger.info("Recognition gRPC server listening on [::]:%d (workers=%d)", i_port, i_max_workers)

    o_stop_event = threading.Event()

    def _shutdown(i_signum, _frame):
        logger.info("Received %s, shutting down...", signal.Signals(i_signum).name)
        o_stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    o_stop_event.wait()
    o_server.stop(grace=5).wait()
    logger.info("Server stopped.")
