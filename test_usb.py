import logging
import os
import datetime
import tqdm

from pathlib import Path
from modules.usbInstall import SwitchUsb

class Handlers:
    def __init__(self):
        self.tqdm = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1024)
    
    def info_cb(self, magic: bytes, cmd_type: int, cmd_id: int, data_size: int):
        self.tqdm.set_description(f"Magic: {magic.decode()} Cmd Type: {cmd_type} Cmd ID: {cmd_id}")

    def progress_cb(self, current, max):
        self.tqdm.total = max
        self.tqdm.update(current)

def init_log(name, log_dir="logs") -> str | None:
    log_name = os.path.join(log_dir, datetime.datetime.today().strftime(f"%d-%m-%Y_%H-%M-%S_{name}.log"))
    logging.basicConfig(filename=log_name,
                filemode='w',
                format='%(asctime)s:%(msecs)d %(name)s %(levelname)s %(message)s',
                datefmt='%H:%M',
                level=logging.INFO)

init_log("test")

handlers = Handlers()
with SwitchUsb() as usb:
    usb.send_roms([Path("nsp/Ori_v1.2.0.xci"), Path("/home/axel/Downloads/homebrew.nsp")])
    usb.poll_commands(prog_cb=handlers.progress_cb, info_cb=handlers.info_cb)