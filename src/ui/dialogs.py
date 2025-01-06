from gi.repository import Gtk, Adw

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/get-started-dialog.ui")
class GetStartedDialog(Adw.Dialog):
    __gtype_name__ = "GetStartedDialog"
    def __init__(self):
        super().__init__()
    
    @Gtk.Template.Callback()
    def get_started_clicked(self, _):
        self.close()

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/upload-alert.ui")
class UploadAlert(Adw.AlertDialog):
    __gtype_name__ = "UploadAlert"
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def do_not_show_again(self, check: Gtk.CheckButton):
        self.settings.set_boolean("show-upload-alert", check.get_active() is True)