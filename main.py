import sys
import os
import asyncio
import tempfile
import uuid
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QTabWidget,
                           QLabel, QComboBox, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import edge_tts
from gtts import gTTS
from docx import Document

class EdgeTTSWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, text, voice_code, output_file=None):
        super().__init__()
        self.text = text
        self.voice_code = voice_code
        self.output_file = output_file
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._speak())
    async def _speak(self):
        communicate = edge_tts.Communicate(self.text, self.voice_code)
        if self.output_file:
            await communicate.save(self.output_file)
            self.finished.emit(self.output_file)
        else:
            temp_file = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.wav")
            await communicate.save(temp_file)
            self.finished.emit(temp_file)

class GttsWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, text, lang, output_file=None):
        super().__init__()
        self.text = text
        self.lang = lang
        self.output_file = output_file
    def run(self):
        tts = gTTS(text=self.text, lang=self.lang)
        if self.output_file:
            tts.save(self.output_file)
            self.finished.emit(self.output_file)
        else:
            temp_file = os.path.join(tempfile.gettempdir(), f"gtts_{uuid.uuid4().hex}.mp3")
            tts.save(temp_file)
            self.finished.emit(temp_file)

class EditTextDialog(QDialog):
    def __init__(self, filename, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chỉnh sửa: {os.path.basename(filename)}")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(text)
        layout.addWidget(self.text_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def get_text(self):
        return self.text_edit.toPlainText()

class TTSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chuyển văn bản thành giọng nói")
        self.setGeometry(100, 100, 1000, 600)
        self.media_player = QMediaPlayer()
        self.current_audio_file = None
        self.is_paused = False
        self.loading_label = None
        self.audio_files = []  # Danh sách các file tạm [{'name':..., 'path':...}]
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        # Bên trái: tabs nhập văn bản
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        tabs = QTabWidget()
        left_layout.addWidget(tabs)
        # Edge TTS tab
        edge_tab = QWidget()
        edge_layout = QVBoxLayout(edge_tab)
        self.text_input = QTextEdit()
        edge_layout.addWidget(QLabel("Nhập văn bản:"))
        edge_layout.addWidget(self.text_input)
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Chọn giọng đọc:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "vi-VN-HoaiMyNeural - Nữ (Nam)",
            "vi-VN-NamMinhNeural - Nam (Nam)"
        ])
        voice_layout.addWidget(self.voice_combo)
        edge_layout.addLayout(voice_layout)
        edge_file_layout = QHBoxLayout()
        self.edge_import_button = QPushButton("Nhập file văn bản")
        self.edge_import_button.clicked.connect(self.import_edge_files)
        edge_file_layout.addWidget(self.edge_import_button)
        edge_layout.addLayout(edge_file_layout)
        button_layout = QHBoxLayout()
        self.speak_button = QPushButton("Đọc thử")
        self.speak_button.clicked.connect(self.speak_edge)
        button_layout.addWidget(self.speak_button)
        edge_layout.addLayout(button_layout)
        edge_tab.setLayout(edge_layout)
        # Google TTS (gtts) tab
        google_tab = QWidget()
        google_layout = QVBoxLayout(google_tab)
        self.gtts_text_input = QTextEdit()
        google_layout.addWidget(QLabel("Nhập văn bản:"))
        google_layout.addWidget(self.gtts_text_input)
        gtts_lang_layout = QHBoxLayout()
        gtts_lang_layout.addWidget(QLabel("Ngôn ngữ:"))
        self.gtts_lang_combo = QComboBox()
        self.gtts_lang_combo.addItems(["vi", "en"])
        gtts_lang_layout.addWidget(self.gtts_lang_combo)
        google_layout.addLayout(gtts_lang_layout)
        gtts_file_layout = QHBoxLayout()
        self.gtts_import_button = QPushButton("Nhập file văn bản")
        self.gtts_import_button.clicked.connect(self.import_gtts_files)
        gtts_file_layout.addWidget(self.gtts_import_button)
        google_layout.addLayout(gtts_file_layout)
        gtts_button_layout = QHBoxLayout()
        self.gtts_speak_button = QPushButton("Đọc thử")
        self.gtts_speak_button.clicked.connect(self.speak_gtts)
        gtts_button_layout.addWidget(self.gtts_speak_button)
        google_layout.addLayout(gtts_button_layout)
        google_tab.setLayout(google_layout)
        tabs.addTab(edge_tab, "Edge TTS")
        tabs.addTab(google_tab, "Google TTS (gtts)")
        # Loading label
        self.loading_label = QLabel("")
        self.loading_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.loading_label)
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 2)
        # Bên phải: danh sách file âm thanh tạm và các nút thao tác
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Danh sách file âm thanh tạm:"))
        self.audio_list = QListWidget()
        self.audio_list.itemSelectionChanged.connect(self.on_audio_selected)
        right_layout.addWidget(self.audio_list)
        audio_btn_layout = QHBoxLayout()
        self.play_button = QPushButton("Phát")
        self.play_button.clicked.connect(self.play_or_pause_audio)
        self.save_button = QPushButton("Lưu file âm thanh")
        self.save_button.clicked.connect(self.save_selected_audio)
        self.delete_button = QPushButton("Xóa file tạm")
        self.delete_button.clicked.connect(self.delete_selected_audio)
        audio_btn_layout.addWidget(self.play_button)
        audio_btn_layout.addWidget(self.save_button)
        audio_btn_layout.addWidget(self.delete_button)
        right_layout.addLayout(audio_btn_layout)
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)

    def add_audio_file(self, name, path):
        self.audio_files.append({'name': name, 'path': path})
        self.audio_list.addItem(name)
        self.audio_list.setCurrentRow(self.audio_list.count()-1)

    def on_audio_selected(self):
        idx = self.audio_list.currentRow()
        if idx >= 0 and idx < len(self.audio_files):
            self.current_audio_file = self.audio_files[idx]['path']
        # Reset nút về 'Phát' khi chọn file khác
        self.play_button.setText("Phát")
        self.is_paused = False

    def play_or_pause_audio(self):
        if not self.current_audio_file:
            return
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.is_paused = True
            self.play_button.setText("Phát")
        else:
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_audio_file)))
            self.media_player.play()
            self.is_paused = False
            self.play_button.setText("Tạm dừng")

    def save_selected_audio(self):
        idx = self.audio_list.currentRow()
        if idx >= 0 and idx < len(self.audio_files):
            audio = self.audio_files[idx]
            ext = os.path.splitext(audio['path'])[1]
            file_path, _ = QFileDialog.getSaveFileName(self, "Lưu file âm thanh", audio['name']+ext, f"*{ext}")
            if file_path:
                try:
                    with open(audio['path'], 'rb') as src, open(file_path, 'wb') as dst:
                        dst.write(src.read())
                except Exception as e:
                    QMessageBox.warning(self, "Lỗi", f"Không thể lưu file: {e}")

    def delete_selected_audio(self):
        idx = self.audio_list.currentRow()
        if idx >= 0 and idx < len(self.audio_files):
            audio = self.audio_files.pop(idx)
            try:
                os.remove(audio['path'])
            except Exception:
                pass
            self.audio_list.takeItem(idx)
            if self.audio_files:
                self.audio_list.setCurrentRow(0)
            else:
                self.current_audio_file = None

    def import_edge_files(self):
        self.import_files(is_edge=True)
    def import_gtts_files(self):
        self.import_files(is_edge=False)
    def import_files(self, is_edge):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn file văn bản", "", "Text files (*.txt *.docx)")
        if not files:
            return
        for file in files:
            text = self.read_text_file(file)
            dlg = EditTextDialog(file, text, self)
            if dlg.exec_() == QDialog.Accepted:
                edited_text = dlg.get_text()
                if is_edge:
                    self.process_edge_file(file, edited_text)
                else:
                    self.process_gtts_file(file, edited_text)
    def read_text_file(self, file):
        if file.lower().endswith('.txt'):
            with open(file, 'r', encoding='utf-8') as f:
                return f.read()
        elif file.lower().endswith('.docx'):
            doc = Document(file)
            return '\n'.join([p.text for p in doc.paragraphs])
        return ""
    def process_edge_file(self, file, text):
        voice_code = self.voice_combo.currentText().split(' ')[0]
        self.show_loading(True)
        self.edge_worker = EdgeTTSWorker(text, voice_code)
        self.edge_worker.finished.connect(lambda temp_path: self.on_edge_file_ready(temp_path, file))
        self.edge_worker.start()

    def on_edge_file_ready(self, temp_path, file):
        self.show_loading(False)
        name = os.path.basename(file) + " (Edge)"
        self.add_audio_file(name, temp_path)
        self.play_audio()

    def process_gtts_file(self, file, text):
        lang = self.gtts_lang_combo.currentText()
        self.show_loading(True)
        self.gtts_worker = GttsWorker(text, lang)
        self.gtts_worker.finished.connect(lambda temp_path: self.on_gtts_file_ready(temp_path, file))
        self.gtts_worker.start()

    def on_gtts_file_ready(self, temp_path, file):
        self.show_loading(False)
        name = os.path.basename(file) + " (Google)"
        self.add_audio_file(name, temp_path)
        self.play_audio()

    def show_loading(self, show=True):
        if show:
            self.loading_label.setText("Đang xử lý, vui lòng chờ...")
        else:
            self.loading_label.setText("")

    def speak_edge(self):
        text = self.text_input.toPlainText()
        if not text:
            return
        voice_code = self.voice_combo.currentText().split(' ')[0]
        self.show_loading(True)
        self.edge_worker = EdgeTTSWorker(text, voice_code)
        self.edge_worker.finished.connect(self.on_edge_tts_finished)
        self.edge_worker.start()

    def on_edge_tts_finished(self, file_path):
        self.current_audio_file = file_path
        self.show_loading(False)
        self.play_audio()

    def speak_gtts(self):
        text = self.gtts_text_input.toPlainText()
        lang = self.gtts_lang_combo.currentText()
        if not text:
            return
        self.show_loading(True)
        self.gtts_worker = GttsWorker(text, lang)
        self.gtts_worker.finished.connect(self.on_gtts_finished)
        self.gtts_worker.start()

    def on_gtts_finished(self, file_path):
        self.current_audio_file = file_path
        self.show_loading(False)
        self.play_audio()

    def play_audio(self):
        if self.current_audio_file:
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_audio_file)))
            self.media_player.play()
            self.is_paused = False
            self.play_button.setText("Tạm dừng")

    def pause_or_resume_audio(self):
        # Không còn dùng nữa, giữ lại cho tương thích nếu gọi từ nơi khác
        self.play_or_pause_audio()

    def stop_and_clear(self):
        self.media_player.stop()
        if self.current_audio_file and self.current_audio_file.endswith('.mp3'):
            reply = QMessageBox.question(self, 'Lưu file?',
                                         'Bạn có muốn lưu file mp3 vừa tạo không?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Lưu file âm thanh", "", "MP3 Files (*.mp3)")
                if file_path:
                    try:
                        with open(self.current_audio_file, 'rb') as src, open(file_path, 'wb') as dst:
                            dst.write(src.read())
                    except Exception as e:
                        QMessageBox.warning(self, "Lỗi", f"Không thể lưu file: {e}")
        self.text_input.clear()
        self.gtts_text_input.clear()
        self.current_audio_file = None
        self.is_paused = False
        self.play_button.setText("Phát")
        self.show_loading(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TTSApp()
    window.show()
    sys.exit(app.exec_()) 