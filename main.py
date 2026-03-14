import sys
try:
    import readline  # Чинит работу Backspace и стрелочек в консоли Linux/macOS
except ImportError:
    pass

from config import HOST
from core.network import NetworkNode
from ui.gui import MessengerGUI
from core.i18n import _

def main():
    try:
        my_port = int(input(_.t('prompt_port')))
        my_username = input("Введите ваш никнейм: ").strip() or "User"
    except ValueError:
        return

    app = MessengerGUI(my_port, my_username)
    
    node = NetworkNode(
        host=HOST,
        port=my_port,
        username=my_username,
        on_message=app.show_incoming_message,
        on_status=app.handle_connection_change,
        on_peer_name=app.update_peer_name
    )
    
    app.set_network(node)
    node.start_listening()
    app.mainloop()

if __name__ == "__main__":
    main()
    