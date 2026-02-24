from gi.repository import Gdk, Gio, GLib

from nxroms.readers import Readable, IReadable
from nxroms.nca.header import ContentType
from nxroms.nca.nca import Nca
from nxroms.nacp import Nacp
from nxroms.roms.nsp import Nsp
from nxroms.roms.xci import Xci

from dataclasses import dataclass


class GFileReadable(Readable):
    def __init__(self, file: Gio.File):
        stream = file.read(None)
        super().__init__(stream)

    def read(self, size):
        return self.source.read_bytes(size, None).get_data()

    def seek(self, offset):
        self.source.seek(offset, GLib.SeekType.SET)

    def close(self):
        self.source.close()


@dataclass
class RomInfo:
    name: str
    version: str
    icon: Gdk.Paintable

    def __init__(self, file: Gio.File, language=0):
        r = GFileReadable(file)
        self.icon = None
        self.name = "Unknown"
        self.version = "Unknown"

        try:
            self.language = language

            self.rom = (
                Nsp(r)
                if file.get_basename().split(".")[1] != "xci"
                else self.handle_xci(r)
            )

            for x in self.rom.get_ncas():
                if x.header.content_type != ContentType.CONTROL:
                    continue

                self.handle_control(x)
        except Exception:
            raise
        finally:
            r.close()

    def handle_xci(self, r: IReadable):
        x = Xci(r)
        return x.open_nsp()

    def handle_dat(self, dat: IReadable):
        _data = b""

        while True:
            chunk = dat.read(1024)
            if not chunk:
                break
            _data += chunk

        _bytes = GLib.Bytes(_data)
        self.icon = Gdk.Texture.new_from_bytes(_bytes)

    def handle_nacp(self, file: IReadable):
        nacp = Nacp(file)

        self.name = nacp.titles[self.language].name
        self.version = nacp.version

    def handle_control(self, control: Nca):
        r = control.open_romfs(control.header.fs_headers[0])

        for x in r.files:
            if x.name.endswith(".dat") and self.icon is None:
                self.handle_dat(r.get_file(x))
                continue

            if x.name == "control.nacp":
                self.handle_nacp(r.get_file(x))
