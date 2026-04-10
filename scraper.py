import requests, re, json
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

HEADERS = {"User-Agent": "Mozilla/5.0"}
PASAR = {
    "sunter": "pasar-sunter-podomoro",
    "senen": "pasar-senen-blok-iii-vi",
    "kramat": "pasar-induk-kramat-jati",
    "minggu": "pasar-minggu",
}

def scrape_home():
    r = requests.get("https://infopangan.jakarta.go.id", headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    data = {}
    for el in soup.find_all(string=re.compile(r"Rp\s*[\d\.]+")):
        txt = el.parent.get_text(" ", strip=True)
        m = re.search(r"([A-Za-z0-9\.\(\)\/\s]{4,50}?)\s+R?p?\s*([\d\.]+)", txt)
        if not m: continue
        nama = re.sub(r"\s+", " ", m.group(1)).strip()
        harga = int(m.group(2).replace(".", ""))
        selisih = 0
        if "Naik" in txt:
            s = re.search(r"Naik\s*R?p?\s*([\d\.]+)", txt)
            if s: selisih = int(s.group(1).replace(".", ""))
        elif "Turun" in txt:
            s = re.search(r"Turun\s*R?p?\s*([\d\.]+)", txt)
            if s: selisih = -int(s.group(1).replace(".", ""))
        if len(nama) > 3:
            data[nama.lower()] = {"nama": nama, "harga": harga, "selisih": selisih}
    return data

def scrape_pasar(slug):
    r = requests.get(f"https://infopangan.jakarta.go.id/market/{slug}", headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    out = {}
    for el in soup.find_all(string=re.compile(r"Rp\s*[\d\.]+")):
        txt = el.parent.get_text(" ", strip=True)
        m = re.search(r"([A-Za-z0-9\.\(\)\/\s]{4,50}?)\s+R?p?\s*([\d\.]+)", txt)
        if m:
            nama = re.sub(r"\s+", " ", m.group(1)).strip().lower()
            harga = int(m.group(2).replace(".", ""))
            out[nama] = harga
    return out

def main():
    home = scrape_home()
    pasar_data = {k: scrape_pasar(v) for k,v in PASAR.items()}

    hasil = []
    for key, d in home.items():
        pasar = {}
        for p_name, p_dict in pasar_data.items():
            if key in p_dict:
                pasar[p_name] = p_dict[key]
        d["pasar"] = pasar
        hasil.append(d)

    hasil = sorted(hasil, key=lambda x: x["nama"])

    tz = pytz.timezone("Asia/Jakarta")
    out = {
        "updated_at": datetime.now(tz).isoformat(),
        "komoditas": hasil
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
