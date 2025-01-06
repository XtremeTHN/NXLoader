from gi.repository import Gtk, Adw

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/dialog.ui")
class GetStartedDialog(Adw.Dialog):
    __gtype_name__ = "GetStartedDialog"
    def __init__(self):
        super().__init__()
    
    @Gtk.Template.Callback()
    def get_started_clicked(self, _):
        self.close()

# @Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/upload-confirmation.ui")