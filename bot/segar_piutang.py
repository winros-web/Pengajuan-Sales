"""Bot SEGAR PIUTANG (Kak Intan 24 Nov 2026: "ada yg udah lunas tapi masih ada di tagihan" ->
"dibikin bot nya ya 30 menit sekali tarik data di accurate").

data/piutang.json hanya ditarik sekali tiap malam/pagi, jadi nota yang dilunasi siang hari masih
tampil di tab Tagih via WA (dan tab piutang lain). Skrip ini menarik faktur BELUM LUNAS dari
Accurate tiap 30 menit (Task Scheduler "Gio - Segar Piutang"), membandingkannya dengan
data/piutang.json yang sedang dipakai halaman, lalu menulis SELISIHNYA saja ke penyimpan
Apps Script (perbarui/segar_piutang) untuk tiap halaman:

    {dibuat, dasar, lunas:[nomor...], ubah:{nomor: sisa}, baru:[baris penuh...], jumlah:{...}}

Halaman memakai selisih itu di atas data/piutang.json: nota lunas dibuang, sisa diperbarui, nota
baru ditambahkan - tanpa menerbitkan ulang situs. Accurate HANYA DIBACA (sales-invoice/list.do).

    python -I bot\\segar_piutang.py            sekali jalan (dipakai Task Scheduler tiap 30 menit)
    python -I bot\\segar_piutang.py --uji      tarik + hitung, TIDAK menulis ke penyimpan
Log: skrip\\log\\segar-piutang.log
"""
import datetime
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIO = os.path.dirname(REPO)
LOG = os.path.join(GIO, "skrip", "log", "segar-piutang.log")
STATUS = os.path.join(GIO, "skrip", "log", "segar-piutang.json")
DASAR = os.path.join(GIO, "dashboard", "data", "piutang.json")
KUNCI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "segar_piutang.lock")

# halaman penyimpan -> nama cabang (gudang) Accurate; harus sama dengan CABANG_HAL di apps_script/Kode.gs
CABANG_HAL = {"jakarta": ["JAKARTA", "TANGERANG"], "bandung": ["BANDUNG"], "medan": ["MEDAN"],
              "palembang": ["PALEMBANG"], "lampung": ["LAMPUNG"], "gresik": ["GRESIK"],
              "kaltim": ["KALIMANTAN TIMUR"], "makassar": ["MAKASSAR"]}
BARU_MAKS = 400          # baris baru yang dikirim per halaman (yang terbaru dulu)
BATAS_BITA = 38000       # penyimpan Apps Script menolak dokumen yang lebih besar dari ini
TULIS_TIAP = 2 * 3600    # walau tidak ada perubahan, segarkan jam-nya tiap 2 jam


def catat(*a):
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + " ".join(str(x) for x in a)
    try:
        print(t, flush=True)
    except Exception:  # noqa: BLE001 - pythonw tanpa konsol
        pass
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(t + "\n")


def eks():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import eksekutor_pengajuan as m  # noqa: E402 - tanpa efek samping saat diimpor
    return m


def tgl(v):
    """tanggal Accurate dd/mm/yyyy -> yyyy-mm-dd (sama seperti dashboard_penjualan.py)"""
    v = (v or "").strip()
    if not v:
        return ""
    try:
        d, b, t = v.split("/")
        return "%s-%s-%s" % (t, b.zfill(2), d.zfill(2))
    except ValueError:
        return ""


def tarik(ek):
    """Semua faktur penjualan yang masih ada sisanya. Satu jalur, 100 baris per halaman."""
    rows, page = [], 1
    while True:
        j = ek.acc("sales-invoice/list.do", {
            "fields": "id,number,transDate,dueDate,primeOwing,totalAmount,customer,masterSalesman,branch,paymentTerm",
            "filter.outstanding": "true", "sp.sort": "id|asc", "sp.page": str(page), "sp.pageSize": "100"})
        d = j.get("d") or []
        rows.extend(d)
        sp = j.get("sp") or {}
        if len(d) < 100 or (sp.get("pageCount") and page >= int(sp["pageCount"])) or page > 400:
            break
        page += 1
    return rows


def baris(p, hari_ini):
    jtp = tgl(p.get("dueDate"))
    lewat = (hari_ini - datetime.date.fromisoformat(jtp)).days if jtp else 0
    termin = ((p.get("paymentTerm") or {}).get("name") or "").strip()
    return {
        "nomor": p.get("number"), "tgl": tgl(p.get("transDate")), "jatuh_tempo": jtp,
        "pelanggan": (p.get("customer") or {}).get("name"),
        "cabang": (p.get("branch") or {}).get("name") or "-",
        "sales_id": (p.get("masterSalesman") or {}).get("id") or 0,
        "sisa": round(float(p.get("primeOwing") or 0), 2),
        "total": round(float(p.get("totalAmount") or 0), 2),
        "hari_lewat": max(lewat, 0), "termin": termin,
        "cod": "COD" in termin.upper().replace(".", "").replace(" ", ""),
        "kecil": None,
    }


def main():
    uji = "--uji" in sys.argv
    if os.path.exists(KUNCI) and time.time() - os.path.getmtime(KUNCI) < 1800:
        catat("masih ada tarikan yang jalan - dilewati")
        return
    open(KUNCI, "w").write(str(os.getpid()))
    try:
        ek = eks()
        dasar = json.load(open(DASAR, encoding="utf-8"))
        dasar_jam = datetime.datetime.fromtimestamp(os.path.getmtime(DASAR)).strftime("%Y-%m-%dT%H:%M:%S")
        peta_dasar = {r["nomor"]: r for r in dasar if r.get("nomor")}
        mulai = time.time()
        rows = tarik(ek)
        hari_ini = datetime.date.today()
        kini = {}
        for p in rows:
            if p.get("number"):
                kini[p["number"]] = p
        catat("tarik %d faktur belum lunas (%.0f dtk), dasar %d baris per %s"
              % (len(kini), time.time() - mulai, len(peta_dasar), dasar_jam))

        lunas = [n for n in peta_dasar if n not in kini]
        ubah, baru = {}, []
        for n, p in kini.items():
            sisa = round(float(p.get("primeOwing") or 0), 2)
            lama = peta_dasar.get(n)
            if lama is None:
                baru.append(baris(p, hari_ini))
            elif abs(float(lama.get("sisa") or 0) - sisa) >= 1:
                ubah[n] = sisa
        baru.sort(key=lambda r: r.get("tgl") or "", reverse=True)
        catat("  lunas %d, sisa berubah %d, nota baru %d" % (len(lunas), len(ubah), len(baru)))

        isi_per_hal = {}
        for hal in ["pusat"] + list(CABANG_HAL) + ["admin-" + h for h in CABANG_HAL]:
            cab = CABANG_HAL.get(hal.replace("admin-", ""))
            if cab is None:
                lun, ub, br = lunas, ubah, baru
            else:
                lun = [n for n in lunas if (peta_dasar[n].get("cabang") or "") in cab]
                ub = {n: v for n, v in ubah.items() if ((kini[n].get("branch") or {}).get("name") or "") in cab}
                br = [r for r in baru if r["cabang"] in cab]
            isi = {
                "dibuat": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "dasar": dasar_jam,
                "lunas": sorted(lun), "ubah": ub, "baru": br[:BARU_MAKS],
                "jumlah": {"lunas": len(lun), "ubah": len(ub), "baru": len(br), "outstanding": len(kini)}}
            # dipangkas supaya muat di penyimpan: nota baru dibuang dari yang paling lama,
            # lunas & sisa-berubah dipertahankan (itu yang membuat nota lunas hilang dari tagihan)
            while len(json.dumps(isi, ensure_ascii=False)) > BATAS_BITA and isi["baru"]:
                isi["baru"] = isi["baru"][:max(0, len(isi["baru"]) * 3 // 4 - 1)]
            isi["baru_dipotong"] = len(br) - len(isi["baru"])
            if len(json.dumps(isi, ensure_ascii=False)) > BATAS_BITA:
                isi["ubah"] = {}
                isi["jumlah"]["ubah_dibuang"] = len(ub)
            isi_per_hal[hal] = isi

        # tulis hanya kalau isinya berubah (atau sudah lebih dari 2 jam) supaya penyimpan tidak dibanjiri
        sidik = json.dumps({h: [i["lunas"], i["ubah"], [r["nomor"] for r in i["baru"]]]
                            for h, i in isi_per_hal.items()}, sort_keys=True)
        try:
            st = json.load(open(STATUS, encoding="utf-8"))
        except (OSError, ValueError):
            st = {}
        if st.get("sidik") == sidik and time.time() - float(st.get("waktu") or 0) < TULIS_TIAP:
            catat("  tidak ada perubahan - penyimpan tidak ditulis")
            return
        if uji:
            catat("  [uji] tidak menulis ke penyimpan")
            return
        ek.apps({"aksi": "tulis", "tulis": [{"halaman": h, "koleksi": "perbarui", "id": "segar_piutang",
                                             "mode": "set", "data": i} for h, i in isi_per_hal.items()]})
        json.dump({"sidik": sidik, "waktu": time.time()}, open(STATUS, "w", encoding="utf-8"))
        catat("  ditulis ke %d halaman" % len(isi_per_hal))
    except Exception as e:  # noqa: BLE001 - jadwal 30 menit, cukup dicatat
        catat("GALAT:", repr(e)[:400])
    finally:
        try:
            os.remove(KUNCI)
        except OSError:
            pass


if __name__ == "__main__":
    main()
