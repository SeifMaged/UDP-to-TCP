import socket
import struct
SYN = 0x01
ACK = 0x02
FIN = 0x04

class TCPonUDP():
    def __init__(self, local_ip, local_port,timeout =1.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((local_ip, local_port))
        self.peer = None
        self.seq = 0
        self.ack = 1
        self.running = True
        self.timeout = timeout  

    


    def udp_checksum(self,data):
        if len(data) % 2 != 0:
            data += b'\x00'  # pad with 0 if odd length

        total = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + (data[i+1])  # combine two bytes  big indian
            total += word
            total = (total & 0xFFFF) + (total >> 16)  # wrap around carry

        return ~total & 0xFFFF  # one's complement
    
    def create_packet(self,flags,payload):    # need to unpack packet in diff method
        header = struct.pack("!IIB", self.seq, self.ack, flags)  
        chksum = self.checksum(header + payload)       
        packet = struct.pack("!H", chksum) + header + payload  
        return packet
    
    def segment_payload(self,flags,data):
        segments = []
        for d in range(0, len(data), self.MSS):
            chunk = data[d:d + self.MSS]
            packet = self.create_packet(self.seq, self.ack, flags, chunk)
            segments.append(packet)
            self.seq = 1 - self.seq  
            self.ack = 1-self.ack
        return segments

             
    def connect(self,server_address):   # client side of hanshake
        self.peer=  server_address
        syn_packet = self.create_packet(self.seq, SYN)
        #self.sock.sendto(syn_packet, self.peer) still need to implement

        # Step 2: Receive SYN-ACK
        response, _ = self.sock.recvfrom(1024)
        flags, server_seq = self.parse_packet(response)

        if flags & (SYN | ACK):
            print("Received SYN-ACK")

            # Step 3: Send ACK
            ack_packet = self.create_packet(server_seq + 1, ACK)
         #   self.sock.sendto(ack_packet, self.server_addr)  still need to implement
            print("Connection established")