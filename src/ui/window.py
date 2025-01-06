# window.py
#
# Copyright 2024 Unknown
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk, Gio, GObject
from gi.repository import GUdev

from ..modules.switchfinder import SwitchFinder
from .get_started_dialog import GetStartedDialog

from .roms_page import RomsPage
from .not_found import NotFoundPage

@Gtk.Template(resource_path='/com/github/XtremeTHN/NXLoader/window.ui')
class NxloaderWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'NXLoaderWindow'

    navigation: Adw.NavigationView = Gtk.Template.Child()
    toast: Adw.ToastOverlay = Gtk.Template.Child()

    def __init__(self, app):
        super().__init__(application=app)
        self.settings = Gio.Settings.new("com.github.XtremeTHN.NXLoader")

        self.finder = SwitchFinder()

        self.finder.connect("connected", self.show_roms_page)
        self.finder.connect("disconnected", self.show_not_found)

        # self.navigation.add(NotFoundPage)
        self.navigation.add(RomsPage(self.finder, self))

        self.navigation.connect("notify::visible-page", self.reset)

        self.finder.start()

    def add_toast(self, title):
        self.toast.add_toast(Adw.Toast.new(title))
    
    def show_not_found(self, _):
        self.navigation.pop_to_tag("switch-not-found-page")
        self.add_toast("Switch disconnected")
    
    def show_roms_page(self, _):
        self.navigation.push_by_tag("roms-page")
        self.add_toast("Switch connected")

    def reset(self, *_):
        if self.navigation.props.visible_page.get_tag() != "roms-page":
            self.finder.protocol.close()
