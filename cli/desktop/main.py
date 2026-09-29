from pathlib import Path

import click
import dearpygui.dearpygui as dpg

from bootstrap.config import config
from src.app.camera_controller import CameraController, CameraState
from src.app.main_thread import MainThread
from src.driver import camera
from src.ui import menu, status

TITLE = config("desktop.title", "Landan Desktop")
ICON = Path(__file__).resolve().parents[2] / "asset" / "icon.png"


@click.command(name="desktop")
def main():
    """Run the desktop app."""
    dpg.create_context()
    dpg.create_viewport(title=TITLE, width=640, height=480,
                        small_icon=str(ICON), large_icon=str(ICON))

    with dpg.window(tag="main", no_title_bar=True, no_move=True, no_resize=True,
                    no_scrollbar=True, no_background=True):
        status.add()

    dpg.set_primary_window("main", True)
    status.render_camera(CameraState.OFF)

    main_thread = MainThread()
    o_camera_controller = CameraController(TITLE, camera, main_thread.post, status.render_camera)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    # Native menu actions already arrive on the main thread; queue them anyway so
    # everything is handled in one place.
    menu.install([
        ("Open Camera", o_camera_controller.open),
        ("Close Camera", o_camera_controller.close),
    ])
    while dpg.is_dearpygui_running():
        menu.reapply()
        main_thread.pump()
        dpg.render_dearpygui_frame()

    o_camera_controller.shutdown()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
