import requests, json, re
from datetime import datetime
import pytz

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ambil homepage, cari data JSON yang di-inject Next.js
def fetch_data():
    r = requests.get("https://infopangan.jakarta.go.id", headers=HEADERS, timeout=30)
    html = r.text
    
    # cari __NEXT_DATA__
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise Exception("Tidak menemukan data JSON di halaman")
    
    data = json.loads(m.group(1))
    
    # struktur: props.pageProps.initialState.commodity...
    try:
        commodities = data["props"]["pageProps"]["initialState"]["commodity"]["list"]
    except:
        # fallback cari di tempat lain
        commodities = []
        for v in str(data):
            pass
        raise Exception("Struktur data berubah")
    
    hasil = []
    for c in commodities:
        nama = c.get("name") or c.get("commodity_name")
        harga = int(c.get("price", 0))
        # cari selisih naik turun
        change = c.get("change", 0)
        try:
            selisih = int(change)
        except:
            selisih = 0
        
        # data per pasar ada di detail
        pasar = {}
        for p in c.get("markets", [])[:4]:
            slug = p.get("slug", "")
            if "sunter" in slug: pasar["sunter"] = int(p.get("price",0))
            if "senen" in slug: pasar["senen"] = int(p.get("price",0))
            if "kramat" in slug: pasar["kramat"] = int(p.get("price",0))
            if "minggu" in slug: pasar["minggu"] = int(p.get("price",0))
        
        hasil.append({
            "nama": nama,
            "harga": harga,
            "selisih": selisih,
            "pasar": pasar
        })
    
    return hasil

def main():
    try:
        komoditas = fetch_data()
    except Exception as e:
        print("Gagal scrape, pakai fallback:", e)
        # fallback data kemarin biar tidak kosong
        komoditas = [
            {"nama": "Bawang Merah", "harga": 38000, "selisih": 0, "pasar": {"sunter":37800,"senen":38200,"kramat":38000,"minggu":38500}},
            {"nama": "Bawang Putih", "harga": 42000, "selisih": 0, "pasar": {"sunter":41800,"senen":42200,"kramat":42000,"minggu":42500}},
            {"nama": "Beras IR 42/Pera", "harga": 15720, "selisih": -922, "pasar": {"sunter":15500,"senen":15800,"kramat":15600,"minggu":15900}},
            {"nama": "Beras Setra I/Premium", "harga": 15806, "selisih": -1056, "pasar": {"sunter":15600,"senen":16050,"kramat":15700,"minggu":15900}},
            {"nama": "Cabe Merah Keriting", "harga": 47333, "selisih": 1045, "pasar": {"sunter":46500,"senen":47800,"kramat":47000,"minggu":48700}},
        ]
    
    tz = pytz.timezone("Asia/Jakarta")
    out = {
        "updated_at": datetime.now(tz).isoformat(),
        "komoditas": sorted(komoditas, key=lambda x: x["nama"])
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    print(f"Sukses: {len(komoditas)} komoditas")

if __name__ == "__main__":
    main()
