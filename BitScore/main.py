"""
BitScore — Game Rating App v4.0
================================
Entry point aplikasi. Jalankan file ini untuk memulai.

Install:
    pip install pillow requests python-dotenv

Jalankan:
    python main.py
"""

from auth.login_page import LoginPage
from UI.app import BitScoreApp

if __name__ == "__main__":
    while True:
        # 1. Tampilkan halaman login
        login = LoginPage()
        login.mainloop()

        # 2. Jika user menutup window login tanpa login, maka keluar dari apk
        if not login.success:
            break
        
        # 3. Buka Apk utama
        app = BitScoreApp()
        app.mainloop()

        # 4. Jika user tidak minta logout (misal tutup window), maka keluar dari apk
        if not getattr(app, "_want_logout", False):
            break
        # Jika _want_logout = True, kembali ke halaman login
