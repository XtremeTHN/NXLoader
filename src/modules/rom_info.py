from gi.repository import Gdk, Gio, GLib

from nxroms.readers import IReadable, Region
from nxroms.nca.header import ContentType
from nxroms.nca.nca import Nca
from nxroms.nacp import Nacp
from nxroms.rom.nsp import Nsp

from dataclasses import dataclass

import struct

class GFileReadable(IReadable):
    def __init__(self, file: Gio.File):
        self.stream = file.read(None)
    
    def skip(self, bytes: int):
        self.seek(self.tell() + bytes)
    
    def seek(self, offset):
        self.stream.seek(offset, GLib.SeekType.SET)

    def tell(self):
        return self.stream.tell()

    def read_at(self, offset, size):
        self.seek(offset)
        return self.read(size)
    
    def read_unpack(self, size: int, format_str: str):
        r = self.read(size)
        return struct.unpack(format_str, r)[0]

    def read_to(self, offset, size, format_str):
        d = self.read_at(offset, size)
        if not d:
            return
        
        return struct.unpack(format_str, d)[0]

    def dump(self, path):
        with open(path, "wb") as f:
            while True:
                chunk = self.read(1024)
                if not chunk:
                    return
                f.write(chunk)
            

    def read(self, size):
        b = self.stream.read_bytes(size)
        return b.get_data()

    def close(self):
        self.stream.close()


@dataclass
class RomInfo:
    name: str
    version: str
    icon: Gdk.Paintable

    def __init__(self, file: Gio.File, language=0):
        r = GFileReadable(file)
        self.language = language

        self.nsp = Nsp(r)
        self.icon = None
        self.name = "Unknown"
        self.version = "Unknown"

        for x in self.nsp.get_files():
            if x.header.content_type != ContentType.CONTROL:
                continue

            self.handle_control(x)
        
        r.close()

    def handle_dat(self, dat: Region):
        _data = b""

        while True:
            chunk = dat.read(1024)
            if not chunk:
                break
            _data += chunk
        
        _bytes = GLib.Bytes(_data)
        self.icon = Gdk.Texture.new_from_bytes(_bytes)

    def handle_nacp(self, file: Region):
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