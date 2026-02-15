from gi.repository import Gtk, Adw, Gio, GLib, Gdk
from .circularprogress import CircularProgressPaintable, Color


from ..modules.usbInstall import SwitchUsb
from ..modules.utils import add_toast

from .dialogs import UploadAlert
from ..modules.rom_info import RomInfo
from nxroms.keys import KeysNotFound

import os


def idle(func, *args):
    GLib.idle_add(func, *args)


class Pulse:
    def __init__(self, progress):
        self.running = GLib.SOURCE_REMOVE
        self.progress = progress

    def start(self):
        if self.running == GLib.SOURCE_CONTINUE:
            return

        self.running = GLib.SOURCE_CONTINUE
        GLib.timeout_add(400, self.pulse)

    def stop(self):
        self.running = GLib.SOURCE_REMOVE

    def pulse(self):
        self.progress.pulse()
        return self.running


@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/rom.ui")
class RomItem(Gtk.ListBoxRow):
    __gtype_name__ = "Rom"

    frame: Gtk.Frame = Gtk.Template.Child()
    icon: Gtk.Picture = Gtk.Template.Child()
    rom_title: Gtk.Label = Gtk.Template.Child()
    rom_version: Gtk.Label = Gtk.Template.Child()
    rom_size: Gtk.Label = Gtk.Template.Child()

    end_button_image: Gtk.Image = Gtk.Template.Child()

    def __init__(self, rom_file: Gio.File, delete_func):
        super().__init__()

        self.file = rom_file
        self.delete_func = delete_func

        self.rom_progress = CircularProgressPaintable(self.end_button_image, "emblem-ok-symbolic")

        self.info = self.file.query_info(
            "standard::size,standard::name", Gio.FileQueryInfoFlags.NONE, None
        )
        self.size = self.info.get_size()
        self.current_progress = 0
    
    def set_normal_data(self):
        filename = os.path.splitext(self.info.get_name())

        i = Gtk.Image.new_from_icon_name("image-missing-symbolic")
        i.set_pixel_size(60)
        self.frame.set_child(i)
        self.rom_title.set_label(filename[0])
        self.rom_version.set_label("Format: " + filename[1])
        self.rom_size.set_label("Size: " + GLib.format_size(self.size))
    
    def set_rom_data(self):
        r = RomInfo(self.file)

        self.rom_title.set_label(r.name)
        self.rom_version.set_label(f"Version: {r.version}")
        self.rom_size.set_label("Size: " + GLib.format_size(self.size))
        self.icon.set_paintable(r.icon)

    def reveal_progress(self, reveal):
        if reveal:
            idle(self.end_button_image.set_from_paintable, self.rom_progress)
        else:
            idle(self.end_button_image.set_from_icon_name, "user-trash-symbolic")

    def get_total_size(self):
        return self.size

    def reset(self):
        idle(self.rom_progress.set_fraction, 0)
        self.reveal_progress(False)
        self.current_progress = 0

    def get_rom_path(self):
        return self.file.get_path()

    @Gtk.Template.Callback()
    def remove_rom(self, _):
        self.delete_func(self)

    def update_progress(self, progress):
        self.current_progress += progress

        if self.current_progress >= self.size:
            self.rom_progress.set_color(Color.SUCCESS)

        idle(self.rom_progress.set_fraction, self.current_progress / self.size)


@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/roms-box.ui")
class RomsBox(Gtk.ListBox):
    __gtype_name__ = "RomsBox"

    def __init__(self):
        super().__init__()

        self.notified_about_keys = False

        self.model = Gio.ListStore.new(Gio.File)
        self.bind_model(self.model, self.build_rom)

    def append(self, file: Gio.File):
        self.model.append(file)

    def remove(self, file: Gio.File):
        if (n := self.model.find(file))[0]:
            self.model.remove(n[1])

    def build_rom(self, rom: Gio.File):
        r = RomItem(rom, self.delete_rom_item)

        try:
            r.set_rom_data()
        except KeysNotFound:
            if self.notified_about_keys is False:
                add_toast(self, "Rom information is only available if a prod.keys file is in ~/.switch")
                self.notified_about_keys = True
            r.set_normal_data()
        except Exception as e:
            print(e)
            add_toast(self, f"Couldn't get rom info: {' '.join([str(x) for x in e.args])}")
            r.set_normal_data()

        return r

    def delete_rom_item(self, item: RomItem):
        self.remove(item.file)

    def check_if_rom_is_added(self, file: Gio.File):
        rom_basename = file.get_basename()

        if os.path.splitext(rom_basename)[1] not in [".nsp", ".xci"]:
            self.get_root().add_toast(f"{rom_basename} is an invalid rom")
            return True

        for r in self.model:
            if r.get_path() == file.get_path():
                self.get_root().add_toast(f"{rom_basename} is already here")
                return True
        return False


@Gtk.Template(resource_path="/com/github/XtremeTHN/NXLoader/roms-page.ui")
class RomsPage(Adw.NavigationPage):
    __gtype_name__ = "RomsPage"

    stack: Gtk.Stack = Gtk.Template.Child()
    no_roms_status_page: Adw.StatusPage = Gtk.Template.Child()
    roms_box: RomsBox = Gtk.Template.Child()

    upload_btt: Gtk.Button = Gtk.Template.Child()
    clear_btt: Gtk.Button = Gtk.Template.Child()

    status_revealer: Gtk.Revealer = Gtk.Template.Child()
    total_progress: Gtk.ProgressBar = Gtk.Template.Child()
    info_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self, protocol: SwitchUsb, window):
        super().__init__()

        self.protocol = protocol
        self.window = window

        self.current_rom: RomItem | None = None
        self.total_roms_size = 0
        self.current_bytes = 0

        self.roms_box.model.connect("items-changed", self.change_widget_states)

        self.pulse = Pulse(self.total_progress)

        target = Gtk.DropTarget(
            formats=Gdk.ContentFormats.new_for_gtype(Gdk.FileList),
            actions=Gdk.DragAction.COPY,
        )

        target.connect("enter", self.__on_enter)
        target.connect("motion", self.__on_motion)
        target.connect("drop", self.__on_drop)

        self.stack.add_controller(target)
        self.change_widget_states(None)

    def change_widget_states(self, *_):
        if_roms = len(self.roms_box.model) > 0

        self.stack.set_visible_child_name("roms" if if_roms else "placeholder")
        self.upload_btt.set_sensitive(if_roms)
        self.clear_btt.set_sensitive(if_roms)

    def __on_enter(self, _, x, y):
        return Gdk.DragAction.COPY

    def __on_motion(self, _, x, y):
        return Gdk.DragAction.COPY

    def __on_drop(self, _, values: Gdk.FileList, x, y):
        for file in values.get_files():
            if self.roms_box.check_if_rom_is_added(file) is False:
                self.roms_box.append(file)
        return True

    def __add_rom_cb(self, dialog: Gtk.FileDialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return

        if self.roms_box.check_if_rom_is_added(file) is False:
            self.roms_box.append(file)

    def __upload_roms(self):
        roms = []

        for index, rom in enumerate(self.roms_box.model):
            roms.append(rom.get_path())
            self.total_roms_size += self.roms_box.get_row_at_index(index).size

        self.protocol.send_roms(roms)

        self.protocol.connect("info", self.on_info)
        self.protocol.connect("send", self.on_update)
        self.protocol.connect("file", self.on_file)
        self.protocol.connect("start", self.change_upload_state)
        self.protocol.connect("exit", lambda _: idle(self.reset_state))
        self.protocol.connect("error", lambda _: idle(self.reset_state))

        self.pulse.start()

        self.protocol.poll_commands()
        self.upload_btt.set_sensitive(False)

    def reset_state(self):
        for index, _ in enumerate(self.roms_box.model):
            self.roms_box.get_row_at_index(index).reset()

        self.info_label.set_label("")
        self.total_progress.set_fraction(0)
        self.status_revealer.set_reveal_child(False)
        self.current_bytes = 0
        self.upload_btt.set_sensitive(True)

    def on_info(self, _, info):
        idle(self.info_label.set_label, info)

    def on_file(self, _, file):
        for index, f in enumerate(self.roms_box.model):
            if f.get_path() == file:
                self.current_rom = self.roms_box.get_row_at_index(index)
                self.current_rom.reveal_progress(True)
                break
        self.pulse.stop()

    def on_update(self, _, read_size):
        if self.current_rom is None:
            print("Current rom is none")
            return
        self.current_rom.update_progress(read_size)
        self.current_bytes += read_size
        idle(
            self.total_progress.set_fraction, self.current_bytes / self.total_roms_size
        )

    def change_upload_state(self, _):
        self.status_revealer.set_reveal_child(True)
        self.upload_btt.set_sensitive(True)
        self.clear_btt.set_sensitive(True)

    @Gtk.Template.Callback()
    def clear_rom_list(self, _):
        self.roms_box.model.remove_all()

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
        else:
            self.__upload_roms()

    @Gtk.Template.Callback()
    def add_rom(self, _):
        dialog = Gtk.FileDialog.new()
        dialog.set_accept_label("Open")

        filter = Gtk.FileFilter.new()
        filter.add_suffix("xci")
        filter.add_suffix("nsp")

        dialog.set_default_filter(filter)

        dialog.open(self.window, callback=self.__add_rom_cb)
