"""Bot PDF TAGIHAN + FOTO NOTA (Kak Intan 20 Nov 2026: "buat botnya ... jangan ke BEN, ke kita aja").

Tab "Tagih via WA" di web Pengajuan-Sales: tombol "PDF + foto (bot)" menulis dokumen perbarui/pdf_<toko> ke penyimpan
Apps Script (koleksi "perbarui" sudah boleh ditulis dari web) berisi nota yang diceklis + id foto Drive.
Skrip ini jalan terus di PC (pythonw, tanpa jendela), memeriksa tiap 60 detik; kalau ada permintaan baru:
  1. tulis {mulai} -> tombol di halaman berubah "bot menyusun",
  2. susun PDF: halaman rincian tagihan + foto nota bercap toko (scan di Drive "2. REKAP NOTA JALAN PENJUALAN"),
     lewat bangun_pdf_tagih.py (PyMuPDF, dijalankan dengan uv - tidak dipasang ke Python utama),
  3. simpan ke G:\\My Drive\\Agen Pajak\\DASHBOARD PENJUALAN\\PENAGIHAN WA\\<YYYY-MM>\\, tunggu Drive memberi id,
  4. tulis {selesai, url, nama} (atau {galat}) -> tombol jadi "Buka PDF".
Accurate tidak disentuh sama sekali. Folder Drive tetap privat; PDF diunduh Kak Intan lalu dilampirkan di chat.

    pythonw -I bot\\pdf_tagih.py            jalan terus (Task Scheduler "Gio - Bot PDF Tagih", saat logon)
    python  -I bot\\pdf_tagih.py --sekali   periksa sekali lalu keluar
Log: skrip\\log\\pdf-tagih.log   (JANGAN dipantau dengan tail -F)
"""
import base64, collections, datetime, hashlib, hmac, json, os, shutil, sqlite3, subprocess, sys, tempfile, time, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIO = os.path.dirname(REPO)
ENV = os.path.join(GIO, ".env")
LOG = os.path.join(GIO, "skrip", "log", "pdf-tagih.log")
STATUS = os.path.join(GIO, "skrip", "log", "pdf-tagih.json")
TT = os.path.join(GIO, "dashboard", "data", "tanda_terima.json")
CACHE = os.path.join(GIO, "dashboard", "cache_penjualan.sqlite")
# 20 Nov 2026 (Kak Intan: "jangan cuma di laptop ini"): lampiran untuk klik dari komputer lain ditaruh di Shared Drive
# kantor yang sudah bisa dibuka staf, lalu halaman menampilkan tombol unduh
BERSAMA = r"G:\Shared drives\1. DOKUMEN INVOICE SVARNA ALL CABANG\'OTOMATISASI\7. LAMPIRAN TAGIHAN WA"
SEMENTARA = os.path.join(os.environ.get("LOCALAPPDATA", r"C:\\Users\\ai\\AppData\\Local"), "Gio", "kirim_wa")
SUMBER = r"G:\Shared drives\1. DOKUMEN INVOICE SVARNA ALL CABANG\'OTOMATISASI\2. REKAP NOTA JALAN PENJUALAN"
KELUAR = r"G:\My Drive\Agen Pajak\DASHBOARD PENJUALAN\PENAGIHAN WA"
PENYUSUN = os.path.join(REPO, "bot", "bangun_pdf_tagih.py")
UV = r"C:\Users\ai\AppData\Local\hermes\bin\uv.exe"
DRIVEFS = os.path.expandvars(r"%LOCALAPPDATA%\Google\DriveFS")
NO_WIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
JEDA = 5  # 20 Nov: "secepat kilat" - 5 dtk di jam kerja (07-21), 30 dtk di luar itu


def env():
    isi = {}
    for b in open(ENV, encoding="utf-8"):
        if "=" in b and not b.lstrip().startswith("#"):
            k, v = b.split("=", 1)
            isi[k.strip()] = v.strip().strip('"')
    return isi


E = env()


def catat(*a):
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + " ".join(str(x) for x in a)
    try:
        print(t, flush=True)
    except Exception:  # noqa: BLE001 - pythonw tanpa konsol
        pass
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(t + "\n")


def apps(isi):
    kunci = hmac.new(E["PENGAJUAN_MASTER"].encode(), b"ADMIN", hashlib.sha256).hexdigest()
    body = json.dumps({"halaman": "ADMIN", "kunci": kunci, **isi}).encode()
    req = urllib.request.Request(E["PENGAJUAN_APPS_URL"], data=body, method="POST", headers={"Content-Type": "text/plain;charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.load(r)
    if not j.get("ok"):
        raise RuntimeError("penyimpan: " + str(j.get("galat")))
    return j


def unggah_langsung(halaman, jalur, nama):
    """21 Nov 2026 (Kak Intan: "jangan 1 menit dong kelamaan"): lampiran untuk komputer lain diunggah LANGSUNG lewat
    Apps Script penyimpan (aksi unggah, folder FOTO PENGAJUAN SALES WEB/<HALAMAN>/LAMPIRAN TAGIHAN WA/<bulan>) - beberapa
    detik, tidak lagi menunggu Google Drive for Desktop selesai menyinkronkan (dulu 20-70 detik). Mengembalikan id Drive."""
    kunci = hmac.new(E["PENGAJUAN_MASTER"].encode(), halaman.encode(), hashlib.sha256).hexdigest()
    b64 = base64.b64encode(open(jalur, "rb").read()).decode()
    body = json.dumps({"halaman": halaman, "kunci": kunci, "aksi": "unggah", "tipe": "application/pdf", "nama": nama, "b64": b64,
                       "folder": "LAMPIRAN TAGIHAN WA/" + datetime.date.today().strftime("%Y-%m")}).encode()
    req = urllib.request.Request(E["PENGAJUAN_APPS_URL"], data=body, method="POST", headers={"Content-Type": "text/plain;charset=utf-8"})
    with urllib.request.urlopen(req, timeout=90) as r:
        j = json.load(r)
    if not j.get("ok"):
        raise RuntimeError("unggah: " + str(j.get("galat")))
    return j["id"]


def tulis(halaman, id_, data):
    apps({"aksi": "tulis", "tulis": [{"halaman": halaman, "koleksi": "perbarui", "id": id_, "mode": "update", "data": data}]})


def kini():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def id_drive(nama, tunggu=240):
    """id Google Drive berkas `nama` dari metadata Drive for Desktop; ditunggu sampai selesai terunggah."""
    batas = time.time() + tunggu
    while time.time() < batas:
        try:
            for akun in os.listdir(DRIVEFS):
                db = os.path.join(DRIVEFS, akun, "metadata_sqlite_db")
                if not os.path.exists(db):
                    continue
                c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
                try:
                    for (i,) in c.execute("select id from items where trashed=0 and is_tombstone=0 and is_folder=0 "
                                          "and local_title=? order by rowid desc", (nama,)):
                        if i and not str(i).startswith("local"):
                            return str(i)
                finally:
                    c.close()
        except Exception as e:  # noqa: BLE001
            catat("  id Drive belum terbaca:", e)
        time.sleep(10)
    return None


def peta_foto():
    """fid Drive -> jalur lokal di G: (dari tanda_terima.json yang dibangun bot tanda terima)."""
    try:
        tt = json.load(open(TT, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {n["fid"]: os.path.join(SUMBER, n["berkas"].replace("/", os.sep)) for n in tt.get("nota") or []
            if n.get("fid") and n.get("berkas")}


def nama_berkas(teks):
    return " ".join(teks.translate({ord(c): " " for c in '\\/:*?"<>|'}).split()) + ".pdf"


def detail_faktur(nomor_list):
    """Detail faktur penjualan dari Accurate (HANYA-BACA) untuk halaman Nota: id dari cache dashboard, kalau tidak ada
    (nota sebelum 2026) dicari lewat list.do nomor. Satu jalur, jeda 0,2 dtk (API maks 8 req/detik)."""
    sys.path.insert(0, r"C:\Users\ai\AccurateMCP")
    import accurate_mcp as acc  # noqa: E402
    ids = {}
    try:
        c = sqlite3.connect("file:%s?mode=ro" % CACHE, uri=True)
        q = ",".join("?" * len(nomor_list))
        ids = dict(c.execute("select nomor, id from faktur where nomor in (%s)" % q, list(nomor_list))) if nomor_list else {}
        c.close()
    except Exception as e:  # noqa: BLE001
        catat("  cache faktur tidak terbaca:", e)
    hasil = {}
    for no in nomor_list:
        try:
            i = ids.get(no)
            if not i:
                r = acc._data_get("sales-invoice/list.do", {"fields": "id,number", "filter.number.op": "EQUAL", "filter.number.val": no})
                d = (r.get("d") or []) if r.get("s") else []
                i = d[0]["id"] if d else None
                time.sleep(0.14)
            if not i:
                continue
            r = acc._data_get("sales-invoice/detail.do", {"id": str(i)})
            time.sleep(0.14)
            if not r.get("s"):
                continue
            d = r["d"]
            hasil[no] = {
                "nomor": d.get("number"), "tgl": d.get("transDateView"), "jt": d.get("dueDateView"),
                "pelanggan": (d.get("customer") or {}).get("name"), "alamat": d.get("toAddress") or "",
                "termin": (d.get("paymentTerm") or {}).get("name") or "", "ket": d.get("description") or "",
                "sub": d.get("subTotal"), "diskon": d.get("cashDiscount") or 0, "pajak": d.get("tax1Amount") or 0, "total": d.get("totalAmount"),
                "baris": [{"kode": (x.get("item") or {}).get("no"), "nama": x.get("detailName") or (x.get("item") or {}).get("name"),
                           "qty": x.get("quantity"), "satuan": (x.get("itemUnit") or {}).get("name") or "", "harga": x.get("unitPrice"),
                           "disk": x.get("itemDiscPercent") or "", "jumlah": x.get("totalPrice")} for x in d.get("detailItem") or []]}
        except Exception as e:  # noqa: BLE001
            catat("  detail", no, "gagal:", e)
    return hasil


def susun(minta, folder=None, nama=None):
    """Bangun PDF -> (jalur rincian, nama, [jalur lain]). Mode Kirim ke WA: rincian TANPA foto + berkas "Nota" berisi
    salinan faktur Accurate per nota diikuti foto nota bercap toko (Kak Intan 20 Nov: "sekalian notanya dikirim PDF-nya")."""
    toko = str(minta.get("pelanggan") or "toko")
    tgl = str(minta.get("tgl_data") or datetime.date.today().isoformat())[:10]
    nama = nama or nama_berkas("Rincian tagihan %s %s" % (toko, tgl))
    folder = folder or os.path.join(KELUAR, tgl[:7])
    os.makedirs(folder, exist_ok=True)
    foto = peta_foto()
    berkas_foto = []
    for f in minta.get("foto") or []:
        p = foto.get(f.get("fid"))
        berkas_foto.append({"do": f.get("do"), "jalur": p if p and os.path.exists(p) else None})
    kerja = {"minta": minta, "foto": berkas_foto, "keluar": os.path.join(folder, nama)}
    lampiran = []
    if minta.get("kirim_wa"):
        # 20 Nov 2026 (Kak Intan: "notanya yang asli yang ada di Drive, kirim gambarnya"): foto/scan nota ASLI dari Drive
        # "2. REKAP NOTA JALAN PENJUALAN" dilampirkan apa adanya (tidak dikecilkan), diberi nama nomor DO-nya. Rincian
        # PDF cukup tabelnya. Salinan berganti nama ditaruh di folder lokal sementara (dibersihkan sesudah 2 hari).
        kerja["tanpa_foto"] = True
        sem = os.path.join(SEMENTARA, nama_berkas(toko)[:-4] + " " + datetime.datetime.now().strftime("%H%M%S"))
        os.makedirs(sem, exist_ok=True)
        ke = collections.Counter()
        for f in berkas_foto:
            if not f.get("jalur"):
                continue
            ke[f["do"]] += 1
            ext = os.path.splitext(f["jalur"])[1].lower() or ".jpg"
            tujuan = os.path.join(sem, "%s nota%s%s" % (f["do"], " %d" % ke[f["do"]] if ke[f["do"]] > 1 else "", ext))
            shutil.copyfile(f["jalur"], tujuan)
            lampiran.append(tujuan)
        catat("  foto nota asli: %d berkas untuk %d nota" % (len(lampiran), len(minta.get("nota") or [])))
    # 20 Nov 2026 ("botnya secepat kilat"): PyMuPDF sudah ada di Python laptop ini -> susun di proses bot sendiri;
    # uv (Python baru, beberapa detik) hanya cadangan kalau impor gagal
    try:
        sys.path.insert(0, os.path.dirname(PENYUSUN))
        import bangun_pdf_tagih as P  # noqa: E402
        laporan = P.bangun(kerja)
    except ImportError:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as t:
            json.dump(kerja, t, ensure_ascii=False)
            jalur_kerja = t.name
        try:
            r = subprocess.run([UV, "run", "--quiet", "--with", "pymupdf", "python", "-I", PENYUSUN, jalur_kerja],
                               cwd=r"C:\Users\ai", capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=600, creationflags=NO_WIN)
        finally:
            os.remove(jalur_kerja)
        if r.returncode:
            raise RuntimeError("PDF gagal disusun: " + (r.stderr or r.stdout)[-300:])
        laporan = r.stdout.strip().splitlines()
    for b in laporan:
        catat("  " + b)
    return kerja["keluar"], nama, lampiran


def _clipboard_berkas(jalur):
    """Taruh daftar berkas di clipboard Windows (CF_HDROP) - sama seperti Ctrl+C berkas di Explorer."""
    import ctypes
    from ctypes import wintypes
    k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
    k32.GlobalAlloc.restype = wintypes.HGLOBAL
    k32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    u32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    u32.SetClipboardData.restype = wintypes.HANDLE
    daftar = ("\0".join(os.path.abspath(p) for p in jalur) + "\0\0").encode("utf-16-le")
    kepala = (20).to_bytes(4, "little") + bytes(8) + bytes(4) + (1).to_bytes(4, "little")  # DROPFILES, fWide=1
    data = kepala + daftar
    h = k32.GlobalAlloc(0x0042, len(data))  # GHND
    p = k32.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    k32.GlobalUnlock(h)
    for _ in range(20):
        if u32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("clipboard sedang dipakai aplikasi lain")
    try:
        u32.EmptyClipboard()
        if not u32.SetClipboardData(15, h):  # CF_HDROP
            raise RuntimeError("clipboard menolak berkas")
    finally:
        u32.CloseClipboard()


def _depan_whatsapp():
    import ctypes
    from ctypes import wintypes
    u32 = ctypes.windll.user32
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(u32.GetForegroundWindow(), ctypes.byref(pid))
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wintypes.DWORD(1024)
        ctypes.windll.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
        return "whatsapp" in buf.value.lower()
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def _ctrl_v():
    import ctypes
    u32 = ctypes.windll.user32
    for vk, naik in ((0x11, 0), (0x56, 0), (0x56, 2), (0x11, 2)):  # Ctrl turun, V turun, V naik, Ctrl naik
        u32.keybd_event(vk, 0, naik, 0)
        time.sleep(0.02)


def buka_wa(nomor, teks, pdfs):
    """PDF ke clipboard -> buka chat WhatsApp Desktop berisi pesan -> Ctrl+V hanya kalau jendela depan benar WhatsApp.
    TIDAK menekan Kirim: Kak Intan yang memeriksa dan mengirim. Semua lewat ctypes (tanpa PowerShell, lebih cepat)."""
    nomor = "".join(ch for ch in str(nomor) if ch.isdigit())
    if not nomor.startswith("62") or len(nomor) < 10:
        raise RuntimeError("nomor WhatsApp tidak sah: " + str(nomor))
    _clipboard_berkas(pdfs)
    os.startfile("whatsapp://send?phone=%s&text=%s" % (nomor, urllib.parse.quote(teks or "")))
    batas = time.time() + 15
    while time.time() < batas and not _depan_whatsapp():
        time.sleep(0.1)
    if not _depan_whatsapp():
        return False
    time.sleep(1.5)  # chat & isi pesan selesai dimuat
    if not _depan_whatsapp():
        return False
    _ctrl_v()
    return True


def bersihkan_sementara(hari=2):
    """salinan foto untuk WA di folder lokal sementara dibuang sesudah 2 hari (arsip tetap di Drive)."""
    if not os.path.isdir(SEMENTARA):
        return
    batas = time.time() - hari * 86400
    for d in os.listdir(SEMENTARA):
        p = os.path.join(SEMENTARA, d)
        if os.path.isdir(p) and os.path.getmtime(p) < batas:
            shutil.rmtree(p, ignore_errors=True)


def kerjakan(halaman, id_, minta):
    catat("permintaan PDF dari %s: %s (%d nota, %d foto)" % (halaman, minta.get("pelanggan"), len(minta.get("nota") or []),
                                                          len(minta.get("foto") or [])))
    tulis(halaman, id_, {"mulai": kini(), "galat": "", "selesai": ""})
    try:
        if not os.path.isdir(KELUAR.rsplit("\\", 1)[0]):
            raise RuntimeError("Google Drive (G:) belum menyala")
        bersihkan_sementara()
        # 21 Nov 2026 (Kak Intan: "dilaptop orang kenapa wa nya masuk ke aku"): bot di laptop kantor TIDAK lagi membuka
        # WhatsApp / menempel lampiran untuk permintaan dari halaman - siapa pun yang mengklik (termasuk halaman lama yang
        # masih bercentang "laptop kantor") dilayani seperti komputer lain: PDF di Shared Drive + tombol unduh.
        # WhatsApp dibuka di komputer yang mengklik oleh Pembantu Gio.
        if minta.get("kirim_wa"):
            # diklik dari komputer lain: WhatsApp/HaloAI sudah dibuka di komputer itu oleh halaman; bot menyiapkan SATU
            # PDF (rincian + foto nota) di Shared Drive kantor, halaman menampilkan tombol unduh
            m2 = dict(minta, kirim_wa=False)
            nm = nama_berkas("Lampiran tagihan %s %s" % (minta.get("pelanggan") or "toko", datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")))
            jalur, nama, _ = susun(m2, folder=os.path.join(BERSAMA, datetime.date.today().strftime("%Y-%m")), nama=nm)
            try:
                fid = unggah_langsung(halaman, jalur, nama)
            except Exception as e:  # noqa: BLE001 - cadangan: tunggu sinkron Drive for Desktop seperti dulu
                catat("  unggah langsung gagal (%s) - menunggu sinkron Drive" % e)
                fid = id_drive(nama, tunggu=300)
            if not fid:
                raise RuntimeError("lampiran sudah dibuat tapi Google Drive belum selesai mengunggah - coba klik lagi sebentar lagi")
            catat("  lampiran untuk komputer lain:", nama, "| id", fid)
            tulis(halaman, id_, {"selesai": kini(), "galat": "", "nama": nama, "url": "https://drive.google.com/file/d/%s/view" % fid,
                                 "unduh": "https://drive.google.com/uc?export=download&id=%s" % fid, "wa_dibuka": kini(), "tempel": False})
            return
        jalur, nama, lain = susun(minta)
        if minta.get("kirim_wa"):
            # 📤 Kirim ke WA: langsung buka WhatsApp, tidak menunggu Drive (PDF tetap tersimpan di Drive sebagai arsip)
            if minta.get("lewat") == "halo":
                # HaloAI sudah dibuka halaman; bot cukup menaruh lampiran di clipboard (Ctrl+V di kotak chat HaloAI)
                _clipboard_berkas([jalur] + lain)
                tempel = False
            else:
                tempel = buka_wa(minta.get("nomor"), minta.get("teks"), [jalur] + lain)
            catat("  %s untuk" % ("HaloAI: lampiran di clipboard" if minta.get("lewat") == "halo" else "WhatsApp dibuka"), minta.get("nomor"),
                  "| %d berkas" % (1 + len(lain)), "ditempel" if tempel else "di clipboard (Ctrl+V)")
            tulis(halaman, id_, {"selesai": kini(), "wa_dibuka": kini(), "tempel": bool(tempel), "galat": "", "nama": nama,
                                 "lokasi": "Drive: Agen Pajak/DASHBOARD PENJUALAN/PENAGIHAN WA/" + os.path.basename(os.path.dirname(jalur))})
            return
        fid = id_drive(nama)
        url = ("https://drive.google.com/file/d/%s/view" % fid) if fid else ""
        catat("  tersimpan", jalur, "| id Drive:", fid or "(belum terunggah)")
        tulis(halaman, id_, {"selesai": kini(), "galat": "", "url": url, "nama": nama,
                             "lokasi": "Drive: Agen Pajak/DASHBOARD PENJUALAN/PENAGIHAN WA/" + os.path.basename(os.path.dirname(jalur))})
    except Exception as e:  # noqa: BLE001
        catat("  GAGAL:", e)
        tulis(halaman, id_, {"selesai": "", "galat": str(e)[:300], "gagal": kini()})


# 21 Nov 2026 (Kak Intan: "kalo kosong nomernya mereka bisa isi terus nanti ke update di pelanggan accuratenya"):
# tab Tagih WA menulis perbarui/telp_<toko> {pelanggan, cabang, nomor}; bot menulis nomor itu ke kolom No. WhatsApp
# (whatsappNo) akun Accurate - HANYA kalau kolom itu kosong / bukan nomor HP. Penulisan lewat fungsi acc() bot
# pengajuan (token tulis yang sama).
_ek = None


def eks():
    global _ek
    if _ek is None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import eksekutor_pengajuan as m  # noqa: E402 - tanpa efek samping saat diimpor
        _ek = m
    return _ek


def nomor_hp(t):
    d = "".join(ch for ch in str(t or "") if ch.isdigit())
    if d.startswith("62"):
        d = "0" + d[2:]
    elif d.startswith("8"):
        d = "0" + d
    return d if d.startswith("08") and 10 <= len(d) <= 14 else ""


def id_pelanggan(nama, cabang):
    nama = (nama or "").strip()
    try:
        for r in json.load(open(os.path.join(GIO, "dashboard", "data", "pelanggan_kredit.json"), encoding="utf-8")):
            if r.get("pelanggan") == nama and r.get("id"):
                return r["id"]
    except (OSError, ValueError):
        pass
    ek = eks()
    ada = [x for x in ek.acc("customer/list.do", {"fields": "id,name,suspended", "filter.keywords.op": "CONTAIN",
                                                 "filter.keywords.val[0]": nama, "sp.pageSize": "50"})["d"]
           if str(x.get("name", "")).strip().upper() == nama.upper() and not x.get("suspended")]
    if len(ada) != 1:
        raise RuntimeError("akun Accurate '%s' tidak ketemu persis satu (%d)" % (nama, len(ada)))
    return ada[0]["id"]


def kerjakan_telp(halaman, id_, minta):
    tulis(halaman, id_, {"mulai": kini(), "galat": "", "selesai": ""})
    try:
        nomor = nomor_hp(minta.get("nomor"))
        if not nomor:
            raise RuntimeError("nomor tidak valid: %s" % minta.get("nomor"))
        ek = eks()
        cid = id_pelanggan(minta.get("pelanggan"), minta.get("cabang"))
        c = ek.acc("customer/detail.do", {"id": cid})["d"]
        lama = (c.get("whatsappNo") or "").strip()
        if nomor_hp(lama) == nomor:
            hasil = "sudah sama"
        elif nomor_hp(lama):
            raise RuntimeError("No. WhatsApp di Accurate sudah terisi %s - tidak ditimpa, ubah langsung di Accurate kalau salah" % lama)
        else:
            ek.acc("customer/save.do", {"id": cid, "whatsappNo": nomor}, tulis=True)
            hasil = "ditulis"
        catat("nomor WA %s (%s): %s -> %s [%s] diisi %s" % (minta.get("pelanggan"), cid, lama or "kosong", nomor, hasil,
                                                          minta.get("oleh_nama") or minta.get("oleh") or "?"))
        tulis(halaman, id_, {"selesai": kini(), "galat": "", "hasil": hasil})
    except Exception as e:  # noqa: BLE001
        catat("nomor WA %s GAGAL: %s" % (minta.get("pelanggan"), e))
        tulis(halaman, id_, {"selesai": "", "galat": str(e)[:300], "gagal": kini()})


def main():
    catat("bot PDF tagih mulai")
    try:
        st = json.load(open(STATUS, encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    sejak, beres = st.get("sejak", 0), st.get("beres", {})
    dok = {}
    while True:
        try:
            for d in apps({"aksi": "daftar", "sejak": sejak})["docs"]:
                sejak = max(sejak, d["diubah"])
                if d["koleksi"] == "perbarui" and str(d["id"]).startswith(("pdf_", "telp_")):
                    dok[(d["halaman"], d["id"])] = None if d["dihapus"] else d["data"]
            for (hal, id_), data in list(dok.items()):
                if not data or not data.get("diminta"):
                    continue
                k = hal + "|" + id_
                if data["diminta"] <= max(beres.get(k, ""), data.get("mulai") or ""):
                    continue
                (kerjakan_telp if id_.startswith("telp_") else kerjakan)(hal, id_, data)
                beres[k] = data["diminta"]
            json.dump({"sejak": sejak, "beres": beres}, open(STATUS, "w", encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            catat("GALAT:", e)
        if "--sekali" in sys.argv:
            break
        jam = datetime.datetime.now().hour
        time.sleep(JEDA if 7 <= jam < 21 else 30)


if __name__ == "__main__":
    main()
