  // ---------- Kompensasi pemasok (Kak Intan 26 Nov 2026: "aku mau ambil alih yang kompensasi ... dashboard pusat") ----------
  // data/kompen.json dari skrip/dashboard_kompen.py (sementara: salinan Pusat Kerja Mac mini / NAMI, baca saja).
  // Hanya halaman pusat (dipasang skrip/bangun.py). Tidak ada tombol tulis: dashboard ini hanya melihat.
  const KP_STATUS = {
    SIAP_TAGIH: ["bad", "Siap tagih", "hak sudah pasti dan lebih besar dari yang diterima - bisa ditagih ke pemasok"],
    HITUNGAN_BEDA: ["warn", "Hitungan beda", "yang diterima tidak sama dengan hak hitungan kita - cek penyebabnya dulu"],
    MENUNGGU_SURAT: ["warn", "Menunggu surat", "tanpa surat/memo periode itu belum boleh ditagih"],
    BELUM_TERBIT: ["mut", "Belum terbit", "reward belum keluar (biasa +- 2 bulan)"],
    TIDAK_BISA_DIUJI: ["mut", "Tidak bisa diuji", "dasar hitung belum lengkap"],
    TANPA_SURAT: ["mut", "Tanpa surat", "program tanpa surat tertulis"],
    SESUAI: ["ok", "Sesuai", "yang diterima sama dengan hak"],
    TUNTAS: ["ok", "Tuntas", "sudah selesai"],
    DILEWATI: ["mut", "Belum dihitung", "program tercatat tetapi belum ada hasil mesin"],
  };
  const kpSt = (s) => KP_STATUS[s] || ["mut", s || "-", ""];
  const kpRp = (v) => v == null ? "–" : rp(v);
  // baris total untuk table(): kolom angka dijumlah, kolom pertama = label
  const kpTotal = (cols, rows) => cols.map((c, i) => i === 0 ? "Total" : c.num ? kpRp(rows.reduce((a, r) => a + (+c.f(r) || 0), 0)) : "");
  async function pKompen(sec) {
    const K = await muatLain("kompen").catch(() => null);
    if (!K) { sec.replaceChildren(el("div", { class: "msg", text: "Data kompensasi belum ada - jalankan skrip\\dashboard_kompen.py lalu bangun ulang halaman." })); return; }
    const R = K.ringkas || {}, M = K.meta || {}, SR = K.status_ringkas || {};
    const semua = K.program || [];
    const sups = [...new Set(semua.map((p) => p.supplier))].sort();
    const lolos = (p) => (!S.kpSup || p.supplier === S.kpSup) && (!S.kpSt || p.status === S.kpSt) && (!S.kpTh || String(p.tahun) === S.kpTh);
    const rows = semua.filter(lolos);
    const n = (st) => semua.filter((p) => p.status === st && (!S.kpSup || p.supplier === S.kpSup)).length;
    // Kak Intan 27 Nov 2026: "ini belum bisa diklik klik ya, kalo di klik muncul datanya" -> tiap kartu ringkasan
    // membuka tabel rincian tepat di bawah kartu-kartunya (klik lagi = tutup).
    const klikSt = (st) => { S.kpRinci = S.kpRinci === st ? "" : st; render(); };
    const kotak = (judul, v, ket, cls, st) => { const k = kpi(judul, v, ket, cls); if (st) { k.style.cursor = "pointer"; k.title = "Klik untuk melihat rinciannya"; k.addEventListener("click", () => klikSt(st)); if (S.kpRinci === st) k.style.outline = "2px solid var(--accent)"; } return k; };

    const pilih = (id, nilai, opsi, ubah) => { const s = el("select", { id }, opsi.map(([v, t]) => el("option", { value: v, text: t, selected: v === nilai }))); s.addEventListener("change", () => { ubah(s.value); render(); }); return s; };
    const saring = el("div", { class: "row", style: "gap:12px;flex-wrap:wrap;align-items:end" },
      el("label", { class: "ctl", for: "kpSup" }, "Pemasok", pilih("kpSup", S.kpSup || "", [["", "Semua pemasok"], ...sups.map((s) => [s, s])], (v) => (S.kpSup = v))),
      el("label", { class: "ctl", for: "kpTh" }, "Tahun", pilih("kpTh", S.kpTh || "", [["", "Semua tahun"], ["2025", "2025"], ["2026", "2026"]], (v) => (S.kpTh = v))),
      el("label", { class: "ctl", for: "kpSt" }, "Status", pilih("kpSt", S.kpSt || "", [["", "Semua status"], ...Object.entries(KP_STATUS).map(([k, v]) => [k, v[1]])], (v) => (S.kpSt = v))));

    const info = el("p", { class: "note" },
      "Sumber: " + (M.sumber || "-") + " · data Accurate per " + (M.data_accurate_per || "-") + ". ",
      el("b", { text: M.catatan || "" }));

    const tautSurat = (p) => (p.surat || []).length
      ? el("span", { style: "display:grid;gap:2px" }, p.surat.map((s) => el("a", { href: s.url, target: "_blank", rel: "noopener", text: "📄 " + String(s.nama || "surat").slice(0, 40) })))
      : el("span", { class: "muted", text: p.surat_status === "TIDAK_ADA" || !p.surat_status ? "–" : String(p.surat_status).toLowerCase().replace(/_/g, " ") });
    function rinci() {
      const r = S.kpRinci;
      if (!r) return el("p", { class: "note", text: "Klik salah satu kotak di atas untuk melihat rinciannya." });
      const sup = (p) => !S.kpSup || p.supplier === S.kpSup;
      const dasar = [
        { h: "Program", f: (p) => p.program, node: (p) => el("span", { title: p.keterangan || "" }, el("b", { text: p.program }), p.keterangan ? el("div", { class: "muted", style: "font-size:12px", text: p.keterangan }) : null) },
        { h: "Pemasok", f: (p) => p.supplier },
        { h: "Periode", f: (p) => p.periode },
        { h: "Status", f: (p) => kpSt(p.status)[1], node: (p) => { const [c, t, k] = kpSt(p.status); return el("span", { class: "pill " + c, title: k + (p.alasan_dilewati ? " - " + p.alasan_dilewati : ""), text: t }); } },
      ];
      const ang = (h, f) => ({ h, f, num: true, fmt: kpRp });
      const DEF = {
        R_KU: ["KU / reward diterima per program", (p) => p.ku_diterima, [ang("Diterima (KU)", (p) => p.ku_diterima), ang("Hak", (p) => p.hak), ang("Selisih", (p) => p.selisih)]],
        R_ACC: ["KU yang terverifikasi di Accurate", (p) => p.ku_accurate, [ang("Di Accurate", (p) => p.ku_accurate), ang("Diterima (KU)", (p) => p.ku_diterima), ang("Mesin belum cocok", (p) => p.mesin_belum_cocok)]],
        R_MESIN: ["KU yang belum ketemu di Accurate", (p) => p.mesin_belum_cocok, [ang("Mesin belum cocok", (p) => p.mesin_belum_cocok), ang("Diterima (KU)", (p) => p.ku_diterima), ang("Di Accurate", (p) => p.ku_accurate)]],
        R_HAK: ["Hak menurut hitungan kita", (p) => p.hak, [ang("Hak", (p) => p.hak), ang("Diterima (KU)", (p) => p.ku_diterima), ang("Selisih", (p) => p.selisih)]],
      };
      let judul, isi;
      if (r === "R_TANPA") {
        const sp = (K.supplier || []).filter((s) => s.ku_diterima_tanpa_program && (!S.kpSup || s.supplier === S.kpSup));
        const kol = [{ h: "Pemasok", f: (s) => s.supplier }, { h: "Jumlah KU", f: (s) => s.n_ku_tanpa_program || 0, num: true, fmt: (v) => nf0.format(v) }, ang("Nilai KU tanpa program", (s) => s.ku_diterima_tanpa_program)];
        judul = "KU yang belum dipasangkan ke program, per pemasok (rincian per nomor KU belum ada di data NAMI)";
        isi = table(kol, sp, { sort: 2, total: kpTotal(kol, sp), empty: "Tidak ada." });
      } else if (DEF[r]) {
        const [j, ada, tambah] = DEF[r];
        const kol = [...dasar, ...tambah];
        const rows = semua.filter((p) => sup(p) && +ada(p));
        judul = j + " - " + nf0.format(rows.length) + " program";
        isi = table(kol, rows, { sort: 4, limit: 100, total: kpTotal(kol, rows), empty: "Tidak ada program." });
      } else {
        const kol = [...dasar, { h: "Kepastian", f: (p) => p.kepastian || "" }, ang("Hak", (p) => p.hak), ang("Diterima (KU)", (p) => p.ku_diterima), ang("Selisih", (p) => p.selisih), { h: "Surat / memo", f: (p) => (p.surat || []).length, saring: false, node: tautSurat }];
        const rows = semua.filter((p) => sup(p) && p.status === r);
        judul = kpSt(r)[1] + " - " + nf0.format(rows.length) + " program" + (kpSt(r)[2] ? " (" + kpSt(r)[2] + ")" : "");
        isi = table(kol, rows, { sort: 5, limit: 100, total: kpTotal(kol, rows), empty: "Tidak ada program." });
      }
      return el("div", { style: "margin-top:14px" },
        el("div", { class: "row", style: "justify-content:space-between;align-items:center;gap:8px" },
          el("b", { text: judul }),
          el("button", { class: "btn", type: "button", text: "Tutup", onclick: () => { S.kpRinci = ""; render(); } })),
        isi);
    }
    const kartuRingkas = card("Ringkasan kompensasi semua pemasok", null, info,
      el("div", { class: "kpis" },
        kotak("KU / reward diterima", rpK(R.ku_diterima), R.n_program + " program punya baris rekap", "", "R_KU"),
        kotak("Terverifikasi di Accurate", rpK(R.ku_terverifikasi_accurate), "nomor KU ditemukan di Accurate", "up", "R_ACC"),
        kotak("Mesin belum cocok", rpK(R.nilai_mesin_belum_cocok), "KU belum ketemu di Accurate - perlu dicek", R.nilai_mesin_belum_cocok ? "warn" : "", "R_MESIN"),
        kotak("Hak (golongan 1-2)", rpK(R.hak), "hitungan kita dari faktur pembelian", "", "R_HAK"),
        kotak("KU tanpa program", rpK(R.ku_diterima_tanpa_program), (R.n_ku_tanpa_program || 0) + " KU belum dipasangkan ke program", "", "R_TANPA")),
      el("div", { class: "kpis" },
        kotak("Siap tagih", nf0.format(n("SIAP_TAGIH")), "program", n("SIAP_TAGIH") ? "down" : "", "SIAP_TAGIH"),
        kotak("Hitungan beda", nf0.format(n("HITUNGAN_BEDA")), "program", n("HITUNGAN_BEDA") ? "warn" : "", "HITUNGAN_BEDA"),
        kotak("Menunggu surat", nf0.format(n("MENUNGGU_SURAT")), "program", "", "MENUNGGU_SURAT"),
        kotak("Belum terbit", nf0.format(n("BELUM_TERBIT")), "program", "", "BELUM_TERBIT"),
        kotak("Belum dihitung", nf0.format(n("DILEWATI")), "dari " + (SR.tercatat || semua.length) + " program tercatat", "", "DILEWATI")),
      rinci());

    const kolSup = [
        { h: "Pemasok", f: (s) => s.supplier },
        { h: "Program", f: (s) => s.n_program || 0, num: true, fmt: (v) => nf0.format(v) },
        { h: "Hak", f: (s) => s.hak, num: true, fmt: kpRp },
        { h: "KU diterima", f: (s) => s.ku_diterima, num: true, fmt: kpRp },
        { h: "Terverifikasi Accurate", f: (s) => s.ku_terverifikasi_accurate, num: true, fmt: kpRp },
        { h: "Mesin belum cocok", f: (s) => s.nilai_mesin_belum_cocok, num: true, fmt: kpRp, },
        { h: "KU tanpa program", f: (s) => s.ku_diterima_tanpa_program, num: true, fmt: kpRp },
        { h: "Final", f: (s) => s.final ? "final" : "sementara" },
      ];
    const kartuSup = card("Per pemasok", "Klik baris untuk menyaring tabel program ke pemasok itu. Sharp belum ada di sumber Mac mini.",
      table(kolSup, K.supplier || [], { sort: 3, total: kpTotal(kolSup, K.supplier || []), onRow: (s) => { S.kpSup = S.kpSup === s.supplier ? "" : s.supplier; render(); } }));

    const kolProg = [
        { h: "Program", f: (p) => p.program, node: (p) => el("span", { title: p.keterangan || "" }, el("b", { text: p.program }), p.keterangan ? el("div", { class: "muted", style: "font-size:12px", text: p.keterangan }) : null) },
        { h: "Pemasok", f: (p) => p.supplier },
        { h: "Periode", f: (p) => p.periode },
        { h: "Kelompok", f: (p) => p.kelompok || "" },
        { h: "Status", f: (p) => kpSt(p.status)[1], node: (p) => { const [c, t, k] = kpSt(p.status); return el("span", { class: "pill " + c, title: k + (p.alasan_dilewati ? " - " + p.alasan_dilewati : ""), text: t }); } },
        { h: "Kepastian", f: (p) => p.kepastian || "" },
        { h: "Hak", f: (p) => p.hak, num: true, fmt: kpRp },
        { h: "Diterima (KU)", f: (p) => p.ku_diterima, num: true, fmt: kpRp },
        { h: "Mesin belum cocok", f: (p) => p.mesin_belum_cocok, num: true, fmt: kpRp },
        { h: "Selisih", f: (p) => p.selisih, num: true, fmt: kpRp },
        { h: "Surat / memo", f: (p) => (p.surat || []).length, saring: false, node: tautSurat },
      ];
    const kartuProg = card("Program kompen", "Status dari analisis NAMI. Siap tagih = ada dasar (surat atau rumus kompen 1%) dan hak lebih besar dari yang diterima. Tanpa surat tidak pernah ditagih.",
      saring,
      table(kolProg, rows, { sort: 7, limit: 50, total: kpTotal(kolProg, rows), empty: "Tidak ada program untuk saringan ini." }));

    const pr = K.peringatan || {};
    const dtl = K.data_tidak_lengkap || {};
    const NAMA_PR = { KU_TIDAK_ADA_DI_CERMIN: "KU tidak ada di Accurate (cermin)", KU_GANDA_LINTAS_PROGRAM: "KU dihitung di dua program", KU_GANDA_DALAM_PROGRAM: "KU ganda dalam satu program", NILAI_BEDA_SUMBER: "Nilai beda antara mesin dan Accurate" };
    const kartuCek = card("Perlu dicek", "Tanda dari mesin NAMI. Angka ini bahan pemeriksaan, bukan kesalahan pasti.",
      el("div", { class: "kpis" },
        ...Object.entries(pr).map(([k, v]) => kpi(NAMA_PR[k] || k.replace(/_/g, " ").toLowerCase(), nf0.format(v), "baris", v ? "warn" : "")),
        kpi("Program belum final", nf0.format(dtl.program_belum_final || 0), "angka masih bisa berubah"),
        kpi("Baris tanpa tanggal transfer", nf0.format(dtl.baris_tanpa_transfer || 0), ""),
        kpi("Program tanpa KU", nf0.format(dtl.program_tanpa_ku || 0), "belum ada reward tercatat")));

    // ---------- Kak Intan 27 Nov 2026: tagihan / cek ke Accurate / pendapatan vs bukti potong (skrip\dashboard_kompen_audit.py) ----------
    const A = K.audit;
    const ekstra = [];
    if (A) {
      const ang = (h, f) => ({ h, f, num: true, fmt: kpRp });
      const pilihA = (kunci, judulPilih, ...kotak) => el("div", { class: "kpis" }, ...kotak.map(([judul, v, ket, cls, k]) => {
        const x = kpi(judul, v, ket, cls); x.style.cursor = "pointer"; x.title = "Klik untuk melihat rinciannya";
        x.addEventListener("click", () => { S[kunci] = S[kunci] === k ? "" : k; render(); });
        if (S[kunci] === k) x.style.outline = "2px solid var(--accent)";
        return x;
      }));
      const tutup = (kunci, judul, isi) => S[kunci] ? el("div", { style: "margin-top:14px" },
        el("div", { class: "row", style: "justify-content:space-between;align-items:center;gap:8px" }, el("b", { text: judul }),
          el("button", { class: "btn", type: "button", text: "Tutup", onclick: () => { S[kunci] = ""; render(); } })), isi)
        : el("p", { class: "note", text: "Klik salah satu kotak di atas untuk melihat rinciannya." });
      const sup = (x) => !S.kpSup || String(x.supplier || x.pabrik || "").toUpperCase().startsWith(S.kpSup.toUpperCase());

      // 1. Tagihan kompen (hutang.json Mac mini)
      const T = A.tagihan || {}, TA = T.all || {}, L = TA.lajur || {}, LL = T.label_lajur || {};
      const tb = (T.baris || []).filter(sup);
      const kolTb = [{ h: "Program", f: (r) => r.program }, { h: "Pemasok", f: (r) => r.supplier }, { h: "Bulan", f: (r) => r.bulan }, { h: "Cabang", f: (r) => r.cabang },
        { h: "Lajur", f: (r) => r.lajur || "", node: (r) => el("span", { title: LL[r.lajur] || "", text: r.lajur ? r.lajur + " - " + String(LL[r.lajur] || "").split(" (")[0] : "-" }) },
        ang("Hak", (r) => r.hak), ang("Cair", (r) => r.cair), ang("Belum cair", (r) => r.belum_cair), ang("KU terbit belum cair", (r) => r.ku_terbit_belum_cair),
        ang("Lebih bayar", (r) => r.lebih_bayar), { h: "Jadwal paling lambat", f: (r) => r.jadwal || "" }, { h: "KU", f: (r) => r.ku || "" }];
      const rinciTag = () => {
        const k = S.kpTag;
        if (k === "TANPA") {
          const r = (T.ku_tanpa_program || []).filter(sup);
          const kol = [{ h: "Pemasok", f: (x) => x.supplier }, { h: "Nomor KU", f: (x) => x.nomor }, { h: "Tanggal", f: (x) => x.tanggal }, { h: "Cabang", f: (x) => x.cabang },
            ang("DPP", (x) => x.dpp), ang("Neto", (x) => x.neto), { h: "Status", f: (x) => x.status }, { h: "Catatan", f: (x) => x.catatan }];
          return table(kol, r, { sort: 4, total: kpTotal(kol, r), empty: "Tidak ada." });
        }
        const r = tb.filter((x) => k === "KU" ? x.ku_terbit_belum_cair : k === "LEBIH" ? x.lebih_bayar : k === "BELUM" ? x.belum_cair : x.lajur === k && x.belum_cair);
        return table(kolTb, r, { sort: 7, limit: 100, total: kpTotal(kolTb, r), empty: "Tidak ada." });
      };
      const judulTag = { BELUM: "Semua yang belum cair", A: LL.A, B: LL.B, C: LL.C, D: LL.D, KU: "KU sudah terbit tapi belum cair", TANPA: "KU terbit tanpa program", LEBIH: "Lebih bayar" };
      ekstra.push(card("Tagihan kompen - hak vs yang sudah cair", "Dari Pusat Kerja Mac mini per " + (T.per || "-") + " (salinan, baca saja). Lajur C = siap ditagih sekarang.",
        pilihA("kpTag", "",
          ["Belum cair", rpK(TA.belum_cair), "hak yang belum masuk", TA.belum_cair ? "down" : "", "BELUM"],
          ["Siap ditagih (C)", rpK(L.C), "KU terbit belum cair", L.C ? "down" : "", "C"],
          ["Lewat jadwal (B)", rpK(L.B), "perlu dicek", L.B ? "warn" : "", "B"],
          ["Belum waktunya (A)", rpK(L.A), "KU belum jatuh jadwal", "", "A"],
          ["Menunggu surat (D)", rpK(L.D), "tidak ditagih, tidak masuk total", "", "D"]),
        pilihA("kpTag", "",
          ["KU terbit belum cair", rpK(TA.ku_terbit_belum_cair), "KU sudah dibuat, uang belum masuk", TA.ku_terbit_belum_cair ? "warn" : "", "KU"],
          ["KU tanpa program", rpK(TA.ku_terbit_tanpa_program), (T.ku_tanpa_program || []).length + " KU", "", "TANPA"],
          ["Lebih bayar", rpK(TA.lebih_bayar), "cair melebihi hak", "", "LEBIH"]),
        tutup("kpTag", judulTag[S.kpTag] || "", S.kpTag ? rinciTag() : null)));

      // 2. Hasil cek ke Accurate & bupot Coretax
      const V = (A.vonis || []).filter(sup);
      const VON = { "BELUM DITERIMA": "bad", "SEBAGIAN": "warn", "TIDAK BISA DIPASTIKAN": "mut", "SUDAH DITERIMA": "ok" };
      const nV = (v) => V.filter((x) => x.vonis === v);
      const sumV = (v, k) => nV(v).reduce((a, x) => a + (+x[k] || 0), 0);
      const kolV = [{ h: "Pemasok", f: (x) => x.pabrik }, { h: "Temuan", f: (x) => x.temuan, node: (x) => el("span", {}, el("b", { text: x.temuan }), x.langkah ? el("div", { class: "muted", style: "font-size:12px", text: "Langkah: " + x.langkah }) : null) },
        { h: "Vonis", f: (x) => x.vonis, node: (x) => el("span", { class: "pill " + (VON[x.vonis] || "mut"), text: x.vonis }) },
        ang("Nilai", (x) => x.nilai), ang("Diterima", (x) => x.diterima), ang("Kurang", (x) => x.kurang),
        { h: "Bukti di sistem", f: (x) => x.bukti, node: (x) => el("span", { class: "muted", style: "font-size:12px", text: x.bukti || "-" }) }];
      const rV = V.filter((x) => !S.kpVon || x.vonis === S.kpVon);
      ekstra.push(card("Hasil cek temuan ke Accurate & bukti potong Coretax (2026)", "Setiap temuan dari dokumen Drive dicek ke Accurate (faktur/KU, pelunasan, potongan hutang) dan bupot Coretax masa 1-10. Belum diterima = harus ditagih.",
        pilihA("kpVon", "",
          ["Belum diterima", nf0.format(nV("BELUM DITERIMA").length), "kurang " + rpK(sumV("BELUM DITERIMA", "kurang")) + " - tagih", nV("BELUM DITERIMA").length ? "down" : "", "BELUM DITERIMA"],
          ["Sebagian", nf0.format(nV("SEBAGIAN").length), "kurang " + rpK(sumV("SEBAGIAN", "kurang")), nV("SEBAGIAN").length ? "warn" : "", "SEBAGIAN"],
          ["Tidak bisa dipastikan", nf0.format(nV("TIDAK BISA DIPASTIKAN").length), "data kurang", "", "TIDAK BISA DIPASTIKAN"],
          ["Sudah diterima", nf0.format(nV("SUDAH DITERIMA").length), rpK(sumV("SUDAH DITERIMA", "diterima")), "up", "SUDAH DITERIMA"]),
        tutup("kpVon", S.kpVon ? S.kpVon + " - " + rV.length + " temuan" : "", S.kpVon ? table(kolV, rV, { sort: 5, limit: 100, total: kpTotal(kolV, rV), empty: "Tidak ada." }) : null)));

      // 3. Pendapatan vs bukti potong
      const B = A.bupot || {};
      const th = S.kpBpTh || "2026";
      const thOk = (x) => String(x.tahun) === th && sup(x);
      const bp = (B.per_pabrik || []).filter(thOk);
      const kolBp = [{ h: "Pemasok", f: (x) => x.pabrik }, ang("Pendapatan (DPP)", (x) => x.pendapatan_dpp), ang("DPP bupot", (x) => x.bupot_dpp), ang("Selisih DPP", (x) => (x.pendapatan_dpp || 0) - (x.bupot_dpp || 0)),
        ang("PPh di bupot", (x) => x.bupot_pph), ang("PPh seharusnya", (x) => x.pph_seharusnya), ang("Selisih PPh", (x) => (x.bupot_pph || 0) - (x.pph_seharusnya || 0)),
        { h: "Catatan", f: (x) => x.catatan || "", node: (x) => el("span", { class: "muted", style: "font-size:12px", text: x.catatan || "" }) }];
      const tbl = (B.tidak_cocok || []).filter(thOk);
      const kolTc = [{ h: "Pemasok", f: (x) => x.pabrik }, { h: "Dokumen / KU", f: (x) => x.dok }, { h: "Tgl / masa", f: (x) => x.tgl }, ang("DPP pendapatan", (x) => x.dpp_pendapatan),
        { h: "No bupot", f: (x) => x.no_bupot || "-" }, ang("DPP bupot", (x) => x.dpp_bupot), ang("PPh bupot", (x) => x.pph_bupot), { h: "Masalah", f: (x) => x.masalah }];
      const pb = (B.per_bulan || []).filter((x) => thOk(x) && (!S.kpBpPab || x.pabrik === S.kpBpPab));
      const kolPb = [{ h: "Pemasok", f: (x) => x.pabrik }, { h: "Bulan", f: (x) => x.bulan }, ang("Pendapatan (DPP)", (x) => x.pendapatan_dpp), ang("DPP bupot", (x) => x.bupot_dpp),
        ang("PPh bupot", (x) => x.bupot_pph), { h: "Catatan", f: (x) => x.catatan || "" }];
      const tot = (k) => bp.reduce((a, x) => a + (+x[k] || 0), 0);
      const tem24 = B.temuan_2024 || [];
      ekstra.push(card("Pendapatan kompensasi vs bukti potong PPh 23", th === "2024"
        ? "2024: dari \"241225 REKAP BUKTI POTONG PABRIK 2024 TERUPDATE.xlsx\" (sheet final BUPOT + Rincian Buku Besar 7100.xx), dicocokkan per JV."
        : "2026: faktur kompensasi di Accurate vs bupot PPh 23 yang diterima di Coretax (masa 1-10). Masa 11 belum ditarik.",
        el("div", { class: "row", style: "gap:12px;flex-wrap:wrap;align-items:end" },
          el("label", { class: "ctl", for: "kpBpTh" }, "Tahun", pilih("kpBpTh", th, [["2026", "2026"], ["2024", "2024"]], (v) => { S.kpBpTh = v; S.kpBpPab = ""; })),
          el("label", { class: "ctl", for: "kpBpPab" }, "Rincian bulanan", pilih("kpBpPab", S.kpBpPab || "", [["", "Semua pemasok"], ...[...new Set(bp.map((x) => x.pabrik))].map((x) => [x, x])], (v) => (S.kpBpPab = v)))),
        el("div", { class: "kpis" },
          kpi("Pendapatan (DPP)", rpK(tot("pendapatan_dpp")), th),
          kpi("DPP di bupot", rpK(tot("bupot_dpp")), "selisih " + rpK(tot("pendapatan_dpp") - tot("bupot_dpp")), Math.abs(tot("pendapatan_dpp") - tot("bupot_dpp")) > 1e6 ? "warn" : "up"),
          kpi("PPh di bupot (kredit)", rpK(tot("bupot_pph")), "seharusnya " + rpK(tot("pph_seharusnya"))),
          (() => { const x = kpi("Baris tidak cocok", nf0.format(tbl.length), "klik untuk rincian", tbl.length ? "warn" : ""); x.style.cursor = "pointer"; x.addEventListener("click", () => { S.kpBpTc = !S.kpBpTc; render(); }); if (S.kpBpTc) x.style.outline = "2px solid var(--accent)"; return x; })()),
        table(kolBp, bp, { sort: 1, total: kpTotal(kolBp, bp), empty: "Tidak ada data." }),
        S.kpBpTc ? el("div", { style: "margin-top:14px" }, el("b", { text: "Baris tidak cocok " + th }), table(kolTc, tbl, { sort: 3, limit: 100, total: kpTotal(kolTc, tbl), empty: "Tidak ada." })) : null,
        el("div", { style: "margin-top:14px" }, el("b", { text: "Per bulan" + (S.kpBpPab ? " - " + S.kpBpPab : "") }), table(kolPb, pb, { sort: 1, limit: 60, total: kpTotal(kolPb, pb), empty: "Tidak ada." })),
        th === "2024" && tem24.length ? el("div", { style: "margin-top:14px" }, el("b", { text: "Temuan 2024" }),
          table([{ h: "Tingkat", f: (x) => x.tingkat, node: (x) => el("span", { class: "pill " + ({ tinggi: "bad", sedang: "warn" }[x.tingkat] || "mut"), text: x.tingkat }) },
            { h: "Temuan", f: (x) => x.judul, node: (x) => el("span", {}, el("b", { text: x.judul }), el("div", { class: "muted", style: "font-size:12px", text: x.rincian })) }, ang("Rupiah", (x) => x.rupiah)], tem24, { sort: 2 })) : null));

      // 4. Rekap dokumen Drive per pabrik
      const D = A.dokumen || {};
      const dr = (D.ringkas || []).filter(sup);
      const kolD = [{ h: "Pemasok", f: (x) => x.pabrik }, { h: "Berkas", f: (x) => x.berkas || 0, num: true, fmt: (v) => nf0.format(v) }, { h: "Program", f: (x) => x.program, num: true, fmt: (v) => nf0.format(v) },
        ang("Diklaim", (x) => x.diklaim), ang("Disetujui pabrik", (x) => x.disetujui), ang("Ada bukti di dokumen", (x) => x.bukti_dokumen)];
      const dt = (D.temuan || []).filter((x) => sup(x) && (!S.kpDokT || x.tingkat === S.kpDokT));
      ekstra.push(card("Rekap dokumen program pabrik 2026 (Drive KOMPENSASI 2026)", "Dibaca dari 642 dokumen Drive (termasuk SHARP yang belum ada di Mac mini). Bukti di dokumen saja - vonis akhirnya lihat kartu Hasil cek di atas. File lengkap: 'OTOMATISASI/10. KOMPEN PABRIK/REKAP KOMPENSASI PABRIK 2026.xlsx.",
        table(kolD, dr, { sort: 4, total: kpTotal(kolD, dr) }),
        el("div", { class: "row", style: "gap:12px;align-items:end;margin-top:10px" },
          el("label", { class: "ctl", for: "kpDokT" }, "Temuan dokumen", pilih("kpDokT", S.kpDokT || "", [["", "Semua tingkat"], ["tinggi", "Tinggi"], ["sedang", "Sedang"], ["rendah", "Rendah"]], (v) => (S.kpDokT = v)))),
        table([{ h: "Pemasok", f: (x) => x.pabrik }, { h: "Tingkat", f: (x) => x.tingkat, node: (x) => el("span", { class: "pill " + ({ tinggi: "bad", sedang: "warn" }[x.tingkat] || "mut"), text: x.tingkat }) },
          { h: "Temuan", f: (x) => x.judul, node: (x) => el("span", {}, el("b", { text: x.judul }), el("div", { class: "muted", style: "font-size:12px", text: x.rincian })) }, ang("Perkiraan Rp", (x) => x.rupiah)], dt, { sort: 3, limit: 50 })));
    }

    // Kak Intan 28 Nov 2026: tautan spreadsheet rekap kompensasi di dashboard
    const tautan = (A && A.tautan || []).length ? el("div", { class: "card", style: "display:flex;flex-wrap:wrap;gap:10px;align-items:center" },
      el("b", { text: "📊 Spreadsheet kompensasi:" }),
      ...A.tautan.map((t) => el("a", { href: t.url, target: "_blank", rel: "noopener", class: "btn", text: t.nama }))) : null;
    // Kak Intan 28 Nov 2026: "excelnya belum ada di dashboard" -> isi REKAP KOMPENSASI 2026 (Tabel 1 per brand) tampil di sini
    let kartuExcel = null;
    const RB = (A && A.rekap_brand) || {};
    const brands = Object.keys(RB);
    if (brands.length) {
      const b = brands.includes(S.kpRbBrand) ? S.kpRbBrand : brands[0];
      const r = RB[b];
      const CAB = ["JAKARTA", "BANDUNG", "PALEMBANG", "LAMPUNG", "SURABAYA", "MEDAN", "SAMARINDA", "MAKASSAR", "LAIN"];
      const BL = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
      const baris = BL.map((n, i) => { const x = r.bulan[String(i + 1)] || {}; const o = { bulan: n }; let t = 0; CAB.forEach((c) => { o[c] = x[c] || 0; t += o[c]; }); o.total = t; return o; });
      const kol = [{ h: "Bulan", f: (x) => x.bulan }, ...CAB.map((c) => ({ h: c, f: (x) => x[c], num: true, fmt: kpRp })), { h: "TOTAL", f: (x) => x.total, num: true, fmt: kpRp }];
      const tbRing = brands.map((k) => ({ brand: k, dpp: RB[k].dpp, pph: RB[k].pph, n: RB[k].n, tanpa: RB[k].tanpa_bupot }));
      const kolRing = [{ h: "Brand", f: (x) => x.brand }, { h: "KU/faktur", f: (x) => x.n, num: true, fmt: (v) => nf0.format(v) },
        { h: "Kompensasi 2026 (DPP)", f: (x) => x.dpp, num: true, fmt: kpRp }, { h: "PPh di bupot", f: (x) => x.pph, num: true, fmt: kpRp },
        { h: "Tanpa bupot", f: (x) => x.tanpa, num: true, fmt: (v) => nf0.format(v) }];
      const linkX = ((A && A.tautan) || [])[0];
      kartuExcel = card("Rekap Kompensasi 2026 per brand (isi Excel)", "Sama dengan Tabel 1 di Excel REKAP KOMPENSASI 2026 - PT SVARNA DIPA: DPP faktur/KU kompensasi di Accurate per bulan x cabang. Klik baris brand untuk ganti brand.",
        linkX ? el("p", {}, el("a", { href: linkX.url, target: "_blank", rel: "noopener", class: "btn", text: "📊 Buka Excel lengkap (sheet per brand)" })) : null,
        table(kolRing, tbRing, { sort: 2, total: kpTotal(kolRing, tbRing), onRow: (x) => { S.kpRbBrand = x.brand; render(); } }),
        el("div", { style: "margin-top:14px" }, el("b", { text: b + " - per bulan per cabang" }), table(kol, baris, { total: kpTotal(kol, baris) })));
    }
    // Kak Intan 28 Nov 2026: bot hitung hak per brand (spek program x pembelian Accurate) + cocok per program
    let kartuHitung = null;
    const HT = (A && A.hitung) || null;
    if (HT && (HT.brand || []).length) {
      const STH = { "COCOK": "ok", "HAK > TERIMA (cek tagih)": "bad", "TERIMA > HAK (cek spek)": "warn", "BELUM TERBIT": "mut" };
      const bAktif = S.kpHtBrand || "";
      const brs = (HT.baris || []).filter((x) => (!bAktif || x.brand === bAktif) && (!S.kpHtSt || x.status === S.kpHtSt));
      const kolB = [{ h: "Brand", f: (x) => x.brand }, { h: "Hak (hitungan bot)", f: (x) => x.hak, num: true, fmt: kpRp },
        { h: "Diterima (faktur Accurate)", f: (x) => x.diterima_faktur, num: true, fmt: kpRp },
        { h: "Cocok", f: (x) => x.cocok || 0, num: true, fmt: (v) => nf0.format(v) },
        { h: "Cek tagih", f: (x) => x.cek_tagih || 0, num: true, fmt: (v) => nf0.format(v) },
        { h: "Nilai cek tagih", f: (x) => x.nilai_cek_tagih, num: true, fmt: kpRp },
        { h: "Belum terbit", f: (x) => x.belum_terbit || 0, num: true, fmt: (v) => nf0.format(v) },
        { h: "Nilai belum terbit", f: (x) => x.nilai_belum_terbit, num: true, fmt: kpRp },
        { h: "Terima > hak", f: (x) => x.cek_spek || 0, num: true, fmt: (v) => nf0.format(v) }];
      const n = (st) => (HT.baris || []).filter((x) => (!bAktif || x.brand === bAktif) && x.status === st).length;
      const kotakSt = (judul, st, ket, cls) => { const k = kpi(judul, nf0.format(n(st)), ket, cls); k.style.cursor = "pointer"; k.title = "Klik untuk menyaring";
        k.addEventListener("click", () => { S.kpHtSt = S.kpHtSt === st ? "" : st; render(); }); if (S.kpHtSt === st) k.style.outline = "2px solid var(--accent)"; return k; };
      const kolR = [{ h: "Brand", f: (x) => x.brand }, { h: "Program", f: (x) => x.program }, { h: "Periode", f: (x) => x.periode }, { h: "Cabang", f: (x) => x.cabang },
        { h: "Status", f: (x) => x.status, node: (x) => el("span", { class: "pill " + (STH[x.status] || "mut"), text: x.status }) },
        { h: "Hak (bot)", f: (x) => x.hak, num: true, fmt: kpRp }, { h: "Diterima", f: (x) => x.diterima, num: true, fmt: kpRp },
        { h: "Selisih", f: (x) => x.selisih, num: true, fmt: kpRp },
        { h: "Penjelasan", f: (x) => x.penjelasan, node: (x) => el("span", { class: "muted", style: "font-size:12px", text: x.penjelasan || "" }) }];
      const kl = HT.kelengkapan || {};
      const klTeks = Object.entries(kl).map(([k, v]) => k + ": " + Object.entries(v).map(([a, b]) => a.toLowerCase() + " " + b).join(", ")).join(" | ");
      kartuHitung = card("Hitungan hak kompensasi per brand (bot hitung)", "Bot menghitung hak tiap program dari spek program (dibaca dari CAMPAIGN 2026, KOMPEN PABRIK, KOMPENSASI 2026) x pembelian Accurate 2026, lalu dicocokkan per program dengan yang diterima (SPHP/KU/BNS/BMBD/CN). Diperbarui tiap pagi 07.30. Klik baris brand / kotak status untuk menyaring." + (HT.dibuat ? " Hitungan per " + HT.dibuat + "." : ""),
        table(kolB, HT.brand, { sort: 1, total: kpTotal(kolB, HT.brand), onRow: (x) => { S.kpHtBrand = S.kpHtBrand === x.brand ? "" : x.brand; render(); } }),
        el("div", { class: "kpis", style: "margin-top:12px" },
          kotakSt("Hak > terima (cek tagih)", "HAK > TERIMA (cek tagih)", "hak belum diterima penuh", "down"),
          kotakSt("Belum terbit", "BELUM TERBIT", "hak ada, dokumen belum keluar", "warn"),
          kotakSt("Terima > hak", "TERIMA > HAK (cek spek)", "diterima lebih dari hitungan (periode 2025 / hadiah tetap)", ""),
          kotakSt("Cocok", "COCOK", "hitungan = yang diterima", "up")),
        el("div", { style: "margin-top:12px" }, el("b", { text: (bAktif || "Semua brand") + (S.kpHtSt ? " - " + S.kpHtSt : "") + " (" + brs.length + " baris)" }),
          table(kolR, brs, { sort: 7, limit: 100, total: kpTotal(kolR, brs), empty: "Tidak ada." })),
        klTeks ? el("p", { class: "note", text: "Kelengkapan berkas yang dibaca - " + klTeks }) : null);
    }
    sec.replaceChildren(...[tautan, kartuHitung, kartuExcel, kartuRingkas, kartuSup, kartuProg, kartuCek, ...ekstra].filter(Boolean));
  }
