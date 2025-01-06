from gi.repository import GObject, GUdev
from .usbInstall import SwitchUsb

class SwitchFinder(GObject.GObject):
    __gsignals__ = {
        "disconnected": (GObject.SIGNAL_RUN_FIRST, None, tuple()),
        "connected": (GObject.SIGNAL_RUN_FIRST, None, tuple())
    }
    def __init__(self):
        super().__init__()

        self.protocol = SwitchUsb()
        if (n:=self.protocol.find_switch()) is not None:
            self.protocol.set_switch(n)
            self.emit("connected")
    
    def start(self):
        # if the switch was finded before GUdev.Client initialize, then emit the connected signal
        if self.protocol.dev is not None:
            self.emit("connected")

        self.client = GUdev.Client.new(["usb/usb_interface"])
        self.client.connect('uevent', self.__create_obj)

    def __create_obj(self, _, action: str, device: GUdev.Device):
        if action == "add":
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
                
            sw = self.protocol.find_switch()
            self.protocol.set_switch(sw)
            self.emit("connected")
        else:
            self.protocol.close()
            self.emit("disconnected")