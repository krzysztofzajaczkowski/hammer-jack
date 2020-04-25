import socket

s = socket.socket()
s.connect(('localhost', 63300))

message = "test"
nick = input("przedstaw sie: ")
while message != "q":
    message = input("->")
    message = nick + '♞' + message
    s.send(message.encode())
    data = s.recv(1024)
    data = data.decode()
    print(data)
s.close()