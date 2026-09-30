from pathlib import Path

import dearpygui.dearpygui as dpg

from container.desktop import TITLE, DesktopContainer
from src.app.camera_controller import CameraState
from src.ui import menu, status

ICON = Path(__file__).resolve().parents[2] / "asset" / "icon.png"


def run(o_container: DesktopContainer) -> None:
    """Run the desktop app on the calling (main) thread until its window closes."""
    dpg.create_context()
    dpg.create_viewport(title=TITLE, width=640, height=480,
                        small_icon=str(ICON), large_icon=str(ICON))

    with dpg.window(tag="main", no_title_bar=True, no_move=True, no_resize=True,
                    no_scrollbar=True, no_background=True):
        status.add()

    dpg.set_primary_window("main", True)
    status.render_camera(CameraState.OFF)

    main_thread = o_container.main_thread()
    o_camera_controller = o_container.camera_controller()

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
