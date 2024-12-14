import usb.core
import usb.util

import os

from struct import unpack, pack
from pathlib import Path

import logging

def info_cb(magic: bytes, cmd_type: int, cmd_id: int, data_size: int):
    print("Magic:", magic.decode())

def progress_cb(current, max):
    print(f"Bytes sended: {current}", flush=True)

EXIT=0
FILE_RANGE=1
FILE_RANGE_PADDED=2

TYPE_RESPONSE=1

def retry(func):
    def wrapper(*args, **kwargs):
        for _ in range(3):
            try:
                result = func(*args, **kwargs)
                return result
            except:
                args[0].logger.exception("Retrying writting...")
        raise Exception("Ran out of retries")
    return wrapper

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
    
class SwitchUsb:
    def __init__(self):
        self.dev: usb.core.Device | None = None
        self.out_ep: usb.core.Endpoint | None = None
        self.in_ep: usb.core.Endpoint | None = None

        self.cfg = None
        self.logger = logging.getLogger("SwitchUsb")

        self.__find_switch()
        self.__configure_usb()

    def __enter__(self):
        """Init

        Returns:
            SwitchUsb: Returns switchusb
        """
        self.__init__()
        return self
    
    def __exit__(self, *args):
        print(args)
        self.close()
        
    def __find_switch(self):
        if self.dev is not None:
            self.close()

        self.dev = usb.core.find(idVendor=0x057E, idProduct=0x3000)
        if self.dev is None:
            self.logger.error("Switch not found")
            raise ValueError("Switch not found")

    def __configure_usb(self):
        self.logger.debug("Configurating device...")
        self.dev.set_configuration()
        self.cfg = self.dev.get_active_configuration()

        self.logger.debug("Finding endpoints...")

        cfg = self.cfg[(0,0)]
        self.out_ep = Endpoint(cfg, usb.util.ENDPOINT_OUT)
        self.in_ep = Endpoint(cfg, usb.util.ENDPOINT_IN)

    def __send_list_header(self, len):
        try:
            self.logger.debug("Sending header with rom list length of %d", len)
            # magic header
            self.out_ep.write(b'TUL0')
            # the length of the rom list
            self.out_ep.write(pack("<I", len))
            # idk what this does
            self.out_ep.write(b'\x00' * 0x8) # padding ?
        except:
            self.logger.exception("Couldn't send header to the switch")
    
    def __send_file_response_header(self, cmd_id, data_size):
        self.out_ep.write(b'TUC0')
        self.out_ep.write(pack("<B", TYPE_RESPONSE))
        self.out_ep.write(b'\x00' * 3)
        self.out_ep.write(pack("<I", cmd_id))
        self.out_ep.write(pack("<Q", data_size))
        self.out_ep.write(b'\x00' * 0xC)

    def close(self):
        self.dev.reset()
        usb.util.dispose_resources(self.dev)
    
    def validate_roms(self, roms: list[Path]):
        result = []
        roms_length = 0
        for file in roms:
            if file.is_file() is False or file.suffix not in [".nsp", ".xci"]:
                self.logger.debug(f"{file.is_file()} {file.suffix}")
                self.logger.warning(f"{str(file)} is not a valid rom")
                continue
            self.logger.debug(f"{file.is_file()} {file.suffix} {file}")
            result.append(str(file) + "\n")
            roms_length += len(str(file)) + 1

        return result, roms_length
    
    def send_roms(self, roms: list[Path]):
        roms_list, roms_len = self.validate_roms(roms)
        self.logger.debug(roms_len)

        # sends header to awoo installer
        self.__send_list_header(roms_len)

        # sends the roms one by one
        for rom in roms_list:
            self.out_ep.write(rom)
        
    def send_roms_folder(self, folder: str):
        folder: Path = Path(folder)

        if folder.is_dir() is False:
            raise FileNotFoundError(f"{folder} doesn't exists")

        self.send_roms(folder.iterdir())
    
    def __send_file(self, prog_cb, padding=False):
        def _unpack(data):
            return unpack('<Q', data)[0]
        header = self.in_ep.read(0x20)

        range_size = _unpack(header[:8])
        range_offset = _unpack(header[8:16])
        rom_name_len = _unpack(header[16:24])

        rom_name = bytes(self.in_ep.read(rom_name_len)).decode()
        cmd_id = FILE_RANGE if not padding else FILE_RANGE_PADDED
        self.__send_file_response_header(cmd_id, range_size)

        BUFFER_SEGMENT_DATA_SIZE = 0x100000
        PADDING_SIZE = 0x1000

        rom_length = os.stat(rom_name).st_size
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
                prog_cb(read_size, rom_length)
                if padding is True:
                    buf = b'\x00' * PADDING_SIZE + buf
                
                self.out_ep.write(buf, timeout=0)
                current_offset += read_size
    
    def poll_commands(self, info_cb=info_cb, prog_cb=progress_cb):
        while True:
            cmd_header = bytes(self.in_ep.read(0x20, timeout=0))
            magic = cmd_header[:4]
            if magic != b"TUC0":
                self.logger.debug(f"unknown magic?: {magic}")
                continue
            
            cmd_id = unpack("<I", cmd_header[8:12])[0]
            cmd_type = unpack('<B', cmd_header[4:5])[0]
            data_size = unpack('<Q', cmd_header[12:20])[0]

            info_cb(magic, cmd_type, cmd_id, data_size)
            
            if cmd_id == EXIT:
                self.logger.info('Exiting')
                break
            elif cmd_id in [FILE_RANGE, FILE_RANGE_PADDED]:
                self.__send_file(prog_cb, padding=cmd_id == FILE_RANGE_PADDED)
            