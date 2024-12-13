import socket
import logging
import os

class SwitchNet(socket.socket):
    def __init__(self, switch_ip, switch_port):
        ...