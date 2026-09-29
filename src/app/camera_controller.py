import enum
import queue

from src.driver import camera


class CameraState(enum.Enum):
    OFF = "off"
    REQUESTING = "requesting"
    ON = "on"
    DENIED = "denied"
    ERROR = "error"


class CameraController:
    """Owns the camera overlay and its lifecycle; reports it through `on_state(state, detail)`.

    dearpygui callbacks run on a worker thread, but AppKit must be driven from the
    main thread, so `open()`/`close()` only enqueue; `pump()` (called from the render
    loop) does the work.
    """

    def __init__(self, title, on_state):
        self._title = title
        self._on_state = on_state
        self._overlay = None
        self._events: "queue.Queue" = queue.Queue()

    def open(self):
        self._events.put(self._open)

    def close(self):
        self._events.put(self._close)

    def pump(self):
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                return
            event()

    def shutdown(self):
        if self._overlay is not None:
            self._overlay.close()
            self._overlay = None

    def _open(self):
        if self._overlay is not None:
            return
        self._on_state(CameraState.REQUESTING)
        camera.request_permission(
            lambda granted: self._events.put(self._show if granted else self._denied))

    def _show(self):
        try:
            self._overlay = camera.build_overlay(self._title)
            self._on_state(CameraState.ON)
        except Exception as err:
            self._on_state(CameraState.ERROR, err)

    def _close(self):
        self.shutdown()
        self._on_state(CameraState.OFF)

    def _denied(self):
        self._on_state(CameraState.DENIED)
