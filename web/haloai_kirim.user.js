// ==UserScript==
// @name         Gio - Kirim template dashboard ke HaloAI
// @namespace    svarnadipa-gio
// @version      1.0
// @description  Dari dashboard Pengajuan-Sales: buka Quick Send HaloAI, isi nomor toko & pesan template. TIDAK menekan Kirim - Kak Intan yang menekan.
// @match        https://www.haloai.co.id/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==
// Dibuat Gio 17 Nov 2026 (permintaan Kak Intan). Dashboard membuka https://www.haloai.co.id/#gio-kirim=<base64 JSON {nomor, teks}>.
// Skrip ini: klik "Tulis chat baru" -> "Quick Send" -> isi nomor -> "Mulai percakapan" -> buka "Balas manual" -> tempel pesan.
// Pesan TIDAK dikirim otomatis. Kalau tampilan HaloAI berubah dan skrip gagal, pesannya disalin ke clipboard sebagai cadangan.
(function () {
  "use strict";
  const KUNCI = "gio-kirim=";
  const tunggu = (cari, ms = 15000) => new Promise((ok, gagal) => {
    const mulai = Date.now();
    (function cek() {
      const x = cari();
      if (x) return ok(x);
      if (Date.now() - mulai > ms) return gagal(new Error("elemen tidak ketemu"));
      setTimeout(cek, 250);
    })();
  });
  // popover HaloAI memakai position:fixed (offsetParent null) -> pakai getClientRects
  const terlihat = (e) => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== "hidden";
  const klik = (e) => e.click();
  // elemen terdalam yang teksnya cocok, lalu naik ke item menu / tombol terdekat (yang bisa diklik)
  const tombolTeks = (re) => {
    const cocok = [...document.querySelectorAll("button, [role=menuitem], [role=option], div, span")].filter((e) => terlihat(e) && re.test((e.innerText || "").trim()) && (e.innerText || "").trim().length < 60);
    const dalam = cocok.filter((e) => !cocok.some((x) => x !== e && e.contains(x)));
    const e = dalam[0];
    return e ? (e.closest("[role=menuitem], button, [role=option]") || e) : null;
  };
  const isiInput = (inp, nilai) => {
    const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
    set.call(inp, nilai);
    inp.dispatchEvent(new Event("input", { bubbles: true }));
    inp.dispatchEvent(new Event("change", { bubbles: true }));
  };
  const pita = (teks, buruk) => {
    let p = document.getElementById("gio-pita");
    if (!p) { p = document.createElement("div"); p.id = "gio-pita"; document.body.appendChild(p); }
    p.style.cssText = "position:fixed;left:50%;top:12px;transform:translateX(-50%);z-index:99999;padding:10px 16px;border-radius:10px;font:600 14px system-ui;box-shadow:0 6px 20px rgba(0,0,0,.2);background:" + (buruk ? "#fde2e1;color:#9b1c1c" : "#e3f6e8;color:#14532d");
    p.textContent = teks;
    clearTimeout(p._t); p._t = setTimeout(() => p.remove(), 9000);
  };
  async function jalankan(nomor, teks) {
    pita("Gio: membuka chat " + nomor + " …");
    // halaman HaloAI baru dimuat: tombol sudah ada tapi belum bereaksi -> klik ulang sampai menu Quick Send muncul
    let quick = null;
    for (let i = 0; i < 20 && !quick; i++) {
      const b = document.querySelector('button[aria-label="Tulis chat baru"]');
      if (b) klik(b);
      await new Promise((r) => setTimeout(r, 800));
      quick = tombolTeks(/^Quick Send/i);
    }
    if (!quick) throw new Error("menu Quick Send tidak muncul");
    klik(quick);
    const inp = await tunggu(() => [...document.querySelectorAll("input")].find((i) => terlihat(i) && /Masukkan nomor/i.test(i.placeholder || "")));
    inp.focus(); isiInput(inp, nomor);
    await new Promise((r) => setTimeout(r, 400));
    const mulai = await tunggu(() => [...document.querySelectorAll("button")].find((b) => terlihat(b) && /Mulai percakapan/i.test(b.innerText || "") && !b.disabled));
    klik(mulai);
    // composer bisa tertutup ("Balas manual ^")
    await new Promise((r) => setTimeout(r, 1500));
    let ed = [...document.querySelectorAll('[contenteditable="true"]')].find(terlihat);
    if (!ed) { const bm = tombolTeks(/^Balas manual/i); if (bm) klik(bm); }
    ed = await tunggu(() => [...document.querySelectorAll('[contenteditable="true"]')].find(terlihat));
    ed.focus();
    document.execCommand("insertText", false, teks);
    pita("Gio: pesan untuk " + nomor + " sudah terisi - periksa lalu klik Kirim.");
  }
  async function cek() {
    const h = location.hash, i = h.indexOf(KUNCI);
    if (i < 0) return;
    let d;
    try { d = JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(h.slice(i + KUNCI.length)))))); } catch (e) { return; }
    history.replaceState(null, "", location.pathname + location.search);
    try { await jalankan(String(d.nomor || ""), String(d.teks || "")); }
    catch (e) {
      try { await navigator.clipboard.writeText(d.teks || ""); } catch (e2) { /* abaikan */ }
      pita("Gio: gagal mengisi otomatis (" + e.message + "). Pesan sudah disalin - buka chat " + d.nomor + " lalu tempel (Ctrl+V).", true);
    }
  }
  window.addEventListener("hashchange", cek);
  cek();
})();
