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
from gi.repository import Gtk, Gio
from gi.repository import GUdev

@Gtk.Template(resource_path='/com/github/XtremeTHN/NXLoader/window.ui')
class NxloaderWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'NXLoaderWindow'

    navigation = Gtk.Template.Child()
    def __init__(self, app):
        super().__init__(application=app)
        self.settings = Gio.Settings.new("com.github.XtremeTHN.NXLoader")

        if self.settings.get_boolean("first-time") is False:
            self.navigation.push_by_tag("main-page")

    @Gtk.Template.Callback()
    def get_started_clicked(self, btt):
        self.navigation.push_by_tag("main-page")
        self.settings.set_boolean("first-time", False)

    def search_switch(self):
        def on_device_event(self):
            ...
        udev = GUdev.Client()
        udev.connect("uevent")