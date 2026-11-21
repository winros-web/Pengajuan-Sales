    // Harga final pemindahan (Kak Intan 14 Nov 2026) - HANYA halaman pusat (data/pricelist_pindah.json tidak dikirim ke
    // halaman cabang; penyimpan juga membuang field harga untuk cabang). Harga = isian pusat (harga_modal) > harga yang
    // dipakai bot di keterangan IT (harga_it) > pricelist bulan terbaru (Aqua/Haier harga bayar, Polytron toko bayar -3%,
    // Palembang -4%, Miyako PL exc PPN, Maspion PL).
    const plPd = (p) => {
      const P = D.pricelist_pindah, r = P && (P.harga || {})[p.item];
      if (!r) return null;
      let h = +r.harga;
      if (r.merk === "POLYTRON") h *= String(p.cabang || "").toUpperCase() === "PALEMBANG" ? 0.96 : 0.97;
      return { harga: Math.round(h), ket: r.merk + " · " + r.sumber + " · " + (P.bulan || "") + (r.merk === "POLYTRON" ? " · toko bayar " + nf0.format(r.harga) + (String(p.cabang).toUpperCase() === "PALEMBANG" ? " −4%" : " −3%") : "") };
    };
    const gudangCab = (() => {
      const m = new Map(), SG = D.stok_gudang || {};
      for (const [c, gs] of Object.entries(SG.gudang || {})) for (const g of gs) if (!m.has(g)) m.set(g, c);
      for (const rows of Object.values(SG.stok || {})) for (const [g, , c] of rows) if (!m.has(g)) m.set(g, c);
      return (g) => m.get(g) || g || "?";
    })();
    // Summary per bulan untuk tarik dana (Kak Intan 17 Nov 2026): SEMUA pemindahan di Accurate (data/pindah_itjson, 60 hari
    // terakhir - Okt & Nov ikut), bukan hanya yang dibuat lewat web. Harga: isian/revisi pusat untuk baris yang ada di daftar
    // web, selain itu pricelist bulan terbaru menurut cabang tujuan. Saringan: bulan, gudang asal, gudang tujuan.
    // Gudang yang TIDAK ikut hitungan tarik dana (Kak Intan 18 Nov 2026: "yang retur dan online, service gak usah
    // dimasukin"), dan pemindahan sesama cabang (mis. DAANMOGOT -> LAKSANA, dua-duanya Jakarta) juga tidak ditarik dananya.
    const GUDANG_LUAR = /RETUR|SERVICE|ONLINE|TRANSIT|BERES/i;
    // gudang toko online (JDID, LOTTE, BLIBLI FDB, GUDANG TITIPAN, ...) namanya tidak memuat kata "ONLINE",
    // jadi disaring lewat cabangnya juga
    const CABANG_LUAR = ["ONLINE", "TRANSIT", "GUDANG BELUM DIPETAKAN"];
    const ikutTarikDana = (r) => !GUDANG_LUAR.test(r.gudang_asal || "") && !GUDANG_LUAR.test(r.gudang_tujuan || "")
      && !CABANG_LUAR.includes(r.cabAsal) && !CABANG_LUAR.includes(r.cabTuj) && r.cabAsal !== r.cabTuj;
    // harga yang diisi tangan di dashboard untuk kode yang tidak ada di pricelist (koleksi db harga_pindah)
    const kunciHargaPd = (item, cab) => String(item + "|" + cab).replace(/[^A-Za-z0-9|]+/g, "_").slice(0, 90);
    const hargaIsian = (item, cab) => {
      const r = (S.hargaPindah || {})[kunciHargaPd(item, cab)];
      return r && +r.harga > 0 ? +r.harga : 0;
    };
    const inputHargaPd = (item, cab, harga, asal) => {
      const info = el("span", { class: "muted", role: "status", style: "font-size:11px" });
      if (S.canWrite === false || !S.db) return el("span", { title: asal || "", text: harga ? nf0.format(harga) : "-" });
      const inp = el("input", { class: "tgt", style: "width:8em", inputmode: "numeric", title: asal || "",
        value: harga ? nf0.format(harga) : "", placeholder: "isi harga", "aria-label": "Harga " + item + " " + cab });
      inp.addEventListener("input", () => { const d = inp.value.replace(/[^\d]/g, ""); inp.value = d ? (+d).toLocaleString("id-ID") : ""; });
      inp.addEventListener("change", () => {
        const v = +inp.value.replace(/[^\d]/g, "");
        simpanUbah("harga_pindah", kunciHargaPd(item, cab), v ? { item, cabang: cab, harga: v } : { item: "", cabang: "", harga: "" }, info);
        S.hargaPindah = S.hargaPindah || {};
        if (v) S.hargaPindah[kunciHargaPd(item, cab)] = { item, cabang: cab, harga: v }; else delete S.hargaPindah[kunciHargaPd(item, cab)];
      });
      return el("span", { style: "display:grid;gap:2px;justify-items:end" }, inp, info);
    };
    // Kak Intan 18 Nov 2026 sore: "di accurate ada harga tapi di dashbordnya ga muncul harga, pastikan semuanya
    // ada harganya jangan ketinggalan". Harga tiap baris IT dicari berlapis sampai ketemu:
    //   1. isian tangan di dashboard (koleksi harga_pindah)
    //   2. harga yang ditulis admin di kolom Keterangan baris IT di Accurate (pindah_it.json elemen ke-3)
    //   3. pricelist bulan terbaru (plPd - Aqua/Haier/Polytron/Miyako/Maspion)
    //   4. REKAP HARGA cabang tujuan (harga_modal.json)
    //   5. REKAP HARGA cabang asal / cabang lain - untuk tujuan yang tidak ada di REKAP (ONLINE, JOGJA, transit)
    //   6. HPP rata-rata Accurate + 11% PPN (items.json) - kode yang memang tidak ada di pricelist mana pun
    // Harga di bawah 10.000 dianggap bukan harga (keterangan IT kadang berisi catatan "100", kode kardus HPP-nya Rp 0,48).
    const HARGA_MIN_PD = 10000;
    const hargaModalPd = (item, ...cabs) => {
      const semua = ((D.harga_modal || {}).cabang) || {};
      for (const c of [...cabs, "JAKARTA", ...Object.keys(semua)]) {
        const r = c ? hm(item, c) : null;
        if (r && +r.harga >= HARGA_MIN_PD) return { harga: Math.round(+r.harga), cab: c };
      }
      return null;
    };
    const hppPd = (item) => {
      const it = (D.itemByNo || new Map()).get(String(item || "").trim().toUpperCase()) || {};
      const h = Math.round((+it.hpp_unit || 0) * 1.11);
      return h >= HARGA_MIN_PD ? h : 0;
    };
    // Unit outdoor AC ("<kode> (OUT)") dipindah satu set dengan unit indoor-nya: di Accurate harganya menempel di
    // baris indoor (keterangan outdoor ditulis "100", faktur belinya Rp 1). Jadi baris outdoor memang Rp 0 -
    // bukan "tanpa harga", dan tidak boleh ditambahkan lagi supaya tarik dananya tidak dobel.
    const POLA_OUT = /\s*\((OUT|OUTDOOR)\)\s*$/i;
    const hargaPindahBaris = (item, cabTuj, cabAsal, hket, kodeIt) => {
      const isian = hargaIsian(item, cabTuj);
      if (isian) return { harga: isian, sumber: "harga diisi di dashboard", isian: true };
      if (POLA_OUT.test(item || "") && kodeIt) {
        const indoor = String(item).replace(POLA_OUT, "").trim().toUpperCase();
        if (kodeIt.has(indoor)) return { harga: 0, sumber: "satu set dengan " + indoor + " - harganya ada di baris unit indoor", set: true };
      }
      if (+hket >= HARGA_MIN_PD) return { harga: Math.round(+hket), sumber: "harga di kolom Keterangan IT Accurate" };
      const pl = plPd({ item, cabang: cabTuj });
      if (pl && +pl.harga >= HARGA_MIN_PD) return { harga: pl.harga, sumber: pl.ket };
      const m = hargaModalPd(item, cabTuj, cabAsal);
      if (m) return { harga: m.harga, sumber: "REKAP HARGA " + m.cab + (m.cab === cabTuj ? "" : " (cabang tujuan tidak ada di REKAP HARGA)") };
      const hpp = hppPd(item);
      if (hpp) return { harga: hpp, sumber: "HPP rata-rata Accurate + 11% - kode ini tidak ada di pricelist" };
      return { harga: 0, sumber: "belum ada harga di sumber mana pun - klik untuk mengisi" };
    };
    // ceklis "sudah tarik dana" + nomor jurnal transfer bank per IT (koleksi db tarik_dana)
    const kunciIt = (no) => "it" + String(no || "").replace(/[^A-Za-z0-9]+/g, "_").slice(0, 90);
    const tarikIt = (no) => (S.tarikDana || {})[kunciIt(no)] || {};
    const simpanTarik = (no, ubah, info) => {
      const key = kunciIt(no), cur = { ...tarikIt(no), ...ubah, no_it: no };
      S.tarikDana = S.tarikDana || {};
      S.tarikDana[key] = cur;
      simpanUbah("tarik_dana", key, cur, info);
    };
    const ceklisTarik = (no) => {
      const cur = tarikIt(no), info = el("span", { class: "muted", role: "status", style: "font-size:11px" });
      if (S.canWrite === false || !S.db) return el("span", { class: cur.tarik ? "pill ok" : "muted", text: cur.tarik ? "✓ sudah" : "–" });
      const cb = el("input", { type: "checkbox", "aria-label": "Sudah tarik dana " + no });
      cb.checked = !!cur.tarik;
      cb.addEventListener("change", () => simpanTarik(no, { tarik: cb.checked, tarik_jam: cb.checked ? new Date().toISOString() : null }, info));
      return el("label", { style: "display:grid;gap:2px;justify-items:center;cursor:pointer" }, cb, info);
    };
    const inputJurnal = (no) => {
      const cur = tarikIt(no), info = el("span", { class: "muted", role: "status", style: "font-size:11px" });
      if (S.canWrite === false || !S.db) return el("span", { class: cur.jurnal ? "mono" : "muted", text: cur.jurnal || "–" });
      const inp = el("input", { class: "tgt", style: "width:11em;text-align:left", placeholder: "mis. JV.2026.11.00123",
        value: cur.jurnal || "", "aria-label": "Nomor jurnal transfer bank " + no });
      inp.addEventListener("change", () => simpanTarik(no, { jurnal: inp.value.trim() }, info));
      return el("span", { style: "display:grid;gap:2px" }, inp, info);
    };
    // Pilihan banyak cabang sekaligus (Kak Intan 18 Nov 2026: "bisa di ceklis yg mau difilter, kaya Excel")
    function pilihBanyak(judul, opsi, terpilih, simpan) {
      const dipilih = new Set(terpilih || []);
      const ring = el("summary", { text: judul + (dipilih.size ? " (" + dipilih.size + ")" : ": semua") });
      const isi = el("div", { style: "display:grid;gap:4px;padding:8px;max-height:230px;overflow:auto" },
        ...opsi.map((o) => {
          const cb = el("input", { type: "checkbox", "aria-label": judul + " " + o });
          cb.checked = dipilih.has(o);
          cb.addEventListener("change", () => { if (cb.checked) dipilih.add(o); else dipilih.delete(o); simpan([...dipilih]); render(); });
          return el("label", { style: "display:flex;gap:6px;align-items:center;white-space:nowrap" }, cb, o);
        }));
      const kosong = el("button", { class: "btn ghost", type: "button", style: "margin:0 8px 8px", text: "Semua" });
      kosong.addEventListener("click", () => { simpan([]); render(); });
      return el("details", { class: "detail", style: "border:1px solid var(--line);border-radius:10px;min-width:12em" }, ring, isi, kosong);
    }
    // Excel (Kak Intan 18 Nov 2026 sore: "jadi 2 sheet aja jangan banyak2", rapi seperti contoh WA):
    //   sheet REKAP       - NO, TANGGAL, NOMOR PEMINDAHAN, GUDANG ASAL, GUDANG TUJUAN, JUMLAH + baris TOTAL merah
    //   sheet SURAT JALAN - semua surat jalan per IT bertumpuk ke bawah dalam satu sheet
    // Pakai xlsx-js-style (SheetJS dengan dukungan garis/warna); kalau gagal dimuat, jatuh ke SheetJS biasa (tanpa gaya).
    let xlsxGayaSiap = null;
    const muatXlsxGaya = () => xlsxGayaSiap || (xlsxGayaSiap = new Promise((ok, gagal) => {
      const s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/xlsx-js-style@1.2.0/dist/xlsx.bundle.js";
      s.onload = () => ok(window.XLSX); s.onerror = () => { xlsxGayaSiap = null; gagal(new Error("muat")); };
      document.head.append(s);
    })).catch(() => muatXlsx());
    const BLN_XL = ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGU", "SEP", "OKT", "NOV", "DES"];
    const tglXl = (v) => { const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(v || "")); return m ? +m[3] + " " + BLN_XL[+m[2] - 1] + " " + m[1] : String(v || ""); };
    async function unduhPindahExcel(judul, perIt, barisPerIt, tombol, pesan) {
      pesan.textContent = "Menyiapkan…"; tombol.disabled = true;
      try {
        const [X, dl] = await Promise.all([muatXlsxGaya(), window.claude ? window.claude.use("downloads").catch(() => null) : null]);
        const wb = X.utils.book_new();
        const garis = { style: "thin", color: { rgb: "808080" } }, kotak = { top: garis, bottom: garis, left: garis, right: garis };
        const huruf = (x) => ({ name: "Arial", sz: 9, ...(x || {}) });
        const G = {
          judul: { font: huruf({ bold: true, sz: 12 }), alignment: { horizontal: "center" } },
          kepala: { font: huruf({ bold: true }), fill: { fgColor: { rgb: "D9D9D9" } }, border: kotak, alignment: { horizontal: "center", vertical: "center", wrapText: true } },
          isi: { font: huruf(), border: kotak, alignment: { vertical: "center" } },
          isiTengah: { font: huruf(), border: kotak, alignment: { horizontal: "center", vertical: "center" } },
          angka: { font: huruf(), border: kotak, numFmt: "#,##0", alignment: { horizontal: "right", vertical: "center" } },
          total: { font: huruf({ bold: true }), fill: { fgColor: { rgb: "D9837F" } }, border: kotak, alignment: { horizontal: "center" } },
          totalAngka: { font: huruf({ bold: true }), fill: { fgColor: { rgb: "D9837F" } }, border: kotak, numFmt: "#,##0", alignment: { horizontal: "right" } },
          pt: { font: huruf({ bold: true, sz: 11 }) },
          sj: { font: huruf({ bold: true, sz: 11 }), alignment: { horizontal: "center", wrapText: true } },
          biasa: { font: huruf() },
          tebal: { font: huruf({ bold: true }) },
          angkaTebal: { font: huruf({ bold: true }), numFmt: "#,##0", alignment: { horizontal: "right" } },
        };
        // tulis satu baris ke sheet: sel = [nilai, gaya] atau null
        const tulis = (ws, r, sel) => sel.forEach((x, c) => { if (!x) return; const [v, s] = x;
          ws[X.utils.encode_cell({ r, c })] = { v, t: typeof v === "number" ? "n" : "s", s, ...(s && s.numFmt ? { z: s.numFmt } : {}) }; });
        // ---- sheet 1: REKAP ----
        const tujuanSama = [...new Set(perIt.map((i) => i.cabTuj || ""))];
        const judulRekap = "REKAP PEMINDAHAN " + (tujuanSama.length === 1 && tujuanSama[0] ? tujuanSama[0] + " " : "")
          + (judul.match(/(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des) \d{4}$/) || [""])[0].toUpperCase();
        const wsR = {}, merR = [{ s: { r: 0, c: 0 }, e: { r: 0, c: 5 } }];
        tulis(wsR, 0, [[judulRekap.trim(), G.judul]]);
        tulis(wsR, 1, ["NO", "TANGGAL", "NOMOR PEMINDAHAN", "GUDANG ASAL", "GUDANG TUJUAN", "JUMLAH"].map((h) => [h, G.kepala]));
        perIt.forEach((i, n) => tulis(wsR, n + 2, [[n + 1, G.isiTengah], [tglXl(i.tgl), G.isiTengah], [i.it || "", G.isiTengah],
          [i.asal || "", G.isiTengah], [i.tujuan || "", G.isiTengah], [Math.round(i.total || 0), G.angka]]));
        const rT = perIt.length + 2;
        tulis(wsR, rT, [["", G.total], ["", G.total], ["TOTAL", G.total], ["", G.total], ["", G.total], [Math.round(perIt.reduce((a, i) => a + (i.total || 0), 0)), G.totalAngka]]);
        merR.push({ s: { r: rT, c: 0 }, e: { r: rT, c: 4 } });
        wsR["!ref"] = X.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: rT, c: 5 } });
        wsR["!merges"] = merR;
        wsR["!cols"] = [{ wch: 5 }, { wch: 14 }, { wch: 22 }, { wch: 22 }, { wch: 22 }, { wch: 16 }];
        X.utils.book_append_sheet(wb, wsR, "REKAP");
        // ---- sheet 2: SURAT JALAN (bertumpuk) ----
        const wsS = {}, merS = [];
        let r = 0;
        for (const i of perIt) {
          const baris = barisPerIt.get(i.it) || [];
          tulis(wsS, r, [["PT. SVARNA DIPA", G.pt], null, null, ["SURAT JALAN PENGIRIMAN BARANG", G.sj]]);
          merS.push({ s: { r, c: 3 }, e: { r, c: 4 } });
          r += 2;
          tulis(wsS, r, [["Kepada", G.biasa], [i.cabTuj || i.tujuan || "", G.tebal], null, [i.it || "", G.tebal]]); r++;
          tulis(wsS, r, [["Tanggal", G.biasa], [tglXl(i.tgl), G.biasa], null, [(i.asal || "") + " → " + (i.tujuan || ""), G.biasa]]); r += 2;
          tulis(wsS, r, ["JUMLAH", "SATUAN", "NAMA BARANG", "HARGA", "JUMLAH"].map((h) => [h, G.kepala])); r++;
          for (const b of baris) {
            tulis(wsS, r, [[+b.qty || 0, G.angka], ["Pcs", G.isiTengah], [(b.nama || b.item || "") + (b.nama && b.item ? " (" + b.item + ")" : ""), G.isi],
              [Math.round(b.harga || 0), G.angka], [Math.round(b.nilai || 0), G.angka]]); r++;
          }
          tulis(wsS, r, [null, null, null, ["TOTAL", G.tebal], [Math.round(i.total || 0), G.angkaTebal]]); r += 2;
          tulis(wsS, r, [null, ["Hormat Kami,", G.biasa], null, ["Penerima,", G.biasa]]); r += 4;
          tulis(wsS, r, [null, ["(______________)", G.biasa], null, ["(______________)", G.biasa]]); r += 3;
        }
        wsS["!ref"] = X.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: Math.max(r - 1, 0), c: 4 } });
        wsS["!merges"] = merS;
        wsS["!cols"] = [{ wch: 9 }, { wch: 8 }, { wch: 46 }, { wch: 14 }, { wch: 16 }];
        X.utils.book_append_sheet(wb, wsS, "SURAT JALAN");
        const buf = X.write(wb, { bookType: "xlsx", type: "array", cellStyles: true });
        const berkas = (judul + " " + new Date().toLocaleDateString("id-ID")).replace(/[\\/:*?"<>|·]+/g, " ").replace(/\s+/g, " ").trim() + ".xlsx";
        if (dl) await dl.save({ filename: berkas, data: buf });
        else simpanBerkas(berkas, buf);
        pesan.textContent = "Tersimpan: " + berkas + " (" + perIt.length + " IT, 2 sheet)";
      } catch (e) {
        pesan.textContent = e && e.code === "declined" ? "Unduhan dibatalkan." : "Gagal mengunduh" + (e && e.code ? " (" + e.code + ")" : "") + ".";
      } finally { tombol.disabled = false; }
    }
    // Summary per bulan untuk tarik dana (Kak Intan 17 Nov 2026): SEMUA pemindahan di Accurate (data/pindah_it.json,
    // mulai 1 Okt 2026), bukan hanya yang dibuat lewat web. Harga: isian/revisi pusat untuk baris yang ada di daftar web,
    // lalu harga yang diisi tangan di sini, lalu pricelist bulan terbaru menurut cabang tujuan.
    function kartuSummaryPindah() {
      const web = new Map((S.pindah || []).filter((p) => p.no_it).map((p) => [p.no_it + "|" + p.item, p]));
      const rows = [];
      for (const d of D.pindah_it || []) {
      const kodeIt = new Set((d.baris || []).map(([i]) => String(i).trim().toUpperCase()));
      for (const [item, q, hket] of d.baris || []) {
        const w = web.get(d.nomor + "|" + item), cab = gudangCab(d.tujuan), cabA = gudangCab(d.asal);
        const hp = hargaPindahBaris(item, cab, cabA, hket, kodeIt);
        // baris yang dibuat lewat web: harga final pengajuannya dulu, kalau kosong baru rantai harga di atas
        const hw = w ? hargaPd(w) : 0;
        const harga = hw || hp.harga;
        rows.push({ no_it: d.nomor, tgl: d.tgl, gudang_asal: d.asal, gudang_tujuan: d.tujuan, cabAsal: cabA, cabTuj: cab,
          item, nama: namaItem(item), qty: +q || 0, harga, nilai: harga * (+q || 0), terima: d.terima,
          isian: !!hp.isian && !hw, set: !!hp.set && !hw, sumber: hw ? "harga final di Daftar pemindahan" : hp.sumber });
      }
      }
      const bln = (r) => String(r.tgl || "").slice(0, 7);
      const semuaRows = rows;
      const dana = rows.filter(ikutTarikDana);
      const bulanAda = [...new Set(dana.map(bln))].filter(Boolean).sort().reverse();
      if (S.pdSumBln == null) S.pdSumBln = "";
      // Kak Intan 18 Nov 2026 sore: saringan cukup dua - Gudang asal, lalu Gudang tujuan (saringan Cabang dibuang)
      const rute = (r) => (r.gudang_asal || "?") + " → " + (r.gudang_tujuan || "?");
      // Kak Intan 18 Nov 2026 sore: pilihan gudang = SEMUA gudang semua cabang (bukan hanya yang ada pemindahannya).
      // Gudang retur/service/online/transit tidak dicantumkan karena memang tidak ikut tarik dana.
      const semuaGudang = [...new Set([
        ...Object.entries(((D.stok_gudang || {}).gudang) || {}).filter(([c]) => !CABANG_LUAR.includes(c)).flatMap(([, gs]) => gs),
        ...semuaRows.flatMap((r) => [r.gudang_asal, r.gudang_tujuan])])].filter((g) => g && !GUDANG_LUAR.test(g)).sort();
      const asalAda = semuaGudang, tujAda = semuaGudang;
      const namaBln = (v) => { const [y, m] = v.split("-"); return ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"][+m - 1] + " " + y; };
      const pilih = (id, nilai, opsi, semua, ubah, label) => { const x = el("select", { id }, el("option", { value: "", text: semua }), opsi.map((o) => el("option", { value: o, text: label ? label(o) : o, selected: o === nilai })));
        x.addEventListener("change", () => { ubah(x.value); render(); }); return x; };
      const asalPilih = S.pdSumAsalM || [], tujPilih = S.pdSumTujM || [];
      const cocok = (r) => (!S.pdSumBln || bln(r) === S.pdSumBln)
        && (!asalPilih.length || asalPilih.includes(r.gudang_asal))
        && (!tujPilih.length || tujPilih.includes(r.gudang_tujuan));
      const tampil = dana.filter(cocok);
      // baris yang tidak ditarik dana (ikut saringan bulan & cabang) + alasannya
      const luar = semuaRows.filter((r) => !ikutTarikDana(r) && (!S.pdSumBln || bln(r) === S.pdSumBln)
        && (!asalPilih.length || asalPilih.includes(r.gudang_asal)) && (!tujPilih.length || tujPilih.includes(r.gudang_tujuan)));
      const alasanLuar = (r) => GUDANG_LUAR.test(r.gudang_asal || "") || GUDANG_LUAR.test(r.gudang_tujuan || "") ? "gudang retur / service / online / transit"
        : CABANG_LUAR.includes(r.cabAsal) || CABANG_LUAR.includes(r.cabTuj) ? "gudang toko online / transit" : "sesama cabang (" + r.cabAsal + ")";
      const grup = new Map(), perIt = new Map(), barisIt = new Map();
      for (const r of tampil) {
        const k = r.gudang_asal + " → " + r.gudang_tujuan;
        const g = grup.get(k) || { asal: r.gudang_asal, tujuan: r.gudang_tujuan, cab: r.cabAsal + " → " + r.cabTuj, it: new Set(), qty: 0, total: 0, tanpa: 0 };
        g.it.add(r.no_it); g.qty += r.qty; g.total += r.nilai; if (!r.harga && !r.set) g.tanpa++; grup.set(k, g);
        const i = perIt.get(r.no_it) || { it: r.no_it, tgl: r.tgl, asal: r.gudang_asal, tujuan: r.gudang_tujuan,
          cab: r.cabAsal + " → " + r.cabTuj, cabTuj: r.cabTuj, barang: 0, qty: 0, total: 0, terima: r.terima };
        i.barang++; i.qty += r.qty; i.total += r.nilai; perIt.set(r.no_it, i);
        if (!barisIt.has(r.no_it)) barisIt.set(r.no_it, []);
        barisIt.get(r.no_it).push(r);
      }
      const total = tampil.reduce((a, r) => a + r.nilai, 0), tanpa = tampil.filter((r) => !r.harga && !r.set).length;
      const sudahTarik = [...perIt.keys()].filter((no) => tarikIt(no).tarik);
      const nilaiTarik = [...perIt.values()].filter((i) => tarikIt(i.it).tarik).reduce((a, i) => a + i.total, 0);
      const hapus = el("button", { class: "btn ghost", type: "button", text: "Hapus saringan" });
      hapus.disabled = !(S.pdSumBln || asalPilih.length || tujPilih.length || S.pdSumKpi);
      hapus.addEventListener("click", () => { S.pdSumBln = ""; S.pdSumAsalM = []; S.pdSumTujM = []; S.pdSumKpi = ""; render(); });
      // Kak Intan 18 Nov 2026 sore: kotak angka bisa diklik -> yang tampil hanya tabel data kotak itu; klik lagi = semua
      const K = S.pdSumKpi || "";
      const lihat = (...kunci) => !K || kunci.includes(K);
      const itTabel = [...perIt.values()].filter((i) => K !== "tarik" || tarikIt(i.it).tarik);
      const judulTabel = (t) => el("h3", { style: "margin:8px 0 0;font-size:15px", text: t });
      const pesanX = el("span", { class: "muted", style: "font-size:12px" });
      const tombolX = el("button", { class: "btn ghost", type: "button", text: "Unduh Excel (rekap + surat jalan)" });
      tombolX.addEventListener("click", () => unduhPindahExcel("Pemindahan barang" + (S.pdSumBln ? " " + namaBln(S.pdSumBln) : ""),
        [...perIt.values()].sort((a, b) => String(b.tgl).localeCompare(String(a.tgl))), barisIt, tombolX, pesanX));
      return card("Summary pemindahan barang (tarik dana)",
        "Gudang retur, service, online, dan transit tidak dihitung; pemindahan sesama cabang (mis. Daanmogot → Laksana) juga tidak ditarik dananya. "
        + "Ceklis \"Sudah tarik dana\" dan nomor jurnal transfer bank diisi di tabel Total per IT.",
        el("div", { class: "row", style: "gap:12px;flex-wrap:wrap;align-items:end" },
          el("label", { class: "ctl", for: "pdSumBln" }, "Bulan", pilih("pdSumBln", S.pdSumBln, bulanAda, "Semua bulan", (v) => (S.pdSumBln = v), namaBln)),
          pilihBanyak("Gudang asal", asalAda, asalPilih, (v) => (S.pdSumAsalM = v)),
          pilihBanyak("Gudang tujuan", tujAda, tujPilih, (v) => (S.pdSumTujM = v)), hapus, tombolX, pesanX),
        el("div", { class: "kpis" }, ...kpiKlikSemua("pdSumKpi",
          { "Total nilai": "nilai", "Sudah tarik dana": "tarik", "Jumlah IT": "it", "Jumlah unit": "unit", "Tanpa harga": "tanpa", "Tidak ditarik dana": "luar" }, [
          kpi("Total nilai", "Rp " + nf0.format(total), S.pdSumBln ? namaBln(S.pdSumBln) : "semua bulan", tanpa ? "warn" : ""),
          kpi("Sudah tarik dana", nf0.format(sudahTarik.length) + " IT", "Rp " + nf0.format(nilaiTarik) + " · sisa Rp " + nf0.format(total - nilaiTarik), sudahTarik.length ? "up" : "warn"),
          kpi("Jumlah IT", nf0.format(perIt.size), nf0.format(tampil.length) + " baris barang"),
          kpi("Jumlah unit", nf0.format(tampil.reduce((a, r) => a + r.qty, 0)), "unit dipindah"),
          kpi("Tanpa harga", nf0.format(tanpa), tanpa ? "klik untuk melihat & mengisi harganya" : "semua baris sudah berharga", tanpa ? "warn" : "up"),
          kpi("Tidak ditarik dana", nf0.format(luar.length), "baris retur/service/online atau sesama cabang")])),
        K ? el("div", { class: "muted", style: "font-size:12px", text: "Menampilkan data kotak yang dipilih saja - klik kotaknya lagi untuk melihat semua." }) : null,
        lihat("nilai") ? judulTabel("Per gudang asal → gudang tujuan") : null,
        !lihat("nilai") ? null : table([
          { h: "Gudang asal", f: (g) => g.asal },
          { h: "Gudang tujuan", f: (g) => g.tujuan },
          { h: "Cabang", f: (g) => g.cab },
          { h: "Jumlah IT", f: (g) => g.it.size, num: true, fmt: nf0.format },
          { h: "Unit", f: (g) => g.qty, num: true, fmt: nf0.format },
          { h: "Total nilai", f: (g) => g.total, num: true, fmt: (v) => nf0.format(v) },
          { h: "Baris tanpa harga", f: (g) => g.tanpa, num: true, fmt: (v) => v ? nf0.format(v) : "-" },
        ], [...grup.values()], { sort: 5, dir: "desc", empty: "Belum ada pemindahan untuk pilihan ini." }),
        lihat("tarik", "it") ? judulTabel(K === "tarik" ? "IT yang sudah tarik dana" : "Total per IT") : null,
        !lihat("tarik", "it") ? null : table([
          { h: "Tanggal IT", f: (i) => i.tgl, fmt: (v) => v ? new Date(v).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" }) : "–" },
          { h: "No. IT", f: (i) => i.it, cls: "mono" },
          { h: "Gudang asal → tujuan", f: (i) => i.asal + " → " + i.tujuan },
          { h: "Cabang", f: (i) => i.cab },
          { h: "Barang", f: (i) => i.barang, num: true, fmt: nf0.format },
          { h: "Unit", f: (i) => i.qty, num: true, fmt: nf0.format },
          { h: "Total nilai", f: (i) => i.total, num: true, fmt: (v) => nf0.format(v) },
          { h: "Sudah tarik dana", f: (i) => (tarikIt(i.it).tarik ? 1 : 0), num: true, node: (i) => ceklisTarik(i.it) },
          { h: "No. jurnal transfer bank", f: (i) => tarikIt(i.it).jurnal || "", node: (i) => inputJurnal(i.it) },
          { h: "Diterima", f: (i) => i.terima ? "ya" : "belum" },
        ], itTabel, { sort: 0, dir: "desc", limit: 500, empty: K === "tarik" ? "Belum ada IT yang dicentang sudah tarik dana." : "Belum ada IT untuk pilihan ini." }),
        !lihat("luar") || !K ? null : judulTabel("Tidak ditarik dana"),
        !lihat("luar") || !K ? null : table([
          { h: "Tanggal", f: (r) => r.tgl, fmt: (v) => v ? tglPendekID(v) : "–" },
          { h: "No. IT", f: (r) => r.no_it, cls: "mono" },
          { h: "Gudang asal → tujuan", f: rute },
          { h: "Kode", f: (r) => r.item, cls: "mono" },
          { h: "Nama barang", f: (r) => r.nama || "" },
          { h: "Qty", f: (r) => r.qty, num: true, fmt: nf0.format },
          { h: "Alasan tidak ditarik", f: alasanLuar },
        ], luar, { sort: 0, dir: "desc", limit: 500, maxH: "60vh", empty: "Tidak ada baris yang dikecualikan." }),
        // Kak Intan 18 Nov 2026 sore: kartu "Pemindahan barang di Accurate (IT)" digabung ke sini - rincian bawah
        // dibuat satu tabel per No. IT (barang satu jurnal digabung, total qty & nilai di bawah tiap IT).
        lihat("unit", "tanpa") ? judulTabel(K === "tanpa" ? "Barang tanpa harga (isi harganya di sini)" : "Rincian per IT (harga bisa diisi di sini)") : null,
        !lihat("unit", "tanpa") ? null : (() => {
          const BATAS = 60;
          // kotak "Tanpa harga": hanya IT yang punya baris tanpa harga, dan hanya baris itu
          const isiIt = (no) => (barisIt.get(no) || []).filter((r) => K !== "tanpa" || (!r.harga && !r.set));
          const blok = [...perIt.values()].filter((i) => isiIt(i.it).length).sort((a, b) => String(b.tgl).localeCompare(String(a.tgl)) || String(b.it).localeCompare(String(a.it)));
          if (!blok.length) return el("div", { class: "empty", text: "Belum ada IT untuk pilihan ini." });
          const kolom = [
            { h: "Kode #", f: (r) => r.item, cls: "mono" },
            { h: "Nama barang", f: (r) => r.nama || "" },
            { h: "Qty", f: (r) => r.qty, num: true, fmt: nf0.format },
            { h: "Harga", f: (r) => r.harga, num: true, node: (r) => r.set ? el("span", { class: "muted", title: r.sumber, text: "satu set" }) : inputHargaPd(r.item, r.cabTuj, r.harga, r.sumber) },
            { h: "Total", f: (r) => r.nilai, num: true, fmt: (v) => v ? nf0.format(v) : "-" },
          ];
          return el("div", { style: "display:grid;gap:16px" }, ...blok.slice(0, BATAS).map((i) => {
            const isi = isiIt(i.it), t = tarikIt(i.it);
            return el("div", { style: "display:grid;gap:6px" },
              el("div", { class: "row", style: "align-items:center;gap:10px;flex-wrap:wrap" },
                el("b", { class: "mono", text: i.it }),
                el("span", { class: "muted", text: tglPendekID(i.tgl) }),
                el("span", { text: i.asal + " → " + (i.tujuan || "?") }),
                el("span", { class: "muted", text: "(" + i.cab + ")" }),
                el("span", { class: "pill " + (i.terima ? "ok" : "mut"), text: i.terima ? "masuk gudang tujuan " + tglPendekID(i.terima) : "belum masuk gudang tujuan" }),
                el("span", { class: "pill " + (t.tarik ? "ok" : "mut"), text: t.tarik ? "sudah tarik dana" + (t.jurnal ? " · " + t.jurnal : "") : "belum tarik dana" })),
              table(kolom, isi, { sort: 0, dir: "asc" }),
              el("div", { class: "row", style: "justify-content:flex-end;gap:18px;font-weight:600;border-top:1px solid var(--line);padding-top:6px" },
                el("span", { class: "muted", style: "font-weight:400", text: isi.length + " barang" }),
                el("span", { text: "Total qty " + nf0.format(i.qty) + " unit" }),
                el("span", { text: "Total nilai " + nf0.format(i.total) })));
          }), blok.length > BATAS ? el("div", { class: "muted", text: "Menampilkan " + BATAS + " IT terbaru dari " + nf0.format(blok.length) + " - pakai saringan bulan / cabang untuk mempersempit; Unduh Excel memuat semuanya." }) : null);
        })());
    }
    // Revisi harga pemindahan (Kak Intan 14 Nov 2026): admin cabang (halaman admin-<cabang>, sandi sendiri) mengajukan
    // harga baru + alasan -> pusat ACC / tolak -> harga final berubah -> bot merevisi keterangan baris IT di Accurate.
    function kolomRevisi(p) {
      const box = el("div", { style: "display:grid;gap:4px;min-width:14em;font-size:12px" }), st = p.revisi_status;
      const info = el("span", { class: "muted", role: "status" });
      if (st) box.append(el("span", { class: "pill " + (st === "acc" ? "ok" : st === "tolak" ? "bad" : "warn"),
          text: st === "acc" ? "Revisi di-ACC pusat" : st === "tolak" ? "Revisi ditolak pusat" : "Revisi menunggu ACC pusat" }),
        el("div", { class: "muted", text: "harga baru " + nf0.format(+p.revisi_harga || 0) + (p.revisi_alasan ? " · " + p.revisi_alasan : "") +
          (p.revisi_oleh ? " · " + String(p.revisi_oleh).replace(/^admin-[a-z]+:/, "") : "") + (p.revisi_jam ? " · " + jamPd(p.revisi_jam) : "") }));
      if (S.adminCab && S.canWrite !== false && S.db && !p.terima && st !== "menunggu") {
        const h = el("input", { class: "tgt", style: "width:8em", inputmode: "numeric", placeholder: "harga baru", "aria-label": "Harga baru " + p.item });
        h.addEventListener("input", () => { const d = h.value.replace(/[^\d]/g, ""); h.value = d ? (+d).toLocaleString("id-ID") : ""; });
        const a = el("input", { style: "width:12em", placeholder: "alasan revisi", "aria-label": "Alasan revisi " + p.item });
        const b = el("button", { class: "btn ghost", type: "button", text: "Ajukan revisi" });
        b.addEventListener("click", async () => {
          const v = +h.value.replace(/[^\d]/g, "");
          if (!v) { info.textContent = "isi harga baru"; return; }
          if (!a.value.trim()) { info.textContent = "isi alasan revisi"; return; }
          b.disabled = true;
          await simpanPindah(p._id, { revisi_harga: v, revisi_alasan: a.value.trim(), revisi_oleh: S.uid || null, revisi_jam: new Date().toISOString(), revisi_status: "menunggu" }, info);
          b.disabled = false;
        });
        box.append(el("div", { style: "display:flex;gap:4px;flex-wrap:wrap;align-items:center" }, h, a, b));
      }
      if (!S.kunci && st === "menunggu" && S.canWrite !== false && S.db) {
        const ok = el("button", { class: "btn", type: "button", text: "ACC revisi" }), no = el("button", { class: "btn ghost", type: "button", text: "Tolak" });
        ok.addEventListener("click", async () => { ok.disabled = no.disabled = true;
          await simpanPindah(p._id, { harga_modal: +p.revisi_harga, revisi_status: "acc", revisi_acc_oleh: S.uid || null, revisi_acc_jam: new Date().toISOString() }, info); });
        no.addEventListener("click", async () => { ok.disabled = no.disabled = true;
          await simpanPindah(p._id, { revisi_status: "tolak", revisi_acc_oleh: S.uid || null, revisi_acc_jam: new Date().toISOString() }, info); });
        box.append(el("div", { style: "display:flex;gap:6px" }, ok, no));
      }
      box.append(info);
      return box;
    }

