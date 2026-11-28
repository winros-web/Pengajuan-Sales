"""Atur sandi (kunci) tiap halaman Pengajuan-Sales - diketik Kak Intan sendiri (Kak Intan 24 Nov 2026:
"semuanya di kasih kunci yaa aku mau masukin kuncinya").

Jalankan di jendela PowerShell biasa (bukan lewat Claude):
    python -I "D:\\AGEN AI\\AGEN IT (GIO)\\pengajuan_sales_web\\skrip\\atur_sandi.py"

Tiap halaman ditanya satu per satu; ketikan tidak tampil di layar. Tekan Enter tanpa mengetik = sandi lama
dipakai terus. Sandi disimpan terenkripsi DPAPI di %LOCALAPPDATA%\\Gio\\sandi_web_penjualan_<halaman>.dpapi
(hanya bisa dibuka akun Windows ini), tidak pernah ditulis polos. Sandi pusat = juga sandi tab Gaji & laporan
keuangan pajak. Sesudah selesai, beri tahu Gio supaya halaman diterbitkan ulang dengan kunci.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "skrip"))
import bangun_web_penjualan as W  # noqa: E402

HALAMAN = [("pusat", "PUSAT")] + [(w, n) for w, (n, _) in W.CABANG.items()] + \
          [("admin-" + w, "ADMIN " + n) for w, (n, _) in W.CABANG.items()] +           [("pasif", "TIM FOLLOW UP - PELANGGAN PASIF SEMUA CABANG")] +           [("pengajuan-admin", "ADMIN PENGAJUAN SALES (wewenang seperti Ibu)")]   # 24 & 27 Nov 2026


def lihat():
    """--lihat: tampilkan sandi yang sekarang dipakai, hanya di jendela Kak Intan sendiri (tidak lewat Claude)."""
    print("Sandi halaman Pengajuan-Sales yang dipakai sekarang (jangan difoto / dibagikan sembarangan):\n")
    for web, nama in HALAMAN:
        f = W.berkas_sandi(web)
        s = W._dpapi(open(f, "rb").read(), False).decode("utf-8") if os.path.exists(f) else "(belum ada)"
        print("  %-22s %s" % (nama, s))
    input("\nTekan Enter untuk menutup (layar dibersihkan).")
    os.system("cls")


def main():
    if "--lihat" in sys.argv:
        return lihat()
    print("Atur kunci halaman Pengajuan-Sales. Enter kosong = sandi lama tetap dipakai.\n")
    diganti = 0
    pilih = [a for a in sys.argv[1:] if not a.startswith("--")]   # mis. atur_sandi.py pasif = halaman itu saja
    for web, nama in [h for h in HALAMAN if not pilih or h[0] in pilih]:
        f = W.berkas_sandi(web)
        ada = os.path.exists(f)
        while True:
            s = getpass.getpass("%-22s%s: " % (nama, " (sudah ada)" if ada else " (BELUM ADA)"))
            if not s:
                if ada:
                    break
                print("   halaman ini belum punya sandi - wajib diisi")
                continue
            if len(s) < 6:
                print("   minimal 6 huruf/angka")
                continue
            if s != getpass.getpass("   ketik sekali lagi    : "):
                print("   tidak sama, ulangi")
                continue
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, "wb").write(W._dpapi(s.encode("utf-8"), True))
            diganti += 1
            break
    print("\nSelesai: %d sandi baru disimpan. Kabari Gio: \"sandi sudah\"." % diganti)
    input("Tekan Enter untuk menutup.")


if __name__ == "__main__":
    main()
