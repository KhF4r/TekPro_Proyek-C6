import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse

class ScraperEngine:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless") # Jalankan tanpa jendela agar cepat
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=chrome_options
        )

    def get_article_links(self, main_url, limit):
        try:
            # Pastikan URL bersih
            main_url = main_url.strip()
            if not main_url.startswith(('http://', 'https://')):
                main_url = 'https://' + main_url
                
            # Gunakan User-Agent agar tidak terdeteksi sebagai robot
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            self.driver.get(main_url)
            
            # Scroll lebih lama untuk CNN karena mereka pakai banyak lazy loading
            for _ in range(4): 
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2)
            
            parsed_main = urlparse(main_url)
            # Ambil domain utama (misal: cnnindonesia.com)
            base_domain = '.'.join(parsed_main.netloc.split('.')[-2:])

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            links = []
            
            # CARA AGRESIF: Cari semua tag <a> di seluruh halaman
            all_a_tags = soup.find_all('a', href=True)
            
            for a_tag in all_a_tags:
                href = a_tag['href']
                full_url = urljoin(main_url, href)
                
                # 1. Harus mengandung domain utama
                if base_domain in full_url:
                    # 2. Filter Sampah
                    garbage = ['facebook', 'twitter', 'instagram', 'whatsapp', 'google', 
                               'login', 'register', 'ads.', 'member', 'service']
                    
                    if not any(x in full_url.lower() for x in garbage):
                        # 3. LOGIKA KHUSUS ARTIKEL:
                        # Artikel CNN/Detik biasanya punya pola angka ID (d-123 atau /12345/)
                        has_id_pattern = any(char.isdigit() for char in full_url)
                        
                        # Pastikan bukan link Home atau Index saja
                        if has_id_pattern and len(full_url) > len(main_url) + 5:
                            if full_url not in links:
                                links.append(full_url)
                
                if len(links) >= limit:
                    break
            
            return links
        except Exception as e:
            print(f"Error: {e}")
            return []

    def extract_data(self, url):
        """Fungsi ini untuk masuk ke dalam artikel dan ambil isinya"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Ambil Judul
            title_tag = soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else soup.title.get_text(strip=True)
            
            # 2. Ambil Tanggal (Gunakan meta tag agar stabil)
            date = "Tidak ditemukan"
            meta_date = soup.find('meta', property='article:published_time') or \
                        soup.find('meta', attrs={'name': 'pubdate'})
            if meta_date:
                date = meta_date.get('content', '').split('T')[0]

            # 3. Ambil Isi Berita (Semua paragraf panjang)
            paragraphs = soup.find_all('p')
            content_parts = []
            for p in paragraphs:
                txt = p.get_text(strip=True)
                if len(txt) > 60: # Hanya ambil paragraf yang benar-benar isi berita
                    if not any(x in txt.lower() for x in ['baca juga', 'follow us', 'klik di sini']):
                        content_parts.append(txt)
            
            full_content = "\n\n".join(content_parts)

            # Validasi: Jika judul ada dan isi berita tidak kosong
            if title and len(full_content) > 100:
                return {
                    "url": url, 
                    "title": title, 
                    "date": date,
                    "content": full_content
                }
            return None
        except Exception as e:
            print(f"Error extract_data pada {url}: {e}")
            return None

    def close(self):
        self.driver.quit()
