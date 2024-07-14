from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QPixmap, QTextCursor
from Video.VideoThread import VideoThread
from Audio.AudioThread import AudioThread

from Socket.SocketCommunicator import SocketCommunicator
from Socket.ServerThread import ServerThread
from Socket.ClientThread import ClientThread

class App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载.ui文件
        uic.loadUi('UI\\App.ui', self)

        # 确保 image_label 是在 UI Designer 中 QLabel 的 objectName
        self.image_label = self.findChild(QtWidgets.QLabel, 'label')
        self.text_edit = self.findChild(QtWidgets.QTextEdit, 'textEdit')
        self.log_edit = self.findChild(QtWidgets.QTextEdit, 'LogText')
        self.call_button = self.findChild(QtWidgets.QPushButton, 'CallButton')
        self.answer_button = self.findChild(QtWidgets.QPushButton, 'AnswerButton')
        self.stop_button = self.findChild(QtWidgets.QPushButton, 'StopButton')

        self.socket_comm = SocketCommunicator('localhost', 12345)
        self.socket_comm.log_text_signal.connect(self.update_log)
        self.socket_comm.update_text_signal.connect(self.update_text)

        # 设置线程和信号连接
        self.video_thread = VideoThread()
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()

        self.audio_thread = AudioThread(self.socket_comm)
        self.audio_thread.start()

        self.call_button.clicked.connect(self.CallButtonClicked)
        self.answer_button.clicked.connect(self.AnswerButtonClicked)
        self.stop_button.clicked.connect(self.StopButtonClicked)

    def update_image(self, cv_img):
        # 转换 QImage 到 QPixmap 并更新 QLabel
        pixmap = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(pixmap)

    def update_text(self, text):
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        self.text_edit.insertPlainText(text)

    def update_log(self, text):
        self.log_edit.moveCursor(QTextCursor.MoveOperation.End)
        self.log_edit.insertPlainText(text)

    def CallButtonClicked(self):
        self.server_thread = ServerThread(self.socket_comm)
        self.server_thread.start()

    def AnswerButtonClicked(self):
        self.server_thread = ClientThread(self.socket_comm)
        self.server_thread.start()

    def StopButtonClicked(self):
        self.socket_comm.send_data(f'\n[INFO] The other party disconnected\n');
        exit(0)

    def closeEvent(self, event):
        self.video_thread.quit()
        self.video_thread.wait()
        self.audio_thread.quit()
