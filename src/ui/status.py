"""The status line shown in the main window."""

import dearpygui.dearpygui as dpg

TAG = "status"
WHITE = (255, 255, 255)
RED = (255, 80, 80)


def add():
    dpg.add_text("", tag=TAG)


def show(text, color=WHITE):
    dpg.set_value(TAG, text)
    dpg.configure_item(TAG, color=color, show=bool(text))


def error(text):
    show(text, RED)
