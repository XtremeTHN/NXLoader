from gi.repository import Gtk, Adw, Gio, GLib
from ..modules.usbInstall import SwitchUsb
from ..modules.glist import List
from ..modules.task import task, CallbackTask, RepeatTask

from .dialogs import UploadAlert

import time
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
    rom_revealer: Gtk.Revealer = Gtk.Template.Child()

    def __init__(self, rom_file: Gio.File, delete_func):
        super().__init__()

        self.file = rom_file
        self.delete_func = delete_func

        info = self.file.query_info("standard::size,standard::name", Gio.FileQueryInfoFlags.NONE, None)
        filename = os.path.splitext(info.get_name())
        self.size = info.get_size()
        self.current_progress = 0

        self.rom_title.set_label(filename[0])
        self.rom_format.set_label("Format: " + filename[1])
        self.rom_size.set_label("Size: " + GLib.format_size(self.size))
    
    def reveal_progress(self):
        idle(self.rom_revealer.set_reveal_child, True)
    
    def get_total_size(self):
        return self.size

    def get_rom_path(self):
        return self.file.get_path()
    
    @Gtk.Template.Callback()
    def remove_rom(self, _):
        self.delete_func(self)

    def update_progress(self, progress):
        self.current_progress += progress
        idle(self.rom_progress.set_fraction, self.current_progress / self.size)
    
class TransferProtocolFunctions:
    def __init__(self, roms: list[RomItem], revealer: Gtk.Revealer, total_progress: Gtk.ProgressBar, prog_label: Gtk.Label):
        self.roms: dict[str, RomItem] = {}

        self.prog_label = prog_label
        self.total_progress = total_progress
        self.total_progress_current = 0
        self.total_progress_max = 0

        self.revealer = revealer

        self.pulse_task = RepeatTask(self.pulse_progress)

        for r in roms:
            self.roms[r.get_rom_path()] = r
            self.total_progress_max += r.get_total_size()
    
    def set_info(self, _, info):
        idle(self.prog_label.set_label, info)

        if info == "Waiting for command...":
            self.pulse_task.start()
        else:
            self.pulse_task.stop()

    def pulse_progress(self):
        idle(self.total_progress.pulse)
        time.sleep(0.4)

    def update_prog(self, _, file, read_size):
        item = self.roms[file]
        item.reveal_progress()
        item.update_progress(read_size)
        self.update_total_progress(read_size)
    
    def on_start(self, _):
        self.revealer.set_reveal_child(True)
    
    def on_exit(self, _):
        self.revealer.set_reveal_child(False)
    
    def update_total_progress(self, progress):
        self.total_progress_current += progress
        idle(self.total_progress.set_fraction, self.total_progress_current / self.total_progress_max)
    
    def connect_functions(self, protocol):
        protocol.connect("info", self.set_info)
        protocol.connect("send", self.update_prog)
        protocol.connect("start", self.on_start)
        protocol.connect("exit", self.on_exit)

@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/roms-page.ui")
class RomsPage(Adw.NavigationPage):
    __gtype_name__ = "RomsPage"

    roms_box: Gtk.Box = Gtk.Template.Child()
    no_roms_status_page: Gtk.Widget = Gtk.Template.Child()

    upload_btt: Gtk.Button = Gtk.Template.Child()
    clear_btt: Gtk.Button = Gtk.Template.Child()

    status_revealer: Gtk.Revealer = Gtk.Template.Child()
    total_progress: Gtk.ProgressBar = Gtk.Template.Child()
    info_label: Gtk.ProgressBar = Gtk.Template.Child()
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
        def alert_cb(dialog, result):
            if dialog is not None:
                choosed = dialog.choose_finish(result)
                if choosed in ["cancel", "close"]:
                    return
                
            self.__upload_roms()

        if self.window.settings.get_boolean("show-upload-alert") is True:
            dialog = UploadAlert(self.window.settings)
            dialog.choose(self.window, None, alert_cb)

    def __upload_roms(self):
        self.protocol.send_roms([x.get_rom_path() for x in self.roms])
        functions = TransferProtocolFunctions(self.roms, self.status_revealer, self.total_progress, self.info_label)
        functions.connect_functions(self.protocol)
        self.protocol.poll_commands()

    @Gtk.Template.Callback()
    def clear_rom_list(self, _):
        self.__clear_rom_list()
    
    @task
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
    
    def __check_if_rom_is_added(self, file):
        for r in self.roms:
            if r.get_rom_path() == file.get_path():
                self.window.add_toast("Rom already added")
                return
            elif os.path.splitext(r.get_rom_path())[1] not in [".nsp", ".xci"]:
                self.window.add_toast("Invalid rom")
                return
    
    def __add_rom_cb(self, dialog: Gtk.FileDialog, result):
        try:
            file = dialog.open_finish(result)
        except:
            return
        
        def add():
            nonlocal file
            item = RomItem(file, self.delete_rom_item)
            idle(self.append_rom_to_box, item)

        CallbackTask(self.__check_if_rom_is_added, add, fn_args=[file]).start()