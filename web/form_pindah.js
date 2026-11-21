  // Formulir pemindahan versi repo Pengajuan-Sales (Kak Intan 14 Nov 2026): stok barang di SEMUA gudang terlihat,
  // gudang asal & cabang + gudang tujuan bisa dipilih, tanggal pengajuan diisi. Data stok: data/stok_gudang.json
  // (dibuat skrip/bangun.py dari ketersediaan stok Accurate per gudang, tarikan malam).
  // 18 Nov 2026 (Kak Intan): BANYAK BARANG sekali ajukan - tiap baris kode barang + qty di sebelahnya + gudang asal,
  // tombol "+ Tambah barang". Tetap disimpan satu dokumen per barang (field grup sama), jadi bot & server tidak berubah:
  // bot sudah menggabungkan barang dengan gudang asal -> tujuan yang sama ke satu Pemindahan Barang Accurate.
  function formPindah(saranAwal) {
    const f = (id, lbl, inp, wide) => el("label", { for: id, class: wide ? "wide" : null }, lbl, inp);
    const SG = D.stok_gudang || { stok: {}, gudang: {} };
    const opt = (v, t) => el("option", { value: v, text: t });
    const daftar = el("datalist", { id: "pdDaftar" }, D.items.map((i) => el("option", { value: i.item, text: i.nama || "" })));
    const dr = S.pdDraf || (S.pdDraf = {});
    if (!Array.isArray(dr.baris) || !dr.baris.length) dr.baris = [{ item: saranAwal?.item || dr.item || "", qty: saranAwal?.qty || dr.qty || "", asal: dr.asal || "" }];
    const d0 = new Date(), hariIni = new Date(d0 - d0.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    const tgl = el("input", { id: "pdTgl", type: "date", value: dr.tgl || hariIni });
    // JOGJA dibuang 18 Nov 2026 (Kak Intan: "ajukan pemindahan cabang jogja gak usah")
    const cabs = Object.keys(SG.gudang).filter((c) => !["ONLINE", "TRANSIT", "GUDANG BELUM DIPETAKAN", "JOGJA"].includes(c)).sort();
    // 16 Nov 2026 (Kak Intan): cabang tujuan BOLEH cabang mana saja, bukan cuma cabang halaman ini
    const cab = el("select", { id: "pdCabang" }, cabs.map((c) => opt(c, c)));
    const cabAwal = saranAwal?.cabang || dr.cabang || S.kunci || "";
    if (cabs.includes(cabAwal)) cab.value = cabAwal;
    // saringan cabang asal: mempersempit daftar gudang asal semua baris (kosong = semua cabang)
    const cabAsal = el("select", { id: "pdCabAsal" }, opt("", "Semua cabang"), ...cabs.map((c) => opt(c, c)));
    if (cabs.includes(dr.cabAsal)) cabAsal.value = dr.cabAsal;
    const tujuan = el("select", { id: "pdTujuan" });
    const sales = el("input", { id: "pdSales", placeholder: "nama sales yang minta (opsional)", value: dr.sales || "" });
    const cat = el("input", { id: "pdCatatan", placeholder: "untuk toko / program / alasan (opsional)", value: dr.catatan || "" });
    const cabTujuan = () => cab.value || S.kunci || "";
    const KODE = (v) => String(v || "").trim().toUpperCase();
    const angka = (v) => +String(v || "").replace(/[^\d]/g, "");
    const stokItem = (kode) => (SG.stok[kode] || [])
      .filter((r) => r[1] > 0 && (!cabAsal.value || r[2] === cabAsal.value))
      .sort((a, b) => b[1] - a[1]);
    const stokDi = (kode, g) => (stokItem(kode).find(([x]) => x === g) || [0, 0])[1];
    const isiTujuan = () => {
      const gs = SG.gudang[cabTujuan()] || [cabTujuan()];
      const lama = tujuan.value || dr.tujuan;
      tujuan.replaceChildren(...gs.map((g) => opt(g, g)));
      tujuan.value = gs.includes(lama) ? lama : gs[0];
    };
    // gudang asal per baris: yang dipilih sebelumnya kalau masih ada stoknya, lalu gudang JKT, lalu stok terbanyak
    const asalAwal = (b) => {
      const rows = stokItem(KODE(b.item));
      if (rows.some(([g]) => g === b.asal)) return b.asal;
      const jkt = rows.find(([g]) => PINDAH_GUDANG_JKT.includes(g));
      return jkt ? jkt[0] : rows.length ? rows[0][0] : "";
    };
    const LBL = "display:grid;gap:3px;font-size:12px;color:var(--muted);font-weight:600";
    const wadah = el("div", { style: "display:grid;gap:10px" });
    let cek = () => {};
    const terisi = () => dr.baris.filter((b) => KODE(b.item) || String(b.qty || "").trim());
    const gambarBaris = () => {
      wadah.replaceChildren(...dr.baris.map((b, i) => {
        const item = el("input", { list: "pdDaftar", placeholder: "kode barang, mis. PAC09VH", value: b.item || "", "aria-label": "Kode barang " + (i + 1), style: "width:100%" });
        const qty = el("input", { inputmode: "numeric", placeholder: "qty", value: b.qty || "", "aria-label": "Jumlah unit barang " + (i + 1), style: "width:100%" });
        const asal = el("select", { "aria-label": "Gudang asal barang " + (i + 1), style: "width:100%" });
        const ket = el("div", { style: "font-size:12px;grid-column:1 / -1" });
        const hapus = el("button", { class: "btn ghost", type: "button", title: "Hapus baris ini", "aria-label": "Hapus barang " + (i + 1), text: "✕", style: "padding:6px 10px" });
        hapus.disabled = dr.baris.length === 1;
        const segar = () => {
          const kode = KODE(item.value), rows = stokItem(kode);
          b.asal = asalAwal(b);
          asal.replaceChildren(...(rows.length ? rows.map(([g, q, c]) => opt(g, g + " (" + c + ") · " + nf0.format(q))) : [opt("", !kode ? "isi kode dulu" : "stok kosong")]));
          asal.value = b.asal;
          const total = rows.reduce((a, r) => a + r[1], 0);
          ket.replaceChildren(!kode ? "" : !D.itemByNo.get(kode) ? el("span", { class: "down", text: "Kode barang tidak dikenal." })
            : el("span", { class: "muted" }, el("b", { text: namaItem(kode) }), " · total stok " + nf0.format(total) + " unit di " + rows.length + " gudang"
              + (cabAsal.value ? " (cabang " + cabAsal.value + ")" : "") + (b.asal && angka(b.qty) > stokDi(kode, b.asal) ? " · " : ""),
              b.asal && angka(b.qty) > stokDi(kode, b.asal) ? el("span", { class: "down", text: "qty melebihi stok " + b.asal + " (" + nf0.format(stokDi(kode, b.asal)) + ")" }) : ""));
        };
        b._segar = segar;
        item.addEventListener("input", () => { b.item = item.value; b.asal = ""; segar(); cek(); });
        qty.addEventListener("input", () => { b.qty = qty.value; segar(); cek(); });
        asal.addEventListener("change", () => { b.asal = asal.value; segar(); cek(); });
        hapus.addEventListener("click", () => { dr.baris.splice(i, 1); gambarBaris(); cek(); });
        segar();
        // kode | qty | hapus di satu baris (qty tepat di sebelah kode), gudang asal di bawahnya - tetap rapi di HP
        return el("div", { style: "display:grid;grid-template-columns:minmax(0,1fr) 6em auto;gap:6px 8px;align-items:end;padding-bottom:8px;border-bottom:1px dashed var(--line)" },
          el("label", { style: LBL }, (i + 1) + ". Kode barang", item), el("label", { style: LBL }, "Qty", qty), hapus,
          el("label", { style: LBL + ";grid-column:1 / -1" }, "Gudang asal", asal), ket);
      }));
    };
    const tambah = el("button", { class: "btn ghost", type: "button", text: "+ Tambah barang", style: "justify-self:start;margin-top:8px" });
    tambah.addEventListener("click", () => { dr.baris.push({ item: "", qty: "", asal: "" }); gambarBaris(); cek(); const ins = wadah.querySelectorAll("input[list]"); if (ins.length) ins[ins.length - 1].focus(); });
    const simpanDraf = () => Object.assign(dr, { tgl: tgl.value, cabang: cab.value, cabAsal: cabAsal.value, tujuan: tujuan.value, sales: sales.value, catatan: cat.value });
    cabAsal.addEventListener("change", () => { for (const b of dr.baris) if (b._segar) b._segar(); cek(); });
    cab.addEventListener("change", isiTujuan);
    for (const x of [tgl, cabAsal, cab, tujuan, sales, cat]) { x.addEventListener("input", simpanDraf); x.addEventListener("change", simpanDraf); }
    isiTujuan(); gambarBaris();
    const info = el("div", { class: S.pdPesan ? S.pdPesan[0] : "msg", hidden: !S.pdPesan, text: S.pdPesan ? S.pdPesan[1] : "" });
    const btn = el("button", { class: "btn", type: "button", text: "Ajukan pemindahan" });
    btn.addEventListener("click", async () => {
      const salah = (t) => { info.hidden = false; info.className = "msg"; info.textContent = t; S.pdPesan = ["msg", t]; };
      if (!tgl.value) return salah("Isi tanggal pengajuan.");
      const isi = terisi();
      if (!isi.length) return salah("Isi minimal satu barang.");
      for (const [i, b] of isi.entries()) {
        const kode = KODE(b.item), n = angka(b.qty), ke = "Barang ke-" + (i + 1) + (kode ? " (" + kode + ")" : "") + ": ";
        if (!D.itemByNo.get(kode)) return salah(ke + "pilih kode barang yang ada di daftar.");
        if (!(n > 0)) return salah(ke + "jumlah unit wajib diisi.");
        if (!b.asal) return salah(ke + "tidak ada stoknya di gudang mana pun.");
        if (b.asal === tujuan.value) return salah(ke + "gudang asal dan gudang tujuan tidak boleh sama.");
        if (n > stokDi(kode, b.asal)) return salah(ke + "stok " + b.asal + " hanya " + nf0.format(stokDi(kode, b.asal)) + " unit - kurangi jumlah atau pilih gudang lain.");
      }
      const kunci = isi.map((b) => KODE(b.item) + "|" + b.asal);
      const dobel = kunci.find((k, i) => kunci.indexOf(k) !== i);
      if (dobel) return salah("Barang " + dobel.split("|")[0] + " dari gudang yang sama ditulis dua kali - gabungkan jumlahnya di satu baris.");
      const grup = "pd" + Date.now().toString(36);
      btn.disabled = true; tambah.disabled = true;
      const ok = [], gagal = [];
      for (const b of isi) {
        const kode = KODE(b.item), n = angka(b.qty);
        const sukses = await simpanPindah(null, { tgl: tgl.value, item: kode, nama: namaItem(kode), merk: brandItem(kode), cabang: cabTujuan(), qty: n,
          gudang_asal: b.asal, gudang_tujuan: tujuan.value, sales: sales.value.trim(), catatan: cat.value.trim(), grup, grup_jumlah: isi.length }, null);
        (sukses ? ok : gagal).push(b);
      }
      btn.disabled = false; tambah.disabled = false;
      info.hidden = false; info.className = gagal.length ? "msg" : "msg ok";
      info.textContent = (ok.length ? "Tersimpan " + ok.length + " barang → " + tujuan.value + ": " + ok.map((b) => KODE(b.item) + " " + nf0.format(angka(b.qty)) + " (" + b.asal + ")").join(", ") + "." : "")
        + (gagal.length ? " TIDAK tersimpan (" + (S.pdGalat || "penyimpanan belum tersambung") + "): " + gagal.map((b) => KODE(b.item)).join(", ") + " - masih di formulir, coba Ajukan lagi." : "");
      S.pdPesan = [info.className, info.textContent];
      dr.baris = gagal.length ? gagal : [{ item: "", qty: "", asal: "" }];
      if (!gagal.length) { cat.value = ""; simpanDraf(); }
      gambarBaris(); cek();
    });
    // 16 Nov 2026 (Kak Intan): tampilan bergaya Retur - langkah bernomor, pilihan berupa tombol, tombol kirim melekat di bawah
    const GAYA_LBL = "display:grid;gap:6px;font-size:12px;color:var(--muted);font-weight:600";
    const L1 = langkahKotak(1, "Barang, qty & gudang asal", el("div", { class: "lbl", style: GAYA_LBL }, "Cabang asal (saringan)", pilihanTombol(cabAsal), cabAsal),
      wadah, tambah, el("div", { class: "muted", style: "font-size:12px", text: "Stok per " + (SG.dibuat || "-") }));
    const L2 = langkahKotak(2, "Tujuan", el("div", { class: "lbl", style: GAYA_LBL }, "Cabang tujuan", pilihanTombol(cab), cab),
      el("div", { class: "lbl", style: GAYA_LBL }, "Gudang tujuan", pilihanTombol(tujuan), tujuan));
    const L3 = langkahKotak(3, "Tanggal & keterangan", el("div", { class: "formgrid" }, f("pdTgl", "Tanggal pengajuan", tgl),
      f("pdSales", "Sales", sales), f("pdCatatan", "Catatan", cat, true)));
    cab.addEventListener("change", () => tujuan.dispatchEvent(new Event("change")));
    cek = () => {
      const isi = terisi();
      L1.tandai(isi.length > 0 && isi.every((b) => !!D.itemByNo.get(KODE(b.item)) && angka(b.qty) > 0 && !!b.asal && angka(b.qty) <= stokDi(KODE(b.item), b.asal)));
      L2.tandai(!!tujuan.value && !isi.some((b) => b.asal === tujuan.value));
      L3.tandai(!!tgl.value);
      btn.textContent = "Ajukan pemindahan" + (isi.length > 1 ? " (" + isi.length + " barang)" : "");
    };
    for (const x of [tgl, cabAsal, cab, tujuan]) { x.addEventListener("input", cek); x.addEventListener("change", cek); }
    btn.className = "btn lebar"; cek();
    return el("div", { class: "form-retur", style: "margin-top:0" }, daftar, L1.node, L2.node, L3.node, el("div", { class: "lekat-bawah" }, btn, info));
  }
