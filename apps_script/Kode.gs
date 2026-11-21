/**
 * Penyimpan PENGAJUAN SALES (uji coba, repo winros-web/Pengajuan-Sales) - Kak Intan 13 Nov 2026.
 *
 * Satu koleksi "pengajuan" bersama untuk pusat + 8 cabang (tidak perlu sinkron cabang->pusat lagi):
 *   - halaman cabang hanya melihat & menulis pengajuan cabangnya, dan TIDAK bisa memberi ACC
 *     (status selain "menunggu" / field acc_* / eksekusi* ditolak di sini, bukan cuma disembunyikan di halaman);
 *   - halaman pusat (Ibu / Bu Diana / admin) melihat semua dan memberi ACC;
 *   - bot di PC Kak Intan (kunci ADMIN) membaca tiap beberapa detik, mengerjakan ACC ke Accurate,
 *     lalu menulis status selesai / gagal.
 * Koleksi lain (target, program, ...) yang dipakai halaman tetap per halaman.
 *
 * Pasang (Kak Intan, sekali): buat Google Sheet baru "PENYIMPAN PENGAJUAN SALES" > Ekstensi > Apps Script >
 * tempel berkas ini > Setelan proyek > Script Properties: MASTER = nilai PENGAJUAN_MASTER di .env PC >
 * Terapkan > Deployment baru > Aplikasi web, Jalankan sebagai: Saya, Akses: Siapa saja > salin URL /exec
 * ke .env PC sebagai PENGAJUAN_APPS_URL=...
 * Kunci halaman = HMAC-SHA256(MASTER, nama halaman); kunci bot = HMAC(MASTER, "ADMIN"). Tidak ada rahasia di kode ini.
 */
const HALAMAN_CABANG = ["jakarta", "bandung", "medan", "palembang", "lampung", "gresik", "kaltim", "makassar"];
// halaman admin cabang (14 Nov 2026): sandi sendiri, melihat harga pemindahan cabangnya, hanya boleh mengajukan revisi harga
const HALAMAN = ["pusat"].concat(HALAMAN_CABANG, HALAMAN_CABANG.map((h) => "admin-" + h));
const cabHal = (h) => CABANG_HAL[String(h).replace(/^admin-/, "")] || [];
const REVISI = ["revisi_harga", "revisi_alasan", "revisi_oleh", "revisi_jam", "revisi_status"];
const CABANG_HAL = { jakarta: ["JAKARTA", "TANGERANG"], bandung: ["BANDUNG"], medan: ["MEDAN"], palembang: ["PALEMBANG"],
  lampung: ["LAMPUNG"], gresik: ["GRESIK"], kaltim: ["KALIMANTAN TIMUR"], makassar: ["MAKASSAR"] };
// koleksi bersama pusat + cabang (disimpan halaman "*"); cabang hanya melihat baris cabangnya
const BERSAMA = ["pengajuan", "pindah_barang"];
const KOLEKSI = ["pengajuan", "target", "program", "harga_spesial", "catatan_piutang", "catatan_retur", "foto_retur",
  "program_beli", "pesan_fix", "tanda_cek", "tagih_cek", "alasan_limit", "pindah_barang", "rute_ubah", "ongkos_ubah", "perbarui",
  // 18 Nov 2026: tab Toko kembali order - ceklis keberhasilan toko lama + catatan sapaan WhatsApp
  "winback_cek", "sapa_toko",
  // 18 Nov 2026: tarik dana pemindahan (ceklis + nomor jurnal transfer bank per IT) dan harga pemindahan
  // yang diisi tangan untuk kode yang tidak ada di pricelist
  "tarik_dana", "harga_pindah"];
// pemindahan barang (14 Nov 2026): tahap cek stok / OK Hana / input Accurate hanya pusat & bot; cabang menulis permintaan
// dan ceklis "Diterima cabang" (sesudah barang dikirim)
const FIELD_PUSAT_PINDAH = ["cek_stok", "cek_stok_waktu", "hana", "hana_waktu", "input_acc", "input_acc_waktu", "no_it",
  "eksekusi", "eksekusi_jam", "eksekusi_galat", "harga_modal", "harga_it", "it_id",
  "revisi_harga", "revisi_alasan", "revisi_oleh", "revisi_jam", "revisi_status", "revisi_acc_oleh", "revisi_acc_jam"];
// harga pemindahan hanya untuk pusat (Kak Intan 14 Nov 2026: sales tidak boleh tahu harga) - dibuang dari bacaan cabang
const HARGA_PINDAH = ["harga_modal", "harga_it"];
// field yang hanya boleh ditulis pusat / bot
const FIELD_PUSAT = ["acc_oleh", "acc_jam", "catatan_acc", "acc_limit", "acc_cod", "pelanggan_id", "eksekusi", "eksekusi_oleh",
  "eksekusi_jam", "eksekusi_galat", "eksekusi_lama", "eksekusi_acc_jam", "dikembalikan_bot"];
const KOLOM = ["halaman", "koleksi", "id", "data", "diubah", "oleh", "dihapus"];
const FOLDER_FOTO = "FOTO PENGAJUAN SALES WEB";

function doGet() { return jawab({ ok: true, layanan: "penyimpan pengajuan sales" }); }

function doPost(e) {
  let q;
  try { q = JSON.parse(e.postData.contents); } catch (err) { return jawab({ ok: false, galat: "permintaan tidak terbaca" }); }
  const admin = q.halaman === "ADMIN";
  if (!admin && HALAMAN.indexOf(q.halaman) < 0) return jawab({ ok: false, galat: "halaman tidak dikenal" });
  if (!q.kunci || q.kunci !== kunciUntuk(q.halaman)) return jawab({ ok: false, galat: "kunci salah" });
  try {
    if (q.aksi === "daftar") return jawab(daftar(admin ? null : q.halaman, Number(q.sejak) || 0));
    if (q.aksi === "unggah" && !admin) return jawab(unggah(q));
    const kunci = LockService.getScriptLock();
    kunci.waitLock(20000);
    try {
      if (q.aksi === "tulis") {
        const t = { halaman: q.halaman, koleksi: q.koleksi, id: q.id, mode: q.mode, data: q.data };
        return jawab(tulis(admin ? (q.tulis || []) : [t], admin ? "bot" : q.oleh, admin));
      }
    } finally { kunci.releaseLock(); }
    return jawab({ ok: false, galat: "aksi tidak dikenal" });
  } catch (err) {
    return jawab({ ok: false, galat: String(err && err.message || err) });
  }
}

function jawab(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

function kunciUntuk(halaman) {
  const master = PropertiesService.getScriptProperties().getProperty("MASTER");
  if (!master) throw new Error("MASTER belum dipasang");
  return Utilities.computeHmacSha256Signature(halaman, master).map((b) => ("0" + (b & 255).toString(16)).slice(-2)).join("");
}

function lembar() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName("isian");
  if (!sh) { sh = ss.insertSheet("isian"); sh.getRange(1, 1, 1, KOLOM.length).setValues([KOLOM]); sh.setFrozenRows(1); }
  return sh;
}

function semuaBaris(sh) {
  const akhir = sh.getLastRow();
  return akhir < 2 ? [] : sh.getRange(2, 1, akhir - 1, KOLOM.length).getValues();
}

// pengajuan disimpan dengan halaman "*" (bersama); koleksi lain per halaman
function bolehLihat(halaman, r) {
  if (!halaman) return true;
  if (BERSAMA.indexOf(r[1]) < 0) return r[0] === halaman;
  if (halaman === "pusat") return true;
  const d = r[6] ? null : JSON.parse(r[3] || "{}");
  return !d || cabHal(halaman).indexOf(String(d.cabang || "").toUpperCase()) >= 0;
}

function daftar(halaman, sejak) {
  const docs = [];
  for (const r of semuaBaris(lembar())) {
    if (Number(r[4]) <= sejak || !bolehLihat(halaman, r)) continue;
    const data = r[6] ? null : JSON.parse(r[3] || "{}");
    if (data && halaman && halaman !== "pusat" && !/^admin-/.test(halaman) && r[1] === "pindah_barang") HARGA_PINDAH.concat(["revisi_harga"]).forEach((f) => delete data[f]);
    docs.push({ halaman: r[0], koleksi: r[1], id: String(r[2]), data: data, diubah: Number(r[4]), oleh: r[5], dihapus: !!r[6] });
  }
  return { ok: true, sekarang: Date.now(), docs: docs };
}

// admin cabang: hanya mengajukan revisi harga pemindahan cabangnya (tidak membuat / menghapus / mengubah field lain)
function aturanAdminCabang(halaman, t, lama, data) {
  if (t.koleksi !== "pindah_barang") throw new Error("halaman admin cabang hanya untuk revisi harga pemindahan");
  if (t.mode !== "update" || !lama) throw new Error("admin cabang hanya boleh mengajukan revisi harga");
  if (cabHal(halaman).indexOf(String(lama.cabang || "").toUpperCase()) < 0) throw new Error("pemindahan cabang lain");
  const kunciSemua = Object.keys(Object.assign({}, lama, data));
  for (const f of kunciSemua) if (REVISI.indexOf(f) < 0 && f !== "diubah" && f !== "diubah_oleh" && JSON.stringify(lama[f]) !== JSON.stringify(data[f]))
    throw new Error("admin cabang hanya boleh mengubah revisi harga (" + f + ")");
  if (data.revisi_status && data.revisi_status !== "menunggu" && data.revisi_status !== lama.revisi_status) throw new Error("ACC revisi hanya dari pusat");
}

function aturanPindah(halaman, lama, data, mode) {
  const cab = CABANG_HAL[halaman];
  if (lama && cab.indexOf(String(lama.cabang || "").toUpperCase()) < 0) throw new Error("pemindahan cabang lain");
  if (mode === "delete") {
    if (lama && (lama.cek_stok || lama.hana || lama.input_acc)) throw new Error("pemindahan yang sudah diproses pusat tidak bisa dihapus cabang");
    return;
  }
  if (cab.indexOf(String(data.cabang || "").toUpperCase()) < 0) throw new Error("cabang tujuan harus " + cab[0]);
  for (const f of FIELD_PUSAT_PINDAH) if (JSON.stringify((lama || {})[f]) !== JSON.stringify(data[f]) && (data[f] != null || (lama || {})[f] != null))
    throw new Error("tahap " + f + " hanya untuk pusat");
  if (data.terima && !(lama && lama.input_acc)) throw new Error("diterima cabang hanya sesudah barang dikirim (input Accurate)");
  if (lama && lama.input_acc && ["item", "qty", "gudang_asal", "gudang_tujuan"].some((f) => JSON.stringify(lama[f]) !== JSON.stringify(data[f])))
    throw new Error("barang sudah dikirim - jumlah/gudang tidak bisa diubah");
}

function aturanCabang(halaman, lama, data, mode) {
  const cab = CABANG_HAL[halaman];
  if (lama && cab.indexOf(String(lama.cabang || "").toUpperCase()) < 0) throw new Error("pengajuan cabang lain");
  if (mode === "delete") {
    if (lama && lama.status && lama.status !== "menunggu") throw new Error("pengajuan yang sudah diputus pusat tidak bisa dihapus cabang");
    return;
  }
  if (cab.indexOf(String(data.cabang || "").toUpperCase()) < 0) throw new Error("cabang pengajuan harus " + cab[0]);
  const stLama = lama ? (lama.status || "menunggu") : "menunggu";
  // cabang boleh memperbaiki pengajuan yang dikembalikan (kembali ke status sebelumnya) - selain itu status tidak boleh berubah
  const stBaru = data.status || "menunggu";
  const boleh = stBaru === stLama || stBaru === "menunggu" || (stLama === "dikembalikan" && stBaru === (lama.status_sebelum || "menunggu"));
  if (!boleh) throw new Error("cabang tidak boleh mengubah status pengajuan");
  if (!lama && stBaru !== "menunggu") throw new Error("pengajuan baru dari cabang harus menunggu ACC pusat");
  for (const f of FIELD_PUSAT) if (JSON.stringify((lama || {})[f]) !== JSON.stringify(data[f]) && data[f] != null) throw new Error("field " + f + " hanya untuk pusat");
}

// mode: set (ganti), update (gabung field), delete, add (id dibuat di sini)
function tulis(daftarTulis, oleh, admin) {
  const sh = lembar();
  const rows = semuaBaris(sh);
  const posisi = {};
  rows.forEach((r, i) => { posisi[r[0] + "|" + r[1] + "|" + r[2]] = i; });
  const hasil = [], baru = [];
  let jam = Date.now();
  for (const t of daftarTulis) {
    if (KOLEKSI.indexOf(t.koleksi) < 0) throw new Error("koleksi tidak dikenal: " + t.koleksi);
    const bersama = BERSAMA.indexOf(t.koleksi) >= 0;
    const hal = bersama ? "*" : t.halaman;
    if (hal !== "*" && HALAMAN.indexOf(hal) < 0) throw new Error("halaman tidak dikenal");
    const id = String(t.id || Utilities.getUuid().replace(/-/g, "").slice(0, 20));
    if (!/^[A-Za-z0-9_.:@-]{1,120}$/.test(id)) throw new Error("id tidak sah");
    const k = hal + "|" + t.koleksi + "|" + id;
    const i = posisi[k];
    const lama = i == null || rows[i][6] ? null : JSON.parse(rows[i][3] || "{}");
    let data;
    if (t.mode === "delete") data = null;
    else if (t.mode === "update") { if (!lama) throw new Error("dokumen tidak ada: " + t.koleksi + "/" + id); data = Object.assign({}, lama, t.data || {}); }
    else data = t.data || {};
    if (!admin && /^admin-/.test(t.halaman)) { if (bersama) aturanAdminCabang(t.halaman, t, lama, data || {}); }
    else if (!admin && bersama && t.halaman !== "pusat") (t.koleksi === "pindah_barang" ? aturanPindah : aturanCabang)(t.halaman, lama, data || {}, t.mode);
    if (bersama && data && !lama) data.dari_halaman = admin ? "bot" : t.halaman;
    const teks = data ? JSON.stringify(data) : "";
    if (teks.length > 45000) throw new Error("isian terlalu besar");
    jam += 1;
    const baris = [hal, t.koleksi, id, teks, jam, String(oleh || "").slice(0, 80), data ? "" : 1];
    if (i == null) { posisi[k] = rows.length + baru.length; baru.push(baris); }
    else { rows[i] = baris; sh.getRange(i + 2, 1, 1, KOLOM.length).setValues([baris]); }
    hasil.push({ id: id, diubah: jam });
  }
  if (baru.length) sh.getRange(sh.getLastRow() + 1, 1, baru.length, KOLOM.length).setValues(baru);
  return { ok: true, hasil: hasil };
}

// foto/PDF lampiran: Drive pemilik skrip, bisa dibuka siapa pun yang punya link
function unggah(q) {
  const tipe = String(q.tipe || "");
  const OFFICE = /^application\/(msword|vnd\.ms-excel|vnd\.openxmlformats-officedocument\.(wordprocessingml\.document|spreadsheetml\.sheet))$/;
  if (!/^(image\/(jpeg|png|webp|gif|heic)|application\/pdf)$/.test(tipe) && !OFFICE.test(tipe)) throw new Error("hanya foto, PDF, Word, atau Excel");
  const bytes = Utilities.base64Decode(q.b64 || "");
  if (bytes.length > 15 * 1024 * 1024) throw new Error("lebih dari 15 MB");
  const akar = folder(DriveApp.getRootFolder(), FOLDER_FOTO);
  // 17 Nov 2026: bukti uang jalan disimpan per hari -> q.folder mis. "UANG JALAN SUPIR/2026-11-17/B9189BXS"
  let tujuan = folder(akar, q.halaman.toUpperCase());
  if (q.folder) String(q.folder).split("/").map((x) => x.replace(/[^\w .-]/g, "").trim()).filter(Boolean).slice(0, 4)
    .forEach((x) => { tujuan = folder(tujuan, x); });
  const f = tujuan.createFile(Utilities.newBlob(bytes, tipe, String(q.nama || "foto").slice(0, 120)));
  f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return { ok: true, id: f.getId(), url: "https://drive.google.com/file/d/" + f.getId() + "/view" };
}

function folder(induk, nama) {
  const it = induk.getFoldersByName(nama);
  return it.hasNext() ? it.next() : induk.createFolder(nama);
}
