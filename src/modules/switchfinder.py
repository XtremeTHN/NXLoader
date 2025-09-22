from gi.repository import GObject, GUdev
from .usbInstall import SwitchUsb
from usb.core import USBError

class SwitchFinder(GObject.GObject):
    __gsignals__ = {
        "disconnected": (GObject.SIGNAL_RUN_FIRST, None, tuple()),
        "connected": (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }
    def __init__(self):
        super().__init__()

        self.protocol = SwitchUsb()
    
    def set_switch(self, dev):
        msg = ""
        try:
            self.protocol.set_switch(dev)
        except USBError:
            msg = "Permission denied"
        finally:
            self.emit("connected", msg)
    
    def start(self):
        # if the switch is connected before GUdev.Client initialize, then emit the connected signal
        if (n:=self.protocol.find_switch()) is not None:
            self.set_switch(n)

        self.client = GUdev.Client.new(["usb/usb_interface"])
        self.client.connect('uevent', self.__create_obj)

    def __create_obj(self, _, action: str, device: GUdev.Device):
        # Check if this device is a nintendo switch
        if device.get_property("ID_VENDOR_FROM_DATABASE") != "Nintendo Co., Ltd":
            return
        
        # PRODUCT is something like this: 57e/3000/100
        if (p:=device.get_property("PRODUCT")) is not None:
            p = p.split("/")
            if len(p) < 2:
                return
            if p[1] != "3000":
                return

        if action == "add":
            sw = self.protocol.find_switch()
            self.set_switch(sw)

        elif action == "remove":
            self.protocol.close()
            self.emit("disconnected")