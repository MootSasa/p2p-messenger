import socket
import threading
import socks
from core.crypto import CryptoManager

class NetworkNode:
    def __init__(self, host, port, socks_port, on_message, on_status):
        self.host = host
        self.port = port
        self.socks_port = socks_port
        self.connection = None
        self.crypto = CryptoManager()
        self.on_message = on_message
        self.on_status = on_status
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

    def start_listening(self):
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while True:
            try:
                conn, addr = self.server_socket.accept()
                if self.connection is None:
                    self.connection = conn
                    if self._perform_handshake(is_initiator=False):
                        self.on_status(True, "Incoming connection")
                        threading.Thread(target=self._receive_loop, daemon=True).start()
                    else:
                        self._disconnect()
                else:
                    conn.close()
            except Exception:
                break

    def connect_to(self, target_host, target_port) -> bool:
        try:
            conn = socks.socksocket()
            conn.set_proxy(socks.SOCKS5, "127.0.0.1", self.socks_port)
            conn.connect((target_host, target_port))
            self.connection = conn
            
            if self._perform_handshake(is_initiator=True):
                self.on_status(True, f"{target_host}")
                threading.Thread(target=self._receive_loop, daemon=True).start()
                return True
            else:
                self._disconnect()
                return False
        except Exception as e:
            self.on_status(False, str(e))
            return False

    def _perform_handshake(self, is_initiator: bool) -> bool:
        try:
            my_pub_bytes = self.crypto.get_public_bytes()
            if is_initiator:
                self.connection.sendall(my_pub_bytes)
                peer_pub_bytes = self.connection.recv(32)
            else:
                peer_pub_bytes = self.connection.recv(32)
                self.connection.sendall(my_pub_bytes)

            if len(peer_pub_bytes) != 32:
                return False

            self.crypto.establish_shared_secret(peer_pub_bytes)
            return True
        except Exception:
            return False

    def send_message(self, text: str) -> bool:
        if self.connection and self.crypto.cipher:
            try:
                encrypted_data = self.crypto.encrypt_message(text)
                msg_length = len(encrypted_data).to_bytes(4, byteorder='big')
                self.connection.sendall(msg_length + encrypted_data)
                return True
            except Exception:
                self._disconnect()
                return False
        return False

    def _receive_loop(self):
        while True:
            try:
                length_prefix = self.connection.recv(4)
                if not length_prefix:
                    break
                
                msg_length = int.from_bytes(length_prefix, byteorder='big')
                encrypted_data = b""
                
                while len(encrypted_data) < msg_length:
                    chunk = self.connection.recv(min(msg_length - len(encrypted_data), 4096))
                    if not chunk:
                        break
                    encrypted_data += chunk

                if not encrypted_data:
                    break

                decrypted_text = self.crypto.decrypt_message(encrypted_data)
                self.on_message(decrypted_text)
            except Exception:
                break
                
        self._disconnect()

    def _disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None
            self.on_status(False, "disconnected")