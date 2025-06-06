#!/usr/bin/env python3

import socket
import select
import time
import sys
import threading
import ssl
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('proxy_server')

# Configuration
LISTENING_ADDR = '0.0.0.0'
LISTENING_PORT = 8080
BUFFER_SIZE = 8192
MAX_CONNECTIONS = 100
TIMEOUT = 60

class ProxyServer:
    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(MAX_CONNECTIONS)
        self.connections = []
        self.running = True
        logger.info(f"Proxy server started on {host}:{port}")

    def handle_client(self, client_socket, client_addr):
        """Handle client connection"""
        try:
            # Receive initial data from client
            request = client_socket.recv(BUFFER_SIZE)
            if not request:
                return

            # Check if this is a CONNECT request (HTTPS)
            if request.startswith(b'CONNECT'):
                self._handle_https_request(client_socket, request)
            else:
                self._handle_http_request(client_socket, request)

        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            if client_socket in self.connections:
                self.connections.remove(client_socket)
            client_socket.close()
    def _handle_http_request(self, client_socket, request):
        """Handle regular HTTP request"""
        try:
            # Parse the first line of the HTTP request
            first_line = request.split(b'\n')[0].decode('utf-8', 'ignore')
            url = first_line.split(' ')[1]

            # Extract hostname and port from the HTTP request
            http_pos = url.find('://')
            if http_pos != -1:
                url = url[(http_pos + 3):]

            port_pos = url.find(':')
            host_pos = url.find('/')

            if host_pos == -1:
                host_pos = len(url)

            host = ''
            port = 80  # Default HTTP port

            if port_pos != -1:
                host = url[:port_pos]
                port = int(url[(port_pos + 1):host_pos])
            else:
                host = url[:host_pos]

            path = url[host_pos:] or '/'

            logger.info(f"Connecting to {host}:{port}{path}")

            # Connect to the remote server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(TIMEOUT)

            try:
                server_socket.connect((host, port))
                logger.info(f"Successfully connected to {host}:{port}")
            except socket.error as e:
                logger.error(f"Failed to connect to {host}:{port}: {e}")
                client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/html\r\n\r\n<html><body><h1>502 Bad Gateway</h1><p>Failed to connect to target server.</p></body></html>")
                return

            # Modify the request to use the path instead of the full URL
            method = first_line.split(' ')[0]
            http_version = first_line.split(' ')[2]
            new_first_line = f"{method} {path} {http_version}\r\n"

            # Replace the first line in the request
            modified_request = new_first_line.encode() + b'\r\n'.join(request.split(b'\r\n')[1:])

            try:
                server_socket.send(modified_request)
                logger.info(f"Request sent to {host}:{port}")
            except socket.error as e:
                logger.error(f"Failed to send request to {host}:{port}: {e}")
                client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/html\r\n\r\n<html><body><h1>502 Bad Gateway</h1><p>Failed to send request to target server.</p></body></html>")
                return

            # Relay data between client and server
            self._relay_data(client_socket, server_socket)

        except Exception as e:
            logger.error(f"HTTP handling error: {e}")
            client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/html\r\n\r\n<html><body><h1>502 Bad Gateway</h1><p>Proxy error: {str(e)}</p></body></html>".format(str(e).encode()))

    def _handle_https_request(self, client_socket, request):
        """Handle HTTPS CONNECT tunneling"""
        try:
            # Parse the CONNECT request
            first_line = request.split(b'\n')[0].decode('utf-8', 'ignore')
            target = first_line.split(' ')[1]

            # Extract host and port
            host, port = target.split(':')
            port = int(port)

            # Connect to the remote server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(TIMEOUT)

            try:
                server_socket.connect((host, port))
                # Send success response to client
                client_socket.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
            except Exception as e:
                logger.error(f"Failed to connect to {host}:{port} - {e}")
                client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                return

            # Relay data between client and server
            self._relay_data(client_socket, server_socket)

        except Exception as e:
            logger.error(f"HTTPS handling error: {e}")
            client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")

    def _relay_data(self, client_socket, server_socket):
        """Relay data between client and server sockets"""
        self.connections.append(server_socket)

        try:
            while True:
                # Wait for data from either socket
                read_sockets, _, error_sockets = select.select(
                    [client_socket, server_socket], [], [client_socket, server_socket], TIMEOUT
                )

                if error_sockets or not read_sockets:
                    break

                for sock in read_sockets:
                    try:
                        data = sock.recv(BUFFER_SIZE)
                        if not data:
                            return

                        # Forward data to the other socket
                        if sock is client_socket:
                            server_socket.send(data)
                        else:
                            client_socket.send(data)
                    except Exception as e:
                        logger.error(f"Error relaying data: {e}")
                        return

        finally:
            if server_socket in self.connections:
                self.connections.remove(server_socket)
            server_socket.close()

    def start(self):
        """Start the proxy server"""
        try:
            while self.running:
                try:
                    client_socket, addr = self.server.accept()
                    client_socket.settimeout(TIMEOUT)
                    self.connections.append(client_socket)
                    logger.info(f"Connection from {addr[0]}:{addr[1]}")

                    # Start a new thread to handle the client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except KeyboardInterrupt:
                    logger.info("Shutting down proxy server...")
                    self.running = False
                    break

        finally:
            # Clean up all connections
            for conn in self.connections:
                conn.close()
            self.server.close()

if __name__ == "__main__":
    try:
        proxy = ProxyServer(LISTENING_ADDR, LISTENING_PORT)
        proxy.start()
    except Exception as e:
        logger.error(f"Error starting proxy server: {e}")
        sys.exit(1)
