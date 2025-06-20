# Vietnamese TTS Application

Ứng dụng Text-to-Speech tiếng Việt với nhiều tính năng mạnh mẽ.

## Tính năng chính

### 1. Text-to-Speech (TTS)
- **Edge TTS**: Sử dụng Microsoft Edge TTS với giọng đọc tiếng Việt chất lượng cao
- **Google TTS**: Sử dụng Google Text-to-Speech với nhiều ngôn ngữ
- Hỗ trợ nhập file văn bản (.txt, .docx)
- Lưu file âm thanh với nhiều định dạng (WAV, MP3, OGG, FLAC)

### 2. Speech-to-Text (STT)
- Nhận diện giọng nói từ file âm thanh
- Ghi âm trực tiếp từ microphone
- Hỗ trợ nhiều định dạng âm thanh
- Lưu kết quả nhận diện thành file văn bản

### 3. Tích hợp Gemini AI
- **Trình duyệt nhúng**: Tích hợp trực tiếp trang web Gemini AI vào ứng dụng.
- **Đăng nhập bằng Cookie**: Hỗ trợ đăng nhập vào tài khoản Google của bạn một cách an toàn thông qua việc nhập cookie, không cần lưu mật khẩu.
- **Sao chép vào TTS**: Dễ dàng lấy nội dung trả lời mới nhất của AI và chuyển sang tab Edge TTS để chuyển đổi thành giọng nói.
- **Điều hướng**: Cung cấp các nút điều hướng cơ bản (Làm mới, Quay lại, Tiến tới).

## Cài đặt

### Cách 1: Sử dụng script tự động (Khuyến nghị)
1. Chạy file `install.bat` để cài đặt tự động
2. Chạy file `run.bat` để khởi động ứng dụng

### Cách 2: Cài đặt thủ công
1. Cài đặt Python 3.7+
2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Sử dụng

### Chạy ứng dụng:
```bash
python main.py
```
Hoặc chạy file `run.bat`

### Hướng dẫn sử dụng Gemini AI

Để sử dụng đầy đủ tính năng của Gemini, bạn cần đăng nhập vào tài khoản Google của mình. Ứng dụng hỗ trợ một phương thức đăng nhập an toàn bằng cách nhập cookie đã được xuất từ trình duyệt chính của bạn.

**Bước 1: Lấy file cookie từ trình duyệt**

1.  Mở trình duyệt bạn hay dùng để đăng nhập Google (ví dụ: Chrome, Edge, Firefox).
2.  Cài đặt một tiện ích (extension) có chức năng xuất cookie. **Cookie-Editor** là một lựa chọn phổ biến và dễ sử dụng:
    *   [Cookie-Editor cho Chrome/Edge](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
    *   [Cookie-Editor cho Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/)
3.  Truy cập vào trang [https://gemini.google.com](https://gemini.google.com) và đảm bảo bạn đã đăng nhập.
4.  Nhấn vào biểu tượng của tiện ích **Cookie-Editor** trên thanh công cụ của trình duyệt.
5.  Tìm và nhấn nút **"Export"** (Xuất).
6.  Trong menu xuất hiện, chọn định dạng **"Export as JSON"**. Một file có tên `cookies.json` sẽ được tải về máy.

**Bước 2: Nhập cookie vào ứng dụng**

1.  Chuyển sang tab **"Gemini AI"** trong ứng dụng.
2.  Nhấn vào nút **"🍪 Nhập Cookie"**.
3.  Một cửa sổ sẽ hiện ra, bạn hãy tìm và chọn file `cookies.json` mà bạn vừa tải về ở Bước 1.
4.  Ứng dụng sẽ tự động nhập cookie và tải lại trang. Nếu thành công, bạn sẽ thấy giao diện Gemini đã đăng nhập.

**Bước 3: Sử dụng các tính năng**

- Sau khi trò chuyện với AI, nhấn nút **"Sao chép vào TTS"** để tự động lấy câu trả lời cuối cùng và điền vào ô văn bản của tab "Edge TTS".

## Cấu trúc thư mục

```
vietnamese-tts/
├── main.py              # File chính của ứng dụng
├── requirements.txt     # Danh sách thư viện cần thiết
├── README.md           # Hướng dẫn sử dụng
├── install.bat         # Script cài đặt tự động
├── run.bat             # Script chạy ứng dụng
└── bin/                # Thư mục chứa ffmpeg
    ├── ffmpeg.exe
    ├── ffplay.exe
    └── ffprobe.exe
```

## Yêu cầu hệ thống

- Windows 10/11
- Python 3.7+
- Microphone (cho tính năng STT)
- Kết nối internet (cho Edge TTS, Google TTS và Gemini)

## Lưu ý

- Đảm bảo có kết nối internet để sử dụng các dịch vụ TTS và Gemini
- Cần cài đặt PyQtWebEngine để sử dụng tính năng Gemini
- File ffmpeg.exe phải có trong thư mục bin/ để xử lý âm thanh
- Nếu gặp lỗi, hãy chạy `install.bat` để cài đặt lại các thư viện 