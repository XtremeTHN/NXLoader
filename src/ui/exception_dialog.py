from gi.repository import Gtk, Adw, GObject
import traceback


@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/exception-dialog.ui")
class ExceptionDialog(Adw.AlertDialog):
    __gtype_name__ = "ExceptionDialog"

    traceback_view: Gtk.TextView = Gtk.Template.Child()

    thread_id = GObject.Property(type=int, nick="thread-id")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if (t := kwargs.get("thread_id")) is not None and t > 0:
            self.thread_id = t

    def set_exception_info(self, exc_type, exc_value, exc_tb):
        self.set_heading(exc_type.__name__)

        buff = self.traceback_view.get_buffer()
        if self.thread_id > 0:
            buff.set_text(f"Thread {self.thread_id}\n")

        buff.insert_at_cursor(
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        )
