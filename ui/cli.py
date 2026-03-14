import sys
from core.i18n import _

class CommandLineInterface:
    def __init__(self):
        self.network = None

    def set_network(self, network_node):
        self.network = network_node

    def show_system_message(self, text):
        sys.stdout.write(f"\n[*] {text}\n")
        sys.stdout.flush()

    def show_error(self, text):
        sys.stdout.write(f"\n[-] {text}\n")
        sys.stdout.flush()

    def show_incoming_message(self, text):
        sys.stdout.write(f"\n{_.t('msg_peer', text=text)}\n")
        sys.stdout.flush()

    def handle_connection_change(self, is_connected, address):
        if is_connected:
            ip_port = address.split(':')
            self.show_system_message(_.t('sys_connected', ip=ip_port[0], port=ip_port[1]))
            self.show_system_message(_.t('sys_can_type'))
        else:
            self.show_error(_.t('sys_disconnected'))

    def start_input_loop(self):
        while True:
            try:
                command = input().strip()
                if not command:
                    continue

                if command.startswith("/connect"):
                    parts = command.split()
                    if len(parts) == 3:
                        ip, port = parts[1], int(parts[2])
                        result = self.network.connect_to(ip, port)
                        if not result:
                            self.show_error(_.t('err_connection_failed', error=""))
                    else:
                        self.show_system_message(_.t('err_cmd_usage'))
                else:
                    if self.network and self.network.connection:
                        success = self.network.send_message(command)
                        if not success:
                            self.show_error(_.t('err_connection_failed', error=""))
                    else:
                        self.show_error(_.t('err_not_connected'))
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.show_error(str(e))
                