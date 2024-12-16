import logging
import socket
import random
import re
import os

from modules.net_requests import Requests
from urllib.parse import quote

import select
import errno

class SwitchNet(socket.socket):
    def __init__(self, roms: list[str], switch_ip: str, switch_port: int):
        """
        A class for installing roms through internet.
        It's mostly a port of the code of ns-usbloader xd.
        There isn't so much documentation about the TinUSB and TinNET protocol and i don't understand the source code of Awoo xd
        """
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.local_ip = self.__get_local_ip()
        # grabbed from ns-usbloader xd
        self.local_port = random.randint(0,999) + 6000
        self.bind((self.__get_local_ip(), self.local_port))
        self.listen(1)

        self.roms = {os.path.basename(rom): rom for rom in roms}

        self.switch_ip = switch_ip
        self.switch_port = switch_port

        self.running = True
        self.requests: Requests | None = None
        self.logger = logging.getLogger("SwitchNet")
    
    def __get_local_ip(self) -> str:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            self.logger.exception("Couldn't get local ip")
            raise Exception("Couldn't get local ip")

    def send_handshake(self):
        self.logger.info("Initializing handshake with the switch...")
        handshake_data = ""
        for rom in self.roms:
            handshake_data += f"{self.local_ip}:{self.local_port}/{quote(rom)}\n"

        handshake_data_size = len(handshake_data)

        handshaker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        handshaker.connect((self.switch_ip, self.switch_port))

        self.logger.info("Sending handshake size to the switch...")
        self.logger.debug("Handshake size: %d", handshake_data_size)
        handshaker.sendall(handshake_data_size.to_bytes(4, "big"))

        self.logger.info("Sending handshake data to the switch...")
        self.logger.debug("Handshake data: %s", handshake_data)
        handshaker.sendall(handshake_data.encode())

        self.logger.info("Switch handshake complete")

        handshaker.close()
    
    def requestLoop(self):
        while self.running:
            client, addr = self.accept()
            self.logger.info("New connection from " + str(addr))

            packet = []
            self.requests = Requests(client)

            while self.running:
                packet = self.requests.read_request()
                self.handleRequest(packet)
                packet.clear()

            client.close()
            self.requests.close()

        self.close()

    def handleRequest(self, packet: list):
        if len(packet) == 0:
            return
        
        if packet[0].startswith("DROP"):
            self.logger.info("Received drop request")
            self.running = False
            return
        
        req_file_name = re.sub(r"(^[A-Za-z\s]+/)|(\s+?.*$)", "", packet[0])
        rom = self.roms.get(req_file_name)

        if req_file_name not in self.roms or os.path.exists(rom) is False:
            self.logger.error("Received request for invalid file: " + req_file_name)
            self.requests.send_code_404()
            return
        
        rom_size = os.stat(rom).st_size
        
        if rom_size < 500:
            self.logger.error("Received request for invalid file: " + rom)
            self.requests.send_code_416()
            return
        
        if packet[0].startswith("HEAD"):
            self.logger.info("Received HEAD request for " + rom)
            self.requests.send_code_200(rom_size)
            return

        if packet[0].startswith("GET"):
            self.logger.info("Received GET request for " + rom)
            for line in packet:
                if line.startswith("Range: ") is False:
                    continue
                
                range = line.lower().replace("range: bytes=", "").split("-", 2)
                if range[0] != "" and range[1] != "":
                    startRange = int(range[0])
                    endRange = int(range[1])
                    
                    if startRange > endRange or endRange > rom_size:
                        self.logger.error("Received request for invalid range: " + rom)
                        self.requests.send_code_400()
                        return

                    self.send_file_chunk(rom, rom_size, startRange, endRange)
                    return
                        
    def send_file_chunk(self, file_name: str, rom_size: int, start_position: int, end_position: int):
        total_bytes = end_position - start_position + 1
        self.logger.info(f"Sending file chunk of {total_bytes} to the switch...")
        self.requests.send_code_206(start_position, end_position, rom_size)
        self.requests.flush()

        with open(file_name, "rb") as file:
            file.seek(start_position)

            offset = 0
            read_piece = 1024
            while offset < total_bytes:
                # if the actual block exceds the range, we adjust the read_piece.
                if offset + read_piece >= total_bytes:
                    read_piece = total_bytes - offset
                
                
                chunk = file.read(read_piece)
                chunk_size = len(chunk)
                if chunk_size < read_piece:
                    self.logger.error(f"The current chunk size: {chunk_size} is less than the read piece: {read_piece}")
                    raise IOError("File ended unexpectedly")

                self.requests.send(chunk)
                offset += read_piece
        self.logger.info("File chunk sent to the switch")
        self.requests.flush()
        self.requests.send("asd")
