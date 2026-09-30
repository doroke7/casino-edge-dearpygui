"""Run the recognition gRPC server and the desktop app in one process."""

import logging
import sys
from concurrent import futures

import click
import grpc
from dependency_injector import providers

import bootstrap
from container.desktop import DesktopContainer
from container.recognition import RecognitionContainer
from src.app import desktop as desktop_app
from src.register import recognition as register_recognition

logger = logging.getLogger(__name__)


@click.command(name="all", help="Recognition gRPC server + desktop app")
@click.option("-p", "--port", "i_port", type=int, default=lambda: bootstrap.config("services.recognition.port"), show_default="config services.recognition.port")
@click.option("-w", "--max_workers", "i_max_workers", type=int, default=lambda: bootstrap.config("services.recognition.max_workers"), show_default="config services.recognition.max_workers")
@click.option("-v", "--verbose", "b_verbose", is_flag=True)
def main(i_port: int, i_max_workers: int, b_verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if b_verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        stream=sys.stderr,
    )

    # The desktop camera writes into this buffer and the gRPC servicers read from it.
    o_desktop_container = DesktopContainer()
    o_recognition_container = RecognitionContainer()
    o_recognition_container.frames.override(providers.Object(o_desktop_container.frames()))

    o_server = recognition(o_recognition_container, int(i_port), int(i_max_workers))
    try:
        # The desktop app owns the main thread (AppKit), so it runs here while the
        # gRPC server keeps serving from its own worker threads until it exits.
        desktop(o_desktop_container)
    finally:
        o_server.stop(grace=5).wait()
        logger.info("Server stopped.")


def recognition(o_container: RecognitionContainer, i_port: int, i_max_workers: int) -> grpc.Server:
    """Start the recognition gRPC server in the background and return it."""
    o_server = grpc.server(futures.ThreadPoolExecutor(max_workers=i_max_workers))
    register_recognition.register(o_server, o_container)
    o_server.add_insecure_port(f"[::]:{i_port}")
    o_server.start()
    logger.info("Recognition gRPC server listening on [::]:%d (workers=%d)", i_port, i_max_workers)
    return o_server


def desktop(o_container: DesktopContainer) -> None:
    """Run the desktop app on the calling (main) thread until its window closes."""
    desktop_app.run(o_container)
