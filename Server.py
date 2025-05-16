import socket
import struct
import UDP_to_TCP as udp
SYN = 0x01
ACK = 0x02
FIN = 0x04  


server = udp.TCPonUDP('127.0.0.1',12345)
server.accept()

server.serve_connection()