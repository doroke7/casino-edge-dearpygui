from dependency_injector import containers, providers

from bootstrap.config import config
from lib.frame_buffer.main import FrameBuffer
from src.app.camera_controller import CameraController
from src.app.main_thread import MainThread
from src.driver import camera
from src.ui import status

TITLE = config("desktop.title", "Landan Desktop")


class DesktopContainer(containers.DeclarativeContainer):
    # The camera writes into it; `all` overrides it to share one with the gRPC servicers.
    frames = providers.Singleton(FrameBuffer)

    main_thread = providers.Singleton(MainThread)

    # A module and a function: wrapped as objects because the container deep-copies its providers.
    camera_driver = providers.Object(camera)
    on_camera_state = providers.Object(status.render_camera)

    camera_controller = providers.Singleton(
        CameraController,
        TITLE,
        camera_driver,
        main_thread.provided.post,
        on_camera_state,
        frames,
    )
