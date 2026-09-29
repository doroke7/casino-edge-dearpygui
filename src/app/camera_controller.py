import enum


class CameraState(enum.Enum):
    OFF = "off"
    REQUESTING = "requesting"
    ON = "on"
    DENIED = "denied"
    ERROR = "error"


class CameraController:
    """Owns the camera overlay and its lifecycle; reports it through `on_state(state, detail)`.

    `driver` provides `request_permission(callback)` and `build_overlay(title)` (see
    src.driver.camera). `post` runs a callable on the main thread, where the driver
    must be used; `open()`/`close()` are safe to call from any thread.
    """

    def __init__(self, title, driver, post, on_state):
        self._title = title
        self._driver = driver
        self._post = post
        self._on_state = on_state
        self._overlay = None

    def open(self):
        self._post(self._open)

    def close(self):
        self._post(self._close)

    def shutdown(self):
        if self._overlay is not None:
            self._overlay.close()
            self._overlay = None

    def _open(self):
        if self._overlay is not None:
            return
        self._on_state(CameraState.REQUESTING)
        self._driver.request_permission(
            lambda granted: self._post(self._show if granted else self._denied))

    def _show(self):
        try:
            self._overlay = self._driver.build_overlay(self._title)
            self._on_state(CameraState.ON)
        except Exception as err:
            self._on_state(CameraState.ERROR, err)

    def _close(self):
        self.shutdown()
        self._on_state(CameraState.OFF)

    def _denied(self):
        self._on_state(CameraState.DENIED)
