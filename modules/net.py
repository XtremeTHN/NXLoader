import socket
import logging
import random

from datetime import datetime
import pytz

from urllib.parse import urlencode

class Requests:
    def __init__(self):
        self.logger = logging.getLogger("Requests")
        self.current_date = datetime.now(pytz.timezone('GMT')).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def get_code_200(self, file_size: int):
        return "HTTP/1.0 200 OK\r\n" \
        "Server: NXLoader Python\r\n" \
        f"Date: {self.current_date}\r\n" \
        "Content-type: application/octet-stream\r\n" \
        "Accept-Ranges: bytes\r\n" \
        f"Content-Range: bytes 0-{file_size -1}/{file_size}\r\n" \
        f"Content-Length: {file_size}\r\n" \
        "Last-Modified: Thu, 01 Jan 1970 00:00:00 GMT\r\n\r\n"

    def get_code_206(self, start_position: int, end_position: int, file_size: int):
        return "HTTP/1.0 206 Partial Content\r\n" \
        "Server: NXLoader Python\r\n" \
        f"Date: {self.current_date}\r\n" \
        "Content-type: application/octet-stream\r\n" \
        "Accept-Ranges: bytes\r\n" \
        f"Content-Range: bytes {start_position}-{end_position}/{file_size}\r\n" \
        f"Content-Length: {end_position - start_position + 1}\r\n" \
        "Last-Modified: Thu, 01 Jan 1970 00:00:00 GMT\r\n\r\n"

    def get_code_400(self):
        return "HTTP/1.0 400 invalid range\r\n" \
        "Server: NXLoader Python\r\n" \
        f"Date: {self.current_date}\r\n" \
        "Connection: close\r\n" \
        "Content-Type: text/html;charset=utf-8\r\n" \
        "Content-Length: 0\r\n\r\n"

    def get_code_404(self):
        return "HTTP/1.0 404 Not Found\r\n" \
        "Server: NXLoader Python\r\n" \
        f"Date: {self.current_date}\r\n" \
        "Connection: close\r\n" \
        "Content-Type: text/html;charset=utf-8\r\n" \
        "Content-Length: 0\r\n\r\n"

    def get_code_416(self):
        return "HTTP/1.0 416 Requested Range Not Satisfiable\r\n" \
        "Server: NXLoader Python\r\n" \
        f"Date: {self.current_date}\r\n" \
        "Connection: close\r\n" \
        "Content-Type: text/html;charset=utf-8\r\n" \
        "Content-Length: 0\r\n\r\n"

class SwitchNet(socket.socket):
    def __init__(self, roms: list[str], switch_ip: str, switch_port: int):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.roms = roms
        self.switch_ip = switch_ip
        self.switch_port = switch_port
        self.local_ip = self.__get_local_ip()
        # grabbed from ns-usbloader xd
        self.local_port = random.randint(0,999) + 6000

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
        for rom in self.roms:
            handshake_data += f"{self.local_ip}:{self.local_port}/{urlencode(rom)}\n"

        handshaker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        handshaker.connect((self.switch_ip, self.switch_port))

