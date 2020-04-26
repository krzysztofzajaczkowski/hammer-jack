import socket
import sys
import time

s = socket.socket()
s.connect(('localhost', 63300))

k = list(sys.argv)
nick, gametype = k[1].strip(), k[2].strip()
message = nick + '♞' + gametype
s.send(message.encode())
while True:
    data = s.recv(1024)
    data = data.decode()
    print(data)
    if data == "DISCONNECT":
        break
    s.send("GAME_STATE".encode())
    time.sleep(3.0)
s.close()
