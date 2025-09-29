# main.py
#
# Copyright 2024 Unknown
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import threading
import traceback
import sys
import gi

gi.require_version("GUdev", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, Adw, Gdk, GLib
from .ui.window import NxloaderWindow
from .ui.exception_dialog import ExceptionDialog
from .modules.task import Task


class NxloaderApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="com.github.XtremeTHN.NXLoader",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)

        self.window = None
        self.thread_hook = threading.excepthook

    def on_thread_exc(self, exc_info: threading.ExceptHookArgs):
        GLib.idle_add(
            self.on_exception,
            exc_info.exc_type,
            exc_info.exc_value,
            exc_info.exc_traceback,
            exc_info.thread.name,
        )

    def on_exception(self, exc_type, exc_value, exc_tb, threadId=None):
        if threadId:
            print("Thread name: ", threadId)

        sys.__excepthook__(exc_type, exc_value, exc_tb)
        dialog = ExceptionDialog()
        dialog.set_exception_info(exc_type, exc_value, exc_tb)

        dialog.connect(
            "response", lambda *_: self.quit() if self.window is None else None
        )

        dialog.present(self.window)

        if self.window is None:
            self.hold()

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        sys.excepthook = self.on_exception
        threading.excepthook = self.on_thread_exc
        self.window = NxloaderWindow(self)
        self.window.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="nxloader",
            application_icon="com.github.XtremeTHN.NXLoader",
            developer_name="Unknown",
            version="0.1.0",
            developers=["Unknown"],
            copyright="© 2024 Unknown",
        )
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        # about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print("app.preferences action activated")

    def cleanup(self):
        if self.window:
            self.window.finder.protocol.close()
        Task.stop_unfinished_tasks()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = NxloaderApplication()
    exit_code = app.run(sys.argv)
    app.cleanup()

    return exit_code
