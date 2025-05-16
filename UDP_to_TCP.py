import socket
import struct
import random

SYN = 0x01
ACK = 0x02
FIN = 0x04


class TCPonUDP():
    def __init__(self, local_ip, local_port,timeout =5.0, packetLossProbability=0.05, packetCorruptionProbability=0.05):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((local_ip, local_port))
        self.peer = None
        self.seq = 0
        self.ack = 1
        self.running = True
        self.timeout = timeout
        self.MSS = 1460
        self.packetLossProbability = packetLossProbability
        self.packetCorruptionProbability = packetCorruptionProbability

    


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
        if len(payload) > self.MSS :
            return None
        header = struct.pack("!IIB", self.seq, self.ack, flags)  
        chksum = self.udp_checksum(header + payload)       
        packet = struct.pack("!H", chksum) + header + payload  
        return packet
    
    '''
    def segment_payload(self,flags,data):
        segments = []
        for d in range(0, len(data), self.MSS):
            chunk = data[d:d + self.MSS]
            packet = self.create_packet(self.seq, self.ack, flags, chunk)
            segments.append(packet)
            self.seq = 1 - self.seq  
            self.ack = 1-self.ack
        return segments
    '''

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
    
    ##
    def parse_packet(self, packet):
        if len(packet) < 9:  # 2 for checksum - 4 for seq - 4 for ack - 1 for flags
            # Doesn't meet minimum packet size requirement 
            raise ValueError("Invalid Packet: Too short.")

        received_chksum = struct.unpack("!H", packet[:2])[0]

        header = packet[2:11] # seq + ack + flags without checksum
        payload = packet[11:]

        
        calc_chksum = self.udp_checksum(header + payload) # Recalculate Checksum For Comparison With Received Packet Checksum
        
        if received_chksum != calc_chksum:
            raise ValueError("Invalid Packet: Checksum Mismatch.")

        seq, ack, flags = struct.unpack("!IIB", header) # Unpack header

        return seq, ack, flags, payload
    
    

    # Implemented But Not Called Yet
    def sendto_with_loss_or_corruption(self, packet, address):
        randomValue = random.random() # generate random value to introduce % of loss or corruption
        
        # Do nothing to simulate packet loss
        if randomValue < self.packetLossProbability:
            print("Packet Lost.")
            return

        # Simulate Corruption by flipping a random bit in a random byte in the packet or for more aggressive option flip all bitss
        if randomValue < self.packetCorruptionProbability:

            corruptedIndex = random.randint(0, len(packet) - 1)
            corruptedByte = self.corrupt_byte(packet[corruptedIndex])

            packet = packet[:corruptedIndex] + bytes([corruptedByte]) + packet[corruptedIndex + 1:]

            print("Packet Corrupted...")

        self.sock.sendto(packet, address)
    
    def corrupt_byte(byte, aggressiveCorruption=False):
        if aggressiveCorruption:
            return byte ^ 0xFF  # flip all bits in the byte
        else:
            bit_to_flip = 1 << random.randint(0, 7) 
            return byte ^ bit_to_flip   # flip only a single random bit
    
    def send_data(self,flags=ACK,payload=b''):
        packet = self.create_packet(flags,payload)
        self.seq = 1-self.seq
        self.ack = 1-self.ack
        self.sock.sendto(packet, self.peer)


