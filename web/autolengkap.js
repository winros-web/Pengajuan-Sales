// Pencarian barang / toko yang langsung mengikuti ketikan (Kak Intan 14 Nov 2026: datalist bawaan browser
// lambat & tidak ikut berubah - ketik "7bey" yang muncul masih hasil "5bey").
// Semua <input list="..."> diganti otomatis: saran disaring tiap ketikan, cocok di tengah kode ("5bey" -> AHA5BEY),
// kode yang diawali ketikan tampil paling atas. Panah atas/bawah + Enter, Esc menutup. Nilai input tetap teks biasa,
// jadi kode halaman lain tidak berubah.
(function () {
  const MAKS = 40;
  const norm = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  const cache = new Map();
  let kotak = null, aktif = null, pilihan = [], idx = -1;

  function opsi(id) {
    const dl = document.getElementById(id);
    if (!dl) return [];
    const c = cache.get(id);
    if (c && c.n === dl.childElementCount && c.dl === dl) return c.isi;
    const isi = [...dl.options].map((o) => { const v = o.value, l = o.label && o.label !== v ? o.label : (o.text && o.text !== v ? o.text : "");
      return { v, l, nv: norm(v), nl: norm(l) }; });
    cache.set(id, { dl, n: dl.childElementCount, isi });
    return isi;
  }
  function saring(id, q) {
    const n = norm(q), semua = opsi(id);
    if (!n) return semua.slice(0, MAKS);
    const a = [], b = [], c = [];
    for (const o of semua) {
      if (o.nv.startsWith(n)) a.push(o); else if (o.nv.includes(n)) b.push(o); else if (o.nl.includes(n)) c.push(o);
      if (a.length >= MAKS) break;
    }
    return a.concat(b, c).slice(0, MAKS);
  }
  function tutup() { if (kotak) kotak.hidden = true; idx = -1; }
  function pakai(o) {
    if (!aktif || !o) return;
    aktif.value = o.v;
    aktif.dispatchEvent(new Event("input", { bubbles: true }));
    aktif.dispatchEvent(new Event("change", { bubbles: true }));
    tutup();
  }
  function tandai() {
    [...kotak.children].forEach((d, i) => { d.style.background = i === idx ? "rgba(120,170,220,.28)" : ""; });
    if (idx >= 0 && kotak.children[idx]) kotak.children[idx].scrollIntoView({ block: "nearest" });
  }
  function tampil(inp) {
    if (!kotak) {
      kotak = document.createElement("div");
      kotak.setAttribute("role", "listbox");
      kotak.style.cssText = "position:fixed;z-index:9999;max-height:320px;overflow:auto;background:#1b232b;color:#e6ecf1;" +
        "border:1px solid rgba(255,255,255,.18);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.45);font-size:14px;padding:4px 0";
      kotak.addEventListener("mousedown", (e) => e.preventDefault());
      document.body.appendChild(kotak);
    }
    aktif = inp;
    pilihan = saring(inp.dataset.daftar, inp.value);
    kotak.replaceChildren(...pilihan.map((o, i) => {
      const d = document.createElement("div");
      d.setAttribute("role", "option");
      d.style.cssText = "padding:6px 12px;cursor:pointer;line-height:1.25";
      const k = document.createElement("div"); k.textContent = o.v; k.style.fontWeight = "600";
      d.appendChild(k);
      if (o.l) { const s = document.createElement("div"); s.textContent = o.l; s.style.cssText = "font-size:12px;opacity:.75"; d.appendChild(s); }
      d.addEventListener("click", () => pakai(o));
      d.addEventListener("mouseenter", () => { idx = i; tandai(); });
      return d;
    }));
    if (!pilihan.length) { const d = document.createElement("div"); d.textContent = "tidak ada yang cocok"; d.style.cssText = "padding:6px 12px;opacity:.6"; kotak.appendChild(d); }
    const r = inp.getBoundingClientRect();
    kotak.style.left = r.left + "px";
    kotak.style.width = Math.max(r.width, 280) + "px";
    const bawah = window.innerHeight - r.bottom;
    if (bawah < 200 && r.top > bawah) { kotak.style.top = ""; kotak.style.bottom = (window.innerHeight - r.top + 4) + "px"; }
    else { kotak.style.bottom = ""; kotak.style.top = (r.bottom + 4) + "px"; }
    kotak.hidden = false; idx = -1;
  }
  function pasang(inp) {
    if (inp.dataset.daftar) return;
    inp.dataset.daftar = inp.getAttribute("list");
    inp.removeAttribute("list");
    inp.setAttribute("autocomplete", "off");
    inp.addEventListener("input", (e) => { if (e.isTrusted) tampil(inp); });
    inp.addEventListener("focus", () => tampil(inp));
    inp.addEventListener("blur", () => setTimeout(() => { if (aktif === inp) tutup(); }, 150));
    inp.addEventListener("keydown", (e) => {
      if (!kotak || kotak.hidden || aktif !== inp) return;
      if (e.key === "ArrowDown") { idx = Math.min(idx + 1, pilihan.length - 1); tandai(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { idx = Math.max(idx - 1, 0); tandai(); e.preventDefault(); }
      else if (e.key === "Enter" && idx >= 0) { pakai(pilihan[idx]); e.preventDefault(); }
      else if (e.key === "Escape") tutup();
    });
  }
  const pindai = (n) => {
    if (n.nodeType !== 1) return;
    if (n.matches && n.matches("input[list]")) pasang(n);
    if (n.querySelectorAll) n.querySelectorAll("input[list]").forEach(pasang);
  };
  new MutationObserver((ms) => { for (const m of ms) m.addedNodes.forEach(pindai); }).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener("scroll", (e) => { if (e.target !== kotak && kotak && !kotak.hidden && aktif) tampil(aktif); }, true);
  window.addEventListener("resize", tutup);
  document.addEventListener("DOMContentLoaded", () => pindai(document.body));
})();
