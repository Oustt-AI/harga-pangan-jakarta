import json, re
from datetime import datetime
import pytz
from playwright.sync_api import sync_playwright

URL_MARKET = "https://infopangan.jakarta.go.id/market"

def parse_rp(text):
    m = re.search(r'Rp\s*([\d\.]+)', text)
    return int(m.group(1).replace('.', '')) if m else 0

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")
        page.goto(URL_MARKET, wait_until="networkidle", timeout=90000)
        # tunggu kartu harga muncul
        page.wait_for_selector("text=Rp", timeout=30000)
        page.wait_for_timeout(3000)  # biar semua kartu ke-load
        
        # ambil semua teks yang terlihat
        body = page.inner_text("body")
        browser.close()
    
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    
    komoditas = []
    for i, line in enumerate(lines):
        if "Rp" in line and "/kg" in line:
            harga = parse_rp(line)
            # nama biasanya 1-2 baris di atasnya
            nama = lines[i-1] if i > 0 else ""
            # bersihkan nama yang kepanjangan atau bukan komoditas
            if len(nama) > 50 or "Rp" in nama or nama.lower() in ["stabil", "naik", "turun"]:
                nama = lines[i-2] if i > 1 else nama
            
            # cari perubahan di baris setelahnya
            change_line = lines[i+1] if i+1 < len(lines) else ""
            selisih = 0
            if "Turun" in change_line:
                selisih = -parse_rp(change_line)
            elif "Naik" in change_line:
                selisih = parse_rp(change_line)
            
            # filter hanya komoditas yang valid
            if nama and harga > 0 and any(k in nama.lower() for k in ["beras", "cabe", "bawang", "daging", "telur", "minyak", "gula", "ikan", "susu", "ayam", "sapi"]):
                # hindari duplikat
                if not any(k["nama"] == nama for k in komoditas):
                    komoditas.append({
                        "nama": nama,
                        "harga": harga,
                        "selisih": selisih,
                        "pasar": {  # untuk sementara isi sama, nanti bisa scrape per pasar
                            "sunter": harga,
                            "senen": harga,
                            "kramat": harga,
                            "minggu": harga
                        }
                    })
    
    if not komoditas:
        raise Exception("Gagal parse data dari halaman market")
    
    return komoditas

def main():
    data = scrape()
    tz = pytz.timezone("Asia/Jakarta")
    out = {
        "updated_at": datetime.now(tz).isoformat(),
        "komoditas": sorted(data, key=lambda x: x["nama"])
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"SUKSES: {len(data)} komoditas live dari infopangan.jakarta.go.id")

if __name__ == "__main__":
    main()
