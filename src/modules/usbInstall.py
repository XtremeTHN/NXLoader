import usb.core
import usb.util
import logging
import os

from struct import unpack, pack

from .task import task
from gi.repository import GObject, Gio

EXIT=0
FILE_RANGE=1
FILE_RANGE_PADDED=2

TYPE_RESPONSE=1

class Endpoint:
    def __init__(self, config, direction):
        def check_endpoint(direction):
            return lambda ep: usb.util.endpoint_direction(ep.bEndpointAddress) == direction
        
        self.ep: usb.core.Endpoint = usb.util.find_descriptor(config, custom_match=check_endpoint(direction))

        endpoint_str = 'In' if direction == usb.util.ENDPOINT_IN else "Out"
        self.logger = logging.getLogger(f"{endpoint_str}Endpoint")
        if self.ep is None:
            self.logger.error(f"{endpoint_str}Endpoint is none ")
    
    def write(self, buff, timeout=20):
        self.logger.debug(f"Writting to endpoint with length: {len(buff)}")
        self.ep.write(buff, timeout)
    
    def read(self, size_or_buffer, timeout=None):
        self.logger.debug("Reading from endpoint...")
        return self.ep.read(size_or_buffer, timeout)
    
class SwitchUsb(GObject.GObject):
    __gsignals__ = {
        "file": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "send": (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        "info": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "start": (GObject.SIGNAL_RUN_FIRST, None, tuple()),
        "exit": (GObject.SIGNAL_RUN_FIRST, None, tuple())
    }
    def __init__(self):
        super().__init__()
        self.dev: usb.core.Device | None = None
        self.out_ep: usb.core.Endpoint | None = None
        self.in_ep: usb.core.Endpoint | None = None

        self.cancellable = Gio.Cancellable.new()

        self.logger = logging.getLogger("SwitchUsb")

    def set_switch(self, switch: usb.Device):
        self.dev = switch
        self.__configure_usb()

    def find_switch(self) -> usb.core.Device | None:
        dev = usb.core.find(idVendor=0x057E, idProduct=0x3000)        
        return dev

    def __configure_usb(self):
        self.logger.debug("Configurating device...")
        self.dev.set_configuration()
        cfg = self.dev.get_active_configuration()[(0,0)]

        self.logger.debug("Finding endpoints...")

        self.out_ep = Endpoint(cfg, usb.util.ENDPOINT_OUT)
        self.in_ep = Endpoint(cfg, usb.util.ENDPOINT_IN)

    def __send_list_header(self, len):
        try:
            self.logger.debug("Sending header with rom list length of %d", len)
            self.emit("info", "Sending rom list...")
            # magic header
            self.out_ep.write(b'TUL0')
            # the length of the rom list
            self.out_ep.write(pack("<I", len))
            # idk what this does
            self.out_ep.write(b'\x00' * 0x8) # padding ?
        except Exception:
            self.logger.exception("Couldn't send header to the switch")
    
    def __send_file_response_header(self, cmd_id, data_size):
        self.out_ep.write(b'TUC0')
        self.out_ep.write(pack("<B", TYPE_RESPONSE))
        self.out_ep.write(b'\x00' * 3)
        self.out_ep.write(pack("<I", cmd_id))
        self.out_ep.write(pack("<Q", data_size))
        self.out_ep.write(b'\x00' * 0xC)

    def close(self):
        if self.dev is not None:
            try:
                self.dev.reset()
            except Exception:
                pass
            usb.util.dispose_resources(self.dev)
    
    def validate_roms(self, roms: list[str]):
        result = []
        roms_length = 0
        for file in roms:
            if os.path.isfile(file) is False or os.path.splitext(file)[1] not in [".nsp", ".xci"]:
                self.logger.warning(f"{file} is not a valid rom")
                continue
            result.append(file + "\n")
            roms_length += len(file) + 1

        return result, roms_length
    
    @task
    def send_roms(self, roms: list[str]):
        if self.dev is None:
            raise ValueError("Switch device is none")
        roms_list, roms_len = self.validate_roms(roms)
        self.logger.debug(roms_len)

        # sends header to awoo installer
        self.__send_list_header(roms_len)

        # sends the roms names one by one
        for rom in roms_list:
            self.out_ep.write(rom)
    
    def __send_file(self, padding=False):
        def _unpack(data):
            return unpack('<Q', data)[0]
        header = self.in_ep.read(0x20)

        range_size = _unpack(header[:8])
        range_offset = _unpack(header[8:16])
        rom_name_len = _unpack(header[16:24])

        rom_name = bytes(self.in_ep.read(rom_name_len)).decode()
        self.emit("file", rom_name)
        self.emit("info", f"Sending rom: {os.path.basename(rom_name)}")

        cmd_id = FILE_RANGE if not padding else FILE_RANGE_PADDED
        self.__send_file_response_header(cmd_id, range_size)

        BUFFER_SEGMENT_DATA_SIZE = 0x100000
        PADDING_SIZE = 0x1000

        # rom_length = os.stat(rom_name).st_size

        with open(rom_name, "rb") as file:
            # move the file cursor to the offset
            file.seek(range_offset)

            current_offset = 0x0
            end_offset = range_size
            read_size = BUFFER_SEGMENT_DATA_SIZE
            if padding is True:
                read_size -= PADDING_SIZE
            
            while current_offset < end_offset:
                if current_offset + read_size >= end_offset:
                    read_size = end_offset - current_offset
                
                buf = file.read(read_size)
                # prog_cb(read_size, rom_length)
                self.emit("send", read_size)
                if padding is True:
                    buf = b'\x00' * PADDING_SIZE + buf
                
                self.out_ep.write(buf, timeout=0)
                current_offset += read_size
    
    @task
    def poll_commands(self):
        self.emit("start")
        while self.cancellable.is_cancelled() is False:
            self.emit("info", "Waiting for command...")

            cmd_header = bytes(self.in_ep.read(0x20, timeout=0))
            magic = cmd_header[:4]
            if magic != b"TUC0":
                self.logger.debug(f"unknown magic?: {magic}")
                continue
            
            cmd_id = unpack("<I", cmd_header[8:12])[0]
            
            if cmd_id == EXIT:
                self.emit("info", "Exit recieved")
                self.emit("exit")
                self.logger.info('Exiting')
                break
            elif cmd_id in [FILE_RANGE, FILE_RANGE_PADDED]:
                self.emit("info", "File command recieved")
                self.__send_file(padding=cmd_id == FILE_RANGE_PADDED)
            
