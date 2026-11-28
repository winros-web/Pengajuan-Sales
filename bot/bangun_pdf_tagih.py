"""Penyusun PDF tagihan + foto nota (dipanggil bot\\pdf_tagih.py lewat `uv run --with pymupdf`).

    uv run --with pymupdf python -I bot\\bangun_pdf_tagih.py <kerja.json>

kerja.json = {"minta": {pelanggan, cabang, sales, tgl_data, nota: [{nomor, tgl, jatuh_tempo, hari_lewat, total, sisa}]},
              "foto": [{"do", "jalur"}], "keluar": "<jalur pdf>"}
Halaman 1..n: rincian tagihan (tabel semua nota terceklis + total). Sesudahnya: satu halaman per foto nota bercap
(jpg/jpeg dipasang pas halaman; scan PDF disisipkan apa adanya), dengan keterangan nomor DO di atasnya.
"""
import builtins
import datetime
import html
import json
import os
import sys

import pymupdf as fitz

A4 = fitz.paper_rect("a4")
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def tgl(s):
    try:
        d = datetime.date.fromisoformat(str(s)[:10])
        return "%d %s %d" % (d.day, BULAN[d.month - 1], d.year)
    except ValueError:
        return "-"


def rp(v):
    return "Rp " + format(round(v or 0), ",").replace(",", ".")


CSS = """
body { font-family: sans-serif; font-size: 9.5pt; }
h1 { font-size: 15pt; margin: 0 0 8pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; }
th { background-color: #282828; color: #ffffff; text-align: left; padding: 3pt; font-size: 8.5pt; }
td { border: 0.5pt solid #bbbbbb; padding: 3pt; font-size: 8.5pt; }
td.k { text-align: right; } tr.tot td { background-color: #ebebeb; font-weight: bold; }
"""
KEPALA = "<tr><th>No</th><th>No faktur</th><th>Tgl faktur</th><th>Jatuh tempo</th><th>Lewat</th><th>Nilai faktur</th><th>Sisa tagihan</th></tr>"


def rincian(doc, m):
    nota = m.get("nota") or []
    total = sum(n.get("sisa") or 0 for n in nota)
    baris = [
        "<tr><td class=k>%d</td><td>%s</td><td>%s</td><td>%s</td><td class=k>%s</td><td class=k>%s</td><td class=k>%s</td></tr>" % (
            i + 1, html.escape(str(n.get("nomor", ""))), tgl(n.get("tgl")), tgl(n.get("jatuh_tempo")),
            ("%s hari" % format(n["hari_lewat"], ",").replace(",", ".")) if (n.get("hari_lewat") or 0) > 0 else "belum",
            rp(n.get("total") or n.get("sisa")), rp(n.get("sisa")))
        for i, n in enumerate(nota)]
    sales = (" &nbsp;|&nbsp; Sales: " + html.escape(m["sales"])) if m.get("sales") else ""
    kop = ("<h1>PT SVARNA DIPA &nbsp;-&nbsp; RINCIAN TAGIHAN</h1><p>Kepada: <b>%s</b><br>Cabang: %s%s<br>Posisi piutang per %s</p>"
           % (html.escape(str(m.get("pelanggan", ""))), html.escape(str(m.get("cabang") or "-")), sales, tgl(m.get("tgl_data"))))
    tot = "<tr class=tot><td></td><td></td><td></td><td></td><td class=k>%d faktur</td><td class=k>Total</td><td class=k>%s</td></tr>" % (len(nota), rp(total))
    tutup = ("<p>Mohon konfirmasi rencana pembayarannya. Bila sudah dibayar, mohon kirimkan bukti transfernya supaya dapat kami "
             "cocokkan.%s Terima kasih atas kerja samanya.</p>" % ((" Foto nota asli bercap toko kami lampirkan terpisah." if m.get("_wa") else " Foto nota bercap toko terlampir di halaman berikutnya.") if m.get("_ada_foto") else ""))
    kotak = A4 + (40, 40, -40, -45)
    # tabel dipecah per halaman: 30 baris di halaman pertama (ada kop), 42 di halaman berikutnya
    potong, i = [], 0
    while i < len(baris) or not potong:
        n = 30 if not potong else 42
        potong.append(baris[i:i + n])
        i += n
    for k, bag in enumerate(potong):
        akhir = k == len(potong) - 1
        isi = (kop if k == 0 else "<p><b>%s</b> - lanjutan</p>" % html.escape(str(m.get("pelanggan", "")))) \
            + "<table>" + KEPALA + "".join(bag) + (tot if akhir else "") + "</table>" + (tutup if akhir else "")
        hal = doc.new_page(width=A4.width, height=A4.height)
        sisa, _ = hal.insert_htmlbox(kotak, isi, css=CSS)
        if sisa < 0:  # tidak muat (baris panjang) - perkecil
            hal.clean_contents()
            doc.delete_page(hal.number)
            hal = doc.new_page(width=A4.width, height=A4.height)
            hal.insert_htmlbox(kotak, isi, css=CSS, scale_low=0)


def foto(doc, fotos):
    n = 0
    for f in fotos:
        p = f.get("jalur")
        if not p:
            continue
        judul = "Foto nota bercap toko - %s" % (f.get("do") or os.path.basename(p))
        if p.lower().endswith(".pdf"):
            try:
                with fitz.open(p) as src:
                    awal = doc.page_count
                    doc.insert_pdf(src)
                    for i in range(awal, doc.page_count):
                        doc[i].insert_text((40, 28), judul, fontsize=9, color=(0.3, 0.3, 0.3))
                n += 1
            except Exception as e:  # noqa: BLE001
                print("lewati", p, e, file=sys.stderr)
            continue
        try:
            hal = doc.new_page(width=A4.width, height=A4.height)
            hal.insert_text((40, 32), judul, fontsize=10)
            # foto HP 3-5 MB -> diperkecil (lebar maks ~1600 px, JPEG 70) supaya PDF muat dikirim lewat WA
            pix = fitz.Pixmap(p)
            while max(pix.width, pix.height) > 2400:
                pix.shrink(1)  # tiap kali jadi setengah
            if pix.alpha or pix.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            hal.insert_image(A4 + (30, 45, -30, -30), stream=pix.tobytes("jpeg", jpg_quality=70), keep_proportion=True)
            n += 1
        except Exception as e:  # noqa: BLE001
            print("lewati", p, e, file=sys.stderr)
    return n


def halaman_nota(doc, d, sisa):
    """Satu halaman salinan faktur dari Accurate (bukan faktur asli - ditandai jelas)."""
    baris = "".join(
        "<tr><td>%s</td><td>%s</td><td class=k>%s %s</td><td class=k>%s</td><td class=k>%s</td><td class=k>%s</td></tr>" % (
            html.escape(str(b.get("kode") or "")), html.escape(str(b.get("nama") or "")),
            format(b.get("qty") or 0, "g"), html.escape(str(b.get("satuan") or "")), rp(b.get("harga")),
            html.escape(str(b.get("disk") or "")) + ("%" if b.get("disk") else ""), rp(b.get("jumlah")))
        for b in d.get("baris") or [])
    ringkas = "".join("<tr><td class=k colspan=5>%s</td><td class=k>%s</td></tr>" % kv for kv in [
        ("Subtotal", rp(d.get("sub"))), ("Diskon", rp(d.get("diskon"))) if d.get("diskon") else None,
        ("PPN" + (" (sudah termasuk)" if abs((d.get("sub") or 0) - (d.get("total") or 0)) < 1 else ""), rp(d.get("pajak"))) if d.get("pajak") else None, ("<b>Total faktur</b>", "<b>%s</b>" % rp(d.get("total"))),
        ("<b>Sisa tagihan</b>", "<b>%s</b>" % rp(sisa)) if sisa is not None else None] if kv)
    isi = ("<h1>PT SVARNA DIPA &nbsp;-&nbsp; NOTA %s</h1>"
           "<p>Tanggal: %s &nbsp;|&nbsp; Jatuh tempo: %s%s<br>Kepada: <b>%s</b><br>%s</p>"
           "<table><tr><th>Kode</th><th>Nama barang</th><th>Qty</th><th>Harga</th><th>Disk</th><th>Jumlah</th></tr>%s%s</table>"
           "<p style='color:#666;font-size:8pt'>Salinan data faktur dari sistem Accurate PT Svarna Dipa, sebagai lampiran tagihan.%s</p>") % (
        html.escape(str(d.get("nomor") or "")), html.escape(str(d.get("tgl") or "-")), html.escape(str(d.get("jt") or "-")),
        (" &nbsp;|&nbsp; Termin: " + html.escape(d["termin"])) if d.get("termin") else "",
        html.escape(str(d.get("pelanggan") or "")), html.escape(str(d.get("alamat") or "")).replace("\n", "<br>"),
        baris, ringkas, (" Keterangan: " + html.escape(d["ket"])) if d.get("ket") else "")
    hal = doc.new_page(width=A4.width, height=A4.height)
    sisa_h, _ = hal.insert_htmlbox(A4 + (40, 40, -40, -45), isi, css=CSS)
    if sisa_h < 0:
        doc.delete_page(hal.number)
        hal = doc.new_page(width=A4.width, height=A4.height)
        hal.insert_htmlbox(A4 + (40, 40, -40, -45), isi, css=CSS, scale_low=0)


def berkas_nota(kerja):
    """Berkas Nota: per nota terceklis -> salinan faktur Accurate + foto nota bercap toko (kalau ada)."""
    m, det = kerja["minta"], kerja.get("nota_detail") or {}
    foto_do = {}
    for f in kerja.get("foto") or []:
        if f.get("jalur"):
            foto_do.setdefault(f.get("do"), []).append(f)
    doc = fitz.open()
    n_faktur = n_foto = 0
    for n in m.get("nota") or []:
        d = det.get(n.get("nomor"))
        if d:
            halaman_nota(doc, d, n.get("sisa"))
            n_faktur += 1
        n_foto += foto(doc, foto_do.get(n.get("nomor"), []))
    if not doc.page_count:
        return None
    nomori(doc)
    simpan(doc, kerja["keluar_nota"])
    return "Nota: %d salinan faktur + %d foto bercap (%d KB)" % (n_faktur, n_foto, os.path.getsize(kerja["keluar_nota"]) // 1024)


def nomori(doc):
    for i, hal in enumerate(doc):
        r = hal.rect  # scan PDF bisa berukuran lain dari A4
        hal.insert_text((r.width - 110, r.height - 14), "Halaman %d dari %d" % (i + 1, doc.page_count), fontsize=7.5, color=(0.45, 0.45, 0.45))


def simpan(doc, jalur):
    sementara = jalur + ".tmp"
    doc.save(sementara, garbage=3, deflate=True)
    doc.close()
    os.replace(sementara, jalur)


def bangun(kerja):
    """Susun PDF dari dict kerja; kembalikan baris laporan. Dipanggil langsung oleh bot\\pdf_tagih.py (20 Nov 2026:
    "botnya secepat kilat") - tanpa menyalakan Python baru."""
    laporan = []
    print = laporan.append  # noqa: A001 - laporan dikembalikan, bukan dicetak
    m = kerja["minta"]
    wa = bool(kerja.get("keluar_nota") or kerja.get("tanpa_foto"))
    m["_wa"] = wa
    m["_ada_foto"] = any(f.get("jalur") for f in kerja.get("foto") or [])
    doc = fitz.open()
    rincian(doc, m)
    n_rinci = doc.page_count
    # mode Kirim ke WA: foto pindah ke berkas Nota, rincian cukup tabelnya
    n_foto = 0 if wa else foto(doc, kerja.get("foto") or [])
    for i, hal in enumerate(doc):
        r = hal.rect  # scan PDF bisa berukuran lain dari A4
        hal.insert_text((r.width - 110, r.height - 14), "Halaman %d dari %d" % (i + 1, doc.page_count), fontsize=7.5, color=(0.45, 0.45, 0.45))
    sementara = kerja["keluar"] + ".tmp"
    doc.save(sementara, garbage=3, deflate=True)
    doc.close()
    os.replace(sementara, kerja["keluar"])
    print("PDF %s: %d halaman rincian + %d foto nota (%d KB)" % (os.path.basename(kerja["keluar"]), n_rinci, n_foto,
                                                                 os.path.getsize(kerja["keluar"]) // 1024))
    if kerja.get("keluar_nota"):
        print(berkas_nota(kerja) or "Nota: tidak ada salinan faktur maupun foto")
    return laporan


def main():
    for b in bangun(json.load(open(sys.argv[1], encoding="utf-8"))):
        builtins.print(b)


if __name__ == "__main__":
    main()
