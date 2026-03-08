import csv

class DataHandler:
    @staticmethod
    def export_to_csv(file_path, data_list):
        if not data_list:
            return False
        try:
            # Gunakan 'utf-8-sig' agar Excel otomatis mengenali karakter Indonesia & simbol
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                # Kolom tabel sesuai permintaan: Judul, Tanggal, URL, Isi
                fieldnames = ["Title", "Date", "URL", "Isi Berita"]
                
                # Gunakan delimiter ';' (titik koma) agar otomatis jadi kolom di Excel region Indonesia
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                
                writer.writeheader()
                for row in data_list:
                    # MEMBERSIHKAN ISI BERITA:
                    # 1. Hapus baris baru (\n) agar tidak merusak baris CSV
                    # 2. Hapus karakter titik koma agar tidak merusak pemisah kolom
                    raw_content = row.get('content', '-')
                    clean_content = raw_content.replace('\n', ' ').replace('\r', ' ').replace(';', ',')
                    
                    writer.writerow({
                        "Title": row.get('title', '-'),
                        "Date": row.get('date', '-'),
                        "URL": row.get('url', '-'),
                        "Isi Berita": clean_content
                    })
            return True
        except Exception as e:
            print(f"Gagal ekspor CSV: {e}")
            return False
