from PyQt5.QtCore import QThread, pyqtSignal
# 1. Pastikan nama kelas sesuai dengan yang ada di scraper_engine.py
from scraper_engine import ScraperEngine 
from concurrent.futures import ThreadPoolExecutor, as_completed

class ScraperWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    data_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, url, limit):
        super().__init__()
        self.url = url
        self.limit = limit
        self.is_running = True

    def run(self):
        # 2. Gunakan nama kelas ScraperEngine (sesuai modul sebelumnya)
        scraper = ScraperEngine() 
        try:
            self.log_signal.emit("Mencari daftar link artikel...")
            links = scraper.get_article_links(self.url, self.limit)
            total = len(links)
            
            if total == 0:
                self.log_signal.emit("Tidak ada link ditemukan.")
                self.finished_signal.emit()
                return

            self.log_signal.emit(f"Ditemukan {total} link. Memulai ekstraksi isi berita...")

            # Menggunakan ThreadPoolExecutor untuk mempercepat pengambilan isi berita
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Menggunakan as_completed agar data yang selesai lebih dulu langsung muncul di tabel
                future_to_url = {executor.submit(scraper.extract_data, link): link for link in links}
                
                done_count = 0
                for future in as_completed(future_to_url):
                    if not self.is_running: 
                        break
                    
                    try:
                        data = future.result()
                        # 3. Validasi data agar tidak memasukkan hasil kosong ke tabel
                        if data and data.get('title'):
                            self.data_signal.emit(data)
                            self.log_signal.emit(f"Berhasil: {data['title'][:50]}...")
                    except Exception as exc:
                        self.log_signal.emit(f"Gagal memproses satu artikel: {exc}")
                    
                    done_count += 1
                    progress = int((done_count / total) * 100)
                    self.progress_signal.emit(progress)

            # 4. Gunakan metode .close() (sesuai yang kita buat di scraper_engine.py)
            scraper.close() 
            self.log_signal.emit("Semua proses selesai!")
            self.finished_signal.emit()
        except Exception as e:
            self.log_signal.emit(f"Error Utama: {str(e)}")
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False