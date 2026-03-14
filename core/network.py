import socket
import threading
import os
from core.crypto import CryptoManager

class NetworkNode:
    def __init__(self, host, port, on_message, on_status):
        self.host = host
        self.port = port
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
                    if self._perform_handshake(False):
                        self.on_status(True, f"{addr[0]}:{addr[1]}")
                        threading.Thread(target=self._receive_loop, daemon=True).start()
                    else:
                        self._disconnect()
                else:
                    conn.close()
            except Exception:
                break

    def connect_to(self, target_ip, target_port) -> bool:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((target_ip, target_port))
            self.connection = conn
            if self._perform_handshake(True):
                self.on_status(True, f"{target_ip}:{target_port}")
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
                payload = b'\x01' + text.encode('utf-8')
                encrypted_data = self.crypto.encrypt_data(payload)
                self.connection.sendall(len(encrypted_data).to_bytes(4, 'big') + encrypted_data)
                return True
            except Exception:
                self._disconnect()
        return False

    def send_file(self, filepath: str) -> bool:
        if self.connection and self.crypto.cipher:
            try:
                filename = os.path.basename(filepath).encode('utf-8')
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                payload = b'\x02' + filename + b'\x00' + file_data
                encrypted_data = self.crypto.encrypt_data(payload)
                self.connection.sendall(len(encrypted_data).to_bytes(4, 'big') + encrypted_data)
                return True
            except Exception:
                self._disconnect()
        return False

    def _receive_loop(self):
        while True:
            try:
                length_prefix = self.connection.recv(4)
                if not length_prefix:
                    break
                msg_length = int.from_bytes(length_prefix, 'big')
                encrypted_data = b""
                while len(encrypted_data) < msg_length:
                    chunk = self.connection.recv(min(msg_length - len(encrypted_data), 4096))
                    if not chunk:
                        break
                    encrypted_data += chunk
                if not encrypted_data:
                    break
                
                decrypted_data = self.crypto.decrypt_data(encrypted_data)
                msg_type = decrypted_data[0]
                
                if msg_type == 1:
                    self.on_message(decrypted_data[1:].decode('utf-8'))
                elif msg_type == 2:
                    content = decrypted_data[1:]
                    sep_idx = content.find(b'\x00')
                    filename = content[:sep_idx].decode('utf-8')
                    file_data = content[sep_idx+1:]
                    
                    os.makedirs('downloads', exist_ok=True)
                    save_path = os.path.join('downloads', filename)
                    with open(save_path, 'wb') as f:
                        f.write(file_data)
                    
                    self.on_message(f"📎 Файл получен: {filename}")
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
            