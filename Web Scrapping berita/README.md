 Aplikasi ini adalah plikasi berbasis Python yang dirancang untuk mengambil data berita secara otomatis (scraping) dari berbagai portal berita populer seperti Detik, Kompas, CNN Indonesia, dan lainnya. Aplikasi ini dilengkapi dengan antarmuka grafis (GUI) dan mendukung proses pengambilan data secara cepat menggunakan teknik multi-threading.

✨ Fitur Utama
Universal Scraping: Mendukung berbagai portal berita dengan algoritma ekstraksi konten yang dinamis.

Multi-threading: Proses pengambilan isi berita dilakukan secara paralel (5x lebih cepat).

Auto-Cleaning: Membersihkan teks berita dari iklan, kode HTML, dan karakter sampah lainnya secara otomatis.

Export to Excel/CSV: Menyimpan hasil scraping (Judul, Tanggal, URL, Isi) ke dalam format file CSV yang rapi.

Modern GUI: Antarmuka pengguna yang intuitif berbasis PyQt5 dengan tema warna kustom (Pink/Modern).

🏗️ Arsitektur Proyek
Proyek ini dibangun dengan struktur modular untuk memudahkan pengembangan:

main.py: Entry point aplikasi.

gui_main.py: Layer antarmuka pengguna (PyQt5).

scraper_engine.py: Mesin utama yang mengontrol Selenium dan BeautifulSoup.

worker_thread.py: Pengatur proses background agar aplikasi tidak freezing.

data_handler.py: Pengelola penyimpanan data ke file fisik.

utils.py: Modul pembantu untuk standarisasi dan pembersihan data.

🛠️ Prasyarat (Requirements)
Sebelum menjalankan program, pastikan Anda telah menginstal library berikut:

Bash
pip install PyQt5 selenium beautifulsoup4 pandas
Pastikan Google Chrome sudah terinstal di sistem Anda karena program ini menggunakan ChromeDriver.

🚀 Cara Penggunaan
Clone atau Download repositori ini.

Buka terminal/command prompt di folder proyek.

Jalankan aplikasi dengan perintah:

Bash
python main.py
Masukkan URL Indeks berita (Contoh: https://news.detik.com/indeks).

Tentukan Limit jumlah berita yang ingin diambil.

Klik Mulai Ambil Berita dan tunggu proses selesai.

Klik Simpan ke Tabel CSV untuk mengunduh data.

Catatan : Jumlah berita yang dapat diambil dan ditampilkan mungkin tidak sama dengan jumlah limitnya