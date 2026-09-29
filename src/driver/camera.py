"""Native camera overlay.

Same idea as the egui version: instead of decoding frames and pushing them through
the UI toolkit, attach an AVCaptureVideoPreviewLayer to the app's own NSWindow so the
OS composites the capture on the GPU. Python never touches a pixel.

All methods must be called from the main thread (AppKit requirement).
"""

import sys
import threading

import numpy as np

IS_MACOS = sys.platform == "darwin"
CAMERA_FPS = 30

if IS_MACOS:
    import AppKit
    import AVFoundation
    import CoreMedia
    import objc
    import Quartz

    _funcs = {}
    objc.loadBundleFunctions(None, _funcs, [("dispatch_queue_create", b"@r*@")])

    class _FrameDelegate(AppKit.NSObject):
        """Receives every captured frame on a private serial queue and keeps the latest."""

        def initWithFrames_(self, frames):
            self = objc.super(_FrameDelegate, self).init()
            if self is not None:
                self.frames = frames
            return self

        def captureOutput_didOutputSampleBuffer_fromConnection_(self, output, sample, connection):
            pixels = CoreMedia.CMSampleBufferGetImageBuffer(sample)
            if pixels is None:
                return
            Quartz.CVPixelBufferLockBaseAddress(pixels, Quartz.kCVPixelBufferLock_ReadOnly)
            try:
                height = Quartz.CVPixelBufferGetHeight(pixels)
                width = Quartz.CVPixelBufferGetWidth(pixels)
                stride = Quartz.CVPixelBufferGetBytesPerRow(pixels)
                base = Quartz.CVPixelBufferGetBaseAddress(pixels)
                rows = np.frombuffer(base.as_buffer(height * stride), np.uint8).reshape(height, stride)
                # BGRA rows may be padded; drop the padding and alpha, and copy out of the
                # buffer because it is recycled as soon as this callback returns.
                frame = rows[:, : width * 4].reshape(height, width, 4)[:, :, :3].copy()
            finally:
                Quartz.CVPixelBufferUnlockBaseAddress(pixels, Quartz.kCVPixelBufferLock_ReadOnly)
            frames = self.frames
            if frames is not None:
                frames.put(frame)


class Overlay:
    def __init__(self, session, view, frames=None, delegate=None):
        self.session = session
        self.view = view
        self.frames = frames
        self.delegate = delegate  # the output holds its delegate weakly, so keep it alive

    def close(self):
        if self.delegate is not None:
            self.delegate.frames = None  # frames still in flight must not repopulate the buffer
        if self.frames is not None:
            self.frames.clear()
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


def build_overlay(window_title, frames=None):
    """Attach a live preview flush with the window's content area.

    If `frames` (a FrameBuffer) is given, every captured frame is also stored in it as a
    BGR numpy array, from the same capture session as the preview.

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

    delegate = None
    if frames is not None:
        output = AVFoundation.AVCaptureVideoDataOutput.alloc().init()
        output.setVideoSettings_({Quartz.kCVPixelBufferPixelFormatTypeKey: Quartz.kCVPixelFormatType_32BGRA})
        output.setAlwaysDiscardsLateVideoFrames_(True)
        delegate = _FrameDelegate.alloc().initWithFrames_(frames)
        output.setSampleBufferDelegate_queue_(delegate, _funcs["dispatch_queue_create"](b"camera.frames", None))
        if not session.canAddOutput_(output):
            raise RuntimeError("cannot capture frames from the camera")
        session.addOutput_(output)

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
    return Overlay(session, view, frames, delegate)
