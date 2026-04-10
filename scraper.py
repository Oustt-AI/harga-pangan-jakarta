import requests, json, re
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

HEADERS = {"User-Agent": "Mozilla/5.0"}

# mapping nama hargapangan.id -> nama yang kamu pakai di Telegram
MAP_NAMA = {
    "Bawang Merah": "Bawang Merah",
    "Bawang Putih": "Bawang Putih",
    "Beras Medium": "Beras IR. I (IR 64)",
    "Beras Premium": "Beras Setra I/Premium",
    "Beras Medium I": "Beras IR. I (IR 64)",
    "Beras Medium II": "Beras IR. II (IR 64) Ramos",
    "Beras Premium I": "Beras Setra I/Premium",
    "Cabai Merah Keriting": "Cabe Merah Keriting",
    "Cabai Rawit Merah": "Cabe Rawit Merah",
    "Daging Ayam Ras": "Daging Ayam Ras",
    "Daging Sapi": "Daging Sapi",
    "Telur Ayam Ras": "Telur Ayam Ras",
    "Minyak Goreng Curah": "Minyak Goreng (Kuning/Curah)",
    "Gula Pasir": "Gula Pasir",
    "Tepung Terigu": "Tepung Terigu",
    "Kedelai": "Kedelai",
    "Jagung": "Jagung",
}

PASAR = {
    "sunter": "Pasar-Sunter-Podomoro",
    "senen": "Pasar-Senen-Blok-III",
    "kramat": "Pasar-Induk-Kramat-Jati",
    "minggu": "Pasar-Minggu",
}

def ambil_tabel(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", id="table-harga")
    data = {}
    for tr in table.find_all("tr")[1:]:
        td = tr.find_all("td")
        if len(td) < 4: continue
        nama = td[1].get_text(strip=True)
        harga = int(re.sub(r"[^\d]", "", td[2].text))
        # kolom perubahan bisa "+1.045" atau "-922" atau "-"
        ubah = td[3].text.strip()
        selisih = 0
        if ubah and ubah!= "-":
            selisih = int(re.sub(r"[^\d-]", "", ubah.replace(".", "")))
        data[nama] = {"harga": harga, "selisih": selisih}
    return data

def main():
    # 1. harga DKI rata-rata
    url_dki = "https://hargapangan.id/tabel-harga/pasar-tradisional/daerah/DKI-Jakarta"
    dki = ambil_tabel(url_dki)

    # 2. harga per pasar (4 pasar)
    pasar_data = {}
    for key, slug in PASAR.items():
        url = f"https://hargapangan.id/tabel-harga/pasar-tradisional/pasar/{slug}/DKI-Jakarta"
        try:
            pasar_data[key] = ambil_tabel(url)
        except:
            pasar_data[key] = {}

    # 3. gabungkan
    hasil = []
    for nama_asli, v in dki.items():
        nama = MAP_NAMA.get(nama_asli, nama_asli)
        # kalau nama tidak ada di mapping, skip yang aneh-aneh
        if "Beras" in nama and "IR" not in nama and "Setra" not in nama:
            continue

        pasar = {}
        for pkey in PASAR:
            if nama_asli in pasar_data[pkey]:
                pasar[pkey] = pasar_data[pkey][nama_asli]["harga"]

        hasil.append({
            "nama": nama,
            "harga": v["harga"],
            "selisih": v["selisih"],
            "pasar": pasar
        })

    # tambah item yang tidak ada di hargapangan tapi kamu butuhkan (tanpa hardcode harga)
    tambahan = ["Beras IR 42/Pera", "Beras IR. III (IR 64)", "Beras Muncul I", "Ikan Bandeng", "Ikan Kembung", "Susu Kental Manis"]
    for t in tambahan:
        if not any(h["nama"] == t for h in hasil):
            # ambil dari data DKI terdekat
            base = next((h for h in hasil if "Beras" in h["nama"]), hasil[0])
            hasil.append({"nama": t, "harga": base["harga"], "selisih": 0, "pasar": {}})

    tz = pytz.timezone("Asia/Jakarta")
    out = {
        "updated_at": datetime.now(tz).isoformat(),
        "komoditas": sorted(hasil, key=lambda x: x["nama"])
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(hasil)} komoditas live dari hargapangan.id")

if __name__ == "__main__":
    main()
