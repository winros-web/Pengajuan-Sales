/* Tema Rosegold gaya Accurate - halaman PUSAT Pengajuan-Sales (Kak Intan 21 Nov 2026:
   "dibikin yg gaul ... warna rosegold, jangan kaya sekarang serem kaya saham ... ceria colorfull ada gambar-gambarnya
   ... kaya accurate tampilannya, tombol, input, formulir, modulnya dipisah yang sebelah kiri").
   Hanya lapisan tampilan: tab asli (nav.tabs .tab) tetap dipakai, menu kiri cuma mengklik tab itu.
   Dipasang skrip/bangun.py khusus halaman pusat. Logika dashboard/index.html tidak diubah. */
(() => {
  "use strict";
  const MODUL = [
    ["Penjualan", "🛍️", "#e8828f", ["harian", "laba", "sales", "aturan"]],
    ["Stok & pembelian", "📦", "#e6a157", ["umur", "jualslow", "pindah", "retur"]],
    ["Piutang & tagihan", "💰", "#c98bd8", ["piutang_usaha", "cod", "telat", "pasif", "kembali", "blokir", "penagihan", "tagihwa"]],
    ["Kirim & nota", "🚚", "#5fb7c9", ["rute", "tanda", "balik"]],
    ["Pengajuan", "📝", "#6cbf8f", ["pengajuan"]],
    ["Gaji", "💵", "#d9a441", ["gaji", "lunas", "bpjs"]],
    ["Pajak", "🏛️", "#8f9be0", ["pajak"]],
    ["Kompensasi", "🤝", "#d98fb0", ["kompen"]],   // Kak Intan 26 Nov 2026
  ];
  const IKON = {
    harian: "📊", laba: "💹", sales: "🏆", aturan: "📜", umur: "⏳", jualslow: "🐢", pindah: "🔄", retur: "↩️",
    piutang_usaha: "📒", cod: "💵", telat: "⏰", pasif: "😴", kembali: "🎉", blokir: "🚫", penagihan: "🧾", tagihwa: "💬",
    rute: "🗺️", tanda: "✍️", balik: "🔁", pengajuan: "📝", gaji: "💵", lunas: "✅", bpjs: "🏥", pajak: "🏛️", kompen: "🤝",
  };
  // ikon kotak angka ditebak dari judulnya
  const IKON_KPI = [
    [/whatsapp|\bwa\b|ditagih wa|chat/i, "💬"], [/toko|pelanggan|outlet/i, "🏪"], [/nota|faktur|invoice|do\b/i, "🧾"],
    [/sisa|tagih|piutang|overdue|lunas|bayar|kas|rp|nilai|omset|omzet|penjualan|jual/i, "💰"],
    [/laba|margin|untung|rugi/i, "📈"], [/stok|barang|unit|qty|gudang/i, "📦"], [/sales|salesman/i, "🧑‍💼"],
    [/bonus|target|capai/i, "🎯"], [/gaji|bpjs|karyawan/i, "💵"], [/retur/i, "↩️"], [/kirim|rute|supir|mobil/i, "🚚"],
    [/pajak|ppn|pph/i, "🏛️"], [/pengajuan|acc|setuju/i, "📝"], [/hari|umur|tempo|telat|jam|tanggal|bulan/i, "⏰"],
  ];

  const CSS = `
:root.tema-rg, :root.tema-rg[data-theme], :root.tema-rg:not([data-theme="light"]) {
  --bg: #fdf4f1 !important; --panel: #ffffff !important; --fg: #45292f !important; --muted: #8d6a70 !important;
  --line: #f1dcd6 !important; --accent: #b76e79 !important; --accent-soft: #fbe6e3 !important;
  --ok: #2c9a68 !important; --warn: #c27a12 !important; --bad: #d4405f !important;
  --ok-soft: #e1f6ea !important; --warn-soft: #fff1d9 !important; --bad-soft: #fde4ea !important; --bar: #f4c1bd !important;
  --font-ui: "Nunito", "Segoe UI", system-ui, sans-serif !important; --font-num: "Nunito", "Segoe UI", system-ui, sans-serif !important;
  --rg1: #b76e79; --rg2: #d8a39a; --rg3: #f3d1c4; --sisi: 252px; --atas: 58px;
  color-scheme: light !important;
}
body.tema-rg { background: radial-gradient(1200px 500px at 100% -10%, #ffe3ec 0%, transparent 60%),
  radial-gradient(900px 500px at -10% 110%, #fff0db 0%, transparent 55%), #fdf4f1 !important;
  color: var(--fg); font-family: var(--font-ui); min-height: 100vh; }
body.tema-rg.rg-siap { padding: var(--atas) 0 0 var(--sisi); }
body.tema-rg * { font-family: inherit; }
body.tema-rg .mono, body.tema-rg .kpi .v, body.tema-rg td.num, body.tema-rg .num { font-family: var(--font-num) !important; font-variant-numeric: tabular-nums; }
body.tema-rg #isi .wrap { max-width: 1480px; padding-top: 18px; }
body.tema-rg #grupTab, body.tema-rg #isi nav.tabs { display: none !important; }
body.tema-rg header.top h1 { display: none; }
body.tema-rg header.top .sub { color: var(--muted); }
body.tema-rg #webKaki { color: var(--muted); }
body.tema-rg #webKaki a { color: var(--rg1); }

/* ===== bilah atas ===== */
#rgAtas { position: fixed; top: 0; left: 0; right: 0; height: var(--atas); z-index: 60; display: flex; align-items: center; gap: 14px;
  padding: 0 18px 0 0; background: #fff; border-bottom: 1px solid var(--line); box-shadow: 0 2px 14px rgba(183,110,121,.10); }
#rgAtas .merek { width: var(--sisi); height: 100%; display: flex; align-items: center; gap: 10px; padding: 0 18px; flex: none;
  background: linear-gradient(135deg, #b76e79 0%, #d8a39a 55%, #efc6b5 100%); color: #fff; font-weight: 800; font-size: 17px; letter-spacing: .01em; }
#rgAtas .logo { width: 34px; height: 34px; border-radius: 11px; background: rgba(255,255,255,.25); display: grid; place-items: center; font-size: 19px;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.45); }
#rgAtas .merek small { display: block; font-weight: 600; font-size: 11px; opacity: .9; letter-spacing: .04em; }
#rgAtas .remah { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--muted); min-width: 0; overflow: hidden; white-space: nowrap; }
#rgAtas .remah b { color: var(--fg); font-weight: 800; }
#rgAtas .kanan { margin-left: auto; display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); }
#rgAtas .chip { padding: 6px 12px; border-radius: 999px; background: var(--accent-soft); color: var(--rg1); font-weight: 700; white-space: nowrap; }
#rgMenuBtn { display: none; appearance: none; border: 0; background: var(--accent-soft); color: var(--rg1); width: 40px; height: 40px; border-radius: 12px;
  font-size: 20px; cursor: pointer; margin-left: 12px; flex: none; }

/* ===== menu modul kiri ===== */
#rgSisi { position: fixed; top: var(--atas); left: 0; bottom: 0; width: var(--sisi); z-index: 55; overflow-y: auto; padding: 14px 10px 30px;
  background: linear-gradient(180deg, #fff7f4 0%, #fdebe6 100%); border-right: 1px solid var(--line); scrollbar-width: thin; }
#rgSisi .cari { width: 100%; height: 36px; border-radius: 10px; border: 1px solid var(--line); background: #fff; padding: 0 12px 0 34px; font-size: 13.5px;
  color: var(--fg); margin-bottom: 10px; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23b76e79' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: 11px 50%; }
#rgSisi .cari:focus { outline: none; border-color: var(--rg1); box-shadow: 0 0 0 3px rgba(183,110,121,.18); }
.rg-modul { margin-bottom: 4px; }
.rg-modul > button { width: 100%; appearance: none; border: 0; background: transparent; display: flex; align-items: center; gap: 11px; padding: 8px 10px;
  border-radius: 12px; font: inherit; font-size: 14px; font-weight: 800; color: #5b3a40; cursor: pointer; text-align: left; }
.rg-modul > button:hover { background: rgba(255,255,255,.75); }
.rg-modul > button .ik { width: 34px; height: 34px; border-radius: 11px; display: grid; place-items: center; font-size: 18px; flex: none;
  background: var(--warna); box-shadow: 0 4px 10px -4px var(--warna); }
.rg-modul > button .pan { margin-left: auto; color: #c79a9f; font-size: 11px; transition: transform .2s; }
.rg-modul.buka > button .pan { transform: rotate(90deg); }
.rg-modul.aktif > button { background: #fff; box-shadow: 0 2px 10px rgba(183,110,121,.12); }
.rg-sub { display: none; padding: 4px 0 6px 22px; margin-left: 17px; border-left: 2px dashed #efcfc8; }
.rg-modul.buka .rg-sub { display: grid; gap: 2px; }
.rg-sub button { appearance: none; border: 0; background: transparent; display: flex; align-items: center; gap: 9px; padding: 7px 10px; border-radius: 10px;
  font: inherit; font-size: 13.5px; font-weight: 600; color: #6e4c52; cursor: pointer; text-align: left; }
.rg-sub button .ik { font-size: 15px; width: 20px; text-align: center; }
.rg-sub button:hover { background: rgba(255,255,255,.85); color: var(--rg1); }
.rg-sub button.aktif { background: linear-gradient(90deg, #b76e79, #d8a39a); color: #fff; box-shadow: 0 4px 12px -4px rgba(183,110,121,.7); }
#rgSisi .hiasan { margin: 18px 6px 0; padding: 14px; border-radius: 16px; text-align: center; font-size: 12.5px; color: #8d6a70; font-weight: 700;
  background: linear-gradient(135deg, #ffe6ee, #fff3dc); border: 1px dashed #f0c7c0; }
#rgSisi .hiasan .besar { font-size: 30px; display: block; margin-bottom: 2px; }
#rgTirai { display: none; }

/* ===== spanduk modul ===== */
#rgSpanduk { position: relative; overflow: hidden; border-radius: 20px; padding: 18px 22px; display: flex; align-items: center; gap: 16px; color: #fff;
  background: linear-gradient(120deg, var(--w1, #b76e79) 0%, var(--w2, #e6a9a0) 60%, #f7d6c4 100%); box-shadow: 0 10px 28px -14px rgba(183,110,121,.8); }
#rgSpanduk .ik { width: 62px; height: 62px; border-radius: 18px; background: rgba(255,255,255,.28); display: grid; place-items: center; font-size: 34px; flex: none;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.5); }
#rgSpanduk .jd { font-size: 24px; font-weight: 800; line-height: 1.15; text-shadow: 0 1px 2px rgba(0,0,0,.08); }
#rgSpanduk .md { font-size: 13px; font-weight: 700; opacity: .92; letter-spacing: .05em; text-transform: uppercase; }
#rgSpanduk svg { position: absolute; right: -10px; top: -10px; height: calc(100% + 20px); opacity: .9; pointer-events: none; }

/* ===== kartu gaya formulir Accurate ===== */
body.tema-rg .card { border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 6px 20px -12px rgba(183,110,121,.35); padding: 0 16px 16px; }
body.tema-rg .card > h2, body.tema-rg .card > .row:first-child > h2 { margin: 0 -16px 2px; padding: 12px 16px; font-size: 15px; font-weight: 800; color: #6b3f47;
  background: linear-gradient(90deg, #fdeae6, #fff6f2); border-bottom: 1px solid var(--line); border-radius: 16px 16px 0 0; }
body.tema-rg .card > h2 .judul-kartu::before { content: "✿ "; color: var(--rg1); }
body.tema-rg .card > :first-child:not(h2) { margin-top: 14px; }
body.tema-rg .card[hidden] { display: none !important; }

/* kotak angka warna-warni */
body.tema-rg .kpi { position: relative; overflow: hidden; border: 0; border-radius: 16px; padding: 14px 16px; box-shadow: 0 6px 18px -10px rgba(120,60,70,.35);
  background: linear-gradient(135deg, var(--k1), var(--k2)); color: #4a2b31; }
body.tema-rg .kpis > .kpi:nth-child(6n+1) { --k1: #ffe1e7; --k2: #ffd0d8; }
body.tema-rg .kpis > .kpi:nth-child(6n+2) { --k1: #fff0d6; --k2: #ffe0b2; }
body.tema-rg .kpis > .kpi:nth-child(6n+3) { --k1: #efe3ff; --k2: #e1cff9; }
body.tema-rg .kpis > .kpi:nth-child(6n+4) { --k1: #dcf5ec; --k2: #c6ecdd; }
body.tema-rg .kpis > .kpi:nth-child(6n+5) { --k1: #dff1fb; --k2: #c9e6f6; }
body.tema-rg .kpis > .kpi:nth-child(6n+6) { --k1: #fde6d9; --k2: #f8cfbb; }
body.tema-rg .kpi .k { color: #7a4f57; font-weight: 800; }
body.tema-rg .kpi .v { font-weight: 800; color: #3f2228; }
body.tema-rg .kpi[data-ikon]::after { content: attr(data-ikon); position: absolute; right: 10px; top: 8px; font-size: 30px; opacity: .85;
  filter: drop-shadow(0 3px 4px rgba(0,0,0,.12)); }
body.tema-rg .kpi[data-ikon] .k { padding-right: 40px; }
body.tema-rg .kotak-bagian .kpi { border-left: 0; }
body.tema-rg .kpi-klik:hover { transform: translateY(-2px); box-shadow: 0 10px 22px -10px rgba(183,110,121,.6); }
body.tema-rg .kpi-klik { transition: transform .15s, box-shadow .15s; }
body.tema-rg .kpi-klik.aktif, body.tema-rg .kotak-bagian .kpi.aktif { box-shadow: 0 0 0 3px #b76e79, 0 10px 22px -10px rgba(183,110,121,.6); }

/* input, pilihan, tombol */
body.tema-rg select, body.tema-rg input:not([type=checkbox]):not([type=radio]):not([type=range]), body.tema-rg textarea,
body.tema-rg .saring-tombol {
  background-color: #fff !important; color: var(--fg) !important; border: 1px solid #e9cbc4 !important; border-radius: 8px !important; font-family: inherit; }
body.tema-rg select:focus, body.tema-rg input:focus, body.tema-rg textarea:focus { outline: none !important; border-color: var(--rg1) !important;
  box-shadow: 0 0 0 3px rgba(183,110,121,.18) !important; }
body.tema-rg input[type=checkbox], body.tema-rg input[type=radio] { accent-color: #b76e79; }
body.tema-rg button.btn, body.tema-rg a.btn:not(.ghost) { background: linear-gradient(180deg, #c77f8a, #b06571) !important; border: 1px solid #a85d69 !important;
  color: #fff !important; border-radius: 8px !important; font-weight: 700; box-shadow: 0 3px 8px -3px rgba(176,101,113,.7); }
body.tema-rg button.btn:hover:not(:disabled) { filter: brightness(1.06); }
body.tema-rg button.btn.ghost, body.tema-rg a.btn.ghost { background: #fff !important; color: var(--rg1) !important; border: 1px solid #e3b9b1 !important; box-shadow: none; }
body.tema-rg button.btn.ghost:hover { background: var(--accent-soft) !important; }
body.tema-rg .btn-update { background: #fff; border-color: #e3b9b1; color: var(--rg1); font-weight: 700; }
body.tema-rg .pilihan button.aktif { background: var(--rg1); border-color: var(--rg1); color: #fff; }
body.tema-rg details.tambah-aju > summary { border-color: var(--rg1); color: var(--rg1); background: #fff7f5; border-radius: 12px; }

/* tabel gaya Accurate */
body.tema-rg table { border-collapse: separate; border-spacing: 0; }
body.tema-rg th { background: #fbe4e0 !important; color: #6b3f47 !important; font-weight: 800; border-bottom: 1px solid #efcdc6 !important; }
body.tema-rg tbody tr:nth-child(even) td { background: #fffafa; }
body.tema-rg tbody tr:hover td { background: #fdeeee !important; }
body.tema-rg td { border-bottom: 1px solid #f6e6e2 !important; }
body.tema-rg .bar-cell .b { background: linear-gradient(90deg, #f9d0cc, #f3b6c4) !important; }
body.tema-rg .pill { border-radius: 999px; font-weight: 700; }

/* jendela & panel melayang */
body.tema-rg .saring-kolom, body.tema-rg .upd-baru { background: #fff !important; border-color: #ecc9c2 !important; border-radius: 14px !important;
  box-shadow: 0 16px 40px -16px rgba(120,60,70,.45) !important; }
body.tema-rg iframe { border-radius: 16px; background: #fdf4f1 !important; }

@media (max-width: 900px) {
  :root.tema-rg { --sisi: 0px; }
  #rgMenuBtn { display: grid; place-items: center; }
  #rgAtas .merek { width: auto; background: none; color: var(--rg1); padding: 0 6px; }
  #rgAtas .merek .logo { background: linear-gradient(135deg, #b76e79, #e6a9a0); color: #fff; }
  #rgAtas .merek small, #rgAtas .kanan .chip.tgl { display: none; }
  #rgAtas .remah { display: none; }
  #rgSisi { width: 280px; transform: translateX(-105%); transition: transform .22s; box-shadow: 10px 0 30px rgba(0,0,0,.15); }
  body.rg-buka #rgSisi { transform: none; }
  body.rg-buka #rgTirai { display: block; position: fixed; inset: var(--atas) 0 0 0; background: rgba(69,41,47,.3); z-index: 54; }
  #rgSpanduk { padding: 14px 16px; } #rgSpanduk .jd { font-size: 19px; } #rgSpanduk .ik { width: 48px; height: 48px; font-size: 26px; }
}
`;

  const HIASAN = '<svg viewBox="0 0 260 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    + '<circle cx="200" cy="30" r="46" fill="#fff" opacity=".16"/><circle cx="245" cy="95" r="34" fill="#fff" opacity=".14"/>'
    + '<g fill="#fff" opacity=".85"><path d="M150 26l3 8 8 3-8 3-3 8-3-8-8-3 8-3z"/><path d="M228 52l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/>'
    + '<path d="M120 84l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/></g>'
    + '<g transform="translate(190 78)"><g fill="#ffd6e0"><circle cx="0" cy="-11" r="9"/><circle cx="10.5" cy="-3.4" r="9"/>'
    + '<circle cx="6.5" cy="9" r="9"/><circle cx="-6.5" cy="9" r="9"/><circle cx="-10.5" cy="-3.4" r="9"/></g><circle r="6" fill="#ffc35c"/></g>'
    + '<g transform="translate(232 24) scale(.6)"><g fill="#fff3c4"><circle cx="0" cy="-11" r="9"/><circle cx="10.5" cy="-3.4" r="9"/>'
    + '<circle cx="6.5" cy="9" r="9"/><circle cx="-6.5" cy="9" r="9"/><circle cx="-10.5" cy="-3.4" r="9"/></g><circle r="6" fill="#f59ab0"/></g></svg>';

  const h = (tag, attrs, html) => { const e = document.createElement(tag); if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]); if (html != null) e.innerHTML = html; return e; };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function modulDari(p) { return MODUL.find((m) => m[3].includes(p)) || ["Lainnya", "✨", "#e3a6b4", [p]]; }

  function pasang(nav) {
    if (document.getElementById("rgSisi")) return;
    const tabs = () => [...nav.querySelectorAll(".tab")];
    const ada = new Set(tabs().map((t) => t.dataset.p));
    const nama = (p) => { const t = nav.querySelector('.tab[data-p="' + p + '"]'); return t ? t.textContent.trim() : p; };
    const lain = [...ada].filter((p) => !MODUL.some((m) => m[3].includes(p)));
    const daftar = MODUL.map((m) => [m[0], m[1], m[2], m[3].filter((p) => ada.has(p))]).filter((m) => m[3].length);
    if (lain.length) daftar.push(["Lainnya", "✨", "#e3a6b4", lain]);

    document.body.classList.add("rg-siap");

    const tgl = new Date().toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    const atas = h("header", { id: "rgAtas" },
      '<button id="rgMenuBtn" type="button" aria-label="Buka menu modul">☰</button>'
      + '<div class="merek"><span class="logo">🌸</span><span>Svarna Dipa<small>PUSAT · PENGAJUAN SALES</small></span></div>'
      + '<div class="remah" id="rgRemah"></div>'
      + '<div class="kanan"><span class="chip tgl">📅 ' + esc(tgl) + '</span></div>');
    const sisi = h("aside", { id: "rgSisi", "aria-label": "Modul" });
    const cari = h("input", { class: "cari", type: "search", placeholder: "Cari menu…", "aria-label": "Cari menu" });
    sisi.appendChild(cari);
    for (const [n, ik, w, ps] of daftar) {
      const m = h("div", { class: "rg-modul", "data-modul": n });
      m.style.setProperty("--warna", w);
      const kepala = h("button", { type: "button" }, '<span class="ik">' + ik + '</span><span>' + esc(n) + '</span><span class="pan">▶</span>');
      const sub = h("div", { class: "rg-sub" });
      for (const p of ps) {
        const buat = (label, ikon, kat) => {
          const b = h("button", { type: "button", "data-p": p }, '<span class="ik">' + ikon + '</span><span>' + esc(label) + '</span>');
          b.addEventListener("click", () => {
            const t = nav.querySelector('.tab[data-p="' + p + '"]');
            if (t) t.click();
            // kategori pengajuan (Kak Intan 27 Nov 2026): halaman menyediakan window.GIO_KAT_AJU
            if (kat !== undefined && typeof window.GIO_KAT_AJU === "function") window.GIO_KAT_AJU(kat);
            document.body.classList.remove("rg-buka");
            window.scrollTo({ top: 0, behavior: "smooth" });
          });
          sub.appendChild(b);
        };
        if (p === "pengajuan") {
          // tiga kategori pengajuan langsung di menu kiri (permintaan Kak Intan/Kogja 27 Nov 2026)
          buat(nama(p), IKON[p] || "•", "");
          buat("Isi posting", "📄", "posting");
          buat("Revisi nota", "✏️", "revisi");
          buat("Kompen", "🏷️", "kompen");
        } else buat(nama(p), IKON[p] || "•");
      }
      kepala.addEventListener("click", () => {
        if (sub.children.length === 1) { sub.querySelector("button").click(); return; }
        m.classList.toggle("buka");
      });
      m.append(kepala, sub);
      sisi.appendChild(m);
    }
    sisi.appendChild(h("div", { class: "hiasan" }, '<span class="besar">🌷✨</span>Semangat hari ini!'));
    cari.addEventListener("input", () => {
      const q = cari.value.trim().toLowerCase();
      sisi.querySelectorAll(".rg-modul").forEach((m) => {
        let cocok = 0;
        m.querySelectorAll(".rg-sub button").forEach((b) => { const ya = !q || b.textContent.toLowerCase().includes(q) || m.dataset.modul.toLowerCase().includes(q); b.hidden = !ya; cocok += ya; });
        m.hidden = !cocok;
        if (q) m.classList.add("buka");
      });
    });
    const tirai = h("div", { id: "rgTirai" });
    tirai.addEventListener("click", () => document.body.classList.remove("rg-buka"));
    document.body.append(atas, sisi, tirai);
    atas.querySelector("#rgMenuBtn").addEventListener("click", () => document.body.classList.toggle("rg-buka"));

    const spanduk = h("div", { id: "rgSpanduk" });
    const sinkron = () => {
      const t = nav.querySelector('.tab[aria-selected="true"]') || tabs()[0];
      if (!t) return;
      const p = t.dataset.p, [mn, mik, mw] = modulDari(p);
      sisi.querySelectorAll(".rg-sub button").forEach((b) => b.classList.toggle("aktif", b.dataset.p === p));
      sisi.querySelectorAll(".rg-modul").forEach((m) => {
        const on = m.dataset.modul === mn;
        m.classList.toggle("aktif", on);
        m.classList.toggle("buka", on);
      });
      document.getElementById("rgRemah").innerHTML = mik + ' ' + esc(mn) + ' <span>›</span> <b>' + esc(t.textContent.trim()) + '</b>';
      spanduk.style.setProperty("--w1", mw);
      spanduk.innerHTML = '<span class="ik">' + (IKON[p] || mik) + '</span><span><span class="md">' + esc(mn) + '</span><br><span class="jd">'
        + esc(t.textContent.trim()) + '</span></span>' + HIASAN;
      const kepala = nav.parentElement.querySelector("header.top");
      if (kepala && spanduk.previousElementSibling !== kepala) kepala.after(spanduk);
    };
    new MutationObserver(sinkron).observe(nav, { subtree: true, attributes: true, attributeFilter: ["aria-selected"] });
    sinkron();

    // ikon kotak angka, dipasang ulang tiap isi tab digambar
    const hiasKpi = () => {
      document.querySelectorAll("#isi .kpi:not([data-ikon])").forEach((k) => {
        const teks = ((k.querySelector(".k") || k).textContent || "").trim();
        const c = IKON_KPI.find(([re]) => re.test(teks));
        k.setAttribute("data-ikon", c ? c[1] : "✨");
      });
    };
    let jadwal = 0;
    new MutationObserver(() => { if (!jadwal) jadwal = requestAnimationFrame(() => { jadwal = 0; hiasKpi(); }); })
      .observe(document.getElementById("isi") || document.body, { childList: true, subtree: true });
    hiasKpi();
  }

  // warna rosegold langsung dipasang (tidak menunggu data ~20 dtk dimuat); menu kiri menyusul begitu tab siap
  const st = document.createElement("style"); st.id = "temaRosegold"; st.textContent = CSS; document.head.appendChild(st);
  if (!document.querySelector('link[href*="family=Nunito"]')) {
    document.head.appendChild(h("link", { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Nunito:wght@500;600;700;800&display=swap" }));
  }
  document.documentElement.classList.add("tema-rg");
  document.body.classList.add("tema-rg");

  const tunggu = setInterval(() => {
    const nav = document.querySelector("#isi nav.tabs");
    if (nav && nav.querySelector('.tab[aria-selected="true"]')) { clearInterval(tunggu); pasang(nav); }
  }, 200);
})();
