from modules.net_new import SwitchNet
from modules.logs import init_log, delete_logs

init_log("test")
delete_logs(3)

# net = SwitchNet(["nsp/homebrew.nsp"], "192.168.0.199", 2000)
net = SwitchNet()
net.set_roms_folder("nsp")
net.set_switch_ip("192.168.0.199")

net.send_handshake()
net.requestLoop()