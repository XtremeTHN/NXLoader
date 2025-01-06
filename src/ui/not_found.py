from gi.repository import Gtk, Adw

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/not-found-page.ui")
class NotFoundPage(Adw.NavigationPage):
    __gtype_name__ = "NotFoundPage"
    def __init__(self):
        super().__init__()