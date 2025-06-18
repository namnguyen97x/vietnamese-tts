# Vietnamese Text-to-Speech (TTS)

Ứng dụng chuyển văn bản thành giọng nói tiếng Việt sử dụng Edge TTS, Google TTS và nhận diện giọng nói (Speech to Text).

## Tính năng (Features)

- Chuyển văn bản thành giọng nói tiếng Việt
- Hỗ trợ hai công nghệ TTS:
  - Microsoft Edge TTS (chất lượng cao, nhiều giọng đọc, đa ngôn ngữ)
  - Google TTS (gTTS)
- Nhận diện giọng nói (Speech to Text):
  - Nhận diện từ file âm thanh (mp3, wav, flac, ...)
  - Nhận diện trực tiếp từ micro
- Giao diện đồ họa dễ sử dụng
- Hỗ trợ nhập văn bản từ file .txt và .docx
- Phát thử và lưu file âm thanh
- Quản lý danh sách file âm thanh tạm
- Khi ấn "Đọc thử", file âm thanh tạm sẽ xuất hiện ngay trong bảng danh sách file tạm để bạn phát lại, lưu hoặc xóa

## Yêu cầu hệ thống (System Requirements)

- Python 3.7 trở lên
- Các thư viện Python (xem requirements.txt)
- Nếu dùng tính năng thu âm micro: cần cài driver micro và có micro trên máy tính

## Cài đặt (Installation)

1. Clone repository:
```bash
git clone https://github.com/namnguyen97x/vietnamese-tts.git
cd vietnamese-tts
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Sử dụng (Usage)

1. Chạy ứng dụng:
```bash
python main.py
```

2. Sử dụng Edge TTS:
   - Chọn tab "Edge TTS"
   - Nhập văn bản hoặc import từ file
   - Chọn giọng đọc (đa dạng, nhiều ngôn ngữ)
   - Nhấn "Đọc thử" để nghe thử (file sẽ xuất hiện trong danh sách file tạm)
   - Lưu file âm thanh nếu muốn

3. Sử dụng Google TTS:
   - Chọn tab "Google TTS"
   - Nhập văn bản hoặc import từ file
   - Chọn ngôn ngữ (vi/en)
   - Nhấn "Đọc thử" để nghe thử
   - Lưu file âm thanh nếu muốn

4. Sử dụng Speech to Text (STT):
   - Chọn tab "Speech to Text (STT)"
   - Nhấn "Nhận diện từ file âm thanh" để chọn file mp3, wav, flac, ... và chuyển thành văn bản
   - Hoặc nhấn "Nhận diện từ micro" để nói trực tiếp, kết quả sẽ hiển thị trong ô bên dưới

## Quản lý file âm thanh (Audio File Management)

- Danh sách file âm thanh tạm hiển thị ở bên phải
- Có thể phát, tạm dừng, lưu hoặc xóa file
- File âm thanh tạm sẽ tự động xóa khi thoát ứng dụng

## Đóng góp (Contributing)

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request.

## Giấy phép (License)

MIT License 