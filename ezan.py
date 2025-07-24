import http.client
import json
import datetime
import time
import sys
import win32gui

# --- Sabitler ---
WM_APPCOMMAND = 0x0319
APPCOMMAND_MEDIA_PLAY_PAUSE = 14

# --- Ayarlar ---
API_KEY = "1KS0Jk764gcL9q4EAgg5GF:02lbliFyUaVLxa0EEu5B07"
PRAYER_CITY = "ankara"

# --- Test Zamanları ---
TEST_TIME = ""         # Durdurma test saati ("HH:MM") — "" yaparsan devre dışı
TEST_START_TIME = ""   # Başlatma test saati ("HH:MM") — "" yaparsan devre dışı

# --- Genel Ayarlar ---
TIME_TO_WAIT_AFTER_PAUSE = 300  # Duraklatmadan sonra bekleme süresi (saniye)
CHECK_INTERVAL = 15             # Kontrol aralığı (saniye)

# --- Ezan Vakitlerini API'den Al ---
def get_prayer_times(city=PRAYER_CITY):
    conn = http.client.HTTPSConnection("api.collectapi.com")
    headers = {
        'content-type': "application/json",
        'authorization': f"apikey {API_KEY}"
    }

    try:
        conn.request("GET", f"/pray/all?city={city}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        parsed = json.loads(data.decode("utf-8"))

        if parsed.get("success"):
            vakitler = {}
            for item in parsed["result"]:
                vakit = item.get("vakit")
                saat = item.get("saat")
                if vakit and saat:
                    vakitler[vakit.lower()] = saat
            return vakitler
        else:
            print("❌ API başarısız:", parsed.get("error", "Bilinmeyen hata"))
            return {}
    except Exception as e:
        print("❌ API Hatası:", e)
        return {}
    finally:
        conn.close()

# --- Spotify Duraklat ---
def stop_spotify():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            win32gui.SendMessage(hwnd, WM_APPCOMMAND, hwnd, APPCOMMAND_MEDIA_PLAY_PAUSE << 16)
            print("⏸️ Spotify duraklatıldı.")
        else:
            print("❌ Pencere bulunamadı (duraklatma).")
    except Exception as e:
        print("❌ Duraklatma hatası:", e)

# --- Spotify Başlat ---
def start_spotify():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            win32gui.SendMessage(hwnd, WM_APPCOMMAND, hwnd, APPCOMMAND_MEDIA_PLAY_PAUSE << 16)
            print("▶️ Spotify başlatıldı.")
        else:
            print("❌ Pencere bulunamadı (başlatma).")
    except Exception as e:
        print("❌ Başlatma hatası:", e)

# --- Ana Script ---
def main():
    current_day = None
    prayer_times = {}
    test_stop_triggered = False
    test_start_triggered = False
    skip_vakitler = ["imsak", "güneş"]

    print("🚀 Spotify Ezan Kontrol Scripti başlatıldı.")
    if TEST_TIME or TEST_START_TIME:
        print("⚠️ TEST MODU AKTİF:")
        if TEST_TIME:
            print(f" - Durdurma Test Saati: {TEST_TIME}")
        if TEST_START_TIME:
            print(f" - Başlatma Test Saati: {TEST_START_TIME}")
    else:
        print("✅ Normal mod: Ezan vakitlerinde Spotify kontrol edilecek.")

    while True:
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M")

        # Yeni gün başlangıcında ezan saatlerini al
        if current_day != now.day:
            current_day = now.day
            test_stop_triggered = False
            test_start_triggered = False
            print(f"\n📅 Yeni gün: {now.strftime('%Y-%m-%d')}")
            if not TEST_TIME and not TEST_START_TIME:
                print("🕋 Ezan vakitleri alınıyor...")
                prayer_times = get_prayer_times()
                if prayer_times:
                    print("📌 Bugünün ezan saatleri:")
                    for name, vakit in prayer_times.items():
                        print(f"  - {name.title()}: {vakit}")
                else:
                    print("⚠️ Ezan vakitleri alınamadı.")

        # --- Test: Durdurma ve Başlatma ---
        if TEST_TIME and time_str == TEST_TIME and not test_stop_triggered:
            print(f"\n🧪 [TEST] Durdurma vakti ({TEST_TIME}).")
            stop_spotify()
            print(f"⏳ {TIME_TO_WAIT_AFTER_PAUSE} saniye bekleniyor...")
            time.sleep(TIME_TO_WAIT_AFTER_PAUSE)
            start_spotify()
            test_stop_triggered = True

        elif TEST_START_TIME and time_str == TEST_START_TIME and not test_start_triggered:
            print(f"\n🧪 [TEST] Başlatma vakti ({TEST_START_TIME}).")
            start_spotify()
            test_start_triggered = True

        # --- Gerçek Ezan Vakitleri ---
        elif not TEST_TIME and prayer_times:
            for name, vakit in prayer_times.items():
                if name in skip_vakitler:
                    continue  # İmsak ve Güneş atlanır
                if time_str == vakit:
                    print(f"\n🕌 {name.title()} vakti ({vakit}) geldi.")
                    stop_spotify()
                    print(f"⏳ {TIME_TO_WAIT_AFTER_PAUSE} saniye bekleniyor...")
                    time.sleep(TIME_TO_WAIT_AFTER_PAUSE)
                    start_spotify()
                    break

        time.sleep(CHECK_INTERVAL)

# --- Çalıştır ---
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Çıkılıyor.")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 FATAL HATA: {e}")
        sys.exit(1)
