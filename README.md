# 🚀 Argos Offline Translator (Portable GUI)

A lightweight **offline translator + dictionary** using Argos Translate, Stanza, and NLTK.
Runs locally with **no internet required after first setup**.

---

## ✨ Features

* 🌐 Fully offline after first run
* 🔄 English ↔ Vietnamese translation
* 📖 Built-in dictionary (WordNet + translation)
* 🧠 Sentence-aware translation (Stanza)
* 📦 Portable (no global install needed)

---

## ⚡ Quick Start (1 phút là chạy)

### 1. Cài Python (nếu chưa có)

#### 🐧 Linux / Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

#### 🍎 macOS (brew)

```bash
brew install python
```

#### 🪟 Windows (winget)

```bash
winget install Python.Python.3
```

---

### 2. Clone repo

```bash
git clone https://github.com/your-username/argostranslate.git
cd argostranslate
```

---

### 3. Chạy app

```bash
python "Translate Offline GUI Argos.py"
```

---

## 🔥 Lần chạy đầu tiên (QUAN TRỌNG)

* Cần **internet**
* App sẽ tự:

  * tải thư viện (argos, nltk, stanza)
  * tải model dịch
  * tải dictionary

👉 Sau khi hoàn tất, file `.offline_ready` sẽ được tạo
=> từ đó về sau **chạy 100% offline**

---

## 📁 Cấu trúc

```
project/
├── lib/                # Python packages (local)
├── argos_packages/     # model dịch
├── stanza_resources/   # model NLP
├── nltk_data/          # dictionary data
├── .offline_ready      # đánh dấu đã setup
```

---

## 🧠 Cách hoạt động

* Không dùng global Python packages
* Tự cài vào `lib/` thông qua:

```python
pip install --target ./lib
```

* Override path để chạy portable 

---

## ⚠️ Lưu ý

* Lần đầu bắt buộc phải có mạng
* Nếu lỗi model:

```bash
rm .offline_ready
```

rồi chạy lại

---

## 💡 Tip

Có thể build thành `.exe` bằng PyInstaller nếu muốn share cho người không biết Python.

---

## 👨‍💻 Author

Made by Kaivian
