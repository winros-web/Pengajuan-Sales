"""Bot PENGAJUAN SALES -> Accurate (Kak Intan, 13 Nov 2026). Versi 2: aturan kerja lengkap 30 Okt 2026
(MACAN / KANCIL / KELINCI, berkas "ATURAN PENGAJUAN SALES 2026").

Tiap 5 detik membaca penyimpan Apps Script (kunci ADMIN). Pengajuan ACC / ACC sementara dikerjakan:

  limit   Naik limit: Batas maks. piutang = limit ACC Ibu (kosong = yang diajukan). Catatan `dd/mm/yy naik 30jt dr 160jt (agen)`.
          Limit lama Rp 1 (buka blokir): dikerjakan, salesman & kategori harga akun dilaporkan.
  umur    Naik umur: Batas umur piutang. Batas umur yang sedang tidak aktif dilaporkan.
  ACC sementara (limit/umur): nilai lama dipasang lagi jam 16.00 hari itu.
  toko    Toko baru: nama tanpa awalan "TOKO ", kategori harga per cabang (Medan BIT MDN, Palembang BIT PLB -0,85%,
          Bandung/Gresik/Lampung Umum, Jakarta+Tangerang zona 1, Kaltim/Makassar zona 3, toko online ONLINE TOKO),
          kategori diskon pkp / non pkp ikut isian sales, termin C.O.D 1 hari atau net N N hari (ACC Ibu menang),
          limit = limit ACC Ibu ("rp1" = Rp 1). Langkah pajak (klik Nama Wajib Pajak) tetap di layar Accurate:
          dicatat untuk admin.
  kompen  Kompen harga (KANCIL): cari dokumen Penyesuaian Harga "KOMPEN <BLN> <YY>" untuk kategori harga + cabang
          toko, ubah HANYA harga minimum = harga kompen / 1,11 - 2 (Kogja 17 Nov). Kode yang ditolak Ibu (barang[].acc
          false, ACC per kode) dilewati. Minimum yang berlaku sudah lebih rendah: tidak diubah.
          Kode belum ada: baris baru. Harga jual Accurate beda dengan rekap harga (harga_modal.json): kode itu ditahan.
          Aktif hanya bila BOT_KOMPEN=1 di .env (menunggu uji simpan sebagian dokumen SPA).
  edit_harga: aturan KELINCI = rekap dulu, eksekusi setelah Kak Intan setuju (rencana ke kolom eksekusi).
  revisi / edit_tgl: BOT_REVISI=1 -> dikerjakan langsung sesuai aturan KELINCI terbaru (Kak Intan 18 Nov 2026,
          lihat kerjakan_revisi / kerjakan_edit_tgl); tanpa BOT_REVISI tetap rekap.
  ktp     Ganti KTP (semua cabang, aturan MACAN 30 Okt / 14 & 17 Nov 2026): akun baru = salinan akun lama + KTP/NPWP
          baru, ID pelanggan = ID lama + nomor berikutnya (DILA 2 -> DILA 3), limit = SISA LIMIT seluruh rantai akun
          dibulatkan ke bawah ke juta (limit asli - [faktur belum lunas - giro] - belum terfaktur; ACC Ibu
          bernominal menang), catatan SATU baris "dd/m/yy akun lama <NAMA LAMA> ganti ktp, limit asli Yjt";
          akun lama diblokir limit Rp 1 + baris catatan blokir. Sisa limit <= 0 -> PERLU TANYA.
  buka    Buka blokir toko: limit akun (sekarang Rp 1) = limit ACC Ibu; salesman, kategori harga cabang, dan alasan
          blokir di catatan akun dilaporkan.
  ktp & buka dikerjakan hanya bila BOT_KTP=1 di .env; tanpa itu antre admin seperti sebelumnya.

Syarat sebelum dikerjakan = syarat di halaman (syaratKurang): konfirmasi WA KTP & bayar (toko/ktp/buka), catatan
supervisor untuk tempo, catatan supervisor cabang + Ko Li untuk naik limit, ceklis SPV (perlu_spv).
Sudah dikerjakan admin (catatan akun hari ini memuat nilai yang sama): Accurate tidak diubah.

Rahasia di D:\\AGEN AI\\AGEN IT (GIO)\\.env: PENGAJUAN_APPS_URL, PENGAJUAN_MASTER, ACCURATE_TULIS_TOKEN,
ACCURATE_TULIS_SECRET, opsional ACCURATE_HOST, PENGAJUAN_PENYETUJU, BOT_KOMPEN.

    python -I bot\\eksekutor_pengajuan.py --uji     tampilkan apa yang AKAN ditulis, tanpa menulis apa pun
    python -I bot\\eksekutor_pengajuan.py           jalan terus
Log: D:\\AGEN AI\\AGEN IT (GIO)\\skrip\\log\\pengajuan-bot.log, cadangan dokumen SPA sebelum diubah: skrip\\log\\cadangan_spa\\
"""
import base64, datetime, hashlib, hmac, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

GIO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = os.path.join(GIO, ".env")
LOG = os.path.join(GIO, "skrip", "log", "pengajuan-bot.log")
CADANGAN = os.path.join(GIO, "skrip", "log", "cadangan_spa")
HARGA_MODAL = os.path.join(GIO, "dashboard", "data", "harga_modal.json")
ARSIP_LAMPIRAN = r"G:\Shared drives\1. DOKUMEN INVOICE SVARNA ALL CABANG\PENGAJUAN SALES"
JEDA = 2  # Kak Intan 13 Nov: hitungan detik sesudah ACC
JAM_KEMBALI = (16, 0)
UJI = "--uji" in sys.argv
KAT_HARGA = {"MEDAN": "BIT MDN", "PALEMBANG": "BIT PLB -0,85%", "BANDUNG": "Umum", "GRESIK": "Umum", "LAMPUNG": "Umum",
             "JAKARTA": "zona 1", "TANGERANG": "zona 1", "KALIMANTAN TIMUR": "zona 3", "MAKASSAR": "zona 3"}
SPV_CABANG = {"PALEMBANG": "Ci Yanty", "LAMPUNG": "Mba Nani", "BANDUNG": "Bu Sulis", "GRESIK": "Mbak Lina"}
BULAN = ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS", "SEPT", "OKT", "NOV", "DES"]
REKAP_DULU = ("edit_harga", "revisi", "edit_tgl")
# 21 Nov 2026 (Kak Intan: "pengajuan kompen jakarta, palembang, makassar, langsung kompen saja, soalnya kategori
# harganya cuma 1 ya mba, jadi ga perlu cek nama pelanggan dan kategori harganya"): cabang ini tidak mencari akun
# pelanggan di Accurate; kategori harga = KAT_HARGA cabang. Tangerang ikut Jakarta (zona 1).
KOMPEN_SATU_KATEGORI = {"JAKARTA", "TANGERANG", "PALEMBANG", "MAKASSAR"}
ANTRE_ADMIN = {"kompen_sharp": "kompensasi Sharp diurus lewat ACC pabrik, bukan Accurate"}
# ganti KTP & buka blokir sudah ditulis bot (aturan MACAN), tapi hanya jalan kalau BOT_KTP=1 di .env
ANTRE_TANPA_KTP = {"ktp": "ganti KTP: bot siap, menunggu BOT_KTP=1 di .env",
                   "buka": "buka blokir: bot siap, menunggu BOT_KTP=1 di .env"}

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def env():
    isi = {}
    if os.path.exists(ENV):
        for b in open(ENV, encoding="utf-8"):
            if "=" in b and not b.lstrip().startswith("#"):
                k, v = b.split("=", 1)
                isi[k.strip()] = v.strip().strip('"')
    return isi


E = env()


def catat(*a):
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(x) for x in a)
    print(t, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(t + "\n")


class PerluTanya(Exception):
    pass


class Dikembalikan(Exception):
    """data pengajuan beda dengan Accurate - kembalikan ke sales (status dikembalikan + catatan)"""


class Sebagian(Exception):
    """sebagian langkah SUDAH tertulis di Accurate, sisanya berhenti (Kak Intan 21 Nov 2026: jangan tampil
    'Gagal - cek agen' kalau DO-nya sudah terhapus; tulis 'Hapus DO berhasil · SO perlu cek')."""
    def __init__(self, ringkas, rinci):
        super().__init__(rinci)
        self.ringkas = ringkas


class Sibuk(Exception):
    """Accurate 429 terus-menerus (kuota token dipakai proses lain) - coba lagi nanti, jangan Gagal"""


_sibuk_sampai = 0.0


# ---------------- penyimpan Apps Script ----------------
def kunci_admin():
    return hmac.new(E["PENGAJUAN_MASTER"].encode(), b"ADMIN", hashlib.sha256).hexdigest()


def apps(isi):
    body = json.dumps({"halaman": "ADMIN", "kunci": kunci_admin(), **isi}).encode()
    req = urllib.request.Request(E["PENGAJUAN_APPS_URL"], data=body, method="POST", headers={"Content-Type": "text/plain;charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.load(r)
    if not j.get("ok"):
        raise RuntimeError("penyimpan: " + str(j.get("galat")))
    return j


def ubah_pengajuan(pid, data):
    if UJI:
        catat("  [uji] dashboard ->", json.dumps(data, ensure_ascii=False)[:400]); return
    apps({"aksi": "tulis", "tulis": [{"halaman": "pusat", "koleksi": "pengajuan", "id": pid, "mode": "update", "data": data}]})


# ---------------- Accurate (token khusus bot) ----------------
HOST = E.get("ACCURATE_HOST") or "https://zeus.accurate.id"


def _kepala():
    ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    sig = base64.b64encode(hmac.new(E["ACCURATE_TULIS_SECRET"].encode(), ts.encode(), hashlib.sha256).digest()).decode()
    return {"Authorization": "Bearer " + E["ACCURATE_TULIS_TOKEN"], "X-Api-Timestamp": ts, "X-Api-Signature": sig}


def acc(ep, params=None, tulis=False):
    url = HOST + "/accurate/api/" + ep
    data = None
    if tulis:
        if UJI:
            catat("  [uji] POST", ep, json.dumps(params, ensure_ascii=False)[:700]); return {"s": True, "d": "uji", "r": {}}
        data = urllib.parse.urlencode(params).encode()
    elif params:
        url += "?" + urllib.parse.urlencode(params)
    # 429 = batas 8 permintaan/detik (bisa terpakai proses lain di database yang sama): tunggu lalu coba lagi
    for coba in range(6):
        req = urllib.request.Request(url, data=data, method="POST" if tulis else "GET", headers=_kepala())
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                j = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and coba < 5:
                time.sleep(1 + coba)
                continue
            if e.code == 429:
                raise Sibuk("Accurate sibuk (HTTP 429, kuota token dipakai proses lain)")
            raise RuntimeError("Accurate HTTP %s: %s" % (e.code, e.read()[:300].decode("utf-8", "replace")))
    time.sleep(0.15)  # batas Accurate 8 permintaan/detik
    if not j.get("s"):
        raise RuntimeError("Accurate menolak: " + json.dumps(j.get("d"), ensure_ascii=False)[:400])
    return j


def jt(v):
    v = float(v or 0)
    if v >= 1e6:
        return ("%.2f" % (v / 1e6)).rstrip("0").rstrip(".") + "jt"
    return "rp%d" % v


def rp(v):
    return "{:,.0f}".format(float(v or 0)).replace(",", ".")


def hari_ini():
    return datetime.datetime.now().strftime("%d/%m/%y")


def catatan_baru(lama, baris):
    return ((lama or "").rstrip() + "\n" + baris + " (agen)").strip()[-2000:]


def pelanggan_dari(p):
    pid = p.get("pelanggan_id")
    if not pid:
        # nama akun Accurate dari halaman; kalau kosong (akun baru, belum ada di tarikan malam) pakai nama toko
        for nama in [(p.get("pelanggan_accurate") or "").strip(), (p.get("toko") or "").strip()]:
            if not nama:
                continue
            cocok = {nama.upper(), nama_toko(nama), "TOKO " + nama_toko(nama)}
            ada = [x for x in acc("customer/list.do", {"fields": "id,name,suspended", "filter.keywords.op": "CONTAIN",
                                                        "filter.keywords.val[0]": nama_toko(nama) or nama, "sp.pageSize": "50"})["d"]
                   if str(x.get("name", "")).strip().upper() in cocok]
            # 21 Nov 2026 (TUNAS ELEKTRONIK Palembang): akun lama yang sudah di-suspend bukan kembaran - abaikan
            if len(ada) > 1 and len([x for x in ada if not x.get("suspended")]) == 1:
                ada = [x for x in ada if not x.get("suspended")]
            if len(ada) == 1:
                pid = ada[0]["id"]
                break
    if not pid:
        raise Dikembalikan("cek nama toko: nama akun Accurate '%s' tidak cocok persis satu akun" % (p.get("pelanggan_accurate") or p.get("toko")))
    return acc("customer/detail.do", {"id": pid})["d"]


def sudah_admin(c, kata):
    """catatan akun hari ini sudah memuat nilai yang sama -> admin sudah mengerjakan"""
    t = hari_ini()
    return any(t in b and kata.lower() in b.lower() for b in (c.get("notes") or "").splitlines())


# ---------------- syarat (sama dengan syaratKurang di halaman) ----------------
def butuh_spv(p):
    return p.get("jenis") in ("limit", "umur") or (p.get("jenis") in ("toko", "ktp", "buka") and p.get("bayar") and p.get("bayar") != "COD")


def syarat_kurang(p):
    k = []
    j = p.get("jenis")
    konf = p.get("konfirmasi") or {}
    if j in ("toko", "ktp", "buka"):
        if not konf.get("ktp"):
            k.append("KTP/NPWP belum dikonfirmasi WA admin")
        if j == "toko" and not konf.get("bayar"):
            k.append("pembayaran belum dikonfirmasi WA admin")
    # Kak Intan 17 Nov 2026 (aturan MACAN): catatan supervisor (Ko Li / Bu Sulis / Mba Nani / Mbak Lina / Ci Yanty)
    # TIDAK lagi menahan eksekusi - "yang penting sudah ada ACC di kolom ACC". Catatannya tetap diisi di halaman dan
    # tetap terlihat di kolom Syarat agen, hanya tidak dipakai menunda pekerjaan lagi.
    if p.get("perlu_spv") and not p.get("spv_konfirmasi") and j != "toko":
        k.append("belum diceklis SPV cabang")
    return k


# ---------------- lampiran: arsip Drive per toko + link di Catatan akun ----------------
def _aman(t):
    return re.sub(r'[\\/:*?"<>|]+', " ", str(t or "")).strip()[:80]


def arsip_lampiran(p):
    """Unduh lampiran pengajuan (link Drive 'siapa saja dengan link') ke PENGAJUAN SALES/<CABANG>/<TOKO>/ dengan nama
    '<KET> <TOKO> <n>.<ext>' (pola folder yang sudah dipakai admin). Kembalikan daftar link. Gagal arsip tidak
    menggagalkan pengajuan."""
    toko = _aman((p.get("toko") or "").upper())
    folder = os.path.join(ARSIP_LAMPIRAN, _aman((p.get("cabang") or "LAIN").upper()), toko)
    sumber = os.path.join(folder, ".sumber.txt")
    links = []
    for f in p.get("foto") or []:
        m = re.search(r"/d/([\w-]{20,})", f.get("url") or "")
        if not m:
            continue
        links.append(f["url"])
        if UJI or not os.path.isdir(ARSIP_LAMPIRAN):
            continue
        try:
            os.makedirs(folder, exist_ok=True)
            if os.path.exists(sumber) and m.group(1) in open(sumber, encoding="utf-8").read():
                continue  # sudah diarsip
            ext = os.path.splitext(f.get("nama") or "")[1].lower() or ".jpg"
            dasar = "%s %s" % (_aman((f.get("ket") or "lampiran").upper()), toko)
            n = 1
            while os.path.exists(os.path.join(folder, "%s %d%s" % (dasar, n, ext))):
                n += 1
            url = "https://drive.usercontent.google.com/download?id=%s&export=download" % m.group(1)
            with urllib.request.urlopen(url, timeout=120) as r:
                isi = r.read()
            nama = os.path.join(folder, "%s %d%s" % (dasar, n, ext))
            with open(nama, "wb") as w:
                w.write(isi)
            with open(sumber, "a", encoding="utf-8") as w:
                w.write(m.group(1) + " " + os.path.basename(nama) + "\n")
        except Exception as e:  # noqa: BLE001
            catat("  arsip lampiran gagal:", e)
    return links


def catatan_lampiran(notes, p):
    links = arsip_lampiran(p)
    if not links:
        return notes
    return catatan_baru(notes, "%s dokumen pengajuan: %s" % (hari_ini(), " , ".join(links)))


# ---------------- MACAN: limit, umur, toko ----------------
def kerjakan_limit(p):
    c = pelanggan_dari(p)
    baru = p.get("acc_limit") if p.get("acc_limit") is not None else p.get("nilai")
    if not baru:
        raise Dikembalikan("cek limit: nilai limit kosong")
    baru = float(baru)
    lama = float(c.get("customerLimitAmountValue") or 0) if c.get("customerLimitAmount") else 0
    if baru < lama and p.get("acc_limit") is None:
        # aturan MACAN: ACC "OK" = limit JADI angka pengajuan; "+X" / "naik X" = limit lama + X. Bot tidak menebak.
        raise Dikembalikan("cek limit: limit diajukan %s lebih kecil dari limit sekarang %s - kalau maksudnya naik %s jadi %s, "
                         "isi limit TOTAL yang diminta, atau Ibu tulis nominalnya di kolom ACC" % (jt(baru), jt(lama), jt(baru), jt(lama + baru)))
    sem = p.get("status") == "acc_sementara"
    # format admin: "26/10/26 naik 25jt dr 100jt" = naik SELISIHNYA dari limit lama (Kak Intan 13 Nov 2026)
    arah = "naik" if baru >= lama else "turun"
    ket = "%s %s %s dr %s%s" % (hari_ini(), arah, jt(abs(baru - lama)), jt(lama), " sementara s.d. 16.00" if sem else "")
    if sudah_admin(c, "%s %s" % (arah, jt(abs(baru - lama)))):
        return "sudah dikerjakan admin (catatan akun hari ini sama), Accurate tidak diubah", {}
    acc("customer/save.do", {"id": c["id"], "customerLimitAmount": "true", "customerLimitAmountValue": str(int(baru)),
                             "notes": catatan_lampiran(catatan_baru(c.get("notes"), ket), p)}, tulis=True)
    if not UJI:
        c2 = acc("customer/detail.do", {"id": c["id"]})["d"]
        if float(c2.get("customerLimitAmountValue") or 0) != baru:
            raise RuntimeError("dibaca ulang: limit di Accurate %s, bukan %s" % (jt(c2.get("customerLimitAmountValue")), jt(baru)))
    tambah = ""
    if lama == 1:
        # aturan MACAN: buka blokir ditandai HIJAU dan tab Penjualan akun dicek - akun yang diblokir sering
        # salesman-nya kosong dan kategori harganya masih "Umum" padahal cabangnya berkategori khusus.
        # Alasan blokir = baris "blokir" terakhir di catatan akun (Kogja 18 Nov 2026).
        kat = (c.get("priceCategory") or {}).get("name")
        wajib = KAT_HARGA.get((p.get("cabang") or c.get("customerBranchName") or "").upper())
        sls = (c.get("salesman") or {}).get("name") if isinstance(c.get("salesman"), dict) else None
        tambah = " | buka blokir: salesman %s, kategori harga %s%s" % (
            sls or "KOSONG - admin isi", kat or "kosong",
            "" if not wajib or (kat or "").strip().lower() == wajib.lower() else " (cabang ini memakai %s - admin cek)" % wajib)
        alasan = [b.strip() for b in (c.get("notes") or "").splitlines() if "blokir" in b.lower()]
        if alasan:
            tambah += " | alasan blokir di catatan: " + alasan[-1][:140]
    return "limit %s -> %s, id %s%s" % (jt(lama), jt(baru), c["id"], tambah), {"limit": lama, "limit_aktif": bool(c.get("customerLimitAmount")), "id": c["id"]}


def kerjakan_umur(p):
    c = pelanggan_dari(p)
    baru = p.get("nilai")
    if not baru:
        raise Dikembalikan("cek umur: umur (hari) kosong")
    baru = int(baru)
    aktif = bool(c.get("customerLimitAge"))
    lama = int(c.get("customerLimitAgeValue") or 0) if aktif else 0
    sem = p.get("status") == "acc_sementara"
    ket = "%s umur %s hr dr %s hr%s" % (hari_ini(), baru, lama, " sementara s.d. 16.00" if sem else "")
    if sudah_admin(c, "umur %s" % baru):
        return "sudah dikerjakan admin, Accurate tidak diubah", {}
    acc("customer/save.do", {"id": c["id"], "customerLimitAge": "true", "customerLimitAgeValue": str(baru),
                             "notes": catatan_lampiran(catatan_baru(c.get("notes"), ket), p)}, tulis=True)
    if not UJI:
        c2 = acc("customer/detail.do", {"id": c["id"]})["d"]
        if int(c2.get("customerLimitAgeValue") or 0) != baru:
            raise RuntimeError("dibaca ulang: umur di Accurate %s, bukan %s" % (c2.get("customerLimitAgeValue"), baru))
    return "umur %s -> %s hari, id %s%s" % (lama, baru, c["id"], "" if aktif else " | batas umur akun tadinya TIDAK aktif"), \
        {"umur": lama, "umur_aktif": aktif, "id": c["id"]}


def nama_toko(t):
    t = re.sub(r"\s+", " ", (t or "").strip().upper())
    return re.sub(r"^TOKO\s+", "", t)


def kerjakan_toko(p):
    nama = nama_toko(p.get("toko"))
    if not nama:
        raise Dikembalikan("cek nama toko: nama toko kosong")
    for f in ("alamat", "hp", "owner"):
        if not str(p.get(f) or "").strip():
            raise Dikembalikan("cek data toko: isian kosong - " + f)
    ada = acc("customer/list.do", {"fields": "id,name,customerNo", "filter.keywords.op": "CONTAIN", "filter.keywords.val[0]": nama, "sp.pageSize": "50"})["d"]
    if any(str(x.get("name", "")).strip().upper() in (nama, "TOKO " + nama) for x in ada):
        return "sudah ada akun bernama %s (dibuat admin?), Accurate tidak diubah" % nama, {}
    # ID Pelanggan = nama pelanggan (Kogja 16 Nov 2026); ID sudah dipakai akun lain -> tanya, jangan menebak
    if any(str(x.get("customerNo", "")).strip().upper() == nama for x in ada):
        raise PerluTanya("ID pelanggan %s sudah dipakai akun lain - admin tentukan ID" % nama)
    cab = (p.get("cabang") or "").upper()
    kat = "ONLINE TOKO" if (p.get("jenis_toko") or "").upper() == "ONLINE" else KAT_HARGA.get(cab)
    if not kat:
        raise PerluTanya("kategori harga untuk cabang %s belum ada aturannya" % cab)
    cod = bool(p.get("acc_cod")) or not p.get("bayar") or p.get("bayar") == "COD"
    hari = 1 if cod else int(p.get("acc_tempo") or p.get("tempo") or 30)
    termin = "C.O.D" if cod else "net %d" % hari
    limit = p.get("acc_limit") if p.get("acc_limit") is not None else p.get("nilai")
    if not limit:
        raise PerluTanya("limit ACC kosong")
    pkp = str(p.get("pkp") or "").strip().upper()
    diskon = "pkp" if pkp in ("PKP", "YA", "TRUE", "1") else "non pkp"
    data = {"name": nama, "customerNo": nama, "transDate": datetime.date.today().strftime("%d/%m/%Y"), "branchName": cab,
            "priceCategoryName": kat, "discountCategoryName": diskon, "termName": termin,
            "customerLimitAmount": "true", "customerLimitAmountValue": str(int(float(limit))),
            "customerLimitAge": "true", "customerLimitAgeValue": str(hari),
            "billStreet": (p.get("alamat") or "")[:250], "mobilePhone": (p.get("hp") or "")[:30],
            "notes": catatan_lampiran(catatan_baru("", "%s toko baru, limit %s sesuai acc ibu. Owner %s, NIK %s" % (
                hari_ini(), jt(limit), p.get("owner") or "-", p.get("nik") or "-")), p)}
    pajak, ket_pajak = data_pajak(p, kat)
    data.update(pajak)
    if p.get("sales_id"):
        try:
            data["salesmanNumber"] = acc("employee/detail.do", {"id": p["sales_id"]})["d"].get("number") or ""
        except Exception:  # noqa: BLE001
            pass
    r = acc("customer/save.do", data, tulis=True)
    rid = (r.get("r") or {}).get("id") if isinstance(r.get("r"), dict) else None
    sales_ok = ""
    if rid and not UJI:
        c2 = acc("customer/detail.do", {"id": rid})["d"]
        sales_ok = "" if c2.get("defaultSalesmanId") or c2.get("salesman") else " | sales belum terpasang - admin isi"
        # baca ulang pajak: yang tidak tersimpan dilaporkan, tidak ditebak
        beda = [k for k, v in pajak.items() if k in ("documentCode", "customerTaxType", "wpType", "wpNumber", "wpName", "nitku", "taxStreet")
                and str(c2.get(k) or "") != v]
        if beda:
            ket_pajak += " | PAJAK TIDAK TERSIMPAN: " + ", ".join(beda) + " - admin isi manual"
    return ("akun %s dibuat, id %s, %s, diskon %s, termin %s, umur %s hari, limit %s%s | pajak: %s" % (
                nama, rid, kat, diskon, termin, hari, jt(limit), sales_ok, ket_pajak)), {"id_baru": rid}


def data_pajak(p, kat):
    """Template pajak pelanggan baru (Kak Intan 13 Nov 2026):
    online marketplace -> Digunggung; selain itu Faktur Pajak, detail 04 - DPP Nilai Lain.
    Nomor Wajib Pajak = NIK/NPWP pengajuan; NITKU = nomor 16 digit + 000000; Nama Wajib Pajak = owner (NIK);
    alamat pajak TIDAK sama dengan alamat penagihan, diisi alamat pajak / KTP dari pengajuan."""
    online = (p.get("jenis_toko") or "").upper() == "ONLINE" or kat == "ONLINE TOKO"
    no = re.sub(r"\D", "", str(p.get("nik") or ""))
    d = {"documentCode": "DIGUNGGUNG" if online else "CTAS_INVOICE"}
    if not online:
        d["customerTaxType"] = "CTAS_DPP_NILAI_LAIN"
    ket = "Digunggung" if online else "Faktur Pajak, 04 - DPP Nilai Lain"
    if len(no) == 15:
        no = "0" + no  # NPWP lama 15 digit -> 16 digit Coretax
    if len(no) != 16:
        return d, ket + " | NIK/NPWP tidak 16 digit (%s) - admin isi tab Pajak" % (p.get("nik") or "kosong")
    npwp = no.startswith("0")  # NIK tidak pernah diawali 0; NPWP badan 16 digit diawali 0
    d.update({"wpType": "NPWP" if npwp else "NIK", "wpNumber": no, "nitku": no + "000000", "countryCode": "IDN"})
    # = tombol rantai "Ambil Nama Wajib Pajak dari NPWP" di tab Pajak (endpoint yang dipanggil tombol itu)
    try:
        djp = acc("company/load-npwp-information.do", {"wpNpwp": no})["d"] or {}
    except Sibuk:
        raise
    except Exception:  # noqa: BLE001
        djp = {}
    if not djp.get("wpName"):
        # aturan admin: nama/alamat tidak muncul dari DJP -> kembalikan, cek pajak (akun belum dibuat)
        raise Dikembalikan("cek pajak: %s %s tidak ditemukan di DJP (nama wajib pajak tidak muncul)" % ("NPWP" if npwp else "NIK", no))
    d["wpName"] = djp["wpName"].strip()
    alamat_djp = (djp.get("companyAddress") or "").strip()
    if not online:
        d["taxSameAsBill"] = "false"  # tidak dicentang: alamat pajak dari DJP
        if alamat_djp or p.get("alamat_pajak"):
            d["taxStreet"] = (alamat_djp or str(p["alamat_pajak"]).strip())[:250]
        if djp.get("companyCity"):
            d["taxCity"] = djp["companyCity"]
    ket += ", %s %s, nama & alamat dari DJP: %s" % (d["wpType"], no, d["wpName"])
    if not online and not alamat_djp:
        ket += " | alamat DJP kosong%s" % (" - dipakai alamat pajak pengajuan" if p.get("alamat_pajak") else " - admin isi alamat pajak")
    return d, ket


def kembalikan_sementara(p):
    lama = p.get("eksekusi_lama") or {}
    if not lama.get("id"):
        return
    c = acc("customer/detail.do", {"id": lama["id"]})["d"]
    if p["jenis"] == "limit":
        par = {"id": lama["id"], "customerLimitAmount": "true" if lama.get("limit_aktif") else "false",
               "customerLimitAmountValue": str(int(float(lama.get("limit") or 0)))}
        ket = "%s limit dikembalikan ke %s (acc sementara selesai)" % (hari_ini(), jt(lama.get("limit")))
    else:
        par = {"id": lama["id"], "customerLimitAge": "true" if lama.get("umur_aktif") else "false",
               "customerLimitAgeValue": str(int(lama.get("umur") or 0))}
        ket = "%s umur dikembalikan ke %s hr (acc sementara selesai)" % (hari_ini(), int(lama.get("umur") or 0))
    par["notes"] = catatan_baru(c.get("notes"), ket)
    acc("customer/save.do", par, tulis=True)
    ubah_pengajuan(p["_id"], {"status": "selesai", "dikembalikan_bot": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                              "eksekusi": (p.get("eksekusi") or "") + " | " + ket})
    catat("KEMBALI", p["_id"], ket)


# ---------------- MACAN: ganti KTP & buka blokir (rantai akun, sisa limit) ----------------
# Aturan rantai akun (Kak Intan 27 Okt 2026, ruang lingkup dipertegas 30 Okt): dipakai HANYA untuk ganti KTP (ID
# pelanggan bernomor) dan akun COD berantai Palembang. Di luar itu piutang & nota tertua dihitung dari akun itu saja.
POLA_NO_RANTAI = re.compile(r"^(.*?)\s+(\d{1,3})$")
POLA_LIMIT_ASLI = re.compile(r"limit asli\s*(?:rp\s*)?([\d.,]+)\s*(jt|juta)?", re.I)
POLA_BLOKIR = re.compile(r"blokir\s*(?:rp\s*)?([\d.,]+)\s*(jt|juta)?", re.I)


def ktp_aktif():
    return E.get("BOT_KTP") == "1"


def alasan_antre(j):
    """jenis yang belum/tidak dikerjakan bot -> alasan untuk kolom eksekusi; None = dikerjakan"""
    if j in ANTRE_ADMIN:
        return ANTRE_ADMIN[j]
    if j in ANTRE_TANPA_KTP and not ktp_aktif():
        return ANTRE_TANPA_KTP[j]
    return None


def no_dasar(no):
    """"DILA 3" -> ("DILA", 3); "TOKO NAGA" -> ("TOKO NAGA", 1)"""
    t = str(no or "").strip()
    m = POLA_NO_RANTAI.match(t)
    return (m.group(1).strip(), int(m.group(2))) if m else (t, 1)


def nominal_catatan(teks, satuan):
    """"341" + "jt" -> 341.000.000; "40.265.000" -> 40265000. Angka tanpa satuan yang kurang dari 100.000
    dianggap juta (catatan admin menulis "blokir 150" untuk 150 juta)."""
    n = float(str(teks).replace(".", "").replace(",", ".") or 0)
    if (satuan or "").lower() in ("jt", "juta") or 0 < n < 100000:
        n *= 1e6
    return n


def rantai_akun(c):
    """Akun satu rantai ganti KTP, urut nomor: ID pelanggan dasar + bernomor (DILA, DILA 2 = YOLANDA, DILA 3 = TOKO
    NAGA). NAMA akun bisa berbeda-beda - yang menyambung rantai adalah ID pelanggan (customerNo)."""
    dasar, _n = no_dasar(c.get("customerNo"))
    pola = re.compile(r"^" + re.escape(dasar) + r"(\s+\d{1,3})?$", re.I)
    ada = {}
    for x in acc("customer/list.do", {"fields": "id,name,customerNo,notes,customerLimitAmount,customerLimitAmountValue",
                                      "filter.keywords.op": "CONTAIN", "filter.keywords.val[0]": dasar,
                                      "sp.pageSize": "100"})["d"]:
        if pola.match(str(x.get("customerNo") or "").strip()):
            ada[x["id"]] = x
    ada[c["id"]] = {"id": c["id"], "name": c.get("name"), "customerNo": c.get("customerNo"), "notes": c.get("notes"),
                    "customerLimitAmount": c.get("customerLimitAmount"),
                    "customerLimitAmountValue": c.get("customerLimitAmountValue")}
    return dasar, sorted(ada.values(), key=lambda x: no_dasar(x.get("customerNo"))[1])


def limit_asli_rantai(akun):
    """Limit asli = limit akun PERTAMA rantai sebelum ganti KTP pertama (Kak Intan 14 Nov 2026: DILA 341jt, bukan
    DILA 2 305jt yang sudah diturunkan admin). Dibaca dari catatan: "limit asli Xjt" dulu, lalu baris "blokir Xjt"
    paling bawah, mulai dari akun paling awal. Tidak ada catatan -> limit akun yang sekarang (Rp 1 hasil blokir
    bukan limit asli)."""
    for pola in (POLA_LIMIT_ASLI, POLA_BLOKIR):
        for a in akun:
            for b in reversed((a.get("notes") or "").splitlines()):
                m = pola.search(b)
                if m:
                    n = nominal_catatan(m.group(1), m.group(2))
                    if n > 1:
                        return n, "catatan akun %s: %s" % (a.get("customerNo"), b.strip()[:120])
    for a in akun:
        n = float(a.get("customerLimitAmountValue") or 0) if a.get("customerLimitAmount") else 0
        if n > 1:
            return n, "limit akun %s sekarang (tidak ada catatan limit asli)" % a.get("customerNo")
    return 0, "tidak ada catatan limit asli dan semua akun rantai berlimit Rp 1"


def saldo_piutang(cid):
    """Saldo piutang pelanggan = balanceList[0].balance di customer/detail. TIDAK dipakai lagi untuk sisa limit
    sejak 20 Nov 2026 (lihat piutang_faktur) - disimpan karena masih dipakai untuk membaca detail pelanggan."""
    c = acc("customer/detail.do", {"id": str(cid)})["d"]
    return float(((c.get("balanceList") or [{}])[0] or {}).get("balance") or 0), c


def piutang_faktur(cid):
    """Piutang pelanggan = jumlah sisa (primeOwing) FAKTUR PENJUALAN yang belum lunas.
    Kak Intan 20 Nov 2026: "total piutang yang belum terbayar (total piutang di faktur belum lunas - giro)"."""
    total = 0.0
    for f in acc("sales-invoice/list.do", {"fields": "id,number,primeOwing", "filter.customerId": str(cid),
                                           "filter.outstanding": "true", "sp.pageSize": "100"})["d"]:
        total += float(f.get("primeOwing") or 0)
    return total


def belum_terfaktur(cid):
    """Piutang belum terfaktur: Pengiriman Barang "Dikirim" (SENT, belum difaktur) + Pesanan Penjualan "Menunggu
    diproses" (QUEUE/WAITING). Nilai DO dari delivery-order/detail (jumlah detailItem totalPrice; sudah inc PPN
    bila dokumennya inclusiveTax)."""
    total, rinci = 0.0, []
    for d in acc("sales-order/list.do", {"fields": "id,number,status,totalAmount", "filter.customerId": str(cid),
                                         "sp.pageSize": "100"})["d"]:
        if d.get("status") in ("QUEUE", "WAITING"):
            total += float(d.get("totalAmount") or 0)
            rinci.append("SO %s" % d.get("number"))
    for d in acc("delivery-order/list.do", {"fields": "id,number,status", "filter.customerId": str(cid),
                                            "filter.status.op": "EQUAL", "filter.status.val": "SENT",
                                            "sp.pageSize": "100"})["d"]:
        dd = acc("delivery-order/detail.do", {"id": str(d["id"])})["d"]
        total += sum(float(b.get("totalPrice") or 0) for b in dd.get("detailItem") or [])
        rinci.append("DO %s" % d.get("number"))
    return total, rinci


def giro_belum_cair(cid):
    """Giro belum cair = penerimaan penjualan bertanggal SESUDAH hari ini (giro mundur)."""
    hari = datetime.date.today()
    try:
        rows = acc("sales-receipt/list.do", {
            "fields": "id,number,transDate,totalPayment", "filter.customerId": str(cid),
            "filter.transDate.op": "BETWEEN",
            "filter.transDate.val[0]": (hari + datetime.timedelta(days=1)).strftime("%d/%m/%Y"),
            "filter.transDate.val[1]": (hari + datetime.timedelta(days=365)).strftime("%d/%m/%Y"),
            "sp.pageSize": "100"})["d"]
    except Sibuk:
        raise
    except Exception:  # noqa: BLE001
        return 0.0, 0
    return sum(float(r.get("totalPayment") or 0) for r in rows), len(rows)


def hitung_sisa_limit(c):
    """Sisa limit akun ganti KTP. Definisi dipastikan Kak Intan 20 Nov 2026 (sama dengan MACAN):
        total piutang = piutang FAKTUR BELUM LUNAS seluruh rantai - giro belum cair (giro = sudah dibayar)
        sisa limit    = limit asli - total piutang - piutang belum terfaktur (SO & DO belum difaktur)
    Sebelumnya memakai saldo balanceList dan giro ikut DIKURANGI (sisa jadi lebih kecil). Rumusnya sama
    dengan yang dilihat pusat di halaman (nodeKtp), bedanya bot membaca Accurate saat eksekusi."""
    dasar, akun = rantai_akun(c)
    asli, asal = limit_asli_rantai(akun)
    piutang = blm = giro = 0.0
    rinci, giro_n = [], 0
    for a in akun:
        s_a = piutang_faktur(a["id"])
        b_a, r_a = belum_terfaktur(a["id"])
        g_a, gn = giro_belum_cair(a["id"])
        piutang += s_a
        blm += b_a
        giro += g_a
        giro_n += gn
        rinci.extend(r_a)
    bersih = max(0.0, piutang - giro)          # giro belum cair dianggap sudah dibayar
    sisa = asli - bersih - blm
    return {"dasar": dasar, "akun": akun, "asli": asli, "asal_asli": asal, "piutang": piutang, "belum": blm,
            "giro": giro, "giro_n": giro_n, "rinci": rinci, "sisa": sisa, "piutang_bersih": bersih,
            "ket": "limit asli %s (%s) - total piutang %s (faktur belum lunas %s - giro belum cair %s) - belum terfaktur %s = sisa limit %s%s" % (
                jt(asli), asal, rp(bersih), rp(piutang), rp(giro), rp(blm), rp(sisa),
                (" | belum terfaktur: " + ", ".join(rinci[:8])) if rinci else "")}


def kerjakan_ktp(p):
    """Ganti KTP: akun baru = salinan akun lama + KTP/NPWP baru (aturan MACAN 30 Okt / 13, 14 & 17 Nov 2026).
    ID pelanggan = ID lama + nomor berikutnya; nama = NAMA AKUN BARU di pengajuan; kategori harga/diskon, termin,
    umur, sales & alamat disalin dari akun lama (kategori harga cabang khusus menang kalau akun lama masih "Umum");
    limit = SISA LIMIT dibulatkan ke bawah ke juta, atau nominal ACC Ibu kalau diisi. Catatan akun baru CUKUP satu
    baris. Sesudah akun baru jadi: akun lama diblokir limit Rp 1 + baris catatan blokir."""
    c = pelanggan_dari(p)
    nama_baru = re.sub(r"\s+", " ", str(p.get("akun_baru") or "").strip()).upper()
    if not nama_baru:
        raise Dikembalikan("cek nama akun baru: kosong - isi di pengajuan")
    d = hitung_sisa_limit(c)
    no_baru = "%s %d" % (d["dasar"], no_dasar(d["akun"][-1].get("customerNo"))[1] + 1)
    kembar = acc("customer/list.do", {"fields": "id,name,customerNo", "filter.keywords.op": "CONTAIN",
                                      "filter.keywords.val[0]": nama_baru, "sp.pageSize": "50"})["d"]
    if any(str(x.get("customerNo") or "").strip().upper() == no_baru.upper() for x in list(kembar) + d["akun"]):
        return "ID pelanggan %s sudah ada (dibuat admin?), Accurate tidak diubah" % no_baru, {}
    if any(str(x.get("name") or "").strip().upper() == nama_baru for x in kembar):
        return "sudah ada akun bernama %s (dibuat admin?), Accurate tidak diubah" % nama_baru, {}
    # limit akun baru
    if p.get("acc_limit") is not None:
        limit = float(p["acc_limit"])
        dasar_limit = "limit ACC Ibu"
    else:
        if d["sisa"] <= 0:
            raise PerluTanya("sisa limit tidak lebih dari nol: %s - tanya Kak Intan dulu (boleh dilanjutkan dengan "
                             "limit tertentu atau Rp 1 atas perintah Kak Intan)" % d["ket"])
        limit = int(d["sisa"] // 1e6) * 1e6 or d["sisa"]  # dibulatkan ke bawah ke juta (14 Nov: 161.293.777 -> 161jt)
        dasar_limit = "sisa limit dibulatkan ke bawah ke juta"
    # kategori harga: disamakan dengan akun lama; akun lama masih "Umum" di cabang berkategori khusus -> kategori
    # cabang (Kak Intan 13 Nov 2026), dan dilaporkan supaya akun lama ikut dibetulkan
    cab = (p.get("cabang") or c.get("customerBranchName") or (c.get("branch") or {}).get("name") or "").upper()
    kat_lama = ((c.get("priceCategory") or {}).get("name") or "").strip()
    kat, ket_kat = kat_lama, "kategori harga sama dengan akun lama (%s)" % (kat_lama or "kosong")
    wajib = KAT_HARGA.get(cab)
    if wajib and wajib.lower() != "umum" and (not kat_lama or kat_lama.lower() == "umum"):
        kat, ket_kat = wajib, ("kategori harga akun lama masih %s padahal cabang %s memakai %s - akun baru dibuat "
                               "%s, akun lama sebaiknya ikut dibetulkan" % (kat_lama or "kosong", cab, wajib, wajib))
    if not kat:
        raise PerluTanya("kategori harga akun lama kosong dan aturan cabang %s belum ada - admin tentukan" % cab)
    pkp = str(p.get("pkp") or "").strip().upper()
    diskon = ("pkp" if pkp in ("PKP", "YA", "TRUE", "1") else "non pkp") if pkp else \
        (((c.get("discountCategory") or {}).get("name") or "").strip() or "non pkp")
    # termin & umur: ikut pengajuan/ACC kalau diisi, kalau tidak disalin dari akun lama
    if p.get("bayar") or p.get("acc_cod"):
        cod = bool(p.get("acc_cod")) or p.get("bayar") == "COD"
        hari = 1 if cod else int(p.get("acc_tempo") or p.get("tempo") or c.get("customerLimitAgeValue") or 30)
        termin = "C.O.D" if cod else "net %d" % hari
    else:
        termin = ((c.get("term") or {}).get("name") or "C.O.D")
        hari = int(c.get("customerLimitAgeValue") or 1)
    data = {"name": nama_baru, "customerNo": no_baru, "transDate": datetime.date.today().strftime("%d/%m/%Y"),
            "branchName": cab, "categoryName": ((c.get("category") or {}).get("name") or "Umum"),
            "priceCategoryName": kat, "discountCategoryName": diskon, "termName": termin, "currencyCode": "IDR",
            "customerLimitAmount": "true", "customerLimitAmountValue": str(int(limit)),
            "customerLimitAge": "true", "customerLimitAgeValue": str(int(hari)),
            "billStreet": (str(p.get("alamat") or "").strip() or c.get("billStreet") or "")[:250],
            "mobilePhone": (str(p.get("hp") or "").strip() or c.get("mobilePhone") or "")[:30],
            # catatan akun baru: CUKUP SATU BARIS (Kak Intan 14 Nov 2026, contoh DILA 3 / TOKO NAGA) - rincian
            # piutang & sisa limit tidak ditulis di sini, cukup di laporan
            "notes": "%s akun lama %s ganti ktp, limit asli %s" % (hari_ini(), c.get("name"), jt(d["asli"]))}
    pajak, ket_pajak = data_pajak(p, kat)
    data.update(pajak)
    sls = (c.get("salesman") or {}).get("number") if isinstance(c.get("salesman"), dict) else None
    if sls:
        data["salesmanNumber"] = sls  # dipakai persis seperti di Accurate (bisa berisi titik/spasi)
    links = arsip_lampiran(p)
    r = acc("customer/save.do", data, tulis=True)
    rid = (r.get("r") or {}).get("id") if isinstance(r.get("r"), dict) else None
    cek = ""
    if rid and not UJI:
        c2 = acc("customer/detail.do", {"id": str(rid)})["d"]
        if float(c2.get("customerLimitAmountValue") or 0) != float(int(limit)):
            raise RuntimeError("dibaca ulang: limit akun baru %s, bukan %s" % (jt(c2.get("customerLimitAmountValue")), jt(limit)))
        if not (c2.get("defaultSalesmanId") or c2.get("salesman")):
            cek += " | sales belum terpasang - admin isi"
        beda = [k for k, v in pajak.items() if k in ("documentCode", "customerTaxType", "wpType", "wpNumber", "wpName", "nitku", "taxStreet")
                and str(c2.get(k) or "") != v]
        if beda:
            cek += " | PAJAK TIDAK TERSIMPAN: " + ", ".join(beda) + " - admin isi manual"
    # blokir akun lama: catatan lama DIPERTAHANKAN + satu baris blokir, limit Rp 1
    lama_limit = float(c.get("customerLimitAmountValue") or 0) if c.get("customerLimitAmount") else 0
    blok = "%s blokir %s, ganti ktp ke %s (%s)" % (hari_ini(), jt(lama_limit if lama_limit > 1 else d["asli"]), nama_baru, no_baru)
    acc("customer/save.do", {"id": c["id"], "customerLimitAmount": "true", "customerLimitAmountValue": "1",
                             "notes": catatan_baru(c.get("notes"), blok)}, tulis=True)
    return ("akun %s (%s) dibuat, id %s, limit %s (%s), %s, diskon %s, termin %s, umur %s hari | %s | akun lama %s "
            "diblokir Rp 1, catatan \"%s\" | pajak: %s%s%s") % (
        nama_baru, no_baru, rid, jt(limit), dasar_limit, ket_kat, diskon, termin, hari, d["ket"], c.get("name"),
        blok, ket_pajak, cek,
        (" | %d lampiran diarsip ke Drive" % len(links)) if links else ""), {"id_baru": rid, "id": c["id"]}


def kerjakan_buka(p):
    """Buka blokir toko = naik limit pada akun yang limitnya Rp 1 (aturan MACAN: ditandai HIJAU, dan tab Penjualan
    akun dicek karena akun yang diblokir sering salesman/kategori harganya kosong). Limit baru = ACC Ibu."""
    c = pelanggan_dari(p)
    lama = float(c.get("customerLimitAmountValue") or 0) if c.get("customerLimitAmount") else 0
    if lama > 1:
        return "akun %s tidak sedang diblokir (limit %s) - Accurate tidak diubah, admin cek dulu" % (c.get("name"), jt(lama)), {}
    return kerjakan_limit(p)


# ---------------- KANCIL: kompen ----------------
# Alur Kak Intan (WA 13 Nov 2026, 14.33):
#   ACC -> cek pelanggan di Accurate: kategori harga & cabang -> Penyesuaian harga/diskon, kata kunci "kompen", cabang +
#   kategori penjualan pelanggan -> cari kode barang:
#     ada  : "harga baru" di dokumen = harga nett (BIT & Cosmos: harga potongan)? sama -> harga minimum = kompen / 1,11
#            beda -> pengajuan DIKEMBALIKAN, catatan "cek harga baru"
#     tidak ada: tambah kode (harga baru = nett / potongan, harga minimum = kompen / 1,11), tanggal dokumen = hari ini
#   Harga minimum tidak pernah dinaikkan (kompen lebih tinggi dari minimum yang ada dibiarkan - aturan 30 Okt).
MERK_POTONGAN = {"COSMOS", "MIYAKO", "SHIMIZU", "RINNAI"}  # "BIT & Cosmos: harga potongan" = nett x 97% (aturan admin)
FAKTOR_POTONGAN = 0.97
_modal = None


def nett_rekap(cab, item, tgl):
    """harga nett inc PPN dari rekap harga (harga_modal.json) yang berlaku di tanggal pengajuan; (harga, merk, edisi)"""
    global _modal
    if _modal is None:
        try:
            _modal = json.load(open(HARGA_MODAL, encoding="utf-8")).get("cabang", {})
        except Exception:  # noqa: BLE001
            _modal = {}
    m = (_modal.get("JAKARTA" if cab == "TANGERANG" else cab) or {}).get(item)
    if not m:
        return None
    harga = m["harga"]
    for t, h in m.get("riwayat") or []:
        if t <= tgl.strftime("%Y-%m-%d"):
            harga = h
    merk = (m.get("merk") or "").upper()
    if merk in MERK_POTONGAN:
        harga = round(harga * FAKTOR_POTONGAN)
    return float(harga), merk, m.get("edisi")


def bulan_harga(p):
    """Bulan harga & campaign yang dipilih di pengajuan (Kogja 18 Nov 2026, kolom "Bulan harga & campaign"):
    "2026-10" -> 31/10/2026 (akhir bulan, supaya edisi pricelist & campaign bulan itu yang dipakai); bulan berjalan
    -> hari ini. Kosong / bukan YYYY-MM -> None (pakai tanggal pengajuan seperti sebelumnya)."""
    m = re.match(r"^(\d{4})-(\d{2})$", str(p.get("bulan") or "").strip())
    if not m:
        return None
    th, bl = int(m.group(1)), int(m.group(2))
    if not 1 <= bl <= 12:
        return None
    akhir = datetime.date(th + (bl == 12), bl % 12 + 1, 1) - datetime.timedelta(days=1)
    hari = min(akhir, datetime.date.today())
    return datetime.datetime(hari.year, hari.month, hari.day)


def dokumen_kompen(kat, cabang, tgl):
    daftar = acc("sellingprice-adjustment/list.do", {"fields": "id,number,transDate,description,priceCategory,suspended",
                                                     "filter.keywords.op": "CONTAIN", "filter.keywords.val[0]": "KOMPEN",
                                                     "sp.pageSize": "100", "sp.sort": "transDate|desc"})["d"]
    bln = BULAN[tgl.month - 1][:3]
    calon = []
    for d in daftar:
        if d.get("suspended") or "KOMPEN" not in (d.get("description") or "").upper() or (d.get("priceCategory") or {}).get("name") != kat:
            continue
        det = acc("sellingprice-adjustment/detail.do", {"id": d["id"]})["d"]
        cabs = [b.get("name") for b in (det.get("listBranch") or [])]
        if not cabs or cabang in cabs:
            calon.append(det)
    if not calon:
        raise PerluTanya("dokumen penyesuaian harga KOMPEN kategori %s cabang %s tidak ada" % (kat, cabang))
    # urutan: khusus cabang itu, bulan pengajuan, tanggal terbaru
    calon.sort(key=lambda d: (bool(d.get("listBranch")), bln in (d.get("description") or "").upper(),
                              datetime.datetime.strptime(d["transDate"], "%d/%m/%Y")), reverse=True)
    return calon[0]


def kerjakan_kompen(p):
    if E.get("BOT_KOMPEN") != "1" and not UJI:
        raise PerluTanya("bot kompen belum diaktifkan (menunggu uji simpan dokumen SPA)")
    cab_aju = (p.get("cabang") or "").strip().upper()
    if cab_aju in KOMPEN_SATU_KATEGORI:
        cab, kat = cab_aju, KAT_HARGA[cab_aju]
    else:
        c = pelanggan_dari(p)
        cab = (c.get("customerBranchName") or p.get("cabang") or "").upper()
        kat = "BIT PLB -0,85%" if cab == "PALEMBANG" else (c.get("priceCategory") or {}).get("name")
    tgl = datetime.datetime.strptime(p.get("tgl") or datetime.date.today().isoformat(), "%Y-%m-%d")
    # Kogja 18 Nov 2026: pengajuan boleh menyebut BULAN stok/campaign-nya (stok campaign Oktober diajukan November)
    # -> harga nett dibandingkan dengan pricelist bulan ITU. Dokumen penyesuaian harga tetap yang berlaku sekarang.
    tgl_h = bulan_harga(p) or tgl
    doc = dokumen_kompen(kat, cab, tgl)
    baris = {r["itemId"]: r for r in doc.get("detailItem") or []}
    barang = p.get("barang") or ([{"item": p.get("item"), "harga": p.get("harga")}] if p.get("item") else [])
    ubah, hasil, beda, tanya = {}, [], [], []
    n, tambah = 0, False
    # Kogja 20 Nov 2026: tombol "Tetap kerjakan di harga minimum" (paksa_minimum) -> harga baru di dokumen tidak
    # dicocokkan dengan rekap (rekap tidak ada / beda tetap jalan); hanya harga minimum yang ditulis.
    paksa = bool(p.get("paksa_minimum"))
    ditolak = [(b.get("item") or "?").strip().upper() for b in barang if b.get("acc") is False]
    barang = [b for b in barang if b.get("acc") is not False]  # ACC per kode (Kogja 16 Nov 2026)
    if not barang:
        raise PerluTanya("semua kode ditolak Ibu, tidak ada yang dikerjakan")
    for b in barang:
        kode, harga = (b.get("item") or "").strip().upper(), float(b.get("harga") or 0)
        if not kode or not harga:
            tanya.append("%s: kode/harga kompen kosong" % (kode or "?")); continue
        try:
            it = acc("item/detail.do", {"no": kode})["d"]
        except Exception:  # noqa: BLE001
            tanya.append("%s: kode tidak ketemu di Accurate" % kode); continue
        rek = nett_rekap(cab, kode, tgl_h)
        r = baris.get(it["id"])
        if not rek and not (paksa and r):
            tanya.append("%s: kode tidak ada di rekap harga cabang %s%s" % (
                kode, cab, " dan belum ada di dokumen kompen (harga baru tidak diketahui)" if paksa else "")); continue
        nett, merk, edisi = rek or (float(r["price"]), "", None)
        # Kogja 17 Nov 2026: harga kompen / 1,11 lalu dikurangi 2 (Accurate membulatkan ke atas)
        minimum = round(harga / 1.11) - 2
        if r:
            if not paksa and abs(float(r["price"]) - nett) > max(100, nett * 0.001):
                beda.append("%s harga baru di Accurate %s, rekap %s %s (%s)" % (
                    kode, rp(r["price"]), "potongan" if merk in MERK_POTONGAN else "nett", rp(nett), edisi or "-"))
                continue
            if float(r.get("minimumPrice") or 0) and minimum >= float(r["minimumPrice"]):
                hasil.append("%s min %s sudah <= kompen %s, tidak diubah" % (kode, rp(r["minimumPrice"]), rp(minimum))); continue
            ubah["detailItem[%d].id" % n] = r["id"]
            ubah["detailItem[%d].minimumPrice" % n] = str(minimum)
            hasil.append("%s min %s -> %s" % (kode, rp(r.get("minimumPrice")), rp(minimum)))
        else:
            ubah.update({"detailItem[%d].itemNo" % n: kode, "detailItem[%d].price" % n: str(int(nett)),
                         "detailItem[%d].minimumPrice" % n: str(minimum)})
            hasil.append("%s kode baru: harga %s, min %s" % (kode, rp(nett), rp(minimum)))
            tambah = True
        n += 1
    if beda:
        # alur Kak Intan: harga baru di Accurate beda -> dikembalikan ke pengajuan, catatan cek harga baru.
        # Tidak ada yang ditulis ke Accurate untuk pengajuan ini.
        raise Dikembalikan("cek harga baru: " + "; ".join(beda))
    if tanya and not n:
        raise PerluTanya("; ".join(tanya))
    if n:
        sebelum = {r["id"] for r in doc["detailItem"]}
        os.makedirs(CADANGAN, exist_ok=True)
        json.dump(doc, open(os.path.join(CADANGAN, "%s_%s.json" % (doc["number"], datetime.datetime.now().strftime("%Y%m%d%H%M%S"))),
                            "w", encoding="utf-8"), ensure_ascii=False)
        if tambah:
            ubah["transDate"] = datetime.date.today().strftime("%d/%m/%Y")
        acc("sellingprice-adjustment/save.do", {"id": doc["id"], **ubah}, tulis=True)
        if not UJI:
            d2 = acc("sellingprice-adjustment/detail.do", {"id": doc["id"]})["d"]
            hilang = sebelum - {r["id"] for r in d2["detailItem"]}
            if hilang:
                raise RuntimeError("BAHAYA: %d baris dokumen %s hilang sesudah simpan - cadangan di skrip\\log\\cadangan_spa" % (len(hilang), doc["number"]))
    return "%s (%s, %s)%s%s: %s%s%s%s" % (doc["number"], kat, cab, " tanggal -> hari ini" if tambah else "",
                                        " [tetap di harga minimum, harga baru tidak dicek]" if paksa else "", "; ".join(hasil) or "-",
                                        (" | harga nett & campaign bulan %s" % tgl_h.strftime("%m/%Y")) if tgl_h != tgl else "",
                                        (" | PERLU TANYA: " + "; ".join(tanya)) if tanya else "",
                                        (" | ditolak Ibu (tidak diubah): " + ", ".join(ditolak)) if ditolak else ""), {}


# ---------------- KELINCI: rekap dulu ----------------
def rekap_nota(p):
    no = (p.get("nomor") or "").strip()
    if not no:
        return "rekap: nomor DO kosong"
    baris = []
    for ep, nama in (("delivery-order", "DO"), ("sales-invoice", "faktur"), ("sales-order", "SO")):
        try:
            d = acc(ep + "/detail.do", {"number": no})["d"]
        except Exception:  # noqa: BLE001
            continue
        lunas = d.get("statusName") or d.get("status")
        baris.append("%s %s tgl %s %s" % (nama, no, d.get("transDate"), lunas or ""))
        bln_ini = datetime.date.today().strftime("/%m/%Y")
        if not str(d.get("transDate", "")).endswith(bln_ini):
            baris.append("nota BUKAN bulan berjalan -> tidak direvisi (KE PAJAK)")
        if p.get("jenis") == "edit_harga":
            for b in p.get("barang") or []:
                kode = (b.get("item") or "").upper()
                cocok = [x for x in d.get("detailItem") or [] if (x.get("item") or {}).get("no", "").upper() == kode]
                if not cocok:
                    baris.append("%s tidak ada di %s" % (kode, nama))
                else:
                    h = float(cocok[0].get("unitPrice") or 0)
                    baris.append("%s harga nota %s (diajukan lama %s, baru %s)%s" % (
                        kode, rp(h), rp(b.get("lama")), rp(b.get("baru")), "" if abs(h - float(b.get("lama") or 0)) < 2 else " TIDAK COCOK"))
        break
    if not baris:
        baris.append("nomor %s tidak ketemu di DO/faktur/SO" % no)
    return "REKAP (menunggu persetujuan Kak Intan, Accurate belum diubah): " + "; ".join(baris)


# ---------------- revisi nota & edit tanggal (KELINCI, Kak Intan 18 Nov 2026) ----------------
# "Edit tanggal & revisi nota tidak perlu ACC Ibu; revisi qty dan edit tanggal sesuai ketentuan" - aturan terbaru berkas
# "revisi nota dan tanggal.md" (agen KELINCI). Aktif hanya bila BOT_REVISI=1 di .env; kalau tidak, tetap REKAP saja.
#   - Bandung (cabang atau branchId 150) TIDAK disentuh.
#   - Nota harus bulan berjalan; nota bulan lalu hanya s.d. tanggal 3. Di luar itu: revisi manual.
#   - Nama toko, nomor DO/SO, kode barang, qty sebelum / tanggal nota dicek dengan Accurate; beda -> dikembalikan.
#   - DO sudah difaktur: faktur dihapus dulu, hanya kalau belum ada pembayaran, belum ada nomor faktur pajak,
#     TTD gudang diceklis. Faktur dibuat ulang oleh admin (dicatat di kolom eksekusi).
#   - Hanya scope keterangan: "revisi DO" = DO saja, "revisi SO" = SO saja, "revisi DO SO" = keduanya, dst.
#   - Qty hanya boleh turun (naik = perlu tanya). Revisi harga tetap lewat edit_harga (REKAP, otoritas Kak Intan).
#   - Sebelum mengubah, dokumen asli disimpan ke skrip\log\cadangan_revisi\; sesudahnya dibaca ulang.
CADANGAN_REVISI = os.path.join(GIO, "skrip", "log", "cadangan_revisi")
CABANG_BANDUNG_ID = 150
# "hapus DO edit SO" (Kogja 20 Nov 2026): DO dihapus, SO-nya TIDAK dihapus - qty SO diubah sesuai pengajuan
AKSI_REVISI = ("revisi DO", "revisi DO SO", "revisi SO", "hapus SO", "hapus DO saja", "hapus DO SO",
               "hapus DO edit SO", "hapus faktur")


def revisi_aktif():
    return E.get("BOT_REVISI") == "1"


def acc_hapus(ep, iden):
    """DELETE <ep>/delete.do?id=..  (UJI: hanya dicatat)"""
    if UJI:
        catat("  [uji] HAPUS", ep, iden)
        return {"s": True}
    url = HOST + "/accurate/api/" + ep + "/delete.do?" + urllib.parse.urlencode({"id": iden})
    for coba in range(6):
        req = urllib.request.Request(url, method="DELETE", headers=_kepala())
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                j = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and coba < 5:
                time.sleep(1 + coba)
                continue
            raise RuntimeError("Accurate HTTP %s: %s" % (e.code, e.read()[:300].decode("utf-8", "replace")))
    time.sleep(0.15)
    if not j.get("s"):
        raise RuntimeError("Accurate menolak hapus %s: %s" % (ep, json.dumps(j.get("d"), ensure_ascii=False)[:400]))
    return j


def no_dok(no, awalan="DO."):
    no = re.sub(r"\s+", "", str(no or "")).upper()
    if re.fullmatch(r"\d{6,}", no):
        no = awalan + no
    return no


def baca_dok(ep, no):
    try:
        return acc(ep + "/detail.do", {"number": no})["d"]
    except RuntimeError as e:
        if str(e).startswith("Accurate menolak"):   # nomor tidak ada; galat HTTP tetap dilempar (jangan dikira tidak ketemu)
            return None
        raise


def faktur_dari(no):
    """faktur bernomor sama dengan DO (pola Svarna) -> dict ringkas atau None"""
    d = acc("sales-invoice/list.do", {"fields": "id,number,transDate,totalAmount,primeOwing,lastPaymentDate,taxNumber,taxDate,branchId",
                                      "filter.number.op": "EQUAL", "filter.number.val[0]": no})["d"]
    return d[0] if d else None


def tgl(s):
    """'18/11/2026', '2026-11-18', '18-11-2026', '18 Nov 2026', '18/11/26' -> date"""
    s = str(s or "").strip()
    bln = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7, "agu": 8, "ags": 8, "aug": 8,
           "sep": 9, "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12}
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return datetime.date(int(m[1]), int(m[2]), int(m[3]))
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", s)
    if m:
        th = int(m[3]) + (2000 if len(m[3]) == 2 else 0)
        return datetime.date(th, int(m[2]), int(m[1]))
    m = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\s+(\d{4})", s)
    if m and m[2].lower() in bln:
        return datetime.date(int(m[3]), bln[m[2].lower()], int(m[1]))
    return None


def dalam_jendela(d):
    """bulan berjalan; bulan lalu hanya sampai tanggal 3 (aturan 5)"""
    h = datetime.date.today()
    if (d.year, d.month) == (h.year, h.month):
        return True
    lalu = (h.replace(day=1) - datetime.timedelta(days=1))
    return (d.year, d.month) == (lalu.year, lalu.month) and h.day <= 3


def fmt_tgl(d):
    return d.strftime("%d/%m/%Y")


def norm_toko(s):
    s = re.sub(r"[^A-Z0-9]+", " ", str(s or "").upper()).strip()
    return re.sub(r"^(TOKO|TK|CV|PT|UD|TB)\s+", "", s)


def cek_toko(p, cust):
    nama = {norm_toko((cust or {}).get("name")), norm_toko((cust or {}).get("customerNo"))} - {""}
    aju = {norm_toko(p.get("pelanggan_accurate")), norm_toko(p.get("toko"))} - {""}
    if not any(a == n or (len(a) >= 4 and (a in n or n in a)) for a in aju for n in nama):
        raise Dikembalikan("cek nama toko: di Accurate '%s', diajukan '%s'" % ((cust or {}).get("name"), p.get("toko")))


def simpan_cadangan(nama, doc):
    if UJI:
        return
    os.makedirs(CADANGAN_REVISI, exist_ok=True)
    json.dump(doc, open(os.path.join(CADANGAN_REVISI, "%s_%s.json" % (re.sub(r"[^\w.]+", "_", nama), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))),
                        "w", encoding="utf-8"), ensure_ascii=False)


def baris_kode(dok, kode):
    kode = str(kode or "").strip().upper()
    hasil = [x for x in dok.get("detailItem") or [] if str((x.get("item") or {}).get("no", "")).upper() == kode]
    if len(hasil) > 1:
        raise PerluTanya("kode %s ada %d baris di %s - revisi manual" % (kode, len(hasil), dok.get("number")))
    return hasil[0] if hasil else None


def rencana_qty(p, dok, nama):
    """[(baris_dok, qty_baru)] dari barang pengajuan; cek kode & qty sebelum"""
    hasil = []
    for b in p.get("barang") or []:
        x = baris_kode(dok, b.get("item"))
        if not x:
            raise Dikembalikan("cek tipe barang: %s tidak ada di %s %s" % (b.get("item"), nama, dok.get("number")))
        lama, baru = float(b.get("qty_lama")), float(b.get("qty_baru"))
        if abs(float(x.get("quantity") or 0) - lama) > 1e-9:
            raise Dikembalikan("cek qty: %s di %s %s qty %g, diajukan sebelum %g" % (b.get("item"), nama, dok.get("number"), float(x.get("quantity") or 0), lama))
        if baru > lama or baru < 0:
            raise PerluTanya("qty %s naik / negatif (%g -> %g) - revisi manual" % (b.get("item"), lama, baru))
        if baru != lama:
            hasil.append((x, baru))
    if not hasil:
        raise Dikembalikan("cek qty: tidak ada qty yang berubah")
    return hasil


def tulis_qty(ep, dok, rencana):
    if all(baru == 0 for _, baru in rencana) and len(rencana) == len(dok.get("detailItem") or []):
        raise PerluTanya("semua barang di %s jadi 0 - pilih keterangan hapus" % dok.get("number"))
    par = {"id": dok["id"], "branchId": dok.get("branchId")}
    for i, (x, baru) in enumerate(rencana):
        par["detailItem[%d].id" % i] = x["id"]
        par["detailItem[%d].itemNo" % i] = x["item"]["no"]
        if baru == 0:
            par["detailItem[%d]._status" % i] = "delete"
        else:
            par["detailItem[%d].quantity" % i] = int(baru) if float(baru).is_integer() else baru
    acc(ep + "/save.do", par, tulis=True)
    if UJI:
        return
    d2 = acc(ep + "/detail.do", {"id": dok["id"]})["d"]
    for x, baru in rencana:
        y = baris_kode(d2, x["item"]["no"])
        q = float(y.get("quantity") or 0) if y else 0.0
        if abs(q - baru) > 1e-9:
            raise RuntimeError("dibaca ulang: %s %s qty %g, bukan %g" % (d2.get("number"), x["item"]["no"], q, baru))


def hapus_faktur_dulu(p, no, langkah, cek_saja=False):
    f = faktur_dari(no)
    if not f:
        raise PerluTanya("DO %s sudah difaktur tapi faktur bernomor sama tidak ketemu - revisi manual" % no)
    if f.get("branchId") == CABANG_BANDUNG_ID:
        raise PerluTanya("faktur Bandung - tidak disentuh bot")
    if f.get("lastPaymentDate") or abs(float(f.get("primeOwing") or 0) - float(f.get("totalAmount") or 0)) > 1:
        raise PerluTanya("faktur %s sudah ada pembayaran - tidak boleh dihapus" % no)
    if f.get("taxNumber"):
        raise PerluTanya("faktur %s sudah punya nomor faktur pajak %s - revisi manual" % (no, f.get("taxNumber")))
    if not (p.get("ket_revisi") or {}).get("ttd"):
        raise PerluTanya("hapus faktur wajib TTD gudang - ceklis TTD kosong")
    d = tgl(f.get("transDate"))
    if not d or not dalam_jendela(d):
        raise PerluTanya("faktur %s tanggal %s bukan bulan berjalan - revisi manual" % (no, f.get("transDate")))
    if cek_saja:
        return
    simpan_cadangan("faktur_" + no, acc("sales-invoice/detail.do", {"id": f["id"]})["d"])
    acc_hapus("sales-invoice", f["id"])
    langkah.append("FAKTUR %s DIHAPUS (buat faktur ulang)" % no)


def sudah_difaktur(do):
    return any(float(x.get("invoiceQuantity") or 0) > 0 for x in do.get("detailItem") or [])


def cadangan_terakhir(nama):
    """cadangan dokumen terakhir yang disimpan agen sebelum menulis (skrip\\log\\cadangan_revisi) atau None"""
    if not os.path.isdir(CADANGAN_REVISI):
        return None
    pola = re.sub(r"[^\w.]+", "_", nama) + "_"
    f = sorted(x for x in os.listdir(CADANGAN_REVISI) if re.fullmatch(re.escape(pola) + r"\d{14}\.json", x))
    return json.load(open(os.path.join(CADANGAN_REVISI, f[-1]), encoding="utf-8")) if f else None


def qty_do_untuk_so(do, no_so):
    """{kode: qty} baris DO yang mengambil dari SO itu"""
    hasil = {}
    for x in (do or {}).get("detailItem") or []:
        if str((x.get("salesOrder") or {}).get("number") or "") == no_so:
            k = str((x.get("item") or {}).get("no", "")).upper()
            hasil[k] = hasil.get(k, 0.0) + float(x.get("quantity") or 0)
    return hasil


def rencana_hapus_so(p, so, do_ambil, do_masih_ada):
    """'hapus SO' / 'hapus DO SO' (Kak Intan 21 Nov 2026, Kogja): SO yang sebagian sudah dipakai DO / faktur lain
    TIDAK bisa dihapus Accurate ("telah digunakan di Rincian Faktur Penjualan") -> SO diedit, bukan dihapus:
      - hapus DO SO : qty SO dikurangi qty DO yang ikut dihapus;
      - hapus SO    : sisa SO yang belum terpakai (kode yang diajukan, atau semua kode kalau kosong) dibuang.
    Boleh asal kode & qty yang diminta belum dipakai DO / faktur lain. Semua dicek SEBELUM menulis apa pun.
    -> ("hapus", None) atau ("edit", [(baris_so, qty_baru)])"""
    baris = so.get("detailItem") or []
    pakai_lain = {}
    for x in baris:
        k = str((x.get("item") or {}).get("no", "")).upper()
        kirim = float(x.get("shipQuantity") or 0)
        if do_masih_ada:            # DO pengajuan ini masih ada -> qty-nya ikut terhitung di shipQuantity
            kirim -= do_ambil.get(k, 0.0)
        pakai_lain[x["id"]] = max(0.0, kirim)
    if not any(pakai_lain.values()):
        return "hapus", None
    rencana = []
    if do_ambil:
        for k, q in do_ambil.items():
            x = baris_kode(so, k)
            if not x:
                raise Dikembalikan("cek nomor SO: %s tidak ada di SO %s" % (k, so.get("number")))
            baru = float(x.get("quantity") or 0) - q
            if baru < pakai_lain[x["id"]] - 1e-9 or baru < 0:
                raise Dikembalikan("cek qty: %s di SO %s qty %g, %g sudah dipakai DO/faktur lain - tidak bisa dikurangi %g"
                                   % (k, so.get("number"), float(x.get("quantity") or 0), pakai_lain[x["id"]], q))
            rencana.append((x, baru))
    else:
        kode = [str(b.get("item") or "").strip().upper() for b in p.get("barang") or [] if b.get("item")]
        for k in kode:
            if not baris_kode(so, k):
                raise Dikembalikan("cek tipe barang: %s tidak ada di SO %s" % (k, so.get("number")))
        for x in baris:
            k = str((x.get("item") or {}).get("no", "")).upper()
            if (not kode or k in kode) and float(x.get("quantity") or 0) > pakai_lain[x["id"]] + 1e-9:
                rencana.append((x, pakai_lain[x["id"]]))
        if not rencana:
            raise Dikembalikan("cek qty: SO %s sudah terpakai semua di DO/faktur - tidak ada sisa yang bisa dihapus" % so.get("number"))
    return "edit", rencana


def teks_qty(rencana):
    return ", ".join("%s %g->%g" % (x["item"]["no"], float(x["quantity"]), b) for x, b in rencana)


def kerjakan_revisi(p):
    aksi = p.get("aksi_revisi") or "revisi DO"   # pengajuan lama tanpa keterangan: qty di DO (penjelasan form lama)
    if aksi not in AKSI_REVISI:
        raise PerluTanya("keterangan revisi tidak dikenal: %s" % aksi)
    kr = p.get("ket_revisi") or {}
    # Kogja 20 Nov 2026: cukup SALAH SATU syarat (nota tanpa TTD gudang biasanya barangnya memang belum keluar)
    if not any(kr.get(k) for k in ("gudang", "cetak", "ttd")):
        raise Dikembalikan("ceklis salah satu: belum keluar gudang / belum cetak / TTD gudang")
    langkah = []
    no = no_dok(p.get("nomor"))
    no_so = no_dok(p.get("nomor_so"), "SO.") if p.get("nomor_so") else ""
    do = so = None
    do_sudah_hapus = False   # DO sudah dihapus agen di putaran sebelumnya (pengajuan yang sama dikerjakan ulang)
    if aksi in ("revisi SO", "hapus SO") and no.startswith("SO."):
        no_so, no = no, ""
    if no:
        do = baca_dok("delivery-order", no)
        if not do and aksi.startswith("hapus DO"):
            # Kak Intan 21 Nov 2026: dulu dikerjakan ulang -> "cek nomor DO: tidak ketemu" padahal agen sendiri yang
            # menghapusnya. Cadangan DO dari agen ada -> DO dianggap selesai, lanjut ke SO.
            do = cadangan_terakhir("do_" + no)
            do_sudah_hapus = bool(do)
        if not do and aksi != "hapus faktur":
            raise Dikembalikan("cek nomor DO: %s tidak ketemu di Accurate" % no)
    if do:
        if do.get("branchId") == CABANG_BANDUNG_ID:
            raise PerluTanya("DO Bandung - tidak disentuh bot (revisi manual)")
        cek_toko(p, do.get("customer"))
        so_do = sorted({str((x.get("salesOrder") or {}).get("number") or "") for x in do.get("detailItem") or []} - {""})
        if no_so and no_so not in so_do:
            raise Dikembalikan("cek nomor SO: DO %s memakai %s, diajukan %s" % (no, ", ".join(so_do) or "-", no_so))
        if not no_so and len(so_do) == 1:
            no_so = so_do[0]
        d = tgl(do.get("transDate"))
        if not do_sudah_hapus and (not d or not dalam_jendela(d)):
            raise PerluTanya("nota %s tanggal %s bukan bulan berjalan - revisi manual (KE PAJAK)" % (no, do.get("transDate")))
    if aksi in ("revisi SO", "revisi DO SO", "hapus SO", "hapus DO SO", "hapus DO edit SO"):
        if not no_so:
            raise Dikembalikan("cek nomor SO: nomor SO kosong")
        so = baca_dok("sales-order", no_so)
        if not so:
            raise Dikembalikan("cek nomor SO: %s tidak ketemu di Accurate" % no_so)
        if so.get("branchId") == CABANG_BANDUNG_ID:
            raise PerluTanya("SO Bandung - tidak disentuh bot (revisi manual)")
        cek_toko(p, so.get("customer"))
        # Kogja 20 Nov 2026: SO tidak berjurnal & tidak ke pajak -> SO bulan lalu boleh direvisi / dihapus asal syarat
        # terpenuhi. Batas bulan berjalan tetap untuk DO dan faktur.
    # Kak Intan 21 Nov 2026: SEMUA dicek dulu - ada yang tidak sesuai -> dikembalikan ke admin, TIDAK ada yang dieksekusi
    r_do = rencana_qty(p, do, "DO") if aksi in ("revisi DO", "revisi DO SO") and not do_sudah_hapus else None
    r_so = rencana_qty(p, so, "SO") if aksi in ("revisi SO", "revisi DO SO", "hapus DO edit SO") else None
    cara_so = None
    if aksi in ("hapus SO", "hapus DO SO"):
        do_ambil = qty_do_untuk_so(do, no_so) if aksi == "hapus DO SO" else {}
        cara_so, r_hapus = rencana_hapus_so(p, so, do_ambil, do_masih_ada=bool(do) and not do_sudah_hapus)
        if cara_so == "edit":
            r_so = r_hapus
    if do and not do_sudah_hapus and aksi != "hapus faktur" and aksi in ("revisi DO", "revisi DO SO", "hapus DO saja", "hapus DO SO", "hapus DO edit SO") and sudah_difaktur(do):
        hapus_faktur_dulu(p, no, [], cek_saja=True)   # syarat hapus faktur dicek sekarang, bukan sesudah ada yang ditulis
    if do_sudah_hapus:
        langkah.append("DO %s sudah dihapus agen sebelumnya" % no)
    ringkas_sudah, sedang = [], ""
    try:
        if aksi == "hapus faktur":
            sedang = "faktur"
            hapus_faktur_dulu(p, no, langkah)
            ringkas_sudah.append("Hapus faktur berhasil")
        elif aksi in ("revisi DO", "revisi DO SO", "hapus DO saja", "hapus DO SO", "hapus DO edit SO") and not do_sudah_hapus:
            sedang = "DO"
            if sudah_difaktur(do):
                sedang = "faktur"
                hapus_faktur_dulu(p, no, langkah)
                ringkas_sudah.append("Hapus faktur berhasil")
                sedang = "DO"
            simpan_cadangan("do_" + no, do)
            if aksi.startswith("hapus"):
                acc_hapus("delivery-order", do["id"])
                langkah.append("DO %s DIHAPUS" % no)
                ringkas_sudah.append("Hapus DO berhasil")
            else:
                tulis_qty("delivery-order", do, r_do)
                langkah.append("REVISI DO %s - %s" % (no, teks_qty(r_do)))
                ringkas_sudah.append("Revisi DO berhasil")
        if aksi in ("revisi SO", "revisi DO SO", "hapus SO", "hapus DO SO", "hapus DO edit SO"):
            sedang = "SO"
            if so is None or not so.get("id"):
                raise PerluTanya("SO tidak terbaca")
            if do and langkah and not do_sudah_hapus:
                so = baca_dok("sales-order", no_so) or so   # shipQuantity SO berubah sesudah DO dihapus/direvisi
                if cara_so == "edit":
                    r_so = [(baris_kode(so, x["item"]["no"]) or x, b) for x, b in r_so]
            simpan_cadangan("so_" + no_so, so)
            if cara_so == "hapus":
                acc_hapus("sales-order", so["id"])
                langkah.append("SO %s DIHAPUS" % no_so)
            else:
                tulis_qty("sales-order", so, r_so)
                langkah.append("%sSO %s - %s" % ("EDIT (tidak bisa dihapus: sebagian sudah difaktur) " if cara_so == "edit" else "REVISI ", no_so, teks_qty(r_so)))
    except Exception as e:  # noqa: BLE001
        if ringkas_sudah:
            raise Sebagian("%s · %s perlu cek" % (", ".join(ringkas_sudah), sedang or "sisanya"),
                           "%s | SUDAH dikerjakan: %s" % (e, "; ".join(langkah)))
        raise
    return "%s (%s)" % ("; ".join(langkah), datetime.date.today().strftime("%d %b %Y")), {}


def kerjakan_edit_tgl(p):
    no = no_dok(p.get("nomor"))
    lama, baru = tgl(p.get("lama")), tgl(p.get("baru"))
    if not lama or not baru:
        raise Dikembalikan("cek tanggal: tanggal nota '%s' / tanggal revisi '%s' tidak terbaca (pakai dd/mm/yyyy)" % (p.get("lama"), p.get("baru")))
    if not dalam_jendela(lama) or not dalam_jendela(baru):
        raise PerluTanya("tanggal di luar bulan berjalan (%s -> %s) - revisi manual" % (fmt_tgl(lama), fmt_tgl(baru)))
    do = baca_dok("delivery-order", no)
    if not do:
        raise Dikembalikan("cek nomor DO: %s tidak ketemu di Accurate" % no)
    if do.get("branchId") == CABANG_BANDUNG_ID:
        raise PerluTanya("DO Bandung - tidak disentuh bot (revisi manual)")
    cek_toko(p, do.get("customer"))
    if p.get("nomor_so"):
        so_do = {str((x.get("salesOrder") or {}).get("number") or "") for x in do.get("detailItem") or []}
        if no_dok(p.get("nomor_so"), "SO.") not in so_do:
            raise Dikembalikan("cek nomor SO: DO %s memakai %s" % (no, ", ".join(sorted(so_do - {""})) or "-"))
    do_sudah = tgl(do.get("transDate")) == baru and lama != baru and cadangan_terakhir("do_" + no) is not None
    if tgl(do.get("transDate")) != lama and not do_sudah:
        raise Dikembalikan("cek tanggal: DO %s tanggal %s, diajukan tanggal nota %s" % (no, do.get("transDate"), fmt_tgl(lama)))
    f = faktur_dari(no) if sudah_difaktur(do) else None
    if sudah_difaktur(do) and not f:
        raise PerluTanya("DO %s sudah difaktur tapi faktur bernomor sama tidak ketemu - revisi manual" % no)
    if f:
        if f.get("taxNumber"):
            raise PerluTanya("faktur %s sudah punya nomor faktur pajak - edit tanggal manual" % no)
        if f.get("lastPaymentDate"):
            raise PerluTanya("faktur %s sudah ada pembayaran - edit tanggal manual" % no)
    langkah = []
    tulis_do = lambda: (simpan_cadangan("do_" + no, do), acc("delivery-order/save.do", {"id": do["id"], "branchId": do.get("branchId"), "transDate": fmt_tgl(baru)}, tulis=True),  # noqa: E731
                        langkah.append("DO %s tgl %s -> %s" % (no, fmt_tgl(lama), fmt_tgl(baru))))

    def tulis_faktur():
        fd = acc("sales-invoice/detail.do", {"id": f["id"]})["d"]
        simpan_cadangan("faktur_" + no, fd)
        par = {"id": f["id"], "branchId": f.get("branchId") or do.get("branchId"), "transDate": fmt_tgl(baru)}
        if tgl(f.get("taxDate")) == lama:
            par["taxDate"] = fmt_tgl(baru)
        acc("sales-invoice/save.do", par, tulis=True)
        langkah.append("FAKTUR %s tgl %s -> %s" % (no, f.get("transDate"), fmt_tgl(baru)))
    try:
        # tanggal DO tidak boleh lewat tanggal faktur: maju -> faktur dulu, mundur -> DO dulu
        urut = [tulis_faktur, tulis_do] if (f and baru > lama) else [tulis_do] + ([tulis_faktur] if f else [])
        if do_sudah:   # dikerjakan ulang: tanggal DO sudah diganti agen sebelumnya
            langkah.append("DO %s sudah bertanggal %s" % (no, fmt_tgl(baru)))
            urut = [fn for fn in urut if fn is not tulis_do]
            if f and tgl(f.get("transDate")) == baru:
                urut = []
        for fn in urut:
            fn()
    except Exception as e:  # noqa: BLE001
        if langkah:
            sudah = "Edit tanggal faktur berhasil" if langkah[0].startswith("FAKTUR") else "Edit tanggal DO berhasil"
            raise Sebagian("%s · %s perlu cek" % (sudah, "DO" if langkah[0].startswith("FAKTUR") else "faktur"),
                           "%s | SUDAH dikerjakan: %s" % (e, "; ".join(langkah)))
        raise
    if not UJI:
        d2 = acc("delivery-order/detail.do", {"id": do["id"]})["d"]
        if tgl(d2.get("transDate")) != baru:
            raise RuntimeError("dibaca ulang: DO %s tanggal %s, bukan %s | %s" % (no, d2.get("transDate"), fmt_tgl(baru), "; ".join(langkah)))
    return "EDIT TANGGAL - %s (%s)" % ("; ".join(langkah), datetime.date.today().strftime("%d %b %Y")), {}


# ---------------- putaran ----------------
KERJA = {"limit": kerjakan_limit, "umur": kerjakan_umur, "toko": kerjakan_toko, "kompen": kerjakan_kompen,
         "ktp": kerjakan_ktp, "buka": kerjakan_buka,  # hanya bila BOT_KTP=1 (lihat alasan_antre)
         "revisi": kerjakan_revisi, "edit_tgl": kerjakan_edit_tgl}  # dua terakhir hanya bila BOT_REVISI=1


def tanda_acc(p):
    """penanda ACC: acc_jam; edit tanggal / revisi nota dari cabang disimpan "menunggu" + tanpa_ibu tanpa acc_jam
    (server hanya izinkan pusat mengubah status) -> pakai waktu dibuat (18 Nov 2026)"""
    return p.get("acc_jam") or (p.get("dibuat") if tanpa_ibu(p) else None) or "-"


def sudah_untuk_acc_ini(p):
    return (p.get("eksekusi_acc_jam") or "-") == tanda_acc(p)


# tanpa_ibu ditulis halaman cabang dan server web TIDAK menjaganya -> hanya sah untuk jenis yang memang boleh tanpa
# ACC Ibu (Gio 18 Nov 2026). Tanpa ini cabang bisa mengirim pengajuan limit/toko/kompen bertanda tanpa_ibu dan
# langsung dikerjakan ke Accurate.
JENIS_TANPA_IBU = ("edit_tgl", "revisi")


def tanpa_ibu(p):
    return bool(p.get("tanpa_ibu")) and p.get("jenis") in JENIS_TANPA_IBU


def boleh_dikerjakan(p):
    # "diproses" = bot sempat berhenti di tengah (mis. dinyalakan ulang) -> dilanjutkan; pekerjaan aman diulang
    # (cek "sudah dikerjakan admin/agen" di catatan akun & akun kembar mencegah tulis dua kali)
    st = p.get("status") or "menunggu"
    if not (st in ("acc", "acc_sementara", "diproses") or (st == "menunggu" and tanpa_ibu(p))) or sudah_untuk_acc_ini(p):
        return False
    peny = [x.strip().lower() for x in E.get("PENGAJUAN_PENYETUJU", "").split(",") if x.strip()]
    if peny and str(p.get("acc_oleh") or "").strip().lower() not in peny and not tanpa_ibu(p):
        return False
    return True


def batas_sementara(eksekusi_jam):
    """ACC sementara berlaku sampai jam 16.00 hari itu; dikerjakan sesudah 16.00 -> sampai 16.00 besoknya
    (13 Nov: sebelumnya ACC sore langsung dikembalikan beberapa detik kemudian)."""
    t = datetime.datetime.fromisoformat(eksekusi_jam).replace(tzinfo=None)
    batas = t.replace(hour=JAM_KEMBALI[0], minute=JAM_KEMBALI[1], second=0, microsecond=0)
    return batas if t < batas else batas + datetime.timedelta(days=1)


def putaran(semua):
    global _sibuk_sampai
    sekarang = datetime.datetime.now()
    jam = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")  # noqa: E731
    for pid, p in semua.items():
        p = {**p, "_id": pid}
        j = p.get("jenis")
        if boleh_dikerjakan(p) and time.time() >= _sibuk_sampai:
            kurang = syarat_kurang(p)
            if kurang:
                teks = "menunggu syarat: " + "; ".join(kurang)
                if p.get("eksekusi") != teks:
                    ubah_pengajuan(pid, {"eksekusi": teks})  # status tetap ACC, dicek lagi tiap putaran
                continue
            antre = alasan_antre(j)
            if antre:
                ubah_pengajuan(pid, {"eksekusi": "antre admin: " + antre, "eksekusi_acc_jam": tanda_acc(p)})
                continue
            if j in ("revisi", "edit_tgl") and revisi_aktif() and str(p.get("cabang") or "").upper() == "BANDUNG":
                ubah_pengajuan(pid, {"eksekusi": "Bandung: revisi manual (aturan KELINCI, bot tidak menyentuh Bandung)", "eksekusi_acc_jam": tanda_acc(p)})
                continue
            if j in REKAP_DULU and not (j in ("revisi", "edit_tgl") and revisi_aktif()):
                try:
                    teks = rekap_nota(p) if j != "edit_tgl" else "edit tanggal dikerjakan admin langsung (aturan 30 Okt). " + rekap_nota(p)
                except Exception as e:  # noqa: BLE001
                    teks = "rekap gagal: %s" % e
                ubah_pengajuan(pid, {"eksekusi": teks, "eksekusi_acc_jam": tanda_acc(p)})
                catat("REKAP", pid, j, teks[:200])
                continue
            if j not in KERJA:
                continue
            asal = (p.get("status") or "menunggu") if p.get("status") != "diproses" else (p.get("proses_dari") or "acc")
            catat("KERJAKAN", pid, j, p.get("toko"), "ACC", p.get("acc_oleh"))
            if not UJI:
                ubah_pengajuan(pid, {"status": "diproses", "proses_dari": asal, "eksekusi": "bot sedang menulis ke Accurate"})
            p["status"] = asal
            try:
                ket, lama = KERJA[j](p)
                ubah_pengajuan(pid, {"status": "acc_sementara" if p["status"] == "acc_sementara" and lama else "selesai",
                                     "eksekusi": "agen: " + ket, "eksekusi_oleh": "bot", "eksekusi_jam": jam(), "eksekusi_lama": lama,
                                     "eksekusi_acc_jam": tanda_acc(p), "eksekusi_galat": None, "dikembalikan_bot": None,
                                     "eksekusi_sebagian": None})
                catat("  OK", ket)
            except Sibuk as e:
                _sibuk_sampai = time.time() + 10
                ubah_pengajuan(pid, {"status": p["status"], "eksekusi": "%s - dicoba lagi otomatis tiap 10 detik" % e})
                catat("  SIBUK", e)
                break
            except Dikembalikan as e:
                ubah_pengajuan(pid, {"status": "dikembalikan", "status_sebelum": p["status"], "catatan_kembali": str(e)[:500],
                                     "kembali_jam": jam(), "kembali_oleh": "bot", "eksekusi": "dikembalikan bot: %s" % e,
                                     # bukan acc_jam: sesudah sales memperbaiki & status kembali ACC, dikerjakan lagi
                                     "eksekusi_acc_jam": "dikembalikan"})
                catat("  DIKEMBALIKAN", e)
            except Sebagian as e:
                # status tetap "gagal" (pusat bisa ▶ Kerjakan lagi / ✓ Sudah dikerjakan), tapi labelnya "Hapus DO berhasil · SO perlu cek"
                ubah_pengajuan(pid, {"status": "gagal", "eksekusi_sebagian": e.ringkas, "eksekusi_galat": str(e)[:500],
                                     "eksekusi": "agen: " + e.ringkas, "eksekusi_jam": jam(), "eksekusi_acc_jam": tanda_acc(p)})
                catat("  SEBAGIAN", e.ringkas, "|", e)
            except PerluTanya as e:
                ubah_pengajuan(pid, {"status": "gagal", "eksekusi_galat": "PERLU TANYA: %s" % e, "eksekusi": "bot berhenti - perlu keputusan", "eksekusi_sebagian": None,
                                     "eksekusi_acc_jam": tanda_acc(p)})
                catat("  PERLU TANYA", e)
            except Exception as e:  # noqa: BLE001
                ubah_pengajuan(pid, {"status": "gagal", "eksekusi_galat": str(e)[:500], "eksekusi": "bot gagal - admin cek", "eksekusi_sebagian": None,
                                     "eksekusi_acc_jam": tanda_acc(p)})
                catat("  GAGAL", e)
        elif (p.get("status") == "acc_sementara" and p.get("eksekusi_jam") and not p.get("dikembalikan_bot")
              and sekarang >= batas_sementara(p["eksekusi_jam"])):
            try:
                kembalikan_sementara(p)
            except Exception as e:  # noqa: BLE001
                catat("  GAGAL KEMBALI", pid, e)


# ---------------- pemindahan barang (Kak Intan 14 Nov 2026) ----------------
# Tab Pemindahan barang ikut repo ini. Ceklis "Hana OK kirim" = persetujuan: bot langsung membuat Pemindahan Barang
# (Proses: Kirim Barang, TRANSFER_OUT) di Accurate, satu IT per gudang asal -> tujuan, lalu mengisi No. Pemindahan
# dan ceklis "Sudah input Accurate". Penerimaan (Terima Barang) tetap oleh cabang / admin.
ACC_PINDAH_SEJAK = "2026-11-14T02:58:30"  # UTC, = 09.58 WIB 14 Nov 2026


_cab_gudang = None


def cabang_gudang(gudang):
    """cabang Accurate untuk IT = cabang gudang asal (pola IT lama: LAKSANA/DAANMOGOT -> JAKARTA, SURABAYA -> GRESIK)"""
    global _cab_gudang
    if _cab_gudang is None:
        _cab_gudang = {}
        try:
            for r in json.load(open(os.path.join(GIO, "dashboard", "data", "slow_moving.json"), encoding="utf-8")):
                for g, _q in r.get("gudang") or []:
                    _cab_gudang.setdefault(g, r["cabang"])
        except Exception:  # noqa: BLE001
            pass
    return _cab_gudang.get(gudang)


_pl = {"waktu": 0, "data": None}


def harga_pricelist(item, cabang_tujuan):
    """keterangan baris IT = harga pricelist bulan terbaru (Kak Intan 14 Nov 2026): Aqua/Haier harga bayar,
    Polytron toko bayar -3% (Palembang -4%), Miyako price list exc PPN, Maspion price list.
    Data dari skrip/pricelist_pindah.py (dibangun ulang otomatis kalau ada folder bulan baru)."""
    if time.time() - _pl["waktu"] > 3600 or _pl["data"] is None:
        try:
            sys.path.insert(0, os.path.join(GIO, "skrip"))
            import pricelist_pindah as PL
            ada = json.load(open(PL.HASIL, encoding="utf-8")) if os.path.exists(PL.HASIL) else {}
            _pl["data"] = _pl["data"] or ada   # hasil terakhir tetap dipakai kalau pembangunan ulang gagal
            # 18 Nov 2026: folder pricelist jadi <TAHUN>/<n. BULAN>/<CABANG>/<MERK>/ - dibangun ulang tiap ada
            # berkas baru diunggah (sidik isi folder), bukan hanya saat ganti bulan
            if PL.perlu_bangun(ada):
                ada, _ = PL.bangun()
                catat("PRICELIST dibangun ulang:", ada.get("bulan"))
            _pl["data"] = ada
        # 18 Nov 2026: modul pricelist dulu melempar SystemExit (folder Drive berganti nama) dan itu lolos dari
        # "except Exception" -> bot mati di tengah membuat IT. SystemExit ikut ditangkap.
        except (Exception, SystemExit) as e:  # noqa: BLE001
            catat("PRICELIST galat (pakai data terakhir):", repr(e))
            _pl["data"] = _pl["data"] or {}
        _pl["waktu"] = time.time()
    r = (_pl["data"].get("harga") or {}).get(item)
    if not r:
        # 18 Nov 2026 (Kak Intan, IT.2026.11.00118 AC SHARP tanpa keterangan): merk di luar aturan pricelist
        # (Sharp, Rinnai, Cosmos, ...) ikut lapisan harga dashboard: REKAP HARGA cabang tujuan > JAKARTA > cabang
        # lain > HPP rata-rata Accurate + 11%. Harga < 10.000 bukan harga (kardus, unit outdoor Rp 1).
        return harga_cadangan_pindah(item, cabang_tujuan)
    h = float(r["harga"])
    if r["merk"] == "POLYTRON":
        h *= 0.96 if str(cabang_tujuan).upper() == "PALEMBANG" else 0.97
    return int(round(h))


HARGA_MIN_PD = 10000
_hpp_pd = None


def harga_cadangan_pindah(item, cabang_tujuan):
    """sama dengan hargaPindahBaris di web (pindah_harga.js) langkah 4-6"""
    global _modal, _hpp_pd
    if _modal is None:
        try:
            _modal = json.load(open(HARGA_MODAL, encoding="utf-8")).get("cabang", {})
        except Exception:  # noqa: BLE001
            _modal = {}
    if POLA_OUT_PD.search(item or ""):
        return None   # unit outdoor AC: harganya menempel di baris unit indoor
    cab = str(cabang_tujuan or "").upper()
    for c in [cab, "JAKARTA", *_modal.keys()]:
        m = (_modal.get(c) or {}).get(item)
        if m and float(m.get("harga") or 0) >= HARGA_MIN_PD:
            return int(round(float(m["harga"])))
    if _hpp_pd is None:
        try:
            _hpp_pd = {i["item"]: float(i.get("hpp_unit") or 0) for i in json.load(open(os.path.join(GIO, "dashboard", "data", "items.json"), encoding="utf-8"))}
        except Exception:  # noqa: BLE001
            _hpp_pd = {}
    h = int(round(_hpp_pd.get(item, 0) * 1.11))
    return h if h >= HARGA_MIN_PD else None


POLA_OUT_PD = re.compile(r"\s*\((OUT|OUTDOOR)\)\s*$", re.I)


def ubah_pindah(pid, data):
    if UJI:
        catat("  [uji] pindah ->", pid, json.dumps(data, ensure_ascii=False)[:300]); return
    apps({"aksi": "tulis", "tulis": [{"halaman": "pusat", "koleksi": "pindah_barang", "id": pid, "mode": "update", "data": data}]})


def putaran_pindah(pindah):
    global _sibuk_sampai
    if E.get("BOT_PINDAH") != "1" or time.time() < _sibuk_sampai:
        return
    # Kak Intan 14 Nov: kolom Hana dihapus dari pusat; ceklis pusat (cek_stok, "ACC pusat -> Accurate") = persetujuan.
    # Hanya centang sesudah aturan ini berlaku (baris yang sudah tercentang sebelumnya tidak ikut terkirim diam-diam).
    siap = [(pid, p) for pid, p in pindah.items() if p.get("cek_stok") and str(p.get("cek_stok_waktu") or "") >= ACC_PINDAH_SEJAK
            and not p.get("input_acc") and not p.get("eksekusi_galat") and float(p.get("qty") or 0) > 0]
    grup = {}
    for pid, p in siap:
        if str(p.get("eksekusi") or "").startswith("bot sedang menulis"):
            # bot berhenti di tengah simpan: jangan buat IT kedua, admin cek dulu
            ubah_pindah(pid, {"eksekusi_galat": "PERLU CEK: bot berhenti saat menulis - cek apakah IT sudah ada di Accurate, isi No. Pemindahan manual"})
            continue
        grup.setdefault((p.get("gudang_asal") or "DAANMOGOT", p.get("gudang_tujuan") or p.get("cabang")), []).append((pid, p))
    jam = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    # harga diubah pusat sesudah IT dibuat -> keterangan baris IT di Accurate ikut direvisi
    for pid, p in pindah.items():
        if not (p.get("input_acc") and p.get("it_id") and p.get("harga_modal") is not None and not p.get("eksekusi_galat")):
            continue
        baru = int(float(p["harga_modal"]))
        if p.get("harga_it") is not None and int(float(p["harga_it"])) == baru:
            continue
        try:
            d = acc("item-transfer/detail.do", {"id": p["it_id"]})["d"]
            r = next((x for x in d.get("detailItem") or [] if (x.get("item") or {}).get("no") == p["item"]), None)
            if not r:
                raise RuntimeError("baris %s tidak ada di %s" % (p["item"], d.get("number")))
            acc("item-transfer/save.do", {"id": d["id"], "branchName": cabang_gudang(d.get("warehouseName") or p.get("gudang_asal")) or "JAKARTA",
                                          "detailItem[0].id": r["id"], "detailItem[0].itemNo": p["item"],
                                          "detailItem[0].quantity": str(int(float(r["quantity"]))),
                                          "detailItem[0].detailNotes": "{:,}".format(baru).replace(",", ".")}, tulis=True)
            ubah_pindah(pid, {"harga_it": baru, "eksekusi": "agen: keterangan %s direvisi ke %s (%s)" % (d.get("number"), "{:,}".format(baru).replace(",", "."), jam)})
            catat("  OK revisi harga", d.get("number"), p["item"], baru)
        except Sibuk as e:
            _sibuk_sampai = time.time() + 10
            catat("  SIBUK", e)
            return
        except Exception as e:  # noqa: BLE001
            ubah_pindah(pid, {"eksekusi": "revisi harga gagal - admin cek", "eksekusi_galat": str(e)[:500]})
            catat("  GAGAL revisi harga", p.get("no_it"), e)
    for (asal, tujuan), baris in grup.items():
        catat("PINDAH", asal, "->", tujuan, ", ".join("%s %s" % (p["item"], p["qty"]) for _, p in baris))
        for pid, _ in baris:
            ubah_pindah(pid, {"eksekusi": "bot sedang menulis ke Accurate"})
        cab = sorted({str(p.get("cabang") or "") for _, p in baris})
        cabang_it = cabang_gudang(asal)
        if not cabang_it:
            for pid, _ in baris:
                ubah_pindah(pid, {"eksekusi": "bot gagal - admin cek", "eksekusi_galat": "cabang Accurate untuk gudang %s tidak diketahui" % asal})
            catat("  GAGAL pindah", asal, "cabang tidak diketahui")
            continue
        par = {"transDate": datetime.date.today().strftime("%d/%m/%Y"), "itemTransferType": "TRANSFER_OUT", "branchName": cabang_it,
               "warehouseName": asal, "referenceWarehouseName": tujuan,
               "description": ("PINDAH BARANG WEB KE %s - ACC PUSAT (agen)" % "/".join(cab))[:250]}
        tanpa_pl, cat = [], []
        for n, (pid, p) in enumerate(baris):
            par["detailItem[%d].itemNo" % n] = p["item"]
            par["detailItem[%d].quantity" % n] = str(int(float(p["qty"])))
            h = int(float(p["harga_modal"])) if p.get("harga_modal") is not None else harga_pricelist(p["item"], p.get("cabang"))
            p["_harga"] = h
            if h:
                par["detailItem[%d].detailNotes" % n] = "{:,}".format(h).replace(",", ".")   # Info lainnya > Keterangan
            else:
                tanpa_pl.append(p["item"])
            cat += [x for x in (p.get("sales"), p.get("catatan")) if x]
        if cat:
            par["description"] = (par["description"] + " | " + "; ".join(cat))[:250]
        try:
            r = acc("item-transfer/save.do", par, tulis=True)
            rid = (r.get("r") or {}).get("id") if isinstance(r.get("r"), dict) else None
            nomor = (r.get("r") or {}).get("number") if isinstance(r.get("r"), dict) else None
            if rid and not nomor and not UJI:
                nomor = acc("item-transfer/detail.do", {"id": rid})["d"].get("number")
            for pid, p in baris:
                ubah_pindah(pid, {"input_acc": True, "input_acc_waktu": jam, "no_it": nomor or "?", "eksekusi_jam": jam,
                                  "it_id": rid, "harga_it": p.get("_harga"),
                                  "eksekusi": "agen: %s dibuat (%s -> %s)%s" % (nomor, asal, tujuan,
                                      (" | tanpa harga pricelist: " + ", ".join(tanpa_pl)) if tanpa_pl else ""), "eksekusi_galat": None})
            catat("  OK pindah", nomor, asal, "->", tujuan)
        except Sibuk as e:
            _sibuk_sampai = time.time() + 10
            for pid, _ in baris:
                ubah_pindah(pid, {"eksekusi": "%s - dicoba lagi otomatis" % e})
            catat("  SIBUK", e)
            return
        except Exception as e:  # noqa: BLE001
            for pid, _ in baris:
                ubah_pindah(pid, {"eksekusi": "bot gagal - admin cek", "eksekusi_galat": str(e)[:500]})
            catat("  GAGAL pindah", asal, "->", tujuan, e)


_KUNCI_SALINAN = None


def kunci_satu_salinan():
    """Hanya boleh ada SATU bot yang jalan.

    18 Nov 2026: ketahuan dua salinan hidup bersamaan (jadwal Task Scheduler menyalakan ulang tiap menit
    kalau proses mati, dan tidak ada yang memeriksa salinan lama). Dua bot membaca antrean yang sama,
    jadi satu pengajuan yang di-ACC bisa dikerjakan dua kali di Accurate (paling berbahaya di pemindahan
    barang: bisa jadi dua dokumen IT). Berkas kunci dipegang selama proses hidup; Windows melepasnya
    sendiri kalau prosesnya mati, jadi tidak ada kunci basi.
    """
    global _KUNCI_SALINAN
    import msvcrt
    f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.lock"), "a+", encoding="utf-8")
    f.seek(0)
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lama = ""
        try:
            lama = open(f.name, encoding="utf-8").read().strip()
        except OSError:
            pass
        catat("berhenti - sudah ada bot lain yang jalan" + (" (PID %s)" % lama if lama else ""))
        sys.exit(0)
    f.seek(0)
    f.truncate()
    f.write(str(os.getpid()))
    f.flush()
    _KUNCI_SALINAN = f          # jangan ditutup / jangan dibuang: kunci ikut terlepas
    return f


def main():
    kurang = [k for k in ("PENGAJUAN_APPS_URL", "PENGAJUAN_MASTER", "ACCURATE_TULIS_TOKEN", "ACCURATE_TULIS_SECRET") if not E.get(k)]
    if kurang:
        sys.exit("Belum lengkap di .env: " + ", ".join(kurang))
    if not UJI and "--sekali" not in sys.argv:
        kunci_satu_salinan()
    catat("Bot pengajuan v2 mulai" + (" (UJI - tidak menulis)" if UJI else "") + (" | kompen AKTIF" if E.get("BOT_KOMPEN") == "1" else " | kompen belum aktif") + (" | pindah AKTIF" if E.get("BOT_PINDAH") == "1" else " | pindah belum aktif")
          + (" | ganti KTP & buka blokir AKTIF" if ktp_aktif() else " | ganti KTP & buka blokir belum aktif"))
    semua, pindah, sejak = {}, {}, 0
    while True:
        try:
            j = apps({"aksi": "daftar", "sejak": sejak})
            for d in j["docs"]:
                sejak = max(sejak, d["diubah"])
                tempat = semua if d["koleksi"] == "pengajuan" else pindah if (d["koleksi"] == "pindah_barang" and d.get("halaman") == "*") else None
                if tempat is None:
                    continue
                if d["dihapus"]:
                    tempat.pop(d["id"], None)
                else:
                    tempat[d["id"]] = d["data"]
            putaran(semua)
            putaran_pindah(pindah)
        except Exception as e:  # noqa: BLE001
            catat("GALAT putaran:", e)
        if "--sekali" in sys.argv or UJI:
            break
        time.sleep(JEDA)


if __name__ == "__main__":
    # 18 Nov 2026: bot pernah mati mendadak di tengah membuat Pemindahan Barang dan TIDAK meninggalkan jejak
    # (dijalankan pythonw, galatnya hilang). Sejak sekarang penyebabnya ditulis ke log yang sama.
    try:
        main()
    except SystemExit as e:
        if e.code not in (0, None):
            catat("BERHENTI (SystemExit):", e.code)
        raise
    except BaseException as e:  # noqa: BLE001
        import traceback
        catat("MATI MENDADAK:", repr(e))
        for baris_jejak in traceback.format_exc().rstrip().splitlines()[-12:]:
            catat("   " + baris_jejak)
        raise
