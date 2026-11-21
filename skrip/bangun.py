"""Bangun halaman GitHub Pages PENGAJUAN SALES (uji coba Kak Intan, 13 Nov 2026) - repo winros-web/Pengajuan-Sales.

Halaman = kerangka sandi dashboard penjualan web + index.html dashboard (sama persis, hanya tab Pengajuan sales
yang tampil) + shim.js (window.claude -> penyimpan Apps Script). Data tiap halaman (berkas data/*.json dashboard,
tanpa gaji & stok) + alamat penyimpan + kunci halaman dikunci AES-GCM dengan sandi halaman itu - sandi yang SAMA
dengan Dashboard-Svarna (berkas DPAPI %LOCALAPPDATA%\\Gio\\sandi_web_penjualan*.dpapi), tidak pernah polos.

    python -I "D:\\AGEN AI\\AGEN IT (GIO)\\pengajuan_sales_web\\skrip\\bangun.py"           (bangun)
    python -I "D:\\AGEN AI\\AGEN IT (GIO)\\pengajuan_sales_web\\skrip\\bangun.py" --kirim   (bangun + commit + push)

Rahasia di D:\\AGEN AI\\AGEN IT (GIO)\\.env (tidak masuk repo):
    PENGAJUAN_MASTER=   kunci induk (dibuat otomatis kalau belum ada; Kak Intan menyalinnya ke Script Properties MASTER)
    PENGAJUAN_APPS_URL= URL /exec Apps Script penyimpan (diisi Kak Intan sesudah deploy)
"""
import base64, datetime, glob, gzip, hashlib, hmac, html, json, os, re, secrets, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIO = os.path.dirname(REPO)
DASH = os.path.join(GIO, "dashboard")
ENV = os.path.join(GIO, ".env")
sys.path.insert(0, os.path.join(GIO, "skrip"))
import bangun_web_penjualan as W  # noqa: E402  (sandi DPAPI + kunci PBKDF2, satu sumber dengan Dashboard-Svarna)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402

BUANG = {"gaji.json", "stok.json"}
# Kak Intan 16 Nov 2026: tab Gaji/Pelunasan/BPJS ikut di halaman PUSAT. Halaman cabang/admin tidak pernah mendapat gaji.json.
# Kak Intan 18 Nov 2026: "dashboard yg gaji di kasih password ya ... lainnya gak usah" -> gaji.json dikunci AES-GCM
# tersendiri (paket["gaji"]) dengan sandi halaman pusat (DPAPI sandi_web_penjualan_pusat), dibuka saat tab gaji dibuka.
GAJI_DI_PUSAT = True
# Kak Intan 16 Nov 2026: "semuanya jangan di passwordin dulu, aku masih testing" - sudah diberi tahu bahwa data
# (laba, HPP, piutang, toko) dan tombol ACC -> bot Accurate jadi terbuka untuk siapa pun yang tahu alamatnya, dan
# memilih tetap tanpa sandi. data.json = gzip polos (base64). Kembalikan ke False begitu uji coba selesai.
TANPA_SANDI = True
HALAMAN = {"pusat": (None, "PENGAJUAN", "Pengajuan Sales Pusat")}
for web, (nama, merek) in W.CABANG.items():
    HALAMAN[web] = (nama, merek, "Pengajuan Sales " + nama.title())
# halaman admin cabang (Kak Intan 14 Nov 2026): revisi harga pemindahan, sandi SENDIRI (bukan sandi sales)
for web, (nama, merek) in W.CABANG.items():
    HALAMAN["admin-" + web] = (nama, "ADMIN " + merek, "Admin " + nama.title() + " - Revisi Harga Pemindahan")


def env():
    isi = {}
    if os.path.exists(ENV):
        for b in open(ENV, encoding="utf-8"):
            if "=" in b and not b.lstrip().startswith("#"):
                k, v = b.split("=", 1)
                isi[k.strip()] = v.strip().strip('"')
    if not isi.get("PENGAJUAN_MASTER"):
        isi["PENGAJUAN_MASTER"] = secrets.token_hex(32)
        with open(ENV, "a", encoding="utf-8") as f:
            f.write("\n# Pengajuan Sales web: kunci induk - salin ke Apps Script > Script Properties > MASTER\n"
                    "PENGAJUAN_MASTER=" + isi["PENGAJUAN_MASTER"] + "\n"
                    "# URL /exec Apps Script penyimpan pengajuan (isi sesudah deploy)\nPENGAJUAN_APPS_URL=\n")
        print("PENGAJUAN_MASTER baru dibuat di .env")
    return isi


def kunci_hal(master, halaman):
    return hmac.new(master.encode(), halaman.encode(), hashlib.sha256).hexdigest()


def kerangka():
    k = open(os.path.join(DASH, "web_kerangka.html"), encoding="utf-8").read()
    shim = open(os.path.join(REPO, "web", "shim.js"), encoding="utf-8").read()
    shim += "\n" + open(os.path.join(REPO, "web", "autolengkap.js"), encoding="utf-8").read()
    ganti = [
        ('<input id="sandi"', '<input id="nama" type="text" autocomplete="name" placeholder="Nama Anda" required '
                              'style="width:100%;height:56px;border-radius:999px;border:1px solid rgba(255,255,255,.14);background:transparent;color:#fff;'
                              'font:600 20px \'Aptos Narrow\',sans-serif;text-align:center">\n    <input id="sandi"'),
        ('Versi web hanya untuk melihat (data <span id="webDibuat"></span>). Isian alasan overdue, target, program, dan ACC pengajuan tetap lewat dashboard Claude.',
         'Pengajuan sales (uji coba) &middot; data Accurate per <span id="webDibuat"></span> &middot; <span id="webSambung">menyambung…</span>'),
        # nama dibaca SEBELUM formulir #masuk dihapus kerangka (bug 13 Nov: halaman kosong)
        ("      const paket = await buka(", "      const nm = document.getElementById('nama').value.trim();\n      const paket = await buka("),
        ('      pasangHalaman(paket);',
         '      try { localStorage.setItem("pengajuan_nama", nm); } catch (e) {}\n'
         '      if (paket.isian && paket.isian.url) pasangClaude(paket.isian, nm);\n'
         '      else document.getElementById("webSambung").textContent = "penyimpan belum dipasang - isian belum bisa disimpan";\n'
         '      if (!location.hash) history.replaceState(null, "", "#pengajuan");\n'
         '      pasangHalaman(paket);'),
        # Kak Intan 16 Nov: pusat = SEMUA tab dashboard pusat (dulu hanya pengajuan/pindah/penagihan);
        # halaman cabang tetap dibatasi kunci.json
        ('<script>', '<script>\n' + shim +
         '\ntry { const n = localStorage.getItem("pengajuan_nama"); if (n) document.getElementById("nama").value = n; } catch (e) {}\n'),
    ]
    # Kak Intan 18 Nov 2026: gaji bersandi walau halaman lain terbuka
    ganti += [
        ("  // halaman dashboard membaca data/<nama>.json lewat fetch: dilayani dari paket yang sudah dibuka\n", '  // Kak Intan 18 Nov 2026: tab Gaji / Pelunasan gaji / BPJS bersandi, tab lain tetap terbuka.\n  // data/gaji.json hanya ada terkunci AES-GCM di paket.gaji; dibuka di browser sesudah sandi benar.\n  const TAB_GAJI = [\'gaji\', \'lunas\', \'bpjs\'];\n  let janjiGaji = null, kotakGaji = null;\n  async function bukaGaji(g, sandi) {\n    const bahan = await crypto.subtle.importKey(\'raw\', new TextEncoder().encode(sandi), \'PBKDF2\', false, [\'deriveKey\']);\n    const kunci = await crypto.subtle.deriveKey({ name: \'PBKDF2\', salt: b64(g.garam), iterations: g.iter, hash: \'SHA-256\' },\n      bahan, { name: \'AES-GCM\', length: 256 }, false, [\'decrypt\']);\n    const polos = await crypto.subtle.decrypt({ name: \'AES-GCM\', iv: b64(g.iv) }, kunci, b64(g.isi));\n    return new Response(new Blob([polos]).stream().pipeThrough(new DecompressionStream(\'gzip\'))).text();\n  }\n  function aturKotakGaji() {\n    if (!kotakGaji) return;\n    const t = document.querySelector(\'.tab[aria-selected="true"]\');\n    kotakGaji.hidden = !TAB_GAJI.includes(t ? t.dataset.p : location.hash.slice(1));\n    if (!kotakGaji.hidden) setTimeout(() => kotakGaji.querySelector(\'input\').focus(), 0);\n  }\n  function mintaGaji(g) {\n    if (!janjiGaji) janjiGaji = new Promise((ok) => {\n      const k = document.createElement(\'div\');\n      k.id = \'kunciGaji\';\n      k.setAttribute(\'style\', \'position:fixed;inset:0;z-index:9999;display:grid;place-items:center;background:rgba(10,14,18,.72);padding:16px\');\n      k.innerHTML = \'<form style="width:min(420px,100%);background:#11171d;color:#e6ecf1;border:1px solid rgba(255,255,255,.14);border-radius:24px;padding:28px;display:grid;gap:14px;font:18px/1.4 \\\'Aptos Narrow\\\',\\\'Arial Narrow\\\',system-ui,sans-serif;text-align:center">\'\n        + \'<b style="font-size:22px;letter-spacing:.12em;text-transform:uppercase">Data gaji</b>\'\n        + \'<span style="color:#9aa8b5;font-size:16px">Tab Gaji, Pelunasan gaji, dan BPJS dikunci. Masukkan sandi untuk membuka.</span>\'\n        + \'<input type="password" autocomplete="current-password" placeholder="Sandi" required style="height:56px;border-radius:999px;border:1px solid rgba(255,255,255,.14);background:#2b6382;color:#fff;font:600 20px \\\'Aptos Narrow\\\',sans-serif;text-align:center">\'\n        + \'<span class="galatGaji" style="color:#ffb4a8;min-height:1.4em;font-size:16px"></span>\'\n        + \'<span style="display:flex;gap:10px;justify-content:center"><button type="submit" style="flex:1;height:48px;border-radius:999px;border:0;background:#e6ecf1;color:#11171d;font:700 17px \\\'Aptos Narrow\\\',sans-serif;cursor:pointer">Buka</button>\'\n        + \'<button type="button" class="batalGaji" style="flex:1;height:48px;border-radius:999px;border:1px solid rgba(255,255,255,.3);background:transparent;color:#e6ecf1;font:700 17px \\\'Aptos Narrow\\\',sans-serif;cursor:pointer">Tab lain</button></span></form>\';\n      document.body.appendChild(k);\n      kotakGaji = k;\n      const f = k.querySelector(\'form\'), inp = k.querySelector(\'input\'), gl = k.querySelector(\'.galatGaji\');\n      k.querySelector(\'.batalGaji\').addEventListener(\'click\', () => {\n        const b = document.querySelector(\'.tab[data-p="pengajuan"]\') || [...document.querySelectorAll(\'.tab\')].find((x) => !TAB_GAJI.includes(x.dataset.p));\n        if (b) b.click(); else kotakGaji.hidden = true;\n      });\n      f.addEventListener(\'submit\', async (ev) => {\n        ev.preventDefault();\n        gl.textContent = \'Sedang membuka...\';\n        try { const t = await bukaGaji(g, inp.value); k.remove(); kotakGaji = null; ok(t); }\n        catch (e) { gl.textContent = \'Sandi salah. Coba lagi.\'; inp.value = \'\'; inp.focus(); }\n      });\n      window.addEventListener(\'hashchange\', aturKotakGaji);\n      // tab dashboard berganti lewat klik (history.replaceState, tanpa hashchange)\n      document.addEventListener(\'click\', () => setTimeout(aturKotakGaji, 0), true);\n      aturKotakGaji();\n    });\n    else aturKotakGaji();\n    return janjiGaji.then((t) => new Response(t, { headers: { \'content-type\': \'application/json\' } }));\n  }\n  // halaman dashboard membaca data/<nama>.json lewat fetch: dilayani dari paket yang sudah dibuka\n'),
        ("      if (p in BERKAS) return Promise.resolve(",
         "      if (p === 'data/gaji.json' && paket.gaji) return mintaGaji(paket.gaji);\n      if (p in BERKAS) return Promise.resolve("),
    ]
    if TANPA_SANDI:
        ganti += [
            ("    const p = await r.json();\n",
             "    const p = await r.json();\n"
             "    if (p.polos) return JSON.parse(await new Response(new Blob([b64(p.polos)]).stream().pipeThrough(new DecompressionStream('gzip'))).text());\n"),
            ('placeholder="Sandi" required>', 'placeholder="Sandi" hidden>'),
            ('<p class="catatan">Isi halaman ini rahasia perusahaan. Jangan bagikan sandi, tangkapan layar, atau isinya kepada pihak lain.</p>', ''),
            ("document.getElementById('webKeluar').addEventListener('click', (e) => { e.preventDefault(); location.reload(); });",
             "document.getElementById('webKeluar').addEventListener('click', (e) => { e.preventDefault(); location.reload(); });\n"
             "  if (document.getElementById('nama').value) document.getElementById('masuk').requestSubmit();"),
        ]
    for a, b in ganti:
        assert k.count(a) == 1, "kerangka berubah, pola tidak ketemu: " + a[:60]
        k = k.replace(a, b)
    return k


def kunci_paket(s, paket, folder):
    polos = gzip.compress(json.dumps(paket, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), mtime=0)
    if TANPA_SANDI:
        json.dump({"polos": W.b64(polos)}, open(os.path.join(folder, "data.json"), "w", encoding="utf-8"))
        return len(polos) // 1024
    garam, iv = os.urandom(16), os.urandom(12)
    isi = AESGCM(W.kunci(s, garam)).encrypt(iv, polos, None)
    json.dump({"garam": W.b64(garam), "iter": W.ITER, "iv": W.b64(iv), "isi": W.b64(isi)},
              open(os.path.join(folder, "data.json"), "w", encoding="utf-8"))
    return len(isi) // 1024


def kunci_gaji(teks):
    polos = gzip.compress(teks.encode("utf-8"), mtime=0)
    garam, iv = os.urandom(16), os.urandom(12)
    isi = AESGCM(W.kunci(W.sandi("pusat"), garam)).encrypt(iv, polos, None)
    return {"garam": W.b64(garam), "iter": W.ITER, "iv": W.b64(iv), "isi": W.b64(isi)}


def data_stok_gudang():
    """stok per barang per gudang (semua cabang) + daftar gudang tujuan per cabang, dari slow_moving.json pusat"""
    sm = json.load(open(os.path.join(DASH, "data", "slow_moving.json"), encoding="utf-8"))
    stok, hitung = {}, {}
    for r in sm:
        for g, q in r.get("gudang") or []:
            if q > 0:
                stok.setdefault(r["item"], []).append([g, q, r["cabang"]])
            if not re.search(r"RETUR|SERVICE|FAS", g):
                c = hitung.setdefault(r["cabang"], {})
                c[g] = c.get(g, 0) + 1
    gudang = {cab: [g for g, _ in sorted(n.items(), key=lambda x: -x[1])] for cab, n in hitung.items()}
    dibuat = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(DASH, "data", "slow_moving.json"))).strftime("%d/%m/%Y %H:%M")
    return {"dibuat": dibuat, "stok": stok, "gudang": gudang}


def bangun():
    e = env()
    url = e.get("PENGAJUAN_APPS_URL", "")
    kr = kerangka()
    isi_dash = open(os.path.join(DASH, "index.html"), encoding="utf-8").read()
    # penanda versi bangunan: ditempel di tautan halaman pajak supaya browser tidak menyajikan versi lama
    # (GitHub Pages menyimpan halaman 10 menit; 18 Nov 2026 Kak Intan sempat melihat halaman pajak versi
    # tanpa sandi dari cache, formulir sandinya tersembunyi dan langsung bilang "sandi salah")
    cap = datetime.datetime.now().strftime("%Y%m%d%H%M")
    # Kak Intan 13 Nov: limit diberi titik ribuan saat diketik; tempo terkunci kalau COD -> beri keterangan
    for a, b in [
        ('const nilaiLimit = el("input", { id: "aLimit", inputmode: "numeric", placeholder: "limit (Rp)" });',
         'const nilaiLimit = el("input", { id: "aLimit", inputmode: "numeric", placeholder: "mis. 20.000.000" });\n'
         '    nilaiLimit.addEventListener("input", () => { const d = nilaiLimit.value.replace(/[^\\d]/g, ""); '
         'nilaiLimit.value = d ? (+d).toLocaleString("id-ID") : ""; });'),
        ('      tempo.disabled = caraBayar.value === "COD";',
         '      tempo.disabled = caraBayar.value === "COD";\n'
         '      tempo.placeholder = tempo.disabled ? "COD - ganti Pembayaran ke Tempo/Giro" : "hari, mis. 30";\n'
         '      if (tempo.disabled) tempo.value = "";'),
        # 20 Nov 2026: keterangan pajak (Digunggung / Faktur Pajak 04) pindah ke dashboard/index.html
        # (labelJenisToko) karena hanya berlaku untuk TOKO BARU - naik limit & naik umur tokonya sudah DPP-4.
        # repo ini satu penyimpanan bersama: pusat langsung melihat, tidak ada agen yang mengirim
        ('text: p.pusat_id ? "sudah diterima pusat" : "menunggu dikirim agen ke pusat" }',
         'text: ["acc", "acc_sementara", "diproses"].includes(st) ? "sudah ACC pusat - bot memasukkan ke Accurate" : '
         'st === "selesai" ? "sudah masuk Accurate" : "sudah tampil di pusat - menunggu ACC Pak Kok Lik / Bu Diana" }'),
        # Kak Intan 14 Nov: pemindahan barang ikut repo ini - ceklis Hana OK -> bot membuat IT (Kirim Barang) di Accurate
        # status + keterangan bot (antre / sedang menulis / sibuk / masuk Accurate) - web/status_pindah.js
        ('  const statusPindah = (p) => p.terima ? ["Diterima", "ok"] : p.input_acc ? ["Dikirim" + (p.no_it ? " · " + p.no_it : ""), "ok"]\n'
         '    : p.hana ? ["Siap input Accurate", "warn"] : p.cek_stok ? ["Menunggu Hana", "mut"] : ["Menunggu cek stok", "mut"];\n',
         open(os.path.join(REPO, "web", "status_pindah.js"), encoding="utf-8").read()),
        ('          { h: "Status", f: (p) => statusPindah(p)[0], node: (p) => el("span", { class: "pill " + statusPindah(p)[1], text: statusPindah(p)[0] }) },',
         '          { h: "Status", f: (p) => statusPindah(p)[0], node: infoBotPindah },'),
        # 14 Nov: "Sudah input Accurate" dicentang manual -> bot melewati baris itu. Kolom ini sekarang hanya diisi bot.
        ('          { h: "Sudah input Accurate", hn: ceklisSemuaTahap(rows, "input_acc"), f: (p) => p.input_acc ? 1 : 0, node: (p) => el("span", { style: "display:grid;gap:4px;justify-items:center" }, ceklisTahap(p, "input_acc"), inputNoIT(p)) },',
         '          { h: "Sudah input Accurate (bot)", f: (p) => p.input_acc ? 1 : 0, node: (p) => el("span", { style: "display:grid;gap:2px;justify-items:center;font-size:12px" }, '
         'el("span", { class: p.input_acc ? "up" : "muted", text: p.input_acc ? "✓ " + (p.no_it || "") : "belum" }), p.input_acc ? el("span", { class: "muted", text: jamPd(p.input_acc_waktu) }) : null) },'),
    ]:
        assert isi_dash.count(a) == 1, "index.html berubah, pola tidak ketemu: " + a[:60]
        isi_dash = isi_dash.replace(a, b)
    # Kak Intan 14 Nov: formulir pemindahan diganti (stok semua gudang, pilih gudang asal / cabang & gudang tujuan, tanggal)
    a0, a1 = "  function formPindah(saranAwal) {", "  async function pPindah(sec) {"
    i0, i1 = isi_dash.index(a0), isi_dash.index(a1)
    assert i0 < i1 and isi_dash.count(a0) == 1
    isi_dash = isi_dash[:i0] + open(os.path.join(REPO, "web", "form_pindah.js"), encoding="utf-8").read() + isi_dash[i1:]
    # Kartu "Siap input Accurate" dibuang seluruhnya (Kak Intan 18 Nov 2026) - sisa alur lama sebelum ada bot.
    k0, k1 = '      card("Siap input Accurate", ', '      (() => { // IT Accurate'
    j0, j1 = isi_dash.index(k0), isi_dash.index(k1)
    assert j0 < j1 and isi_dash.count(k0) == 1 and isi_dash.count(k1) == 1
    isi_dash = isi_dash[:j0] + isi_dash[j1:]
    for a, b in [
        ('      muatLain("pindah_it").catch(() => (D.pindah_it = null))]);',
         '      muatLain("pindah_it").catch(() => (D.pindah_it = null)), muatLain("stok_gudang").catch(() => (D.stok_gudang = null))]);'),
        ('      for (const r of [...(D.slow_moving || []), ...(D.stok_jkt || [])]) for (const [gd, q] of r.gudang || []) {',
         '      const sgRows = Object.entries((D.stok_gudang || {}).stok || {}).map(([item, gs]) => ({ item, gudang: gs.map(([g, q]) => [g, q]) }));\n'
         '      for (const r of [...(D.slow_moving || []), ...(D.stok_jkt || []), ...sgRows]) for (const [gd, q] of r.gudang || []) {'),
        ('{ h: "Diminta", f: (p) => p.dibuat || "", fmt: (v) => v ? new Date(v).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "" },',
         '{ h: "Tgl pengajuan", f: (p) => p.tgl || p.dibuat || "", fmt: (v) => v ? new Date(v).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" }) : "" },'),
        ('card("Ajukan pemindahan dari JKT", "Cabang / sales menulis tipe yang mau dikirim dari JKT. Stok JKT langsung terlihat saat kode barang diketik. Gudang asal " + PINDAH_ASAL + ", gudang tujuan = gudang utama cabang.", formPindah())',
         'card("Ajukan pemindahan barang", "Ketik kode barang: stok di semua gudang langsung terlihat. Pilih gudang asal, cabang & gudang tujuan, tanggal pengajuan. Sesudah pusat mencentang ACC pusat, bot langsung membuat Pemindahan Barang (Kirim Barang) di Accurate.", formPindah())'),
        # Kak Intan 18 Nov 2026 ("belum ada disini nih gabung kesini aja"): Dashboard Pajak jadi tab di halaman ini.
        # Halaman pajaknya tetap satu-satunya sumber (../pajak/, dari dashboard_pajak) - di sini hanya dibingkai,
        # jadi tidak ada dua salinan kode pajak yang bisa berbeda. Halaman cabang membuang tab ini lewat kunci.json.
        ('    <button class="tab" role="tab" id="t-bpjs" data-p="bpjs">BPJS</button>',
         '    <button class="tab" role="tab" id="t-bpjs" data-p="bpjs">BPJS</button>\n'
         '    <button class="tab" role="tab" id="t-pajak" data-p="pajak">Dashboard pajak</button>'),
        ('<section class="page" id="bpjs" role="tabpanel" hidden></section>',
         '<section class="page" id="bpjs" role="tabpanel" hidden></section>\n'
         '<section class="page" id="pajak" role="tabpanel" hidden></section>'),
        ('gaji: pGaji, lunas: pLunas, bpjs: pBpjs };',
         'gaji: pGaji, lunas: pLunas, bpjs: pBpjs, pajak: pPajak };\n'
         '  function pPajak(sec) {\n'
         '    const bingkai = el("iframe", { src: "../pajak/?v=' + cap + '", title: "Dashboard Pajak", loading: "lazy",\n'
         '      style: "width:100%;height:calc(100vh - 180px);min-height:520px;border:0;border-radius:14px;background:#11171d" });\n'
         # kartu bot hanya untuk tampilan "Bot" di dalam bingkai: halaman pajak mengirim postMessage
         # {pajakView}. Sebelum pesan pertama datang kartunya tetap tampil, supaya tombol bot tidak
         # hilang kalau halaman pajaknya masih versi lama (18 Nov 2026).
         '    const kotakBot = el("div", { class: "kotak-bot", hidden: !!(S.pajakView && S.pajakView !== "bot") },\n'
         '      kartuBotPajak(), kartuBotBeni());\n'
         '    if (!window._pajakViewPasang) {\n'
         '      window._pajakViewPasang = true;\n'
         '      window.addEventListener("message", (ev) => {\n'
         '        const v = ev.data && ev.data.pajakView;\n'
         '        if (!v) return;\n'
         '        S.pajakView = v;\n'
         '        const k = document.querySelector("#pajak .kotak-bot");\n'
         '        if (k) k.hidden = v !== "bot";\n'
         '      });\n'
         '    }\n'
         '    sec.replaceChildren(kotakBot, el("div", { class: "card" },\n'
         '      el("div", { class: "row", style: "gap:10px;align-items:center;justify-content:space-between;margin-bottom:8px" },\n'
         '        el("span", { class: "muted", style: "font-size:12.5px", text: "Dashboard pajak grup Svarna: kepatuhan tiap PT, billing & NTPN, SPT, ekualisasi, laporan keuangan. Laporan keuangan & SPT Tahunan terkunci - sandinya sama dengan tab Gaji." }),\n'
         '        el("a", { class: "btn ghost", href: "../pajak/?v=' + cap + '", target: "_blank", rel: "noopener", text: "Buka di tab sendiri" })),\n'
         '      bingkai));\n'
         '  }\n' +
         # Kak Intan 18 Nov 2026: kartu Bot pajak (tombol jalankan bot PPh 23) di atas bingkai - web/bot_pajak.js
         open(os.path.join(REPO, "web", "bot_pajak.js"), encoding="utf-8").read() +
         # Kak Intan 18 Nov 2026: bot kedua BENI (billing & NTPN -> Drive + rekap + ekualisasi) - web/bot_beni.js
         open(os.path.join(REPO, "web", "bot_beni.js"), encoding="utf-8").read()),
        ('["Gaji", ["gaji", "lunas", "bpjs"]]];',
         '["Gaji", ["gaji", "lunas", "bpjs"]],\n    ["Pajak", ["pajak"]]];'),
        # Kak Intan 14 Nov: kolom Hana tidak ditampilkan; ceklis pusat (dulu "Stok JKT dicek") = ACC -> bot input Accurate
        ('          { h: "Hana OK kirim", hn: ceklisSemuaTahap(rows, "hana"), f: (p) => p.hana ? 1 : 0, node: (p) => el("span", { style: "display:grid;gap:4px;justify-items:center" }, ceklisTahap(p, "hana"), inputTglKirim(p)) },\n', ''),
        ('{ h: "Stok JKT dicek", hn: ceklisSemuaTahap(rows, "cek_stok"),', '{ h: "ACC pusat → Accurate", hn: ceklisSemuaTahap(rows, "cek_stok"),'),
        ('        kpi("Menunggu cek stok", nf0.format(aktif.filter((p) => !p.cek_stok).length),', '        kpi("Menunggu ACC pusat", nf0.format(aktif.filter((p) => !p.cek_stok).length),'),
        ('        kpi("Menunggu Hana", nf0.format(aktif.filter((p) => p.cek_stok && !p.hana).length), "konfirmasi kiriman ke cabang"),\n', ''),
        # Kak Intan 18 Nov 2026: "siap input Accurate maksudnya apa, kalo gak butuh hapus aja" - tahap itu sisa alur
        # lama (Hana mencentang, admin mengetik sendiri di Accurate). Sekarang bot yang membuat IT begitu ACC pusat
        # dicentang, jadi kotak KPI, pilihan saringan, dan kartunya dibuang (kartunya dipotong di bawah).
        ('        kpi("Siap input Accurate", nf0.format(siap.length), grupSiap.size + " pemindahan (gudang asal → tujuan)", siap.length ? "warn" : ""),\n', ''),
        ('const KPI_PD = { "Menunggu cek stok": "cek", "Menunggu ACC pusat": "cek", "Menunggu Hana": "hana", "Siap input Accurate": "siap", "Dikirim, belum diterima": "kirim", "Saran pindah dari JKT": "saran" };',
         # Kak Intan 18 Nov 2026 sore: "saran pindah dihapus aja" - kotak KPI & kartunya dibuang
         'const KPI_PD = { "Menunggu ACC pusat": "cek", "Dikirim, belum diterima": "kirim" };'),
        ('        kpi("Saran pindah dari JKT", nf0.format(saran.length), "barang yang cabang perlu pesan dan stok JKT lebih")])),',
         '        ])),'),
        # Kak Intan 18 Nov 2026 sore: kartu "Pemindahan barang di Accurate (IT)" digabung ke Summary (halaman pusat);
        # halaman cabang tidak punya Summary, jadi kartu IT tetap tampil di sana.
        ('      (() => { // IT Accurate', '      S.kunci ? (() => { // IT Accurate'),
        ('[["aktif", "Belum diterima"], ["Menunggu cek stok", "Menunggu cek stok"], ["Menunggu Hana", "Menunggu Hana"], ["Siap input Accurate", "Siap input Accurate"], ["Dikirim", "Dikirim"], ["Diterima", "Diterima"], ["semua", "Semua"]]',
         # pilihannya disamakan dengan status yang benar-benar dipakai status_pindah.js (saringan memakai startsWith)
         '[["aktif", "Belum diterima"], ["Menunggu ACC pusat", "Menunggu ACC pusat"], ["Antre", "Antre bot Accurate"], '
         '["Bot gagal", "Bot gagal - perlu dicek"], ["Sudah masuk Accurate", "Sudah masuk Accurate"], '
         '["Diterima", "Diterima cabang"], ["semua", "Semua"]]'),
        ('"Ceklis per tahap: Stok JKT dicek → Hana OK kirim (isi rencana tanggal kirim) → Sudah input Accurate (isi No. Pemindahan, ceklis ikut tercentang) → Diterima cabang.',
         '"Ceklis per tahap: ACC pusat (bot langsung membuat Pemindahan Barang / Kirim Barang di Accurate) → Sudah input Accurate (No. Pemindahan diisi bot) → Diterima cabang.'),
        # Kak Intan 14 Nov: harga final pricelist + total per baris / per IT / summary bulanan - hanya pusat; cabang tanpa harga
        ('muatLain("stok_gudang").catch(() => (D.stok_gudang = null))]);',
         'muatLain("stok_gudang").catch(() => (D.stok_gudang = null)), S.kunci && !S.adminCab ? null : muatLain("pricelist_pindah").catch(() => (D.pricelist_pindah = null))]);'),
        ('    const hargaPd = (p) => p.harga_modal != null ? +p.harga_modal : ((hm(p.item, p.cabang) || {}).harga || 0);\n',
         open(os.path.join(REPO, "web", "pindah_harga.js"), encoding="utf-8").read() +
         '    const hargaPd = (p) => S.kunci && !S.adminCab ? 0 : p.harga_modal != null ? +p.harga_modal : p.harga_it != null ? +p.harga_it : ((plPd(p) || {}).harga || 0);\n'),
        ('      const h = hm(p.item, p.cabang), harga = hargaPd(p);\n'
         '      const ket = p.harga_modal != null ? "diubah manual" + (h ? " · pricelist " + nf0.format(h.harga) : "") : h ? h.merk + " · " + h.sheet + " · edisi " + h.edisi + " (netto incl PPN)" : "kode ini tidak ada di REKAP HARGA zona cabang ini";',
         '      const h = plPd(p), harga = hargaPd(p);\n'
         '      const ket = p.harga_modal != null ? "diubah pusat" + (h ? " · pricelist " + nf0.format(h.harga) : "") : p.harga_it != null ? "harga di keterangan IT" : h ? h.ket : "kode ini tidak ada di pricelist bulan terbaru - isi manual";'),
        ('placeholder: "harga modal", title: ket, "aria-label": "Harga modal "', 'placeholder: "harga final", title: ket, "aria-label": "Harga final "'),
        ('          { h: "Harga modal", f: hargaPd, num: true, node: inputModalPd },\n'
         '          { h: "Nilai", f: (p) => hargaPd(p) * (+p.qty || 0), num: true, fmt: (v) => v ? nf0.format(v) : "-" },',
         '          ...(S.kunci && !S.adminCab ? [] : [{ h: "Harga final (pricelist)", f: hargaPd, num: true, node: inputModalPd },\n'
         '          { h: "Total (harga × qty)", f: (p) => hargaPd(p) * (+p.qty || 0), num: true, fmt: (v) => v ? nf0.format(v) : "-" },\n'
         '          { h: "Revisi harga", f: (p) => p.revisi_status || "", node: kolomRevisi }]),'),
        ('    const kolHarga = (fItem, fCab, fQty) => [', '    const kolHarga = (fItem, fCab, fQty) => S.kunci ? [] : ['),
        ('      })(),\n      card("Saran pindah dari JKT",',
         '      })() : null,\n      S.kunci ? null : kartuSummaryPindah(),\n      null && card("Saran pindah dari JKT",'),
        # halaman admin cabang (14 Nov): harga terlihat tapi hanya-baca, tab = Revisi harga pemindahan, tanpa formulir ajukan
        ('      if (!bolehPd(p, "modal")) return el("span", { title: ket, text: harga ? nf0.format(harga) : "-" });',
         '      if (S.kunci || !bolehPd(p, "modal")) return el("span", { title: ket, text: harga ? nf0.format(harga) : "-" });'),
        ('card("Ajukan pemindahan barang", "Ketik', 'S.adminCab ? null : card("Ajukan pemindahan barang", "Ketik'),
        ('    if (h) h.textContent = "Dashboard Cabang " + k.cabang;\n    document.title = "Dashboard Cabang " + k.cabang;',
         '    if (h) h.textContent = (S.adminCab ? "Admin Cabang " : "Dashboard Cabang ") + k.cabang;\n    document.title = (S.adminCab ? "Admin Cabang " : "Dashboard Cabang ") + k.cabang;'),
        ('    S.kunci = k.cabang;\n',
         '    S.kunci = k.cabang;\n    if (k.peran === "admin") { S.adminCab = true; const tb = document.querySelector(\'.tab[data-p="pindah"]\'); if (tb) tb.textContent = "Revisi harga pemindahan"; }\n'),
        # Kak Intan 18 Nov 2026 (butir 6): saringan cabang bisa dicentang banyak sekaligus + saringan bulan;
        # (butir 8) kolom harga bisa diklik & diisi kalau kodenya tidak ada di pricelist; (butir 9) unduh Excel.
        ('          if ((S.itCabAsal && ca !== S.itCabAsal) || (S.itCabTuj && ct !== S.itCabTuj)) continue;\n',
         '          const kodeIt = new Set((x.baris || []).map(([k]) => String(k).trim().toUpperCase()));\n'
         '          const blnIt = String(x.tgl || "").slice(0, 7);\n'
         '          if (S.itBulan && blnIt !== S.itBulan) continue;\n'
         '          if ((S.itCabAsalM || []).length && !S.itCabAsalM.includes(ca)) continue;\n'
         '          if ((S.itCabTujM || []).length && !S.itCabTujM.includes(ct)) continue;\n'),
        ('            .map(([item, q]) => { const h = bolehHarga ? ((hm(item, ct) || {}).harga || 0) : 0;\n',
         '            .map(([item, q, hket]) => { const hp = !bolehHarga ? { harga: 0, sumber: "" } : hargaPindahBaris(item, ct, ca, hket, kodeIt), h = hp.harga;\n'),
        ('        hapusIt.disabled = !(S.itCabAsal || S.itCabTuj);\n'
         '        hapusIt.addEventListener("click", () => { S.itCabAsal = S.itCabTuj = ""; render(); });',
         '        hapusIt.disabled = !((S.itCabAsalM || []).length || (S.itCabTujM || []).length || S.itBulan);\n'
         '        hapusIt.addEventListener("click", () => { S.itCabAsalM = []; S.itCabTujM = []; S.itBulan = ""; render(); });\n'
         '        const blnItAda = [...new Set((D.pindah_it || []).map((x) => String(x.tgl || "").slice(0, 7)))].filter(Boolean).sort().reverse();\n'
         '        const namaBlnIt = (v) => { const [y, m] = v.split("-"); return ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"][+m - 1] + " " + y; };\n'
         '        const selBlnIt = el("select", { id: "itBulan" }, el("option", { value: "", text: "Semua bulan" }),\n'
         '          blnItAda.map((b) => el("option", { value: b, text: namaBlnIt(b), selected: b === S.itBulan })));\n'
         '        selBlnIt.addEventListener("change", () => { S.itBulan = selBlnIt.value; render(); });\n'
         '        const pesanItX = el("span", { class: "muted", style: "font-size:12px" });\n'
         '        const tombolItX = el("button", { class: "btn ghost", type: "button", text: "Unduh Excel (rekap + surat jalan)" });\n'
         '        tombolItX.addEventListener("click", () => {\n'
         '          const perIt = dok.map((x) => ({ it: x.nomor, tgl: x.tgl, asal: x.asal, tujuan: x.tujuan || "", cab: x.ca + " \u2192 " + x.ct,\n'
         '            cabTuj: x.ct, barang: x.isi.length, qty: x.totQty, total: x.totNilai, terima: x.terima }));\n'
         '          const baris = new Map(dok.map((x) => [x.nomor, x.isi.map((r) => ({ item: r.item, nama: namaItem(r.item), qty: r.q, harga: r.harga, nilai: r.nilai }))]));\n'
         '          unduhPindahExcel("Pemindahan barang Accurate" + (S.itBulan ? " " + namaBlnIt(S.itBulan) : ""), perIt, baris, tombolItX, pesanItX);\n'
         '        });'),
        ('          el("div", { class: "row", style: "gap:12px;flex-wrap:wrap;align-items:end" },\n'
         '            el("label", { class: "ctl", for: "itCabAsal" }, "Cabang asal", pilihCab("itCabAsal", S.itCabAsal, (v) => (S.itCabAsal = v))),\n'
         '            el("label", { class: "ctl", for: "itCabTuj" }, "Cabang tujuan", pilihCab("itCabTuj", S.itCabTuj, (v) => (S.itCabTuj = v))),\n'
         '            el("label", { for: "pdItSemua", style: "display:flex;gap:6px;align-items:center" }, cb, "Tampilkan semua IT (termasuk antar gudang lain)"),\n'
         '            hapusIt),',
         '          el("div", { class: "row", style: "gap:12px;flex-wrap:wrap;align-items:end" },\n'
         '            el("label", { class: "ctl", for: "itBulan" }, "Bulan", selBlnIt),\n'
         '            pilihBanyak("Cabang asal", cabsIt, S.itCabAsalM || [], (v) => (S.itCabAsalM = v)),\n'
         '            pilihBanyak("Cabang tujuan", cabsIt, S.itCabTujM || [], (v) => (S.itCabTujM = v)),\n'
         '            el("label", { for: "pdItSemua", style: "display:flex;gap:6px;align-items:center" }, cb, "Tampilkan semua IT (termasuk antar gudang lain)"),\n'
         '            hapusIt, tombolItX, pesanItX),'),
        ('              return { item, q, harga: h, nilai: h * q, dipakai: pakaiIt.has(String(x.nomor).toUpperCase() + "|" + item) }; });',
         '              return { item, q, ct, harga: h, sumber: hp.sumber, set: !!hp.set, nilai: h * q, dipakai: pakaiIt.has(String(x.nomor).toUpperCase() + "|" + item) }; });'),
        ('            { h: "Harga modal", f: (r) => r.harga, num: true, fmt: (v) => v ? nf0.format(v) : "-" },',
         '            { h: "Harga modal", f: (r) => r.harga, num: true, node: (r) => r.set ? el("span", { class: "muted", title: r.sumber, text: "satu set" }) : inputHargaPd(r.item, r.ct, r.harga, r.sumber) },'),
    ]:
        assert isi_dash.count(a) == 1, "index.html berubah, pola tidak ketemu: " + a[:60]
        isi_dash = isi_dash.replace(a, b)
    stok_gudang = json.dumps(data_stok_gudang(), ensure_ascii=False, separators=(",", ":"))
    hasil = []
    for web, (cabang, merek, judul) in HALAMAN.items():
        sumber = os.path.join(DASH, "data") if not cabang else os.path.join(DASH, "cabang", cabang, "data")
        if not os.path.isdir(sumber):
            print("LEWATI", web, "- tidak ada", sumber); continue
        berkas = {"data/" + os.path.basename(f): open(f, encoding="utf-8").read()
                  for f in sorted(glob.glob(os.path.join(sumber, "*.json"))) if os.path.basename(f) not in BUANG}
        gaji = None
        if not cabang and GAJI_DI_PUSAT and os.path.exists(os.path.join(sumber, "gaji.json")):
            gaji = kunci_gaji(open(os.path.join(sumber, "gaji.json"), encoding="utf-8").read())
        berkas["data/stok_gudang.json"] = stok_gudang
        admin = web.startswith("admin-")
        if not cabang or admin:   # harga hanya pusat & admin cabang - sales di halaman cabang tidak boleh tahu harga
            berkas["data/pricelist_pindah.json"] = open(os.path.join(GIO, "skrip", "log", "pricelist_pindah.json"), encoding="utf-8").read()
        else:
            berkas.pop("data/harga_modal.json", None)
        if cabang:
            berkas["data/kunci.json"] = json.dumps({"cabang": cabang, "tab": ["pindah"], "peran": "admin"} if admin else
                                                   {"cabang": cabang, "tab": ["pengajuan", "pindah"]})
        paket = {"dibuat": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "berkas": berkas,
                 "isian": {"url": url, "halaman": web, "kunci": kunci_hal(e["PENGAJUAN_MASTER"], web)} if url else None}
        if gaji:
            paket["gaji"] = gaji
        folder = os.path.join(REPO, web)
        os.makedirs(folder, exist_ok=True)
        hal = kr.replace("<!--MEREK-->", html.escape(merek)).replace("<!--JUDUL-->", html.escape(judul)).replace("<!--HALAMAN-->", isi_dash)
        if web == "pusat":
            # Kak Intan 21 Nov 2026: halaman pusat bertema rosegold ceria gaya Accurate (menu modul di kiri) - web/tema_rosegold.js.
            # Hanya lapisan tampilan; halaman cabang/admin tetap tampilan lama.
            assert hal.count("</body>") == 1, "kerangka berubah: </body> tidak ketemu"
            # layar pembuka sudah rosegold sejak detik pertama (skrip tema baru jalan sesudah ~860 KB halaman terbaca)
            assert hal.count("</head>") == 1, "kerangka berubah: </head> tidak ketemu"
            hal = hal.replace("</head>", "<style>body{background:#fdf4f1!important;color:#45292f!important}"
                              "#masuk .raksasa{color:#d8a39a;opacity:.6}#masuk h1{color:#b76e79}#galat{color:#d4405f}#masuk .catatan{color:#8d6a70}"
                              "#masuk button{background:linear-gradient(180deg,#c77f8a,#b06571)!important;color:#fff!important;border:0!important;"
                              "box-shadow:0 6px 16px -6px rgba(176,101,113,.7)}"
                              "#masuk input{background:#fff!important;color:#45292f!important;border:1px solid #e9cbc4!important}"
                              "#masuk input::placeholder{color:#b8959a!important}</style>\n</head>", 1)
            hal = hal.replace("</body>", "<script>\n" + open(os.path.join(REPO, "web", "tema_rosegold.js"), encoding="utf-8").read() + "\n</script>\n</body>")
        open(os.path.join(folder, "index.html"), "w", encoding="utf-8").write(hal)
        if admin and not TANPA_SANDI and not os.path.exists(W.berkas_sandi(web)):
            raise SystemExit("sandi halaman %s belum dibuat (jangan sampai jatuh ke sandi umum/sales)" % web)
        hasil.append((web, judul, len(berkas), kunci_paket(None if TANPA_SANDI else W.sandi(web), paket, folder)))
    # halaman admin tidak dicantumkan di daftar depan (link dibagikan langsung ke admin cabang)
    daftar = "\n".join('    <li><a href="%s/">%s</a></li>' % (w, html.escape(j)) for w, j, _, _ in hasil if not w.startswith("admin-"))
    if bangun_pajak():
        daftar += '\n    <li><a href="pajak/?v=%s">Dashboard Pajak</a></li>' % cap
    open(os.path.join(REPO, "index.html"), "w", encoding="utf-8").write(
        '<!doctype html>\n<html lang="id"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow">\n'
        '<title>Pengajuan Sales</title>\n<style>body{margin:0;background:#11171d;color:#e6ecf1;font:18px/1.5 "Aptos Narrow","Arial Narrow",system-ui,sans-serif}'
        'main{max-width:520px;margin:12vh auto;padding:0 16px}h1{font-size:22px;letter-spacing:.3em;text-transform:uppercase;color:#9aa8b5}'
        'ul{list-style:none;padding:0}li a{display:block;padding:14px 20px;margin:8px 0;border:1px solid rgba(255,255,255,.18);border-radius:999px;color:#e6ecf1;text-decoration:none;text-transform:uppercase;letter-spacing:.08em}'
        'li a:hover{background:#e6ecf1;color:#11171d}</style></head>\n<body><main><h1>Pengajuan Sales</h1>\n  <ul>\n' + daftar +
        '\n  </ul></main></body></html>\n')
    open(os.path.join(REPO, ".nojekyll"), "w").close()
    for w, j, n, kb in hasil:
        print("%-10s %3d berkas %7d KB terkunci" % (w, n, kb))
    if not url:
        print("CATATAN: PENGAJUAN_APPS_URL belum diisi - halaman terbuka tapi isian belum bisa disimpan.")


# Dashboard Pajak ikut repo ini (Kak Intan 18 Nov 2026: "yang dashboard pajak di tarik ya aku mau edit edit
# digabung sama punya kita"). Sumber halaman & datanya tetap satu: AGEN IT (GIO)\dashboard_pajak, dirakit
# skrip\bangun_web_pajak.py. Yang beda hanya pembungkusnya - sandinya ikut TANPA_SANDI repo ini.
def bangun_pajak():
    sys.path.insert(0, os.path.join(GIO, "skrip"))
    import bangun_web_pajak as P  # noqa: E402
    if not os.path.exists(os.path.join(P.SUMBER, "index.html")):
        print("LEWATI pajak - dashboard_pajak\\index.html tidak ada")
        return False
    kr = P.halaman()
    folder = os.path.join(REPO, "pajak")
    os.makedirs(folder, exist_ok=True)
    # Kak Intan 18 Nov 2026 (siang, menggantikan "kunci semua" pagi itu): tampilan 1, 2, 4 TERBUKA, tampilan 3
    # (SPT Tahunan & laporan keuangan) BERSANDI = sandi tab Gaji (sandi halaman pusat, DPAPI). Kak Intan sudah diberi
    # tahu kepatuhan tiap PT, billing & NTPN, rekap SPT masa jadi terbuka ("iyaa"). data.json = P.data_json:
    # {dibuat, polos: dataset terbuka + status bot, kunci: AES-GCM dataset lk_* & spt_tahunan}.
    isi = P.data_json(lambda g: W.kunci(W.sandi("pusat"), g), W.ITER)
    json.dump(isi, open(os.path.join(folder, "data.json"), "w", encoding="utf-8"))
    kr = kr.replace("Khusus untuk tim pajak dan pihak yang diberi sandi.",
                    "Laporan keuangan & SPT Tahunan terkunci - sandinya sama dengan tab Gaji.", 1)
    # Kak Intan 21 Nov 2026 ("kok yang pajak belum yaa"): halaman pajak ikut tema rosegold pusat - web/tema_rosegold_pajak.css
    assert kr.count("</head>") == 1, "kerangka pajak berubah: </head> tidak ketemu"
    kr = kr.replace("</head>", '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@500;600;700;800&display=swap">\n<style>\n'
                    + open(os.path.join(REPO, "web", "tema_rosegold_pajak.css"), encoding="utf-8").read() + "</style>\n</head>", 1)
    open(os.path.join(folder, "index.html"), "w", encoding="utf-8").write(kr)
    print("%-10s terbuka %d KB, terkunci %d KB" % ("pajak", len(isi["polos"]) // 1024, len(isi["kunci"]["isi"]) // 1024))
    return True


def kirim():
    # satu commit tanpa riwayat + force push (data terkunci ~10 MB per halaman; riwayat tidak dibiarkan membengkak)
    g = lambda *a: subprocess.run(["git", "-C", REPO, *a], check=True)  # noqa: E731
    g("checkout", "-q", "--orphan", "terbit-baru")
    g("add", "-A")
    g("commit", "-q", "-m", "Pengajuan sales web " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    subprocess.run(["git", "-C", REPO, "branch", "-q", "-D", "main"], capture_output=True)
    g("branch", "-q", "-m", "main")
    g("push", "-q", "-f", "origin", "main")
    print("Terkirim ke GitHub.")


if __name__ == "__main__":
    bangun()
    if "--kirim" in sys.argv:
        kirim()
