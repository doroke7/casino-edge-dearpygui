import queue
from pathlib import Path

import click
import dearpygui.dearpygui as dpg

from bootstrap.config import config
from src.driver import camera
from src.ui import menu

TITLE = config("desktop.title", "Landan Desktop")
ICON = Path(__file__).resolve().parents[1] / "asset" / "icon.png"

# dearpygui callbacks run on a worker thread, but AppKit must be driven from the main
# thread, so callbacks only enqueue; the render loop below does the work.
actions: "queue.Queue[str]" = queue.Queue()

overlay = None


def set_status(text, color=(255, 255, 255)):
    dpg.set_value("status", text)
    dpg.configure_item("status", color=color, show=bool(text))


def open_camera():
    if overlay is not None:
        return
    set_status("Requesting camera permission...")
    camera.request_permission(lambda granted: actions.put("show" if granted else "denied"))


def show_overlay():
    global overlay
    try:
        overlay = camera.build_overlay(TITLE)
        set_status("")
    except Exception as err:
        set_status(f"Camera error: {err}", (255, 80, 80))


def close_camera():
    global overlay
    if overlay is not None:
        overlay.close()
        overlay = None
    set_status("Camera is off. Open it from the Settings menu in the menu bar.")


def pump_actions():
    while True:
        try:
            action = actions.get_nowait()
        except queue.Empty:
            return
        if action == "open":
            open_camera()
        elif action == "close":
            close_camera()
        elif action == "show":
            show_overlay()
        elif action == "denied":
            set_status("Camera error: Camera access permission was denied", (255, 80, 80))


@click.command(name="desktop")
def main():
    """Run the desktop app."""
    dpg.create_context()
    dpg.create_viewport(title=TITLE, width=640, height=480,
                        small_icon=str(ICON), large_icon=str(ICON))

    with dpg.window(tag="main", no_title_bar=True, no_move=True, no_resize=True,
                    no_scrollbar=True, no_background=True):
        dpg.add_text("", tag="status")

    dpg.set_primary_window("main", True)
    set_status("Camera is off. Open it from the Settings menu in the menu bar.")

    dpg.setup_dearpygui()
    dpg.show_viewport()
    # Native menu actions already arrive on the main thread; queue them anyway so
    # everything is handled in one place.
    menu.install(lambda: actions.put("open"), lambda: actions.put("close"))
    while dpg.is_dearpygui_running():
        menu.reapply()
        pump_actions()
        dpg.render_dearpygui_frame()

    if overlay is not None:
        overlay.close()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
