from datetime import datetime
import pytz
import logging
from io import BytesIO
from urllib.parse import quote

class Requests:
    def __init__(self, client):
        """Helper class for constructing requests"""
        self.logger = logging.getLogger("Requests")
        self.output: BytesIO = client.makefile("rb")
        self.input: BytesIO = client.makefile("wb")
        self.current_date = datetime.now(pytz.timezone('GMT')).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def send_code_200(self, file_size: int):
        """
        Return a HTTP response with a 200 status code, which is sent when the switch requests a file via HTTP.
        
        :param file_size: The size of the file in bytes.
        :return: A string containing the HTTP response.
        """
        self.logger.debug("Sending code 200 to the switch with file size: " + str(file_size) + "...")
        return self.send(
            "HTTP/1.0 200 OK\r\n" \
            "Server: NXLoader Python\r\n" \
            f"Date: {self.current_date}\r\n" \
            "Content-type: application/octet-stream\r\n" \
            "Accept-Ranges: bytes\r\n" \
            f"Content-Range: bytes 0-{file_size -1}/{file_size}\r\n" \
            f"Content-Length: {file_size}\r\n" \
            "Last-Modified: Thu, 01 Jan 1970 00:00:00 GMT\r\n\r\n"
        )

    def send_code_206(self, start_position: int, end_position: int, file_size: int):
        """
        Return a HTTP response with a 206 status code, which is sent when the switch requests a partial file via HTTP.
        
        :param start_position: The start position of the range in bytes.
        :param end_position: The end position of the range in bytes.
        :param file_size: The size of the file in bytes.
        :return: A string containing the HTTP response.
        """
        self.logger.debug("Sending code 206 to the switch...")
        return self.send(
            "HTTP/1.0 206 Partial Content\r\n" \
            "Server: NXLoader Python\r\n" \
            f"Date: {self.current_date}\r\n" \
            "Content-type: application/octet-stream\r\n" \
            "Accept-Ranges: bytes\r\n" \
            f"Content-Range: bytes {start_position}-{end_position}/{file_size}\r\n" \
            f"Content-Length: {end_position - start_position + 1}\r\n" \
            "Last-Modified: Thu, 01 Jan 1970 00:00:00 GMT\r\n\r\n"
        )

    def send_code_400(self):
        """
        Return a HTTP response with a 400 status code, which is sent when the switch sends an invalid range.
        
        :return: A string containing the HTTP response.
        """
        self.logger.debug("Sending code 400 to the switch...")
        return self.send(
            "HTTP/1.0 400 invalid range\r\n" \
            "Server: NXLoader Python\r\n" \
            f"Date: {self.current_date}\r\n" \
            "Connection: close\r\n" \
            "Content-Type: text/html;charset=utf-8\r\n" \
            "Content-Length: 0\r\n\r\n"
        )

    def send_code_404(self):
        """
        Return a HTTP response with a 404 status code, which is sent when the switch requests a non-existent file via HTTP.
        
        :return: A string containing the HTTP response.
        """
        self.logger.debug("Sending code 404 to the switch...")
        return self.send(
            "HTTP/1.0 404 Not Found\r\n" \
            "Server: NXLoader Python\r\n" \
            f"Date: {self.current_date}\r\n" \
            "Connection: close\r\n" \
            "Content-Type: text/html;charset=utf-8\r\n" \
            "Content-Length: 0\r\n\r\n"
        )

    def send_code_416(self):
        """
        Return a HTTP response with a 416 status code, which is sent when the switch requests a range of a file that is less than 500 bytes.
        
        :return: A string containing the HTTP response.
        """
        self.logger.debug("Sending code 416 to the switch...")
        return self.send(
            "HTTP/1.0 416 Requested Range Not Satisfiable\r\n" \
            "Server: NXLoader Python\r\n" \
            f"Date: {self.current_date}\r\n" \
            "Connection: close\r\n" \
            "Content-Type: text/html;charset=utf-8\r\n" \
            "Content-Length: 0\r\n\r\n"
        )

    def send(self, buf: str | bytes):
        if isinstance(buf, str):
            buf = buf.encode()
        self.input.write(buf)
    
    def flush(self):
        self.input.flush()
    
    def readline(self) -> bytes:
        return self.output.readline()

    def read_request(self):
        packet = []
        while True:
            data = self.readline().decode("utf-8")
            if data.strip(" ") == "":
                return packet
            packet.append(data)
    
    def close(self):
        self.output.close()
        self.input.close()