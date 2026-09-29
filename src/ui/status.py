"""The status line shown in the main window."""

import dearpygui.dearpygui as dpg

from src.app.camera_controller import CameraState

TAG = "status"
WHITE = (255, 255, 255)
RED = (255, 80, 80)

_TEXT = {
    CameraState.OFF: "Camera is off. Open it from the Settings menu in the menu bar.",
    CameraState.REQUESTING: "Requesting camera permission...",
    CameraState.ON: "",
    CameraState.DENIED: "Camera error: Camera access permission was denied",
}
_ERRORS = (CameraState.DENIED, CameraState.ERROR)


def add():
    dpg.add_text("", tag=TAG)


def render_camera(state, detail=None):
    text = f"Camera error: {detail}" if state is CameraState.ERROR else _TEXT[state]
    dpg.set_value(TAG, text)
    dpg.configure_item(TAG, color=RED if state in _ERRORS else WHITE, show=bool(text))
