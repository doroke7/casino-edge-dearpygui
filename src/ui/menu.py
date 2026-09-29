"""Native macOS menu bar (top of the screen) with a "Settings" menu.

GLFW installs its own default menu while the window is being set up, which can
clobber a menu installed only once, so `reapply()` is meant to be called for the
first few seconds of the render loop (same race the egui version works around).
"""

import sys
import time

IS_MACOS = sys.platform == "darwin"
REAPPLY_SECONDS = 3.0

if IS_MACOS:
    import AppKit
    import objc

    class _Target(AppKit.NSObject):
        def initWithHandlers_(self, handlers):
            self = objc.super(_Target, self).init()
            if self is not None:
                self.handlers = handlers
            return self

        def openCamera_(self, sender):
            self.handlers["open"]()

        def closeCamera_(self, sender):
            self.handlers["close"]()


_menu = None
_target = None  # NSMenuItem holds its target weakly, so keep a reference
_started = 0.0


def install(on_open, on_close):
    """Build and install the menu. Call from the main thread, after the window exists."""
    global _menu, _target, _started
    if not IS_MACOS:
        return
    _target = _Target.alloc().initWithHandlers_({"open": on_open, "close": on_close})

    menu = AppKit.NSMenu.alloc().init()

    app_item = AppKit.NSMenuItem.alloc().init()
    app_menu = AppKit.NSMenu.alloc().init()
    quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Quit", "terminate:", "q"
    )
    app_menu.addItem_(quit_item)
    app_item.setSubmenu_(app_menu)
    menu.addItem_(app_item)

    settings_item = AppKit.NSMenuItem.alloc().init()
    settings_menu = AppKit.NSMenu.alloc().initWithTitle_("Settings")
    for title, action in (("Open Camera", "openCamera:"), ("Close Camera", "closeCamera:")):
        item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
        item.setTarget_(_target)
        settings_menu.addItem_(item)
    settings_item.setSubmenu_(settings_menu)
    menu.addItem_(settings_item)

    _menu = menu
    _started = time.monotonic()
    AppKit.NSApp.setMainMenu_(menu)


def reapply():
    if _menu is not None and time.monotonic() - _started < REAPPLY_SECONDS:
        AppKit.NSApp.setMainMenu_(_menu)
