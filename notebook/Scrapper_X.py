

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
import getpass




def setup_driver():
    chrome_options = Options()

    # Anti-bot detection
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })
    return driver




def start_interactive_scraping(jumlah_scroll=5):
    try:
        driver = setup_driver()
    except Exception as e:
        print(f"Gagal membuka Chrome: {e}")
        return []

    driver.get("https://x.com/")

    print("=" * 60)
    print("✨ BROWSER TERBUKA & SIAP DIGUNAKAN ✨")
    print("=" * 60)
    print("CARA KERJA:")
    print("1. Login ke X/Twitter di jendela Chrome yang baru terbuka.")
    print("2. Ketik kata kunci secara manual di kotak pencarian X (Chrome).")
    print("3. Kembali ke Jupyter ini, ketik 'lanjut' lalu tekan ENTER untuk mulai merekam data.")
    print("4. Ketik 'selesai' lalu tekan ENTER jika sudah ingin berhenti & simpan data.")
    print("=" * 60)

    semua_data = set()
    ronde = 1

    try:
        while True:
            # Gunakan kotak input yang jelas di Jupyter
            perintah = input(
                f"\n[Ronde {ronde}] TEKAN ENTER / ketik 'lanjut' untuk scrap, ATAU ketik 'selesai': ").strip().lower()

            if perintah == 'selesai':
                print("\n🚨 Mengakhiri sesi scraping dan menutup browser...")
                break

            current_url = driver.current_url
            print(
                f"\n[+] Memulai Scroll {jumlah_scroll}x di Halaman Anda Saat Ini...")

            time.sleep(2)

            data_ronde_ini = 0

            # Mulai scraping
            for i in range(jumlah_scroll):
                tweet_elements = driver.find_elements(
                    By.XPATH, '//article[@data-testid="tweet"]')

                for tweet in tweet_elements:
                    try:
                        teks_mentah = tweet.text
                        teks_bersih = tweet.find_element(
                            By.XPATH, ".//*[@data-testid='tweetText']").text.strip()
                        if teks_bersih:
                            semua_data.add(teks_bersih)
                            data_ronde_ini += 1
                    except Exception:
                        continue

                # Scroll otomatis
                driver.execute_script(
                    "window.scrollBy(0, document.body.scrollHeight);")
                print(
                    f"   -> Scroll {i+1}/{jumlah_scroll} selesai (Total data smentara terkumpul: {len(semua_data)})...")
                time.sleep(4)  # Tunggu tweet lama loading dimuat

            print(
                f"✅ Selesai ronde {ronde}. Anda sekarang bisa mencari manual URL Tagar/Kata kunci lain di Chrome.")
            ronde += 1

    except KeyboardInterrupt:
        print("\n\n[!] Sesi dihentikan secara paksa oleh Pengguna.")
    except Exception as e:
        print(f"\n[!] Terjadi kesalahan saat scraping: {e}")
    finally:
        driver.quit()

    return list(semua_data)






def save_to_csv(data):
    df = pd.DataFrame(data, columns=["Isi Postingan"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"X_feedback_kumpulan_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"\n📁 File berhasil disimpan ke excel dengan nama: {filename}")





# 19jutalapanganpekerjaan
# prabowo / #presidenprabowo
# boardofpeace
# indonesiauntukdunia
# cekkesehatangratis
# danantara
# infrastrukturindonesia

if __name__ == "__main__":
    print("Inputkan jumlah scroll per ronde (default 5): ", end="")
    try:
        jumlah_scroll = int(input())
    except ValueError:
        jumlah_scroll = 5

    hasil = start_interactive_scraping(jumlah_scroll=jumlah_scroll)

    print("=" * 60)
    print(f"BERHASIL MENGUMPULKAN TOTAL {len(hasil)} TWEET UNIK.")
    print("=" * 60)

    if len(hasil) > 0:
        save_to_csv(hasil)
