"""Tombol "Update data" di web Pengajuan-Sales (Kak Intan 17 Nov 2026).

Halaman web menulis dokumen perbarui/status {diminta, oleh} ke penyimpan Apps Script. Skrip ini (jalan terus di PC)
memeriksa tiap 60 detik; kalau ada permintaan baru:
  1. tulis {mulai} ke halaman yang meminta (tombol berubah "sedang diperbarui"),
  2. jalankan tugas Task Scheduler "Gio - Dashboard Penjualan Harian" (tarik Accurate + semua data turunan),
  3. tunggu sampai jadwal selesai, lalu bangun ulang & terbitkan web (bangun.py --kirim),
  4. tulis {selesai} (atau {galat}) ke halaman yang meminta.
Permintaan yang masuk selama proses berjalan digabung ke putaran berikutnya.

    python -I bot\\tombol_update.py            jalan terus
    python -I bot\\tombol_update.py --sekali   periksa sekali lalu keluar
Log: skrip\\log\\tombol-update.log
"""
import datetime, hashlib, hmac, json, os, subprocess, sys, time, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIO = os.path.dirname(REPO)
ENV = os.path.join(GIO, ".env")
LOG = os.path.join(GIO, "skrip", "log", "tombol-update.log")
LOG_JADWAL = os.path.join(GIO, "skrip", "log", "dashboard-penjualan-jadwal.log")
TUGAS = "Gio - Dashboard Penjualan Harian"   # dimatikan 24 Nov 2026 - diganti BOT_MALAM
# 24 Nov 2026 (Kak Intan: "dikasih bot nya 1 - 1 deh dipisah"): jadwal malam = 6 bot skrip\bot_harian.ps1.
# Tombol Update menyalakan keenamnya sekaligus; mereka sendiri yang bergiliran (Accurate satu jalur) dan menunggu.
BOT_MALAM = ["Gio - Malam %d %s" % x for x in [(1, "Tarik Accurate"), (2, "Pajak"), (3, "Rute kirim"), (4, "Penagihan"),
                                                (5, "Hitungan"), (6, "Terbit")]]


def status_bot(n):
    try:
        st = json.load(open(os.path.join(GIO, "skrip", "log", "bot-malam-%d.json" % n), encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return st
JEDA = 60
BATAS_JAM = 4  # tarikan + bangun lebih dari ini dianggap macet


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
    print(t, flush=True)
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


def tulis_status(halaman, data):
    apps({"aksi": "tulis", "tulis": [{"halaman": h, "koleksi": "perbarui", "id": "status", "mode": "update", "data": data} for h in halaman]})


def kini():
    # UTC "Z" seperti new Date().toISOString() di halaman, supaya bisa dibandingkan sebagai teks
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ps(perintah):
    return subprocess.run(["powershell", "-NoProfile", "-Command", perintah], capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.strip()


def tarik_lain_jalan():
    return ps("@(Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | ? { $_.CommandLine -like '*dashboard_penjualan.py*' }).Count") not in ("", "0")


def bangun_web():
    r = subprocess.run([sys.executable.replace("pythonw.exe", "python.exe"), "-I", os.path.join(REPO, "skrip", "bangun.py"), "--kirim"],
                       capture_output=True, text=True, timeout=1800, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode:
        catat("bangun gagal:", (r.stderr or r.stdout)[-400:])
        return False, "web gagal dibangun"
    catat("web diterbitkan")
    return True, ""


def jalankan_pembaruan():
    """True kalau jadwal selesai & web terbit."""
    awal = time.time()
    # 17 Nov: kalau tarikan lain (bot per jam / jadwal malam) sedang jalan, tunggu selesai lalu terbitkan saja -
    # jangan menyalakan jadwal penuh (akan dibatalkan jadwal dan tombol jadi merah "gagal")
    if tarik_lain_jalan():
        catat("tarikan lain sedang jalan - ditunggu, lalu web diterbitkan")
        while tarik_lain_jalan() and time.time() - awal < BATAS_JAM * 3600:
            time.sleep(60)
        return bangun_web()
    # tombol Update = pembaruan manual: bot pajak ikut jalan walau hari ini sudah (Kak Intan 20 Nov 2026)
    open(os.path.join(GIO, "skrip", "log", "pajak-paksa.txt"), "w").close()
    mulai = datetime.datetime.now().isoformat(timespec="seconds")
    # 27 Nov 2026: dulu keenam bot dinyalakan sekaligus - enam tarikan berat berebut RAM dan sebagian
    # dimatikan Windows di tengah jalan (kode 0xC000013A). Sekarang satu-satu: tunggu yang depan selesai.
    for t in BOT_MALAM:
        if ps("(Get-ScheduledTask -TaskName '%s').State" % t) == "Running":
            catat("tugas", t, "sudah berjalan - ditunggu")
        else:
            ps("Start-ScheduledTask -TaskName '%s'" % t)
            catat("tugas", t, "dijalankan")
        time.sleep(20)
        while ps("(Get-ScheduledTask -TaskName '%s').State" % t) == "Running":
            if time.time() - awal >= BATAS_JAM * 3600:
                catat("GAGAL: bot malam belum selesai sesudah", BATAS_JAM, "jam")
                return False, "bot malam belum selesai sesudah %d jam" % BATAS_JAM
            time.sleep(60)
    time.sleep(5)
    while time.time() - awal < BATAS_JAM * 3600:
        if not any(ps("(Get-ScheduledTask -TaskName '%s').State" % t) == "Running" for t in BOT_MALAM):
            break
        time.sleep(60)
    else:
        catat("GAGAL: bot malam belum selesai sesudah", BATAS_JAM, "jam")
        return False, "bot malam belum selesai sesudah %d jam" % BATAS_JAM
    b1, b6 = status_bot(1), status_bot(6)
    if not (b1.get("ok") and str(b1.get("mulai", "")) >= mulai[:16]):
        catat("tarikan Accurate tidak selesai baik:", "; ".join(b1.get("gagal") or ["status bot 1 tidak ada"]))
        return False, "tarikan Accurate gagal (lihat skrip\\log\\bot-malam.log)"
    if b6.get("ok") and str(b6.get("mulai", "")) >= mulai[:16]:
        catat("bot 6 sudah menerbitkan web")
        return True, ""
    return bangun_web()


def main():
    catat("tombol update mulai")
    selesai_terakhir, status, sejak = {}, {}, 0
    while True:
        try:
            # 27 Nov 2026: kalau penyimpan menjawab tanpa "docs" (galat/jawaban sepotong), jangan sampai
            # putarannya mati dengan "GALAT putaran: 'docs'" - lewati saja putaran itu.
            for d in apps({"aksi": "daftar", "sejak": sejak}).get("docs") or []:
                sejak = max(sejak, d["diubah"])
                if d["koleksi"] == "perbarui" and d["id"] == "status":
                    status[d["halaman"]] = None if d["dihapus"] else d["data"]
            minta = {h: st for h, st in status.items() if st and st.get("diminta")
                     and st["diminta"] > max(st.get("mulai") or "", selesai_terakhir.get(h, ""))}
            if minta:
                hal = sorted(minta)
                catat("permintaan update dari", ", ".join("%s (%s)" % (h, minta[h].get("oleh") or "-") for h in hal))
                mulai = kini()
                tulis_status(hal, {"mulai": mulai, "galat": ""})
                ok, galat = jalankan_pembaruan()
                akhir = kini()
                tulis_status(hal, {"selesai": akhir, "galat": galat} if ok else {"selesai": "", "galat": galat, "gagal": akhir})
                for h in hal:
                    selesai_terakhir[h] = akhir
        except Exception as e:  # noqa: BLE001
            catat("GALAT:", e)
        if "--sekali" in sys.argv:
            break
        time.sleep(JEDA)


if __name__ == "__main__":
    main()
