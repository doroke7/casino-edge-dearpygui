"""Native camera overlay.

Same idea as the egui version: instead of decoding frames and pushing them through
the UI toolkit, attach an AVCaptureVideoPreviewLayer to the app's own NSWindow so the
OS composites the capture on the GPU. Python never touches a pixel.

All methods must be called from the main thread (AppKit requirement).
"""

import sys
import threading

IS_MACOS = sys.platform == "darwin"
CAMERA_FPS = 30

if IS_MACOS:
    import AppKit
    import AVFoundation
    import CoreMedia
    import Quartz


class Overlay:
    def __init__(self, session, view):
        self.session = session
        self.view = view

    def close(self):
        # stopRunning blocks until the device is released; keep it off the UI thread.
        threading.Thread(target=self.session.stopRunning, daemon=True).start()
        self.view.removeFromSuperview()


def request_permission(callback):
    """Ask for camera access. `callback(granted: bool)` may run on any thread."""
    if not IS_MACOS:
        callback(False)
        return
    status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(AVFoundation.AVMediaTypeVideo)
    if status == AVFoundation.AVAuthorizationStatusAuthorized:
        callback(True)
    elif status == AVFoundation.AVAuthorizationStatusNotDetermined:
        AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
            AVFoundation.AVMediaTypeVideo, lambda granted: callback(bool(granted))
        )
    else:
        callback(False)


def _find_window(title):
    windows = AppKit.NSApp.windows()
    for w in windows:
        if w.title() == title:
            return w
    return windows[0] if windows else None


def build_overlay(window_title):
    """Attach a live preview flush with the window's content area.

    Returns an Overlay, or raises RuntimeError.
    """
    if not IS_MACOS:
        raise RuntimeError("camera is not supported on this platform")

    window = _find_window(window_title)
    if window is None:
        raise RuntimeError("app window not found")

    device = AVFoundation.AVCaptureDevice.defaultDeviceWithMediaType_(AVFoundation.AVMediaTypeVideo)
    if device is None:
        raise RuntimeError("no camera found")

    cam_input, err = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)
    if cam_input is None:
        raise RuntimeError(f"cannot open camera: {err}")

    session = AVFoundation.AVCaptureSession.alloc().init()
    if session.canSetSessionPreset_(AVFoundation.AVCaptureSessionPreset1280x720):
        session.setSessionPreset_(AVFoundation.AVCaptureSessionPreset1280x720)
    session.addInput_(cam_input)

    # Pin the capture to 30fps so every build is benchmarked at the same rate.
    ok, _ = device.lockForConfiguration_(None)
    if ok:
        frame_duration = CoreMedia.CMTimeMake(1, CAMERA_FPS)
        device.setActiveVideoMinFrameDuration_(frame_duration)
        device.setActiveVideoMaxFrameDuration_(frame_duration)
        device.unlockForConfiguration()

    layer = AVFoundation.AVCaptureVideoPreviewLayer.layerWithSession_(session)
    layer.setVideoGravity_(AVFoundation.AVLayerVideoGravityResizeAspect)
    layer.setBackgroundColor_(Quartz.CGColorGetConstantColor(Quartz.kCGColorBlack))

    content = window.contentView()
    bounds = content.bounds()
    frame = ((0, 0), (bounds.size.width, bounds.size.height))
    view = AppKit.NSView.alloc().initWithFrame_(frame)
    view.setLayer_(layer)  # layer-hosting: set the layer first, then wantsLayer
    view.setWantsLayer_(True)
    # Ride AppKit's autoresizing so the preview tracks the window for free.
    view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
    content.addSubview_(view)

    threading.Thread(target=session.startRunning, daemon=True).start()
    return Overlay(session, view)
