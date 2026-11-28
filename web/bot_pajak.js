  // 18 Nov 2026 (Kak Intan): "kumpulan pencet-pencet jalankan bot" di tab Dashboard pajak.
  // Tombol menulis perbarui/bot_pajak {pt, tahun, dari, sampai, banding, diminta, oleh}; PC/Mac mini
  // (AGEN PPH 23 KREDIT PAJAK\bot\panel_bot.py, periksa tiap 30 detik) menjalankan bot lalu menulis
  // perbarui/bot_pajak_status {status, pt, masa, langkah, hasil, mulai, selesai, untuk}.
  // Login & ganti profil Coretax tetap Kak Intan - bot berhenti dengan status "perlu" kalau belum siap.
  const BOT_PT = ["SVARNA DIPA", "GEMA SARANA TRANSPORTASI", "RAJAWALI ADHIRAJASA PERKASA", "WINROS SUKSES INDONESIA", "LAROSE ARTA SVARNA", "YUSUF MULYONO"];
  const BOT_BLN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
  function kartuBotPajak() {
    const now = new Date(), lalu = now.getMonth() === 0 ? 12 : now.getMonth();
    const opsiEl = (arr, val) => arr.map((t, i) => el("option", { value: val ? String(i + 1) : t, text: t }));
    const pt = el("select", { class: "inp", style: "min-width:230px" }, ...opsiEl(BOT_PT));
    const tahun = el("input", { class: "inp", type: "number", value: String(now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()), style: "width:90px" });
    const dari = el("select", { class: "inp" }, ...opsiEl(BOT_BLN, true));
    const sampai = el("select", { class: "inp" }, ...opsiEl(BOT_BLN, true));
    dari.value = "1"; sampai.value = String(lalu);
    const banding = el("input", { type: "checkbox" }); banding.checked = true;
    const tombol = el("button", { class: "btn", type: "button", text: "▶ Jalankan bot download PPh 23" });
    const lencana = el("span", { class: "pill mut", text: "siap" });
    const info = el("span", { class: "muted", style: "font-size:12.5px" });
    const hasil = el("pre", { style: "white-space:pre-wrap;margin:8px 0 0;font:13px/1.45 inherit;background:#0d1217;border:1px solid #26313b;border-radius:10px;padding:10px", hidden: true });
    const lbl = (t, x) => el("label", { style: "display:grid;gap:4px;font-size:12px", class: "muted" }, t, x);
    // 19 Nov 2026: jadwal harian 12.00 semua jenis pajak semua PT (panel_bot.py menulis perbarui/bot_harian_status)
    const harian = el("div", { class: "muted", style: "font-size:12.5px;margin-top:8px" });
    const harianRinci = el("pre", { style: "white-space:pre-wrap;margin:6px 0 0;font:12.5px/1.45 inherit;background:#0d1217;border:1px solid #26313b;border-radius:10px;padding:10px;max-height:260px;overflow:auto", hidden: true });
    const gambarHarian = (h) => {
      if (!h || !h.tanggal) { harian.textContent = "Jadwal harian: tiap hari jam 12.00, semua jenis pajak semua PT (belum pernah jalan)."; harianRinci.hidden = true; return; }
      const label = { berjalan: "sedang jalan", selesai: "selesai", perlu: "perlu Kak Intan", gagal: "ada yang gagal" }[h.status] || h.status;
      harian.textContent = "Jadwal harian 12.00 · " + h.tanggal + " · " + label + (h.status === "berjalan" && h.langkah ? " · " + h.langkah : "");
      const r = (h.hasil || []).map((x) => {
        const baris = String(x.hasil || "").split("\n").filter((l) => /HASIL|PERLU/.test(l)).slice(-1)[0];
        return (x.pt !== "-" ? x.pt.replace(/^PT /, "") + " · " : "") + x.tugas + ": " + x.status + (baris ? "\n   " + baris : "");
      });
      harianRinci.textContent = r.join("\n"); harianRinci.hidden = !r.length;
    };
    let st = {}, minta = null;
    const jam = (x) => x ? new Date(x).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "";
    function gambar() {
      const antre = minta && minta.diminta && (!st.untuk || st.untuk < minta.diminta);
      const jalan = antre || st.status === "berjalan";
      const peta = { berjalan: ["sedang jalan", "warn"], selesai: ["selesai", "ok"], perlu: ["perlu Kak Intan", "bad"], gagal: ["gagal", "bad"], dihentikan: ["dihentikan", "bad"] };
      const [t, k] = antre ? ["menunggu PC", "mut"] : (peta[st.status] || ["siap", "mut"]);
      lencana.textContent = t; lencana.className = "pill " + k;
      tombol.disabled = !!jalan;
      tombol.textContent = jalan ? "⟳ Bot sedang jalan…" : "▶ Jalankan bot download PPh 23";
      const ket = antre ? "Permintaan " + jam(minta.diminta) + " untuk " + minta.pt + " - menunggu PC mengambil (maks ±1 menit)."
        : st.pt ? st.pt + " · masa " + st.masa + (st.mulai ? " · mulai " + jam(st.mulai) : "") + (st.selesai ? " · selesai " + jam(st.selesai) : "") : "Belum ada bot yang dijalankan dari sini.";
      info.textContent = ket + (st.langkah && jalan && !antre ? " · " + st.langkah : "");
      hasil.hidden = !st.hasil || antre; hasil.textContent = st.hasil || "";
    }
    tombol.onclick = async () => {
      if (+dari.value > +sampai.value) { alert('Masa "dari" harus sebelum "sampai".'); return; }
      if (!confirm("Jalankan bot download PPh 23 lawan transaksi untuk " + pt.value + "?\n\nPastikan Coretax di PC sudah login dengan profil " + pt.value + ".")) return;
      if (!S.db) { alert("Penyimpan belum tersambung - muat ulang halaman lalu coba lagi."); return; }
      minta = { pt: pt.value, tahun: +tahun.value, dari: +dari.value, sampai: +sampai.value, banding: banding.checked, diminta: new Date().toISOString(), oleh: S.uid || null };
      gambar();
      try { await S.db.doc("perbarui/bot_pajak").set(minta); }
      catch (e) { minta = null; alert("Permintaan tidak terkirim (" + (e.message || e) + ")"); gambar(); }
    };
    let pasang = false;
    const sambung = () => {
      if (pasang || !S.db) return;
      pasang = true;
      S.db.collection("perbarui").onSnapshot((snap) => {
        const a = snap.docs.find((x) => x.id === "bot_pajak_status"), b = snap.docs.find((x) => x.id === "bot_pajak");
        st = a ? a.data() : {}; minta = b ? b.data() : minta; gambar();
        const c = snap.docs.find((x) => x.id === "bot_harian_status"); gambarHarian(c ? c.data() : null);
      });
    };
    sambung(); const tunggu = setInterval(() => { sambung(); if (pasang) clearInterval(tunggu); }, 1500);
    gambar(); gambarHarian(null);
    return el("div", { class: "card", style: "margin-bottom:12px" },
      el("div", { style: "display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap" },
        el("b", { text: "Bot pajak · Download PPh 23 lawan transaksi" }), lencana),
      el("div", { class: "muted", style: "font-size:12.5px;margin:4px 0 10px", text: "Tarik bupot PPh 23 yang diterima dari Coretax → arsip PDF ke Drive → rekap → banding Accurate → bersihkan Downloads. Sebelum menekan: login Coretax di PC bot dan pilih profil PT yang sama." }),
      el("div", { style: "display:flex;gap:10px;align-items:end;flex-wrap:wrap" },
        lbl("PT", pt), lbl("Tahun", tahun), lbl("Masa dari", dari), lbl("Masa sampai", sampai),
        el("label", { style: "display:flex;gap:6px;align-items:center;font-size:13px" }, banding, "banding Accurate"), tombol),
      el("div", { style: "margin-top:8px" }, info), hasil, harian, harianRinci);
  }
