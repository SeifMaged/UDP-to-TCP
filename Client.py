import UDP_to_TCP as udp2tcp
ACK = 0x02

client = udp2tcp.TCPonUDP('127.0.0.1',12000)
client.connect(('127.0.0.1',12345))
data = b'hello World!'
client.send_data(ACK,data)
client.close()




packet = client.create_packet(ACK,data)
print(packet)
#data = b'\x68\xE9\x68\xC9\xD1\xB2'
#chksum = client.udp_checksum(data)
#print(hex(data[0]))
#print(hex(data[1]))
#print(hex(chksum))
