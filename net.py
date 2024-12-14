import socket
import logging
import os

from urllib.parse import urlencode



class SwitchNet(socket.socket):
    def __init__(self, roms: list[str], switch_ip: str, switch_port: int):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.roms = roms
        self.switch_ip = switch_ip
        self.switch_port = switch_port
        self.local_ip = self.__get_local_ip()
        self.local_port = 0000

        self.logger = logging.getLogger("SwitchNet")
    
    def __get_local_ip(self) -> str:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            self.logger.exception("Couldn't get local ip")
            raise Exception("Couldn't get local ip")

    def send_handshake(self):
        handshake_data = ""
        for roms in self.roms:
            

        handshaker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        handshaker.connect((self.switch_ip, self.switch_port))

