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
    try:
        s.send("GAME_STATE".encode())
    except BrokenPipeError:
        s.close()
        break
    time.sleep(4.5)
s.close()
