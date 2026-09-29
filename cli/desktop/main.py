from pathlib import Path

import click
import dearpygui.dearpygui as dpg

from bootstrap.config import config
from src.service.camera_controller import CAMERA_OFF, CameraController
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
    status.show(CAMERA_OFF)

    o_camera_controller = CameraController(TITLE, status.show, status.error)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    # Native menu actions already arrive on the main thread; queue them anyway so
    # everything is handled in one place.
    menu.install(lambda: o_camera_controller.request("open"), lambda: o_camera_controller.request("close"))
    while dpg.is_dearpygui_running():
        menu.reapply()
        o_camera_controller.pump()
        dpg.render_dearpygui_frame()

    o_camera_controller.shutdown()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
