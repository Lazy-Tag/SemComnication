import socket
import pickle
import struct
import numpy as np
import cv2

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QImage

class SocketCommunicator(QObject):
    log_text_signal = pyqtSignal(str)
    update_text_signal = pyqtSignal(str)
    change_pixmap_signal = pyqtSignal(QImage)

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
                self.log_text_signal.emit(f"[ERROR] {e}\n")
                self.close_connection()
        else:
            self.log_text_signal.emit(f"[INFO] Not Connected!\n")

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
                    if isinstance(deserialized_data, str) and deserialized_data.startswith("Text:"):
                        text_data = deserialized_data[len("Text:"):]
                        self.update_text_signal.emit(f"[TEXT] Received text: {text_data}\n")
                    elif isinstance(deserialized_data, bytes) and deserialized_data.startswith(b"Image:"):
                        image_data = deserialized_data[len("Image:"):]
                        self.update_text_signal.emit(
                            f"[IMAGE] Received image data of length: {len(image_data)} bytes\n")
                        nparr = np.frombuffer(image_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = rgb_image.shape
                            bytes_per_line = ch * w
                            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                            scaled_image = qt_image.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
                            self.change_pixmap_signal.emit(scaled_image)
                    else:
                        self.update_text_signal.emit(f"[UNKNOWN] Received unknown data type\n")
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

