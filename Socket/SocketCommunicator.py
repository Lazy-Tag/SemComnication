import socket
import pickle
import struct
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

class SocketCommunicator(QObject):
    log_text_signal = pyqtSignal(str)
    update_text_signal = pyqtSignal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.addr = None
        self.listening = False

    def start_server(self):
        if self.listening or self.conn:
            if self.listening:
                self.log_text_signal.emit(f"[INFO] Listening on {self.host}:{self.port}...\n")
            else:
                self.log_text_signal.emit(f"[INFO] Connected!\n")
            return False

        if self.sock.fileno() == -1:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        self.listening = True

        self.log_text_signal.emit(f"[INFO] Listening on {self.host}:{self.port}...\n")
        self.conn, self.addr = self.sock.accept()
        self.listening = False
        self.log_text_signal.emit(f"[INFO] Connected by {self.addr}\n")

        self.receive_data()
        return True

    def start_client(self):
        if self.listening or self.conn:
            if self.listening:
                self.log_text_signal.emit(f"[INFO] Listening on {self.host}:{self.port}...\n")
            else:
                self.log_text_signal.emit(f"[INFO] Connected!\n")
            return

        self.log_text_signal.emit(f"[INFO] Connect {self.host}:{self.port}\n")
        try:
            self.sock.connect((self.host, self.port))
        except socket.error as e:
            self.log_text_signal.emit(f"[ERROR] Connection failed: {e}\n")
            return False
        self.conn = self.sock
        self.receive_data()

    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        data_length = struct.pack('!I', len(serialized_data))
        if self.conn:
            try:
                self.conn.sendall(data_length + serialized_data)
            except socket.error as e:
                self.log_text_signal.emit(f"[ERROR] Error sending data: {e}\n")
                self.close_connection()

    def receive_data(self):
        while self.conn:
            try:
                data_length = self.recvall(4)
                if not data_length:
                    break
                data_length = struct.unpack('!I', data_length)[0]
                data = self.recvall(data_length)
                if data:
                    deserialized_data = pickle.loads(data)
                    self.update_text_signal.emit(f"[DATA] Received data: {deserialized_data}\n")
            except Exception as e:
                self.log_text_signal.emit(f"[ERROR] {e}\n")
                break

    def recvall(self, n):
        data = b''
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def close_connection(self):
        self.log_text_signal.emit(f"[INFO] Connection is closed.\n")
        if self.conn:
            self.conn.close()
            self.conn = None
        else:
            return
        self.sock.close()

