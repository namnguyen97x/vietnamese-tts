import sys
import os
import asyncio
import tempfile
import uuid
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QTabWidget,
                           QLabel, QComboBox, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import edge_tts
from gtts import gTTS
from docx import Document
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
import subprocess
import sounddevice as sd
import numpy
import wave

# Thêm ./bin vào PATH để pydub và subprocess luôn tìm thấy ffmpeg/ffprobe
if hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(sys.executable))
bin_dir = os.path.join(base_dir, 'bin')
os.environ["PATH"] += os.pathsep + bin_dir
ffmpeg_path = os.path.join(bin_dir, 'ffmpeg.exe')
ffprobe_path = os.path.join(bin_dir, 'ffprobe.exe')
print("[DEBUG] ffmpeg_path:", ffmpeg_path)
print("[DEBUG] ffprobe_path:", ffprobe_path)
if os.path.exists(ffmpeg_path):
    print(f"[INFO] Đã tìm thấy ffmpeg tại: {ffmpeg_path}")
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
else:
    print(f"[WARNING] Không tìm thấy ffmpeg tại: {ffmpeg_path}. Hãy kiểm tra lại tên file và vị trí!")
if os.path.exists(ffprobe_path):
    print(f"[INFO] Đã tìm thấy ffprobe tại: {ffprobe_path}")
    AudioSegment.ffprobe = ffprobe_path
else:
    print(f"[WARNING] Không tìm thấy ffprobe tại: {ffprobe_path}. Hãy kiểm tra lại tên file và vị trí!")

# --- LẤY DANH SÁCH GIỌNG ĐỌC KHẢ DỤNG ---
def get_available_voices():
    """
    Lấy danh sách voice khả dụng từ edge-tts, chỉ giữ lại tiếng Việt và Multilingual.
    """
    url = "https://eastus.tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy danh sách voice: {resp.status_code} - {resp.text}")
    voices = resp.json()
    filtered = {}
    for v in voices:
        # Tiếng Việt
        if v["Locale"] == "vi-VN":
            filtered[v["ShortName"]] = f"{v['LocalName']} ({'Nữ' if v['Gender']=='Female' else 'Nam'} - Tiếng Việt)"
        # Multilingual
        elif "MultilingualNeural" in v["ShortName"]:
            lang = v["Locale"]
            name = v["LocalName"]
            gender = "Nữ" if v["Gender"] == "Female" else "Nam"
            filtered[v["ShortName"]] = f"{name} ({gender} - {lang}, Đa ngôn ngữ)"
    return filtered

# Danh sách giọng đọc mặc định nếu không lấy được từ API
VOICE_LIST = {
    "vi-VN-HoaiMyNeural": "Hoài My (Nữ - Tiếng Việt)",
    "vi-VN-NamMinhNeural": "Nam Minh (Nam - Tiếng Việt)",
    "de-DE-FlorianMultilingualNeural": "Florian (Nam - Đa ngôn ngữ)",
    "de-DE-SeraphinaMultilingualNeural": "Seraphina (Nữ - Đa ngôn ngữ)",
    "en-US-AndrewMultilingualNeural": "Andrew (Nam - Đa ngôn ngữ)",
    "en-US-AvaMultilingualNeural": "Ava (Nữ - Đa ngôn ngữ)",
    "en-US-BrianMultilingualNeural": "Brian (Nam - Đa ngôn ngữ)",
    "en-US-EmmaMultilingualNeural": "Emma (Nữ - Đa ngôn ngữ)",
    "fr-FR-RemyMultilingualNeural": "Remy (Nam - Đa ngôn ngữ)",
    "fr-FR-VivienneMultilingualNeural": "Vivienne (Nữ - Đa ngôn ngữ)",
    "it-IT-GiuseppeMultilingualNeural": "Giuseppe (Nam - Đa ngôn ngữ)",
    "ko-KR-HyunsuMultilingualNeural": "Hyunsu (Nam - Đa ngôn ngữ)",
    "pt-BR-ThalitaMultilingualNeural": "Thalita (Nữ - Đa ngôn ngữ)",
}

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

class MicrophoneWorker(QThread):
    result = pyqtSignal(str)
    error = pyqtSignal(str)
    listening = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._audio_file = None
        self._stream = None
        self._frames = []
        self._samplerate = 16000
        self._channels = 1
        self._dtype = 'int16'
    def run(self):
        self._running = True
        self.listening.emit(True)
        self._frames = []
        try:
            def callback(indata, frames, time, status):
                if not self._running:
                    raise sd.CallbackStop()
                self._frames.append(indata.copy())
            with sd.InputStream(samplerate=self._samplerate, channels=self._channels, dtype=self._dtype, callback=callback):
                while self._running:
                    sd.sleep(100)
            # Lưu file wav tạm
            self._audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wf = wave.open(self._audio_file.name, 'wb')
            wf.setnchannels(self._channels)
            wf.setsampwidth(np.dtype(self._dtype).itemsize)
            wf.setframerate(self._samplerate)
            wf.writeframes(b''.join([f.tobytes() for f in self._frames]))
            wf.close()
            self.listening.emit(False)
            # Nhận diện bằng speech_recognition
            recognizer = sr.Recognizer()
            with sr.AudioFile(self._audio_file.name) as source:
                audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio, language='vi-VN')
                self.result.emit(text)
            except Exception as e:
                self.error.emit(f"Lỗi nhận diện: {e}")
        except Exception as e:
            self.listening.emit(False)
            self.error.emit(f"Lỗi ghi âm: {e}")
    def stop(self):
        self._running = False
        # Không cần terminate, callback sẽ tự dừng

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
        try:
            # Thử lấy danh sách giọng đọc từ API
            voices = get_available_voices()
            self.voice_combo.addItems([f"{code} - {name}" for code, name in voices.items()])
        except Exception:
            # Nếu không lấy được thì dùng danh sách mặc định
            self.voice_combo.addItems([f"{code} - {name}" for code, name in VOICE_LIST.items()])
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
        # Thêm tab Speech to Text (STT)
        stt_tab = QWidget()
        stt_layout = QVBoxLayout(stt_tab)
        self.stt_result = QTextEdit()
        self.stt_result.setPlaceholderText("Kết quả nhận diện sẽ hiển thị ở đây...")
        stt_layout.addWidget(self.stt_result)
        stt_btn_layout = QHBoxLayout()
        self.stt_file_btn = QPushButton("Nhận diện từ file âm thanh")
        self.stt_file_btn.clicked.connect(self.stt_from_file)
        stt_btn_layout.addWidget(self.stt_file_btn)
        self.stt_mic_start_btn = QPushButton("Bắt đầu ghi")
        self.stt_mic_start_btn.clicked.connect(self.start_mic_recording)
        stt_btn_layout.addWidget(self.stt_mic_start_btn)
        self.stt_mic_stop_btn = QPushButton("Dừng ghi")
        self.stt_mic_stop_btn.clicked.connect(self.stop_mic_recording)
        self.stt_mic_stop_btn.setEnabled(False)
        stt_btn_layout.addWidget(self.stt_mic_stop_btn)
        stt_layout.addLayout(stt_btn_layout)
        self.stt_countdown_label = QLabel("")
        font = self.stt_countdown_label.font()
        font.setPointSize(36)
        font.setBold(True)
        self.stt_countdown_label.setFont(font)
        self.stt_countdown_label.setAlignment(Qt.AlignCenter)
        stt_layout.addWidget(self.stt_countdown_label)
        # Nút lưu văn bản
        self.stt_save_btn = QPushButton("Lưu văn bản...")
        self.stt_save_btn.clicked.connect(self.save_stt_text)
        stt_layout.addWidget(self.stt_save_btn)
        stt_tab.setLayout(stt_layout)
        tabs.addTab(stt_tab, "Speech to Text (STT)")
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
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "Lưu file âm thanh", audio['name']+ext,
                "WAV (*.wav);;MP3 (*.mp3);;OGG (*.ogg);;FLAC (*.flac)")
            if file_path:
                try:
                    from pydub import AudioSegment
                    # Xác định định dạng đích
                    if selected_filter == 'WAV (*.wav)' or file_path.endswith('.wav'):
                        with open(audio['path'], 'rb') as src, open(file_path, 'wb') as dst:
                            dst.write(src.read())
                    else:
                        # Chuyển đổi sang định dạng khác bằng pydub
                        sound = AudioSegment.from_file(audio['path'])
                        if selected_filter == 'MP3 (*.mp3)' or file_path.endswith('.mp3'):
                            sound.export(file_path, format='mp3')
                        elif selected_filter == 'OGG (*.ogg)' or file_path.endswith('.ogg'):
                            sound.export(file_path, format='ogg')
                        elif selected_filter == 'FLAC (*.flac)' or file_path.endswith('.flac'):
                            sound.export(file_path, format='flac')
                        else:
                            raise Exception('Định dạng không hỗ trợ!')
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
        voice_code = self.voice_combo.currentText().split(' - ')[0]  # Lấy mã giọng đọc từ combobox
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
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập văn bản cần đọc.")
            return
        voice_code = self.voice_combo.currentText().split(' - ')[0]  # Lấy mã giọng đọc từ combobox
        self.show_loading(True)
        self.edge_worker = EdgeTTSWorker(text, voice_code)
        self.edge_worker.finished.connect(self.on_edge_tts_finished)
        self.edge_worker.start()

    def on_edge_tts_finished(self, file_path):
        self.current_audio_file = file_path
        self.show_loading(False)
        # Thêm file tạm vào danh sách
        name = f"TTS_{os.path.basename(file_path)}"
        self.add_audio_file(name, file_path)
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
        # Thêm file tạm vào danh sách
        name = f"TTS_{os.path.basename(file_path)}"
        self.add_audio_file(name, file_path)
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

    def stt_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file âm thanh", "", "Audio Files (*.wav *.mp3 *.flac *.aiff *.ogg)")
        if not file_path:
            return
        recognizer = sr.Recognizer()
        temp_wav = None
        try:
            print(f"[DEBUG] Đang chuyển đổi file: {file_path}")
            # Luôn chuyển sang wav tạm PCM 16-bit mono 16kHz
            try:
                audio = AudioSegment.from_file(file_path)
                tmp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                audio.export(tmp_wav.name, format='wav', parameters=['-acodec', 'pcm_s16le', '-ac', '1'])
                tmp_wav.close()
                temp_wav = tmp_wav.name
                file_path = temp_wav
                print(f"[DEBUG] File wav tạm (pydub): {file_path}")
            except Exception as e:
                print(f"[WARNING] Pydub lỗi: {e}, thử chuyển bằng ffmpeg trực tiếp...")
                tmp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                tmp_wav.close()
                cmd = [ffmpeg_path, '-y', '-i', file_path, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', tmp_wav.name]
                print("[DEBUG] CMD:", cmd)
                subprocess.run(cmd, check=True)
                temp_wav = tmp_wav.name
                file_path = temp_wav
                print(f"[DEBUG] File wav tạm (ffmpeg): {file_path}")
        except Exception as e:
            self.stt_result.setPlainText(f"Lỗi chuyển đổi file: {e}")
            return
        try:
            with sr.AudioFile(file_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language='vi-VN')
            self.stt_result.setPlainText(text)
        except Exception as e:
            self.stt_result.setPlainText(f"Lỗi nhận diện: {e}")
        finally:
            if temp_wav and os.path.exists(temp_wav):
                os.remove(temp_wav)

    def start_mic_recording(self):
        self.stt_result.setPlainText("")
        self.stt_countdown_label.setText("")
        self.stt_mic_start_btn.setEnabled(False)
        self.stt_mic_stop_btn.setEnabled(False)
        self._countdown = 3
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_countdown)
        self._update_countdown()
        self._timer.start(1000)

    def _update_countdown(self):
        if self._countdown > 0:
            self.stt_countdown_label.setText(str(self._countdown))
            self._countdown -= 1
        else:
            self.stt_countdown_label.setText("")
            self._timer.stop()
            self._start_mic_worker()

    def _start_mic_worker(self):
        self.stt_result.setPlainText("Đang nghe... Nhấn 'Dừng ghi' để kết thúc.")
        self.stt_mic_start_btn.setEnabled(False)
        self.stt_mic_stop_btn.setEnabled(True)
        self.mic_worker = MicrophoneWorker()
        self.mic_worker.result.connect(self.on_mic_result)
        self.mic_worker.error.connect(self.on_mic_error)
        self.mic_worker.listening.connect(self.on_mic_listening)
        self.mic_worker.start()

    def stop_mic_recording(self):
        if hasattr(self, 'mic_worker') and self.mic_worker.isRunning():
            self.mic_worker.stop()
            self.stt_result.append("\nĐang xử lý...")
        self.stt_mic_start_btn.setEnabled(True)
        self.stt_mic_stop_btn.setEnabled(False)

    def on_mic_result(self, text):
        self.stt_result.setPlainText(text)
        self.stt_mic_start_btn.setEnabled(True)
        self.stt_mic_stop_btn.setEnabled(False)

    def on_mic_error(self, msg):
        self.stt_result.setPlainText(msg)
        self.stt_mic_start_btn.setEnabled(True)
        self.stt_mic_stop_btn.setEnabled(False)

    def on_mic_listening(self, listening):
        if listening:
            self.stt_result.setPlainText("Đang nghe... Nhấn 'Dừng ghi' để kết thúc.")
        else:
            self.stt_result.append("\nĐang xử lý...")

    def save_stt_text(self):
        text = self.stt_result.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Cảnh báo", "Không có văn bản để lưu!")
            return
        file_path, ext = QFileDialog.getSaveFileName(self, "Lưu văn bản", "stt_result", "Text file (*.txt);;Word file (*.docx)")
        if not file_path:
            return
        if ext == 'Text file (*.txt)' or file_path.endswith('.txt'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
        elif ext == 'Word file (*.docx)' or file_path.endswith('.docx'):
            from docx import Document
            doc = Document()
            for line in text.splitlines():
                doc.add_paragraph(line)
            doc.save(file_path)
        else:
            QMessageBox.warning(self, "Lỗi", "Định dạng file không hỗ trợ!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TTSApp()
    window.show()
    sys.exit(app.exec_()) 