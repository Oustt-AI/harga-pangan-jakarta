import json
from datetime import datetime
import pytz
from playwright.sync_api import sync_playwright

URL = "https://infopangan.jakarta.go.id"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        
        # ambil data Next.js yang sama dipakai website
        data = page.evaluate("() => window.__NEXT_DATA__")
        browser.close()
    
    props = data["props"]["pageProps"]
    
    # cari list komoditas - struktur bisa berubah, kita coba 2 lokasi
    try:
        items = props["initialState"]["commodity"]["list"]
    except:
        items = props.get("commodities", [])
    
    hasil = []
    for it in items:
        nama = it.get("name") or it.get("commodity_name")
        harga = int(it.get("price") or it.get("harga") or 0)
        selisih = int(it.get("change") or it.get("selisih") or 0)
        
        pasar = {}
        for m in it.get("markets", []):
            slug = m.get("slug", "").lower()
            price = int(m.get("price", 0))
            if "sunter" in slug: pasar["sunter"] = price
            if "senen" in slug: pasar["senen"] = price
            if "kramat" in slug: pasar["kramat"] = price
            if "minggu" in slug: pasar["minggu"] = price
        
        if nama and harga > 0:
            hasil.append({
                "nama": nama,
                "harga": harga,
                "selisih": selisih,
                "pasar": pasar
            })
    
    if not hasil:
        raise Exception("Data kosong dari infopangan")
    
    return hasil

def main():
    komoditas = scrape()
    tz = pytz.timezone("Asia/Jakarta")
    out = {
        "updated_at": datetime.now(tz).isoformat(),
        "komoditas": sorted(komoditas, key=lambda x: x["nama"])
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(komoditas)} komoditas live")

if __name__ == "__main__":
    main()
