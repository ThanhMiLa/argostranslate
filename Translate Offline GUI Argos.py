
import os
import sys
import subprocess
import threading
import re
import socket
import tkinter as tk
from tkinter import ttk, scrolledtext
import importlib

# =========================
# PATH CONFIGURATION
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(BASE_DIR, "lib")
ARGOS_DIR = os.path.join(BASE_DIR, "argos_packages")
NLTK_DIR = os.path.join(BASE_DIR, "nltk_data")
STANZA_DIR = os.path.join(BASE_DIR, "stanza_resources")
LOCK_FILE = os.path.join(BASE_DIR, ".offline_ready")

# Tạo thư mục nếu chưa có
for directory in [LIB_DIR, ARGOS_DIR, NLTK_DIR, STANZA_DIR]:
    os.makedirs(directory, exist_ok=True)

def is_online():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        return False

# =========================
# AUTO INSTALL DEPENDENCIES
# =========================
def setup_local_dependencies():
    if os.path.exists(LOCK_FILE):
        return

    required_packages = ["argostranslate", "nltk", "stanza"]
    lib_argos_path = os.path.join(LIB_DIR, "argostranslate")

    if not os.path.exists(lib_argos_path):
        if not is_online():
            print("[FATAL] First run requires an internet connection to download dependencies.")
            sys.exit(1)

        print("First time setup: Downloading required libraries to 'lib' folder...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--target", LIB_DIR] + required_packages
            )
            importlib.invalidate_caches()
            print("Libraries installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[FATAL] Failed to install libraries: {e}")
            sys.exit(1)

setup_local_dependencies()

# Ép hệ thống dùng thư viện cục bộ
sys.path.insert(0, LIB_DIR)

# Cấu hình môi trường cho Argos và Stanza lưu dữ liệu tại thư mục hiện tại
os.environ["ARGOS_PACKAGES_DIR"] = ARGOS_DIR
os.environ["ARGOS_DEVICE_DATA_DIR"] = os.path.join(ARGOS_DIR, "device_data")
os.environ["STANZA_RESOURCES_DIR"] = STANZA_DIR
os.environ["ARGOS_STANZA_DIR"] = STANZA_DIR  # Bắt buộc Argos phải đưa thư mục này cho Stanza

import argostranslate.package
import argostranslate.translate
import nltk
from nltk.corpus import wordnet
import stanza

# =========================
# MONKEY-PATCH STANZA (Trị tận gốc lỗi đòi mạng & lỗi sai thư mục)
# =========================
original_pipeline = stanza.Pipeline

def custom_pipeline(*args, **kwargs):
    # 1. Ép buộc Stanza PHẢI tìm file resources.json ở đúng thư mục cục bộ
    kwargs['dir'] = STANZA_DIR 
    
    # 2. Nếu đang ở chế độ Offline (hoặc cúp mạng), chặn hoàn toàn kết nối Internet
    if os.path.exists(LOCK_FILE) or not is_online():
        try:
            from stanza.pipeline.core import DownloadMethod
            kwargs['download_method'] = DownloadMethod.REUSE_RESOURCES
        except ImportError:
            kwargs['offline'] = True
            
    return original_pipeline(*args, **kwargs)

stanza.Pipeline = custom_pipeline

nltk.data.path.append(NLTK_DIR)

LANG_CODES = {
    "English": "en",
    "Vietnamese": "vi"
}

# =========================
# CORE LOGIC
# =========================
class TranslatorCore:
    def __init__(self, log_callback=None):
        self.ensure_models(log_callback)

    def ensure_models(self, log_callback):
        # 1. Kiểm tra mô hình dịch thuật của Argos
        installed_packages = argostranslate.package.get_installed_packages()
        installed_pairs = [(p.from_code, p.to_code) for p in installed_packages]
        required_pairs = [("en", "vi"), ("vi", "en")]
        missing_pairs = [pair for pair in required_pairs if pair not in installed_pairs]

        if missing_pairs:
            if os.path.exists(LOCK_FILE):
                raise FileNotFoundError("Lock file exists but Argos models are missing. Please delete .offline_ready.")
            if not is_online():
                raise ConnectionError("Internet connection required to download translation models.")

            if log_callback: log_callback("Downloading translation models to local storage...")
            try:
                argostranslate.package.update_package_index()
                available_packages = argostranslate.package.get_available_packages()
                for src, tgt in missing_pairs:
                    pkg_to_install = next((p for p in available_packages if p.from_code == src and p.to_code == tgt), None)
                    if pkg_to_install:
                        if log_callback: log_callback(f"Installing language package: {src} -> {tgt}...")
                        argostranslate.package.install_from_path(pkg_to_install.download())
            except Exception as e:
                raise ConnectionError(f"Failed to download Argos models: {str(e)}")

        # 2. Kiểm tra mô hình chia câu của Stanza
        has_stanza_en = os.path.exists(os.path.join(STANZA_DIR, "en"))
        has_stanza_vi = os.path.exists(os.path.join(STANZA_DIR, "vi"))
        
        if not (has_stanza_en and has_stanza_vi):
            if os.path.exists(LOCK_FILE):
                raise FileNotFoundError("Lock file exists but Stanza models are missing. Please delete .offline_ready.")
            if not is_online():
                raise ConnectionError("Internet required to download Stanza tokenizers.")
            
            if log_callback: log_callback("Downloading sentence-splitting models (Stanza)...")
            stanza.download('en', model_dir=STANZA_DIR, verbose=False)
            stanza.download('vi', model_dir=STANZA_DIR, verbose=False)

        if log_callback:
            log_callback("All translation modules (Argos + Stanza) ready.")

    def translate(self, text, src_code, tgt_code):
        installed_languages = argostranslate.translate.get_installed_languages()
        src_lang = next((lang for lang in installed_languages if lang.code == src_code), None)
        tgt_lang = next((lang for lang in installed_languages if lang.code == tgt_code), None)
        
        if not src_lang or not tgt_lang:
            return "[Error: Language package missing.]"
            
        translation = src_lang.get_translation(tgt_lang)
        if not translation:
            return "[Error: Translation path missing.]"
            
        return translation.translate(text)

class DictionaryCore:
    def __init__(self, log_callback=None):
        self.ensure_nltk_data(log_callback)
        self.vi_chars = re.compile(
            r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', 
            re.IGNORECASE
        )

    def ensure_nltk_data(self, log_callback):
        # Dùng os để check vật lý thay vì dùng nltk.find() để tránh lỗi vớ vẩn của thư viện
        wn_path = os.path.join(NLTK_DIR, "corpora", "wordnet")
        omw_path = os.path.join(NLTK_DIR, "corpora", "omw-1.4")
        wn_zip = os.path.join(NLTK_DIR, "corpora", "wordnet.zip")
        omw_zip = os.path.join(NLTK_DIR, "corpora", "omw-1.4.zip")

        if (os.path.exists(wn_path) or os.path.exists(wn_zip)) and (os.path.exists(omw_path) or os.path.exists(omw_zip)):
            if log_callback:
                log_callback("Dictionary data detected. Offline dictionary ready.")
            return

        if os.path.exists(LOCK_FILE):
            raise FileNotFoundError("Lock file exists but dictionary data is missing. Please delete .offline_ready.")

        if not is_online():
            raise ConnectionError("Internet connection required to download dictionary data.")

        if log_callback:
            log_callback("Downloading NLTK dictionary datasets...")
            
        try:
            success_wn = nltk.download('wordnet', download_dir=NLTK_DIR, quiet=True)
            success_omw = nltk.download('omw-1.4', download_dir=NLTK_DIR, quiet=True)
            
            if not success_wn or not success_omw:
                raise ConnectionError("NLTK download failed. Network might be restricted.")
        except Exception as e:
            raise ConnectionError(f"Failed to download NLTK data: {str(e)}")

    def is_likely_vietnamese(self, text):
        return bool(self.vi_chars.search(text))

    def lookup(self, text, translator, mode="Auto-detect"):
        text = text.strip().lower()
        if not text:
            return "Please enter a word."

        is_vi = False
        if mode == "Auto-detect":
            is_vi = self.is_likely_vietnamese(text)
        elif mode == "Vietnamese -> English":
            is_vi = True

        if is_vi:
            eng_trans = translator.translate(text, LANG_CODES["Vietnamese"], LANG_CODES["English"])
            result = f"Input (Vietnamese): {text.upper()}\n"
            result += "=" * 45 + "\n\n"
            result += f"English Vocabulary:\n"
            result += f"➤ {eng_trans.capitalize()}\n"
            return result
        else:
            vi_trans = translator.translate(text, LANG_CODES["English"], LANG_CODES["Vietnamese"])
            result = f"Input (English): {text.upper()}\n"
            result += "=" * 45 + "\n\n"
            result += f"Direct Translation:\n"
            result += f"➤ {vi_trans.capitalize()}\n\n"
            
            synsets = wordnet.synsets(text)
            if not synsets:
                result += "No detailed definitions found in the offline dictionary."
                return result
                
            result += "Detailed Explanations:\n"
            result += "-" * 45 + "\n"
            
            for i, syn in enumerate(synsets[:3]):
                pos_map = {'n': 'Noun', 'v': 'Verb', 'a': 'Adjective', 's': 'Adjective', 'r': 'Adverb'}
                pos = pos_map.get(syn.pos(), syn.pos())
                eng_def = syn.definition()
                vi_def = translator.translate(eng_def, LANG_CODES["English"], LANG_CODES["Vietnamese"])
                
                result += f"{i+1}. [{pos}]\n"
                result += f"   EN: {eng_def.capitalize()}.\n"
                result += f"   VI: {vi_def.capitalize()}.\n"
                
                examples = syn.examples()
                if examples:
                    vi_ex = translator.translate(examples[0], LANG_CODES["English"], LANG_CODES["Vietnamese"])
                    result += f"   Example: \"{examples[0]}\"\n"
                    result += f"            \"{vi_ex}\"\n"
                result += "\n"
            return result

# =========================
# GUI APPLICATION
# =========================
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Portable Offline Suite (Argos Translate) made by Kaivian")
        self.root.geometry("900x700")
        
        self.setup_ui()
        self.update_trans_output("Initializing System...\n")
        self.translate_btn.config(state=tk.DISABLED)
        self.dict_search_btn.config(state=tk.DISABLED)
        
        threading.Thread(target=self.initialize_cores, daemon=True).start()

    def log_to_ui(self, message):
        self.root.after(0, lambda msg=message: self.trans_output.insert(tk.END, f"- {msg}\n"))
        self.root.after(0, lambda: self.trans_output.see(tk.END))

    def initialize_cores(self):
        try:
            self.translator = TranslatorCore(log_callback=self.log_to_ui)
            self.dictionary = DictionaryCore(log_callback=self.log_to_ui)
            
            if not os.path.exists(LOCK_FILE):
                with open(LOCK_FILE, "w") as f:
                    f.write("Setup completed successfully. Application is now completely offline.")
                self.log_to_ui("Initial setup completed. The application can now be run entirely offline.")

            self.root.after(0, self.on_cores_loaded)
        except Exception as e:
            err_msg = f"Initialization Error:\n\n{str(e)}"
            self.root.after(0, lambda msg=err_msg: self.update_trans_output(msg))

    def on_cores_loaded(self):
        self.log_to_ui("\nSystem initialized successfully. Ready to use offline.")
        self.translate_btn.config(state=tk.NORMAL)
        self.dict_search_btn.config(state=tk.NORMAL)

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_trans = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_trans, text=" Translator ")
        self.build_translation_tab()

        self.tab_dict = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dict, text=" Dictionary ")
        self.build_dictionary_tab()

    def build_translation_tab(self):
        frame_top = tk.Frame(self.tab_trans)
        frame_top.pack(pady=10)

        self.src_lang_var = tk.StringVar(value="English")
        self.tgt_lang_var = tk.StringVar(value="Vietnamese")

        ttk.Label(frame_top, text="Source:").grid(row=0, column=0, padx=5)
        ttk.Combobox(frame_top, textvariable=self.src_lang_var, 
                     values=list(LANG_CODES.keys()), width=15, state="readonly").grid(row=0, column=1, padx=5)

        ttk.Label(frame_top, text="Target:").grid(row=0, column=2, padx=5)
        ttk.Combobox(frame_top, textvariable=self.tgt_lang_var, 
                     values=list(LANG_CODES.keys()), width=15, state="readonly").grid(row=0, column=3, padx=5)

        self.translate_btn = ttk.Button(frame_top, text="Translate", command=self.start_translation)
        self.translate_btn.grid(row=0, column=4, padx=15)

        ttk.Label(self.tab_trans, text="Input Text:").pack(anchor=tk.W, padx=10)
        self.trans_input = scrolledtext.ScrolledText(self.tab_trans, height=12)
        self.trans_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(self.tab_trans, text="System Logs / Output Text:").pack(anchor=tk.W, padx=10)
        self.trans_output = scrolledtext.ScrolledText(self.tab_trans, height=12)
        self.trans_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def build_dictionary_tab(self):
        frame_top = tk.Frame(self.tab_dict)
        frame_top.pack(pady=15)

        ttk.Label(frame_top, text="Enter Word/Phrase:").grid(row=0, column=0, padx=5)
        self.dict_input = ttk.Entry(frame_top, width=30, font=("Arial", 12))
        self.dict_input.grid(row=0, column=1, padx=5)
        self.dict_input.bind("<Return>", lambda event: self.start_dictionary_lookup())
        
        self.dict_mode_var = tk.StringVar(value="Auto-detect")
        ttk.Combobox(frame_top, textvariable=self.dict_mode_var, 
                     values=["Auto-detect", "English -> Vietnamese", "Vietnamese -> English"], 
                     width=20, state="readonly").grid(row=0, column=2, padx=5)

        self.dict_search_btn = ttk.Button(frame_top, text="Search", command=self.start_dictionary_lookup)
        self.dict_search_btn.grid(row=0, column=3, padx=5)

        ttk.Label(self.tab_dict, text="Definitions & Explanations:").pack(anchor=tk.W, padx=20)
        self.dict_output = scrolledtext.ScrolledText(self.tab_dict, height=22, font=("Consolas", 11))
        self.dict_output.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    def update_trans_output(self, text):
        self.trans_output.delete("1.0", tk.END)
        self.trans_output.insert(tk.END, text)

    def start_translation(self):
        src = self.src_lang_var.get()
        tgt = self.tgt_lang_var.get()
        input_data = self.trans_input.get("1.0", tk.END).strip()

        if src == tgt:
            self.update_trans_output("Source and target languages must differ.")
            return
        if not input_data:
            return

        self.translate_btn.config(state=tk.DISABLED)
        self.update_trans_output("Translating...")
        
        threading.Thread(
            target=self.process_translation, 
            args=(input_data, LANG_CODES[src], LANG_CODES[tgt]), 
            daemon=True
        ).start()

    def process_translation(self, text, src_code, tgt_code):
        try:
            translated = self.translator.translate(text, src_code, tgt_code)
            self.root.after(0, lambda msg=translated: self.update_trans_output(msg))
        except Exception as e:
            err_msg = f"Translation Error: {str(e)}"
            self.root.after(0, lambda msg=err_msg: self.update_trans_output(msg))
        finally:
            self.root.after(0, lambda: self.translate_btn.config(state=tk.NORMAL))

    def start_dictionary_lookup(self):
        word = self.dict_input.get().strip()
        mode = self.dict_mode_var.get()
        
        if not word: return
            
        self.dict_output.delete("1.0", tk.END)
        self.dict_output.insert(tk.END, f"Analyzing and translating '{word}'... Please wait.\n")
        self.dict_search_btn.config(state=tk.DISABLED)
        
        threading.Thread(
            target=self.process_dictionary_lookup, 
            args=(word, mode), 
            daemon=True
        ).start()

    def process_dictionary_lookup(self, word, mode):
        try:
            result = self.dictionary.lookup(word, self.translator, mode)
            self.root.after(0, lambda msg=result: self._set_dict_output(msg))
        except Exception as e:
            err_msg = f"Dictionary Error: {str(e)}"
            self.root.after(0, lambda msg=err_msg: self._set_dict_output(msg))
        finally:
            self.root.after(0, lambda: self.dict_search_btn.config(state=tk.NORMAL))
            
    def _set_dict_output(self, text):
        self.dict_output.delete("1.0", tk.END)
        self.dict_output.insert(tk.END, text)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()