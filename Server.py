import socket
import struct
SYN = 0x01
ACK = 0x02
FIN = 0x04

class TCPonUDP():
    def __init__(self, local_ip, local_port,timeout =5.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((local_ip, local_port))
        self.peer = None
        self.seq = 0
        self.ack = 1
        self.running = True
        self.timeout = timeout  
        self.MSS = 1460

    


    def udp_checksum(self,data):
        if len(data) % 2 != 0:
            data += b'\x00'  # pad with 0 if odd length

        total = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + (data[i+1])  # combine two bytes  big indian
            total += word
            total = (total & 0xFFFF) + (total >> 16)  # wrap around carry

        return ~total & 0xFFFF  # one's complement
    
    def create_packet(self,flags,payload=b''):    # need to unpack packet in diff method
        if len(payload) > self.MSS :
            return None
        header = struct.pack("!IIB", self.seq, self.ack, flags)  
        chksum = self.udp_checksum(header + payload)       
        packet = struct.pack("!H", chksum) + header + payload  
        return packet
    
    def parse_packet(self, packet): # unpack packet
        # Extract and verify checksum
        received_chksum = struct.unpack("!H", packet[0:2])[0]
        header = packet[2:11]  # 9 bytes
        payload = packet[11:]

        # Verify checksum
        calc_chksum = self.udp_checksum(header + payload)
        if received_chksum != calc_chksum:
            raise ValueError("Checksum mismatch")

        # Unpack header
        seq, ack, flags = struct.unpack("!IIB", header)
        
        return seq, ack, flags, payload
    '''
    def segment_payload(self,flags,data):              
        segments = []
        for d in range(0, len(data), self.MSS):
            chunk = data[d:d + self.MSS]
            packet = self.create_packet(seq, self.ack, flags, chunk)
            segments.append(packet)
            self.seq = 1 - self.seq  
            self.ack = 1-self.ack
        return segments
    '''

             
    def connect(self,server_address):   # client side of hanshake
        
        self.peer=  server_address
        syn_packet = self.create_packet(SYN)
        self.seq = 1-self.seq
        self.sock.sendto(syn_packet, self.peer) 
       

        # Step 2: Receive SYN-ACK
        self.sock.settimeout(self.timeout)
        response, _ = self.sock.recvfrom(1024)
        server_seq , server_ack, flags, payload  = self.parse_packet(response)
        
        if flags & (SYN | ACK):
            print("Received SYN-ACK")
            self.ack = server_seq+1

            # Step 3: Send ACK
            ack_packet = self.create_packet(ACK)                         # '''server_seq + 1,'''
            self.sock.sendto(ack_packet, self.peer)  
            print("Connection established")

    def accept(self):  # server side of hanshake
        print("Server listening for handshake...")

        while True:
            try:
                # Receive packet from any client
                packet, client_addr = self.sock.recvfrom(1024)
                #self.peer = client_addr
                client_seq, client_ack, flags, payload = self.parse_packet(packet)

                if flags & SYN:
                    print(f"Received SYN from {client_addr}")

                    # Initialize server sequence number and ack
                    #self.seq = 0  # or random initial seq
                    #self.ack = client_seq + 1
                    self.peer = client_addr  # save client address

                    # Send SYN-ACK
                    syn_ack_packet = self.create_packet(SYN | ACK)
                    self.sock.sendto(syn_ack_packet, self.peer)
                    print(f"Sent SYN-ACK to {self.peer}")

                    # Wait for ACK to complete handshake
                    self.sock.settimeout(self.timeout)
                    ack_packet, addr = self.sock.recvfrom(1024)
                    ack_seq, ack_ack, ack_flags, ack_payload = self.parse_packet(ack_packet)

                    if addr == client_addr and (ack_flags & ACK) :
                        print(f"Received ACK from {client_addr}")
                        print("Connection established")
                        return client_addr  # handshake complete, return client info

                    else:
                        print("Handshake failed or unexpected packet")
            except socket.timeout:
                print("Timeout waiting for handshake packets")

    def serve_connection(self):
        print("Server ready to receive data or close connection...")
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                seq, ack, flags, payload = self.parse_packet(data)

                if flags & FIN:
                    print("Received FIN from client. Sending ACK and closing.")
                    ack_packet = self.create_packet(ACK)
                    self.sock.sendto(ack_packet, self.peer)
                    self.running = False
                    self.sock.close()
                    break

                # Else handle data packets here...
                print("Received data:", payload)

            except socket.timeout:
                continue



    def close(self):
        if not self.peer:
            print("No active connection to close.")
            return

        # Send FIN
        fin_packet = self.create_packet(FIN)
        self.sock.sendto(fin_packet, self.peer)
        print("FIN sent, waiting for ACK...")

        try:
            self.sock.settimeout(self.timeout)
            response, _ = self.sock.recvfrom(1024)
            seq, ack, flags, payload = self.parse_packet(response)

            if flags & ACK:
                print("FIN-ACK received. Closing socket.")
                self.sock.close()
                self.running = False
        except socket.timeout:
            print("Timeout waiting for FIN-ACK. Closing anyway.")
            self.sock.close()
            self.running = False


server =TCPonUDP('127.0.0.1',12345)
server.accept()

server.serve_connection()