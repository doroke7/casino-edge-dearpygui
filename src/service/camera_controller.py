import queue

from src.driver import camera

CAMERA_OFF = "Camera is off. Open it from the Settings menu in the menu bar."


class CameraController:
    """Owns the camera overlay and its lifecycle; reports state through `on_status`.

    dearpygui callbacks run on a worker thread, but AppKit must be driven from the
    main thread, so `request()` only enqueues; `pump()` (called from the render loop)
    does the work.
    """

    def __init__(self, title, on_status, on_error):
        self._title = title
        self._on_status = on_status
        self._on_error = on_error
        self._overlay = None
        self._actions: "queue.Queue[str]" = queue.Queue()

    def request(self, action):
        self._actions.put(action)

    def pump(self):
        handlers = {
            "open": self._open,
            "close": self._close,
            "show": self._show,
            "denied": self._denied,
        }
        while True:
            try:
                action = self._actions.get_nowait()
            except queue.Empty:
                return
            handlers[action]()

    def shutdown(self):
        if self._overlay is not None:
            self._overlay.close()
            self._overlay = None

    def _open(self):
        if self._overlay is not None:
            return
        self._on_status("Requesting camera permission...")
        camera.request_permission(lambda granted: self.request("show" if granted else "denied"))

    def _show(self):
        try:
            self._overlay = camera.build_overlay(self._title)
            self._on_status("")
        except Exception as err:
            self._on_error(f"Camera error: {err}")

    def _close(self):
        self.shutdown()
        self._on_status(CAMERA_OFF)

    def _denied(self):
        self._on_error("Camera error: Camera access permission was denied")
