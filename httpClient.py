from UDP_to_TCP import TCPonUDP
import socket

server_host = "127.0.0.1"
server_port = 8081
ACK = 0x02

class HTTPClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conn = TCPonUDP(server_host, server_port, bind=False)

    def send_get(self, path="/index.html", params=""):
        if params:
            path += '?'
            path += params

        self.conn.connect((server_host, server_port))
        request = self.build_get_request(path)
        self.conn.send_data(ACK, request.encode())
        response = self.conn.serve_connection()
        print("[CLIENT] Received response:")
        print(response)
        self.conn.close()

    def send_post(self, path="/submit", body="Body of Post Request"):
        self.conn.connect((server_host, server_port))
        request = self.build_post_request(path, body)
        self.conn.send_data(ACK, request.encode())
        response = self.conn.serve_connection()

        print("[CLIENT] Received response:")
        print(response)
        self.conn.close()

    def build_get_request(self, path: str) -> str:
        return f"""GET {path} HTTP/1.0\r
        Host: {server_host}\r
        Connection: close\r
        \r
        """

    def build_post_request(self, path: str, body) -> str:
        return f"""POST {path} HTTP/1.0\r
        Host: {server_host}\r
        Content-Length: {len(body)}\r
        Connection: close\r
        \r
        {body}"""


if __name__ == "__main__":
    client = HTTPClient()
    data = "This is the body of post request test"
    params = "q='var'&numbers=4"
    print("[CLIENT] Sending GET request...")
    client.send_get("/index.html", params)
