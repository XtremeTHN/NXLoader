from gi.repository import Gtk, GLib

def add_toast(self: Gtk.Widget, message: str):
    r = self.get_root()
    s = GLib.markup_escape_text(message)
    r.add_toast(s)