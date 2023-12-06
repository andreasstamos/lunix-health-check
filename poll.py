import socket
from lunix_protocol import LunixStateMachine
from multiprocessing import Process, Manager
import time

HOST = "lunix.cslab.ece.ntua.gr"
PORT = 49152
RECV_SIZE = 256
TIMEOUT = 3

def poll_alive(status):
    def update_status(current, reason="unknown", sensors=None):
        if current != status.current: status.last_update = time.time()

        status.current = current

        if current == "up": status.sensors = sensors.copy()
        if current == "down":
            status.reason = reason
            status.sensors = None

    status.sensors = None
    status.last_update = None
    status.current = "reconnect"
    while True:
        lunix = LunixStateMachine()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            try:
                s.connect((HOST, PORT))
            except TimeoutError:
                update_status("down", reason="Connect timed out.")
            except Exception:
                update_status("down")
            
            try:
                while True:
                    data = s.recv(RECV_SIZE)
                    if len(data) == 0:
                        update_status("down", reason="reset")
                        break
                    lunix.receive(data)
                    if len(lunix.sensors) != 0: update_status("up", sensors=lunix.sensors)
            except TimeoutError:
                update_status("down", reason="nodata")
            except Exception as e:
                update_status("down")

def start_poll():
    manager = Manager()
    status = manager.Namespace()
    Process(target=poll_alive, args=(status,)).start()
    return status

