from config import HOST
from core.network import NetworkNode
from ui.gui import MessengerGUI
from core.i18n import _

def main():
    try:
        my_port = int(input(_.t('prompt_port')))
    except ValueError:
        return

    app = MessengerGUI(my_port)
    
    node = NetworkNode(
        host=HOST,
        port=my_port,
        on_message=app.show_incoming_message,
        on_status=app.handle_connection_change
    )
    
    app.set_network(node)
    node.start_listening()
    app.mainloop()

if __name__ == "__main__":
    main()
    