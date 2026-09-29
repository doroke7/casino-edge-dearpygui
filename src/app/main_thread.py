import queue


class MainThread:
    """Runs callables posted from any thread on the thread that calls `pump()`.

    dearpygui and native callbacks may fire on a worker thread, but AppKit must be
    driven from the main thread, so they `post()` and the render loop `pump()`s.
    """

    def __init__(self):
        self._tasks: "queue.Queue" = queue.Queue()

    def post(self, fn):
        self._tasks.put(fn)

    def pump(self):
        while True:
            try:
                task = self._tasks.get_nowait()
            except queue.Empty:
                return
            task()
