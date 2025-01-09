from gi.repository import Gtk, Adw

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/get-started-dialog.ui")
class GetStartedDialog(Adw.Dialog):
    __gtype_name__ = "GetStartedDialog"
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.connect("closed", self.on_close)
    
    def on_close(self, _):
        self.settings.set_boolean("first-run", False)
    
    @Gtk.Template.Callback()
    def get_started_clicked(self, _):
        self.close()

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/upload-alert.ui")
class UploadAlert(Adw.AlertDialog):
    __gtype_name__ = "UploadAlert"

    check_btt = Gtk.Template.Child()
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        self.check_btt.connect("toggled", self.do_not_show_again)

    def do_not_show_again(self, check: Gtk.CheckButton):
        self.settings.set_boolean("show-upload-alert", check.get_active() is False)