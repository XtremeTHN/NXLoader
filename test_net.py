from modules.net import SwitchNet
import logging
import glob, os, datetime

# def init_logger():
#     console = logging.StreamHandler()
#     console.setLevel(logging.DEBUG)
#     fmt = logging.Formatter("[ %(name)s ] [%(levelname)s] %(message)s")
#     console.setFormatter(fmt)
#     logging.getLogger('').addHandler(console)

# init_logger()

def delete_logs(max_logs, log_dir="logs"):
    logger = logging.getLogger("delete_logs()")
    if max_logs != -1:
        logs = glob.glob(os.path.join(log_dir,"*.log"))
        if len(logs) > max_logs:
            logger.debug("Log limit reached!. Deleting logs...")
            
            try:
                for x in logs:
                    os.remove(x)
            except Exception as e:
                print("Removal of logs has failed!")
                print(e)
        logger.debug("There were %d logs", len(logs))

    
def init_log(name, log_dir="logs") -> str | None:
    log_name = os.path.join(log_dir, datetime.datetime.today().strftime(f"%d-%m-%Y_%H-%M-%S_{name}.log"))
    logging.basicConfig(filename=log_name,
                filemode='w',
                format='%(asctime)s:%(msecs)d %(name)s %(levelname)s %(message)s',
                datefmt='%H:%M',
                level=logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[ %(name)s ][%(levelname)s] %(message)s')
    console.setFormatter(formatter)
    console.setFormatter
    logging.getLogger('').addHandler(console)
    return [
        getattr(logging.getLoggerClass().root.handlers[0], 'baseFilename', "Null"),
        console,
    ]

init_log("test")
delete_logs(3)

net = SwitchNet(["nsp/Ori_WOW.nsp"], "192.168.0.199", 2000)
net.send_handshake()
net.requestLoop()