from gi.repository import Gtk, Adw, Gio, GLib
from ..modules.usbInstall import SwitchUsb
from ..modules.glist import List
from ..modules.task import Task, CTask

import os

def idle(func, *args):
    GLib.idle_add(func, *args)

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/rom.ui")
class RomItem(Adw.Bin):
    __gtype_name__ = "Rom"

    rom_title: Gtk.Label = Gtk.Template.Child()
    rom_format: Gtk.Label = Gtk.Template.Child()
    rom_size: Gtk.Label = Gtk.Template.Child()
    rom_progress: Gtk.ProgressBar = Gtk.Template.Child()

    def __init__(self, rom_file: Gio.File, delete_func):
        super().__init__()

        self.file = rom_file
        self.delete_func = delete_func

        info = self.file.query_info("standard::size,standard::name", Gio.FileQueryInfoFlags.NONE, None)
        filename = os.path.splitext(info.get_name())
        self.rom_title.set_label(filename[0])
        self.rom_format.set_label("Format: " + filename[1])
        self.rom_size.set_label("Size: " + GLib.format_size(info.get_size()))
    
    def get_rom_path(self):
        return self.file.get_path()
    
    @Gtk.Template.Callback()
    def remove_rom(self, _):
        self.delete_func(self)

    def set_progress(self, prog):
        ...

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/roms-page.ui")
class RomsPage(Adw.NavigationPage):
    __gtype_name__ = "RomsPage"

    roms_box: Gtk.Box = Gtk.Template.Child()
    no_roms_status_page: Gtk.Widget = Gtk.Template.Child()

    upload_btt: Gtk.Button = Gtk.Template.Child()
    clear_btt: Gtk.Button = Gtk.Template.Child()
    def __init__(self, protocol: SwitchUsb, window):
        super().__init__()

        self.protocol = protocol
        self.window = window
        self.roms = List()

        self.roms.connect("appended", self.change_widget_states)
        self.roms.connect("removed", self.change_widget_states)

        self.change_widget_states(None)

    def change_widget_states(self, _):
        if_roms = len(self.roms) > 0
        self.no_roms_status_page.set_visible(if_roms is False)
        
        self.upload_btt.set_sensitive(if_roms)
        self.clear_btt.set_sensitive(if_roms)

    @Gtk.Template.Callback()
    def upload_roms(self, _):
        ...

    @Gtk.Template.Callback()
    def clear_rom_list(self, _):
        self.__clear_rom_list()
    
    @Task
    def __clear_rom_list(self):
        for r in self.roms:
            idle(self.delete_rom_item, r)
    
    def delete_rom_item(self, item):
        self.roms_box.remove(item)
        self.roms.remove(item)

    def append_rom_to_box(self, item):
        self.roms_box.append(item)
        self.roms.append(item)

        if len(self.roms) > 0:
            self.no_roms_status_page.set_visible(False)
    
    @Gtk.Template.Callback()
    def add_rom(self, _):
        dialog = Gtk.FileDialog.new()
        dialog.set_accept_label("Open")

        filter = Gtk.FileFilter.new()
        filter.add_suffix("xci")
        filter.add_suffix("nsp")

        dialog.set_default_filter(filter)

        dialog.open(self.window, callback=self.__add_rom_cb)
    
    def __check_if_rom_is_added(self, file, cb):
        for r in self.roms:
            if r.get_rom_path() == file.get_path():
                self.window.add_toast("Rom already added")
                return
        cb()
    
    def __add_rom_cb(self, dialog: Gtk.FileDialog, result):
        try:
            file = dialog.open_finish(result)
        except:
            return
        
        def add():
            nonlocal file
            item = RomItem(file, self.delete_rom_item)
            idle(self.append_rom_to_box, item)
        
        CTask(self.__check_if_rom_is_added, fn_args=[file, add]).start()