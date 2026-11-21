// Bookmark "Isi dari Gio" (17 Nov 2026) - versi tanpa Tampermonkey dari haloai_kirim.user.js.
// Dashboard membuka HaloAI dengan #gio-kirim=<base64 JSON {nomor, teks}>; Kak Intan klik bookmark ini di tab HaloAI.
// Isi: buka Quick Send, isi nomor, Mulai percakapan, buka Balas manual, tempel pesan. TIDAK menekan Kirim.
(async () => {
  const h = location.hash, i = h.indexOf("gio-kirim=");
  const pita = (t, b) => { let p = document.getElementById("gio-pita"); if (!p) { p = document.createElement("div"); p.id = "gio-pita"; document.body.appendChild(p); } p.style.cssText = "position:fixed;left:50%;top:12px;transform:translateX(-50%);z-index:99999;padding:10px 16px;border-radius:10px;font:600 14px system-ui;box-shadow:0 6px 20px rgba(0,0,0,.2);background:" + (b ? "#fde2e1;color:#9b1c1c" : "#e3f6e8;color:#14532d"); p.textContent = t; clearTimeout(p._t); p._t = setTimeout(() => p.remove(), 9000); };
  if (i < 0) { pita("Gio: belum ada pesan dari dashboard. Klik template di dashboard dulu.", 1); return; }
  let d; try { d = JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(h.slice(i + 10)))))); } catch (e) { pita("Gio: data pesan rusak.", 1); return; }
  history.replaceState(null, "", location.pathname + location.search);
  const tidur = (ms) => new Promise((r) => setTimeout(r, ms));
  const lihat = (e) => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== "hidden";
  const tunggu = async (f, ms = 15000) => { const m = Date.now(); for (;;) { const x = f(); if (x) return x; if (Date.now() - m > ms) throw new Error("elemen tidak ketemu"); await tidur(250); } };
  const teks = (re) => { const c = [...document.querySelectorAll("button,[role=menuitem],[role=option],div,span")].filter((e) => lihat(e) && re.test((e.innerText || "").trim()) && (e.innerText || "").trim().length < 60); const e = c.filter((e) => !c.some((x) => x !== e && e.contains(x)))[0]; return e ? (e.closest("[role=menuitem],button,[role=option]") || e) : null; };
  try {
    pita("Gio: membuka chat " + d.nomor + " …");
    let q = null;
    for (let k = 0; k < 20 && !q; k++) { const b = document.querySelector('button[aria-label="Tulis chat baru"]'); if (b) b.click(); await tidur(800); q = teks(/^Quick Send/i); }
    if (!q) throw new Error("menu Quick Send tidak muncul");
    q.click();
    const inp = await tunggu(() => [...document.querySelectorAll("input")].find((x) => lihat(x) && /Masukkan nomor/i.test(x.placeholder || "")));
    inp.focus(); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(inp, d.nomor);
    inp.dispatchEvent(new Event("input", { bubbles: true })); inp.dispatchEvent(new Event("change", { bubbles: true }));
    await tidur(400);
    (await tunggu(() => [...document.querySelectorAll("button")].find((b) => lihat(b) && /Mulai percakapan/i.test(b.innerText || "") && !b.disabled))).click();
    await tidur(1500);
    let ed = [...document.querySelectorAll('[contenteditable="true"]')].find(lihat);
    if (!ed) { const bm = teks(/^Balas manual/i); if (bm) bm.click(); }
    ed = await tunggu(() => [...document.querySelectorAll('[contenteditable="true"]')].find(lihat));
    ed.focus(); if (d.teks) document.execCommand("insertText", false, d.teks);
    pita("Gio: pesan untuk " + d.nomor + " sudah terisi - periksa lalu klik Kirim.");
  } catch (e) {
    try { await navigator.clipboard.writeText(d.teks || ""); } catch (e2) { /* abaikan */ }
    pita("Gio: gagal mengisi otomatis (" + e.message + "). Pesan sudah disalin - tempel di chat " + d.nomor + " (Ctrl+V).", 1);
  }
})();
