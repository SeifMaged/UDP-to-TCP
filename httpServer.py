from UDP_to_TCP import TCPonUDP

ACK = 0x02
server_host = "127.0.0.1"
server_port = 8081


class HTTPServer:
    def __init__(self, host=server_host, port=server_port):
        self.host = host
        self.port = port
        self.tcp = TCPonUDP(host, port)
        print(f"[SERVER] Listening on {host}:{port}")

    def accept(self):
        print("[SERVER] Waiting for new connection...")
        client_addr = self.tcp.accept()
        self.handle_connection()

    def handle_connection(self):
        request = self.tcp.serve_connection()
        print("[SERVER] Received request:")
        print(request)

        response = self.http_request(request)
        self.tcp.send_data(0, response.encode())
        self.tcp.close()

    def http_request(self, request: str) -> str:
        lines = request.splitlines()
        if not lines:
            return self.http_response(400, "Bad Request")

        request_line = lines[0]
        method, path, *_ = request_line.split()
        headers = self.parse_headers(lines[1:])

        if method == "GET":
            return self.http_get(path)
        elif method == "POST":
            content_length = int(headers.get("Content-Length", 0))
            body_index = request.find("\r\n\r\n")
            body = request[body_index + 4 :] if body_index != -1 else ""
            body = body[:content_length]
            return self.http_post(path, body)
        else:
            return self.http_response(405, "Method Not Allowed")

    def parse_headers(self, header_lines: list[str]):
        headers = {}
        for line in header_lines:
            if line.strip() == "":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        return headers

    def http_get(self, path: str) -> str:
        if path == "/index.html":
            return self.http_response(
                200,
                "OK",
                headers={
                    "Content-Type": "text/html",
                    "Connection": "close",
                },
                body="<h1>Welcome to my server</h1>",
            )
        else:
            return self.http_response(
                404,
                "Not Found",
                headers={
                    "Content-Type": "text/plain",
                    "Connection": "close",
                },
                body="404 Not Found.",
            )

    def http_post(self, path: str, body: str) -> str:
        print(f"[SERVER] POST data received at {path}: {body}")

        return self.http_response(
            200, "OK", headers={"Content-Length": "0", "Connection": "close"}
        )

    def http_response(self, code: int, status: str, headers=None, body="") -> str:
        lines = [f"HTTP/1.0 {code} {status}"]
        headers = headers or {}
        for k, v in headers.items():
            lines.append(f"{k}: {v}")
        lines.append("")  # End of headers
        lines.append(body)
        return "\r\n".join(lines)


def main():
    server = HTTPServer()
    server.accept()


if __name__ == "__main__":
    main()
