import socket

HOST = "lunix.cslab.ece.ntua.gr"
PORT = 49152

#HOST = "edu-dy.cn.ntua.gr"
#PORT = 23

def isalive():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            s.settimeout(1)
            data = s.recv(5)
            if len(data) == 0: return False
        except Exception as e:
            return False
    return True
    
#print(data.decode())
isalive()

