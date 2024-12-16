import socket
import random
import logging
import os
import re

from pathlib import Path
from urllib.parse import quote
from modules.net_requests import Requests

class SwitchNet:
    def __init__(self):
        self.logger = logging.getLogger("SwitchNet")

        self.local_ip = self.__get_local_ip()
        self.local_port = random.randint(0,999) + 6000

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.local_ip, self.local_port))

        self.socket.listen(1)
        self.logger.info(f"Listening on {self.local_ip}:{self.local_port}")
        
        self.requests = None
        self.switch_ip = ""
        self.switch_port = 2000

        self.roms = {}

    def __get_local_ip(self) -> str:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            self.logger.exception("Couldn't get local ip")
            raise Exception("Couldn't get local ip")
    
    def set_switch_ip(self, switch_ip: str):
        self.switch_ip = switch_ip
    
    def set_roms_folder(self, roms_folder: Path | str):
        roms_folder = Path(roms_folder) if isinstance(roms_folder, str) else roms_folder
        self.set_roms(roms_folder.iterdir())
    
    def set_roms(self, roms: list[Path]):
        self.roms = {}

        for rom in roms:
            if os.path.isfile(rom) is False:
                self.logger.warning("Rom is not a file: " + rom)
                continue
                
            # TODO: Check if the file size is more than 500 bytes

            if os.path.splitext(rom)[1] not in [".xci", ".nsp"]:
                self.logger.warning("Invalid file extension: " + rom)
                continue
            self.roms[rom.parts[-1]] = str(rom)
    
    def send_handshake(self):
        self.logger.info("Initializing handshake with the switch...")
        handshake_data = ""
        for rom in self.roms:
            handshake_data += f"{self.__get_local_ip()}:{self.local_port}/{quote(rom)}\n"

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
        while True:
            client = self.socket.accept()
            self.logger.info("New connection from " + str(client[1]))

            self.requests = Requests(client[0])

            packet = []
            while True:
                data = self.requests.readline().decode("utf-8")
                if data.strip(" ") == "":
                    if packet == []:
                        continue
                    self.handle_request(packet)
                    packet.clear()
                else:
                    packet.append(data)
    
    def handle_request(self, packet):
        if packet[0].startswith("DROP"):
            self.logger.info("Received drop request")
            return

        requested_file_name = re.sub(r"(^[A-Za-z\s]+/)|(\s+?.*$)", "", packet[0])
        file = self.roms.get(requested_file_name)

        if requested_file_name not in self.roms:
            self.logger.error("Received request for non-existent file: " + requested_file_name)
            self.requests.send_code_404()
            return

        requested_file_size = os.path.getsize(file)

        if packet[0].startswith("HEAD"):
            self.logger.info("Received HEAD request for " + file)
            self.requests.send_code_200(requested_file_size)
            return

        if packet[0].startswith("GET"):
            self.logger.info("Received GET request for " + file)
            for line in packet:
                # self.logger.debug(line)
                if line.startswith("Range") is False:
                    continue

                range = line.lower().replace("range: bytes=", "").split("-", 2)
                start_position = int(range[0])
                end_position = int(range[1])

                if start_position > end_position:
                    self.logger.error("Start position is greater than end position")
                    self.requests.send_code_400()
                    return
                
                self.send_file_chunk(file, requested_file_size, start_position, end_position)
                # self.requests.send_code_206(start_position, end_position, requested_file_size)
    
    def send_file_chunk(self, file_name: str, rom_size: int, start_position: int, end_position: int):
        total_bytes = end_position - start_position + 1
        self.logger.info(f"Sending file chunk of {total_bytes} to the switch...")
        self.requests.send_code_206(start_position, end_position, rom_size)

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
                if chunk_size != read_piece:
                    self.logger.error(f"The current chunk size: {chunk_size} is less than the read piece: {read_piece}")
                    raise IOError("File ended unexpectedly")

                self.requests.send(chunk)
                offset += read_piece
        self.logger.info("File chunk sent to the switch")
        self.requests.flush()