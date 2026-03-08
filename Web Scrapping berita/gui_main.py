from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QTableWidget, QProgressBar, 
                             QTextEdit, QHeaderView, QTableWidgetItem, QLabel, 
                             QSpinBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from worker_thread import ScraperWorker
from data_handler import DataHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplikasi Web Scrapping Berita")
        self.resize(1100, 700)
        
        self.scraped_data = []
        self.worker = None
        
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # --- Panel Kontrol Atas ---
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Contoh: https://news.detik.com/indeks")
        
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 100)
        self.limit_spin.setValue(5)
        
        self.btn_start = QPushButton("Mulai Ambil Berita")
        self.btn_start.setStyleSheet("background-color: #27ae60; color: blue; padding: 8px;")
        self.btn_start.clicked.connect(self.run_process)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #c0392b; color: blue; padding: 8px;")
        self.btn_stop.clicked.connect(self.stop_process)

        input_layout.addWidget(QLabel("URL Indeks:"))
        input_layout.addWidget(self.url_input, 4)
        input_layout.addWidget(QLabel("Limit:"))
        input_layout.addWidget(self.limit_spin)
        input_layout.addWidget(self.btn_start)
        input_layout.addWidget(self.btn_stop)

        # --- Progress Bar ---
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignCenter)

        # --- Tabel 4 Kolom (Hati-hati: urutan kolom harus pas) ---
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Judul", "Tanggal", "URL", "Isi Berita (Preview)"])
        
        # Pengaturan Lebar Kolom
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)      # Judul lebar
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Tanggal pas teks
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # URL bisa digeser
        header.setSectionResizeMode(3, QHeaderView.Stretch)      # Isi lebar
        
        self.table.setAlternatingRowColors(True)

        # --- Log Console ---
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(100)
        self.log_display.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")

        # --- Tombol Simpan ---
        self.btn_csv = QPushButton("Simpan ke Tabel CSV (Excel)")
        self.btn_csv.setEnabled(False)
        self.btn_csv.setMinimumHeight(40)
        self.btn_csv.setStyleSheet("font-weight: bold; background-color: #2980b9; color: white;")
        self.btn_csv.clicked.connect(self.save_to_csv)

        # Masukkan ke Layout Utama
        layout.addLayout(input_layout)
        layout.addWidget(self.progress)
        layout.addWidget(self.table)
        layout.addWidget(QLabel("Status Sistem:"))
        layout.addWidget(self.log_display)
        layout.addWidget(self.btn_csv)

        main_widget.setLayout(layout)

    def run_process(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Kosong", "Silakan masukkan URL dahulu.")
            return

        self.scraped_data = []
        self.table.setRowCount(0)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_csv.setEnabled(False)

        # Memulai Worker (Pastikan worker_thread.py juga sudah diupdate link/limit-nya)
        self.worker = ScraperWorker(url, self.limit_spin.value())
        self.worker.log_signal.connect(self.update_log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.data_signal.connect(self.update_table)
        self.worker.finished_signal.connect(self.process_finished)
        self.worker.start()

    def update_table(self, data):
        self.scraped_data.append(data)
        self.btn_csv.setEnabled(True)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Isi Sel Tabel
        self.table.setItem(row, 0, QTableWidgetItem(data['title']))
        self.table.setItem(row, 1, QTableWidgetItem(data['date']))
        self.table.setItem(row, 2, QTableWidgetItem(data['url']))
        
        # Preview Isi: Ambil 70 karakter saja agar tidak memenuhi layar
        preview_text = data['content'][:70].replace('\n', ' ') + "..."
        self.table.setItem(row, 3, QTableWidgetItem(preview_text))

    def update_log(self, msg):
        self.log_display.append(f"> {msg}")

    def stop_process(self):
        if self.worker:
            self.worker.stop()

    def process_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.update_log("Pekerjaan Selesai.")

    def save_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan File", "", "CSV Files (*.csv)")
        if path:
            if DataHandler.export_to_csv(path, self.scraped_data):
                QMessageBox.information(self, "Sukses", "Data berhasil disimpan sebagai tabel.")
