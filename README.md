# Argos Offline Translator

Argos Offline Translator là phần mềm dịch thuật và tra cứu từ điển ngoại tuyến với giao diện đồ họa, hoạt động dựa trên nền tảng Argos Translate, Stanza và NLTK. Ứng dụng được thiết kế theo mô hình độc lập (Portable), cho phép vận hành hoàn toàn không cần kết nối mạng sau khi hoàn tất thiết lập ban đầu.

## Yêu cầu hệ thống

1. Python phiên bản 3.8 trở lên.
2. Kết nối mạng chỉ cần thiết trong lần chạy đầu tiên để tải tài nguyên.
3. Tương thích các hệ điều hành phổ biến: Windows, macOS, Linux.

## Hướng dẫn cài đặt và sử dụng

### 1. Chuẩn bị môi trường Python

Trên Ubuntu hoặc Linux:
```bash
sudo apt update && sudo apt install python3 python3-pip
```

Trên macOS:
```bash
brew install python
```

Trên Windows:
```cmd
winget install Python.Python.3
```

### 2. Tải mã nguồn

```bash
git clone https://github.com/ThanhMiLa/argostranslate.git
cd argostranslate
```

### 3. Khởi chạy ứng dụng

```bash
python "Translate Offline GUI Argos.py"
```

## Quá trình khởi tạo lần đầu

Trong lần khởi động đầu tiên, ứng dụng yêu cầu kết nối mạng để tự động tải các thành phần cần thiết:

1. Thư viện phụ thuộc được cài đặt trực tiếp vào thư mục lib nội bộ gồm Argos Translate, Stanza và NLTK.
2. Gói mô hình ngôn ngữ dịch thuật Anh Việt và Việt Anh.
3. Dữ liệu xử lý ngôn ngữ tự nhiên từ Stanza.
4. Cơ sở dữ liệu từ điển WordNet từ NLTK.

Sau khi hoàn tất quá trình tải, tệp cờ .offline_ready sẽ tự động được tạo. Những lần khởi động tiếp theo ứng dụng sẽ hoạt động ở chế độ ngoại tuyến hoàn toàn.

## Cấu trúc thư mục

```text
argostranslate/
  lib/                 Thư viện phụ thuộc cài đặt cục bộ
  argos_packages/      Dữ liệu mô hình dịch thuật
  stanza_resources/    Tài nguyên xử lý câu Stanza
  nltk_data/           Cơ sở dữ liệu từ điển WordNet
  .offline_ready       Tệp xác nhận hoàn tất thiết lập ngoại tuyến
```

## Khắc phục sự cố

Trường hợp quá trình tải ban đầu bị gián đoạn hoặc thiếu tệp mô hình, thực hiện xóa tệp đánh dấu để tải lại:

```bash
rm .offline_ready
```

Sau khi xóa, đảm bảo máy tính có kết nối mạng và khởi chạy lại ứng dụng để chương trình tự động hoàn tất quá trình thiết lập.

## Đóng gói ứng dụng

Để phân phối cho người dùng cuối không có sẵn môi trường Python, có thể sử dụng PyInstaller để đóng gói thành tệp thực thi độc lập:

```bash
pyinstaller "Translate Offline GUI Argos.py"
```
