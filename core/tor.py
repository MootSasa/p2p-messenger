import socket
import tempfile
from stem.process import launch_tor_with_config
from stem.control import Controller

class TorManager:
    def __init__(self, local_port):
        self.local_port = local_port
        self.control_port = self._get_free_port()
        self.socks_port = self._get_free_port()
        self.tor_process = None
        self.controller = None
        self.onion_address = None
        self.data_dir = tempfile.mkdtemp()

    def _get_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def start(self) -> str:
        self.tor_process = launch_tor_with_config(
            config={
                'SocksPort': str(self.socks_port),
                'ControlPort': str(self.control_port),
                'DataDirectory': self.data_dir,
            },
            take_ownership=True
        )
        self.controller = Controller.from_port(port=self.control_port)
        self.controller.authenticate()
        response = self.controller.create_ephemeral_hidden_service(
            {80: self.local_port},
            await_publication=True
        )
        self.onion_address = f"{response.service_id}.onion"
        return self.onion_address

    def stop(self):
        if self.controller:
            self.controller.close()
        if self.tor_process:
            self.tor_process.terminate()
            