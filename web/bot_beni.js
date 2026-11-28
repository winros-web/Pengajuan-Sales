  // 18 Nov 2026 (Kak Intan): bot kedua di tab Dashboard pajak - BENI (Bot Billing & NTPN).
  // Tombol menulis perbarui/bot_beni {pt: [..], uji, diminta, oleh}; PC Kak Intan
  // (AGEN BILLING NTPN\bot\beni_tombol.py, periksa tiap 20 detik) menjalankan bot\beni.py:
  // filing billing+BPN dari folder Drive "BELUM DI MASUKAN KE FILENYA" -> rekap Excel -> ekualisasi buku besar,
  // lalu menulis perbarui/bot_beni_status {status, ditangani, mulai, selesai, pt, uji, ringkas, laporan}.
  // Yang janggal tidak dipindah bot, hanya dilaporkan di kartu ini.
  const BENI_PT = [["SVARNA", "PT Svarna Dipa"], ["GEMA", "PT Gema Sarana Transportasi"], ["RAJAWALI", "PT Rajawali Adhirajasa Perkasa"],
    ["WINROS", "PT Winros Sukses Indonesia"], ["YUSUF", "Yusuf Mulyono"], ["DIANA", "Diana Mulya"]];
  function kartuBotBeni() {
    const cek = BENI_PT.map(([v, t]) => { const c = el("input", { type: "checkbox", value: v }); c.checked = true; return [c, t]; });
    const semua = el("input", { type: "checkbox" }); semua.checked = true;
    semua.onchange = () => cek.forEach(([c]) => { c.checked = semua.checked; });
    cek.forEach(([c]) => { c.onchange = () => { semua.checked = cek.every(([x]) => x.checked); }; });
    const uji = el("input", { type: "checkbox" });
    const tombol = el("button", { class: "btn", type: "button", text: "▶ Jalankan BENI" });
    const lencana = el("span", { class: "pill mut", text: "siap" });
    const info = el("span", { class: "muted", style: "font-size:12.5px" });
    const hasil = el("div", { style: "display:grid;gap:8px;margin-top:8px" });
    const kotak = (c, t) => el("label", { style: "display:flex;gap:6px;align-items:center;font-size:13px" }, c, t);
    let st = {}, minta = null;
    const jam = (x) => x ? new Date(x).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "";
    const tabel = (judul, kolom, baris) => !baris || !baris.length ? null : el("div", null,
      el("div", { class: "muted", style: "font-size:12.5px;margin-bottom:4px", text: judul + " (" + baris.length + ")" }),
      el("div", { style: "overflow:auto;max-height:22rem" }, el("table", { style: "width:100%;border-collapse:collapse;font-size:12.5px" },
        el("thead", null, el("tr", null, kolom.map(([h, , kanan]) => el("th", { scope: "col", style: "text-align:" + (kanan ? "right" : "left") + ";padding:4px 8px;border-bottom:1px solid #26313b", class: "muted", text: h })))),
        el("tbody", null, baris.map((r) => el("tr", null, kolom.map(([, f, kanan]) => el("td", { style: "padding:4px 8px;border-bottom:1px solid #1d262f;vertical-align:top;text-align:" + (kanan ? "right" : "left"), text: String(f(r) ?? "") }))))))));
    function gambar() {
      const antre = minta && minta.diminta && minta.diminta !== st.ditangani;
      const jalan = antre || st.status === "berjalan";
      const peta = { berjalan: ["sedang jalan", "warn"], selesai: ["selesai", "ok"], galat: ["gagal", "bad"] };
      const janggal = ((st.laporan || {}).janggal || []).length;
      const [t, k] = antre ? ["menunggu PC", "mut"] : st.status === "selesai" && janggal ? ["selesai · " + janggal + " janggal", "warn"] : (peta[st.status] || ["siap", "mut"]);
      lencana.textContent = t; lencana.className = "pill " + k;
      tombol.disabled = !!jalan;
      tombol.textContent = jalan ? "⟳ BENI sedang jalan…" : "▶ Jalankan BENI";
      const lama = antre ? (Date.now() - new Date(minta.diminta).getTime()) / 60000 : 0;
      info.textContent = antre ? "Permintaan " + jam(minta.diminta) + " (" + (minta.pt || []).join(", ") + ")" + (lama > 10 ? " belum diambil lebih dari 10 menit - pastikan PC Kak Intan menyala." : " - menunggu PC mengambil (maks ±1 menit).")
        : st.status === "berjalan" ? "Berjalan sejak " + jam(st.mulai) + " · " + (st.pt || []).join(", ") + (st.uji ? " (uji)" : "")
        : st.selesai ? "Terakhir " + jam(st.selesai) + " · " + (st.ringkas || "") : "Belum pernah dijalankan dari sini.";
      const L = st.laporan || {};
      hasil.replaceChildren(...(antre || jalan ? [] : [
        tabel("Difiling ke Drive" + (L.uji ? " - RENCANA, belum dipindah (mode uji)" : ""), [["PT", (r) => r.pt], ["Nama berkas", (r) => r.jadi], ["Folder", (r) => r.folder],
          ["Rekap No", (r) => (r.rekap_no || []).join(", ")], ["Nominal", (r) => rp(r.nominal), true]], L.difiling),
        tabel("Janggal - tetap di kotak masuk, perlu dicek Kak Intan", [["Berkas", (r) => r.berkas], ["Alasan", (r) => r.alasan]], L.janggal),
      ].filter(Boolean)));
    }
    tombol.onclick = async () => {
      const pt = cek.filter(([c]) => c.checked).map(([c]) => c.value);
      if (!pt.length) { alert("Pilih minimal satu PT."); return; }
      if (!uji.checked && !confirm("Jalankan BENI untuk " + pt.join(", ") + "?\n\nBerkas billing & BPN di folder Drive \"BELUM DI MASUKAN KE FILENYA\" akan dipindah ke folder PT-nya, ditambahkan ke rekap Excel, lalu diekualisasi.")) return;
      if (!S.db) { alert("Penyimpan belum tersambung - muat ulang halaman lalu coba lagi."); return; }
      minta = { pt, uji: uji.checked, diminta: new Date().toISOString(), oleh: S.uid || null };
      gambar();
      try { await S.db.doc("perbarui/bot_beni").set(minta); }
      catch (e) { minta = null; alert("Permintaan tidak terkirim (" + (e.message || e) + ")"); gambar(); }
    };
    let pasang = false;
    const sambung = () => {
      if (pasang || !S.db) return;
      pasang = true;
      S.db.collection("perbarui").onSnapshot((snap) => {
        const a = snap.docs.find((x) => x.id === "bot_beni_status"), b = snap.docs.find((x) => x.id === "bot_beni");
        st = a ? a.data() : {}; minta = b ? b.data() : minta; gambar();
      });
    };
    sambung(); const tunggu = setInterval(() => { sambung(); if (pasang) clearInterval(tunggu); }, 1500);
    gambar();
    return el("div", { class: "card", style: "margin-bottom:12px" },
      el("div", { style: "display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap" },
        el("b", { text: "BENI · Bot Billing & NTPN" }), lencana),
      el("div", { class: "muted", style: "font-size:12.5px;margin:4px 0 10px", text: "Folder Drive \"BELUM DI MASUKAN KE FILENYA\" → filing billing & BPN ke folder PT (dibaca isinya, dipasangkan lewat kode billing) → rekap Excel → ekualisasi buku besar (Svarna dari Accurate). Yang janggal tidak dipindah, hanya dilaporkan." }),
      el("div", { style: "display:flex;gap:6px 16px;flex-wrap:wrap;align-items:center" }, kotak(semua, el("b", { text: "Semua" })), ...cek.map(([c, t]) => kotak(c, t))),
      el("div", { style: "display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px" }, tombol, kotak(uji, "uji dulu (tampilkan rencana, tidak memindah apa pun)")),
      el("div", { style: "margin-top:8px" }, info), hasil);
  }
