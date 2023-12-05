import socket
from lunix_protocol import LunixStateMachine
from multiprocessing import Process, Manager
import time

HOST = "lunix.cslab.ece.ntua.gr"
PORT = 49152
RECV_SIZE = 256

def poll_alive(status):
    def update_status(sensors, reason="unknown"):
        status.sensors = sensors.copy() if sensors is not None else None
        status.last_update = time.time()
        if status.sensors is None: status.reason = reason
        else: status.reason = None

    status.last_update = None
    while True:
        lunix = LunixStateMachine()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            try:
                s.connect((HOST, PORT))
            except TimeoutError:
                update_status(None, "timeout")
            except Exception:
                update_status(None)
            
            try:
                while True:
                    data = s.recv(RECV_SIZE)
                    if len(data) == 0:
                        update_status(sensors, "reset")
                        break
                    lunix.receive(data)
                    update_status(lunix.sensors)
            except TimeoutError:
                update_status(None, "nodata")
            except Exception as e:
                update_status(None)

def start_poll():
    manager = Manager()
    status = manager.Namespace()
    status.last_update = None
    status.sensors = None
    Process(target=poll_alive, args=(status,)).start()
    return status

