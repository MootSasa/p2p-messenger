import customtkinter as ctk
from tkinter import filedialog
from core.i18n import _

class MessengerGUI(ctk.CTk):
    def __init__(self, listen_port):
        super().__init__()
        self.network = None
        self.listen_port = listen_port
        
        self.title("P2P Messenger")
        self.geometry("700x500")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)
        
        self.status_label = ctk.CTkLabel(self.top_frame, text=_.t('sys_node_started', port=self.listen_port))
        self.status_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.ip_entry = ctk.CTkEntry(self.top_frame, placeholder_text="IP (e.g. 127.0.0.1)")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=10, sticky="e")
        
        self.port_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Port", width=60)
        self.port_entry.grid(row=0, column=2, padx=5, pady=10, sticky="e")
        
        self.connect_btn = ctk.CTkButton(self.top_frame, text="Connect", command=self.connect_peer, width=80)
        self.connect_btn.grid(row=0, column=3, padx=10, pady=10, sticky="e")
        
        self.chat_box = ctk.CTkTextbox(self, state="disabled")
        self.chat_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        
        self.msg_entry = ctk.CTkEntry(self.bottom_frame, placeholder_text="Type a message...")
        self.msg_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        
        self.file_btn = ctk.CTkButton(self.bottom_frame, text="📁", command=self.send_file, width=40)
        self.file_btn.grid(row=0, column=1, padx=(0, 5), pady=10)

        self.send_btn = ctk.CTkButton(self.bottom_frame, text="Send", command=self.send_message, width=80)
        self.send_btn.grid(row=0, column=2, padx=(5, 10), pady=10)

    def set_network(self, network_node):
        self.network = network_node

    def append_chat(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text + "\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.yview("end")

    def show_system_message(self, text):
        self.after(0, self.append_chat, f"[*] {text}")

    def show_error(self, text):
        self.after(0, self.append_chat, f"[-] {text}")

    def show_incoming_message(self, text):
        self.after(0, self.append_chat, _.t('msg_peer', text=text))

    def handle_connection_change(self, is_connected, address):
        def update_ui():
            if is_connected:
                self.status_label.configure(text=_.t('sys_connected', address=address), text_color="green")
                self.show_system_message(_.t('sys_can_type'))
            else:
                self.status_label.configure(text=_.t('sys_node_started', port=self.listen_port), text_color="gray")
                self.show_error(_.t('sys_disconnected'))
        self.after(0, update_ui)

    def connect_peer(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        if ip and port.isdigit():
            self.show_system_message(f"Connecting to {ip}:{port}...")
            result = self.network.connect_to(ip, int(port))
            if not result:
                self.show_error(_.t('err_connection_failed', error=""))

    def send_message(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        if self.network and self.network.connection:
            success = self.network.send_message(text)
            if success:
                self.append_chat(f"[You]: {text}")
                self.msg_entry.delete(0, "end")
            else:
                self.show_error(_.t('err_connection_failed', error=""))
        else:
            self.show_error(_.t('err_not_connected'))

    def send_file(self):
        if not (self.network and self.network.connection):
            self.show_error(_.t('err_not_connected'))
            return
            
        filepath = filedialog.askopenfilename()
        if filepath:
            filename = filepath.split('/')[-1]
            self.show_system_message(f"Отправка файла {filename}...")
            success = self.network.send_file(filepath)
            if success:
                self.append_chat(f"[You]: 📎 Отправлен файл {filename}")
            else:
                self.show_error("Ошибка при отправке файла.")
