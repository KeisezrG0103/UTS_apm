from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
import getpass


def setup_facebook_driver():
    """Initialize the Edge webdriver with custom options"""
    options = webdriver.EdgeOptions()

    # Anti-bot detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Pengaturan tambahan agar lebih optimal untuk Facebook
    options.add_argument("start-maximized")
    # Mematikan popup notifikasi
    options.add_argument("--disable-notifications")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Inisialisasi WebDriver untuk Edge
    driver = webdriver.Edge(options=options)

    # Menyembunyikan status otomatisasi dari deteksi bot via CDP command
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })

    return driver


def start_facebook_scraping(jumlah_scroll=5):
    driver = setup_facebook_driver()
    print("Membuka Facebook...")
    driver.get("https://www.facebook.com/")

    print("=" * 60)
    print("✨ BROWSER SIAP DIGUNAKAN UNTUK SCRAPING ✨")
    print("1. Cari grup, halaman, atau postingan yang ingin di-scrap secara manual di browser.")
    print("2. Jika sudah berada di halaman target, kembali ke sini dan ketik 'lanjut'.")
    print("=" * 60)

    semua_data = set()
    ronde = 1

    try:
        while True:
            perintah = input(
                f"\n[Ronde {ronde}] Ketik 'lanjut' untuk scrap, ATAU 'selesai': ").strip().lower()

            if perintah == 'selesai':
                break

            print(f"\n[+] Memulai Scroll {jumlah_scroll}x...")
            time.sleep(2)

            # Mulai scraping data (Menyesuaikan dengan selector Facebook)
            # Catatan: Class pada FB sering berubah karena React
            for i in range(jumlah_scroll):
                # ==========================================================
                # TAMBAHAN 1: KLIK TOMBOL "LIHAT SELENGKAPNYA" / "SEE MORE"
                # ==========================================================
                try:
                    # Mencari elemen yang memiliki teks "Lihat selengkapnya" atau "See more"
                    see_more_btns = driver.find_elements(
                        By.XPATH, '//div[text()="Lihat selengkapnya" or text()="See more" or text()="Lihat Selengkapnya"]'
                    )

                    for btn in see_more_btns:
                        try:
                            # Menggunakan JavaScript click menghindari ElementClickInterceptedException
                            # yang sering terjadi pada UI Facebook yang tumpang tindih
                            driver.execute_script("arguments[0].click();", btn)
                            # Tunggu setengah detik per klik agar animasi expand selesasi
                            time.sleep(0.5)
                        except:
                            continue
                except:
                    pass  # Abaikan jika tidak ada error lain

                # ==========================================================
                # TAMBAHAN 2: EKSTRAKSI TEKS POSTINGAN (SUDAH DI-EXPAND)
                # ==========================================================
                # post_elements = driver.find_elements(
                #     By.XPATH, '//div[@data-ad-preview="message" or @dir="auto"]')
                post_elements = driver.find_elements(
                    By.XPATH, '//div[@data-ad-preview="message" or @data-ad-comet-preview="message"]')
                for post in post_elements:
                    try:
                        teks_bersih = post.text.strip()
                        # Filter teks terlalu pendek dan teks yang sisa-sisa tombol
                        if teks_bersih and len(teks_bersih) > 10 and teks_bersih not in ["Lihat selengkapnya", "See more"]:
                            semua_data.add(teks_bersih)
                    except Exception:
                        continue

                # Scroll ke bawah
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                print(
                    f"   -> Scroll {i+1} selesai (Total data terkumpul: {len(semua_data)})")

                # Berikan waktu jeda loading baru setelah scroll
                time.sleep(4)

            print(f"✅ Selesai ronde {ronde}.")
            ronde += 1

    except KeyboardInterrupt:
        print("\nSesi dihentikan.")
    finally:
        driver.quit()

    return list(semua_data)


# =========================
# EKSEKUSI
# =========================
if __name__ == "__main__":
    ## give input 
    print("Inputkan jumlah scroll per ronde (default 5): ", end="")
    try:
        jumlah_scroll = int(input())
    except ValueError:
        jumlah_scroll = 5
    hasil_fb = start_facebook_scraping(jumlah_scroll=jumlah_scroll)

    if hasil_fb:
        df = pd.DataFrame(hasil_fb, columns=["Isi Postingan"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FB_scrap_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n📁 Data FB berhasil disimpan: {filename}")
