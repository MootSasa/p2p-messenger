from config import HOST
from core.network import NetworkNode
from ui.cli import CommandLineInterface
from core.i18n import _

def main():
    try:
        my_port = int(input(_.t('prompt_port')))
    except ValueError:
        return

    ui = CommandLineInterface()
    
    node = NetworkNode(
        host=HOST,
        port=my_port,
        on_message=ui.show_incoming_message,
        on_status=ui.handle_connection_change
    )
    
    ui.set_network(node)
    
    ui.show_system_message(_.t('sys_node_started', port=my_port))
    node.start_listening()
    ui.start_input_loop()

if __name__ == "__main__":
    main()
    