from gi.repository import Gtk, Adw
from ..modules.switchfinder import SwitchFinder

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/rom.ui")
class RomItem(Gtk.Box):
    __gtype_name__ = "Rom"

    rom_title: Gtk.Label = Gtk.Template.Child()
    rom_format: Gtk.Label = Gtk.Template.Child()
    rom_size: Gtk.Label = Gtk.Template.Child()
    rom_progress: Gtk.ProgressBar = Gtk.Template.Child()

    def __init__(self, rom_path, delete_func):
        super().__init__(self)

        self.rom_path = rom_path
        self.delete_func = delete_func
    
    @Gtk.Template.Callback()
    def remove_rom(self, _):
        self.delete_func(self)

    def set_progress(self, prog):
        ...

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/roms_page.ui")
class RomsPage(Adw.NavigationPage):
    __gtype_name__ = "RomsPage"

    roms_box: Gtk.Box = Gtk.Template.Child()
    no_roms_status_page: Gtk.Widget = Gtk.Template.Child()
    def __init__(self, protocol: SwitchFinder):
        self.protocol = protocol
        super().__init__()

    @Gtk.Template.Callback()
    def upload_roms(self, _):
        ...

    @Gtk.Template.Callback()
    def clear_rom_list(self, _):
        ...