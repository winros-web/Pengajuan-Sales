  // Status pemindahan + keterangan bot (Kak Intan 14 Nov 2026: "ada info sedang antre atau apa" seperti pengajuan sales).
  // ACC pusat = ceklis cek_stok; bot di PC membuat Pemindahan Barang (Kirim Barang) di Accurate lalu mengisi no_it.
  const ACC_PINDAH_SEJAK = "2026-11-14T02:58:30"; // sama dengan bot: centang sebelum ini tidak diproses otomatis
  const jamPd = (v) => v ? new Date(v).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "";
  const statusPindah = (p) => p.terima ? ["Diterima cabang", "ok"]
    : p.input_acc ? ["Sudah masuk Accurate" + (p.no_it ? " · " + p.no_it : ""), "ok"]
    : p.eksekusi_galat ? ["Bot gagal - admin cek", "bad"]
    : !p.cek_stok ? ["Menunggu ACC pusat", "mut"]
    : String(p.cek_stok_waktu || "") < ACC_PINDAH_SEJAK ? ["Centang ulang ACC pusat", "warn"]
    : /^bot sedang/.test(p.eksekusi || "") ? ["Bot sedang menulis ke Accurate", "warn"]
    : /sibuk/i.test(p.eksekusi || "") ? ["Accurate sibuk - antre", "warn"]
    : ["Antre bot Accurate", "warn"];
  function infoBotPindah(p) {
    const t = [];
    if (p.terima) t.push("diterima " + jamPd(p.terima_waktu));
    if (p.input_acc) t.push("masuk Accurate " + jamPd(p.input_acc_waktu || p.eksekusi_jam) + (p.no_it ? " · " + p.no_it : "") + (p.eksekusi_jam ? " · oleh bot" : ""));
    else if (p.eksekusi_galat) t.push(p.eksekusi_galat);
    else if (!p.cek_stok) t.push("diajukan " + jamPd(p.dibuat) + " · menunggu pusat mencentang ACC pusat");
    else if (String(p.cek_stok_waktu || "") < ACC_PINDAH_SEJAK) t.push("dicentang sebelum bot aktif - hapus centang ACC pusat lalu centang lagi supaya diproses bot");
    else {
      t.push("ACC pusat " + jamPd(p.cek_stok_waktu));
      if (/^bot sedang/.test(p.eksekusi || "")) t.push("bot sedang menyimpan Pemindahan Barang di Accurate…");
      else if (/sibuk/i.test(p.eksekusi || "")) t.push("Accurate sedang sibuk (kuota token dipakai proses lain) - bot mencoba lagi otomatis tiap 10 detik");
      else t.push("antre bot - biasanya masuk Accurate dalam 5-15 detik");
      const lama = (Date.now() - new Date(p.cek_stok_waktu)) / 60000;
      if (lama > 5) t.push("sudah " + Math.round(lama) + " menit belum diproses - bot mungkin mati, kabari Gio");
    }
    return el("div", { style: "display:grid;gap:4px;min-width:14em" }, el("span", { class: "pill " + statusPindah(p)[1], text: statusPindah(p)[0] }),
      ...t.map((x) => el("div", { class: "muted", style: "font-size:12px", text: x })), tombolUlangPindah(p));
  }
  // Kak Intan 18 Nov 2026: "di daftar pemindahan ditambahin kalo gagal bisa refresh lagi, botnya dijalankan lagi".
  // Tombol ini menghapus tanda gagal dan menyegarkan jam ACC pusat, jadi bot mengambilnya lagi di putaran berikutnya.
  // Kalau tandanya "PERLU CEK" (bot mati saat menulis), tombolnya minta klik dua kali - IT-nya bisa saja sudah
  // terlanjur ada di Accurate, dan bot tidak boleh membuat yang kedua.
  function tombolUlangPindah(p) {
    if (!p.eksekusi_galat || p.input_acc || p.terima || S.canWrite === false || !S.db) return null;
    const perluCek = /^PERLU CEK/i.test(String(p.eksekusi_galat));
    const info = el("span", { class: "muted", role: "status", style: "font-size:11px" });
    const teksAwal = perluCek ? "Jalankan bot lagi (cek dulu di Accurate)" : "Jalankan bot lagi";
    const b = el("button", { class: "btn ghost", type: "button", style: "padding:4px 10px;font-size:12px;justify-self:start", text: teksAwal });
    let yakin = false, jam = null;
    b.addEventListener("click", async () => {
      if (perluCek && !yakin) {
        yakin = true; b.textContent = "Pastikan IT-nya belum ada di Accurate - klik lagi";
        clearTimeout(jam); jam = setTimeout(() => { yakin = false; b.textContent = teksAwal; }, 8000);
        return;
      }
      clearTimeout(jam); b.disabled = true; info.textContent = "menyiapkan…";
      await simpanPindah(p._id, { eksekusi_galat: null, eksekusi: null, cek_stok: true,
        cek_stok_waktu: new Date().toISOString(), diulang_oleh: S.uid || null, diulang_jam: new Date().toISOString() }, info);
      b.disabled = false;
    });
    return el("div", { style: "display:grid;gap:2px;justify-items:start" }, b, info);
  }
