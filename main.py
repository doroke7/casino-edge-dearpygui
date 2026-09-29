import threading
from pathlib import Path

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

TITLE = "Landan Desktop"
ICON = Path(__file__).parent / "asset" / "icon.png"
CAMERA_INDEX = 0


class Camera:
    """Grabs frames on a worker thread; the UI thread only reads the latest one."""

    def __init__(self):
        self.cap = None
        self.thread = None
        self.running = False
        self.lock = threading.Lock()
        self.frame = None  # latest RGBA float32 frame, or None
        self.error = None

    def open(self):
        if self.running:
            return
        self.error = None
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            self.error = "Cannot open camera (check permission / device)"
            return
        self.cap = cap
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def close(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        self.cap = self.thread = None
        with self.lock:
            self.frame = None

    def _loop(self):
        while self.running:
            ok, bgr = self.cap.read()
            if not ok:
                self.error = "Camera stopped delivering frames"
                self.running = False
                break
            rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA).astype(np.float32) / 255.0
            with self.lock:
                self.frame = rgba

    def take_frame(self):
        with self.lock:
            frame, self.frame = self.frame, None
        return frame


camera = Camera()
texture_size = (640, 480)  # (w, h) of the current texture


def ensure_texture(w, h):
    global texture_size
    if texture_size == (w, h):
        return
    if dpg.does_item_exist("cam_tex"):
        dpg.delete_item("cam_tex")
    blank = np.zeros((h, w, 4), dtype=np.float32)
    dpg.add_raw_texture(w, h, blank, format=dpg.mvFormat_Float_rgba,
                        tag="cam_tex", parent="tex_registry")
    if dpg.does_item_exist("cam_image"):
        dpg.configure_item("cam_image", texture_tag="cam_tex")
    texture_size = (w, h)


def open_camera():
    camera.open()
    refresh_status()


def close_camera():
    camera.close()
    dpg.configure_item("cam_image", show=False)
    refresh_status()


def refresh_status():
    if camera.error:
        dpg.set_value("status", f"Camera error: {camera.error}")
        dpg.configure_item("status", color=(255, 80, 80), show=True)
    elif camera.running:
        dpg.configure_item("status", show=False)
    else:
        dpg.set_value("status", "Camera is off. Open it from the Settings menu.")
        dpg.configure_item("status", color=(255, 255, 255), show=True)


def update_frame():
    frame = camera.take_frame()
    if frame is not None:
        h, w = frame.shape[:2]
        ensure_texture(w, h)
        dpg.set_value("cam_tex", frame)
        dpg.configure_item("cam_image", show=True)

    if camera.error and not camera.running:
        refresh_status()

    # Fit the image into the window, keeping aspect ratio and centered.
    if texture_size and dpg.is_item_shown("cam_image"):
        tw, th = texture_size
        vw, vh = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
        vh -= 20  # menu bar
        scale = max(min(vw / tw, vh / th), 0.01)
        w, h = int(tw * scale), int(th * scale)
        dpg.configure_item("cam_image", width=w, height=h,
                           pos=((vw - w) // 2, (vh - h) // 2))


def main():
    dpg.create_context()
    dpg.create_viewport(title=TITLE, width=640, height=480,
                        small_icon=str(ICON), large_icon=str(ICON))

    with dpg.texture_registry(tag="tex_registry"):
        dpg.add_raw_texture(640, 480, np.zeros((480, 640, 4), dtype=np.float32),
                            format=dpg.mvFormat_Float_rgba, tag="cam_tex")

    with dpg.viewport_menu_bar():
        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Open Camera", callback=open_camera)
            dpg.add_menu_item(label="Close Camera", callback=close_camera)

    with dpg.window(tag="main", no_title_bar=True, no_move=True, no_resize=True,
                    no_scrollbar=True, no_background=True):
        dpg.add_text("", tag="status")
        dpg.add_image("cam_tex", tag="cam_image", show=False)

    dpg.set_primary_window("main", True)
    refresh_status()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    while dpg.is_dearpygui_running():
        update_frame()
        dpg.render_dearpygui_frame()

    camera.close()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
