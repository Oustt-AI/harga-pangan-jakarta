import json, re
from datetime import datetime
import pytz
from playwright.sync_api import sync_playwright

URL = "https://infopangan.jakarta.go.id"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        
        # ambil data JSON yang disuntik Next.js
        next_data = page.evaluate("() => window.__NEXT_DATA__")
        browser.close()
    
    # struktur data ada di props.pageProps
    props = next_data["props"]["pageProps"]
    
    # cari list komoditas (nama bisa berubah, kita cari yang ada 'price')
    komoditas = []
    # biasanya di initialState.commodity.list atau di props.commodities
    try:
        raw = props["initialState"]["commodity"]["list"]
    except:
        # fallback cari di semua props
        raw = []
        for v in str(props):
            pass
        # jika tidak ketemu, cari di halaman lain
        raw = props.get("commodities", [])
    
    for item in raw:
        nama = item.get("name") or item.get("commodity_name") or item.get("komoditas")
        harga = int(item.get("price", item.get("harga", 0)))
        # selisih bisa positif/negatif
        selisih = int(item.get("change", item.get("selisih", 0)) or 0)
        
        # harga per pasar
        pasar = {}
        for m in item.get("markets", [])[:10]:
            slug = m.get("slug", "").lower()
            if "sunter" in slug: pasar["sunter"] = int(m.get("price",0))
            if "senen" in slug: pasar["senen"] = int(m.get("price",0))
            if "kramat" in slug: pasar["kramat"] = int(m.get("price",0))
            if "minggu" in slug: pasar["minggu"] = int(m.get("price",0))
        
        if nama and harga > 0:
            komoditas.append({
                "nama": nama,
                "harga": harga,
                "selisih": selisih,
                "pasar": pasar
            })
    
    return komoditas

def main():
    data = scrape()
    if not data:
        raise Exception("Gagal ambil data dari infopangan")
    
    tz = pytz.timezone("Asia/Jakarta")
    out = {
        "updated_at": datetime.now(tz).isoformat(),
        "komoditas": sorted(data, key=lambda x: x["nama"])
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    print(f"Sukses: {len(data)} komoditas dari infopangan.jakarta.go.id")

if __name__ == "__main__":
    main()
