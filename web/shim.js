// Pengganti window.claude untuk halaman GitHub Pages: db / user / assets dilayani penyimpan Apps Script.
// Dipasang oleh kerangka sesudah sandi benar: pasangClaude({url, kunci, halaman}, nama).
// Halaman dashboard memakai API yang sama dengan artifact (collection().onSnapshot / add, doc().set / update / delete),
// jadi kode tab Pengajuan sales tidak perlu diubah.
function pasangClaude(isian, nama) {
  const HAL = isian.halaman, BERSAMA = ['pengajuan', 'pindah_barang', 'sapa_toko'];
  const cache = {}, pendengar = {};
  let sejak = 0, sibuk = false, siap = false;
  const panggil = async (isi) => {
    // text/plain = permintaan sederhana, tanpa preflight CORS ke Apps Script
    const r = await fetch(isian.url, { method: 'POST', headers: { 'content-type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ halaman: HAL, kunci: isian.kunci, oleh: HAL + ':' + nama, ...isi }) });
    const j = await r.json();
    if (!j.ok) {
      const g = j.galat || 'gagal';
      // 20 Nov 2026: kalau penyimpan Apps Script belum di-deploy ulang, koleksi baru ditolak dan fiturnya
      // gagal diam-diam (cuma "tidak tersimpan" kecil di tabel). Sekarang ditulis jelas di bar sambungan.
      if (/koleksi tidak dikenal/.test(g)) tanda('Penyimpan Apps Script masih versi lama: ' + g + ' - minta deploy ulang dulu', true);
      const e = new Error(g); e.code = /hanya untuk pusat|tidak boleh|cabang/.test(g) ? 'permission_denied' : 'invalid_argument'; throw e;
    }
    return j;
  };
  const snap = (k) => ({ docs: Object.entries(cache[k] || {}).map(([id, d]) => ({ id, data: () => JSON.parse(JSON.stringify(d)) })) });
  const kabari = (k) => (pendengar[k] || []).forEach((f) => { try { f(snap(k)); } catch (e) { console.error(e); } });
  async function tarik() {
    if (sibuk) return; sibuk = true;
    try {
      const j = await panggil({ aksi: 'daftar', sejak });
      const ubah = new Set();
      for (const d of j.docs) {
        if (!BERSAMA.includes(d.koleksi) && d.halaman !== HAL) continue;
        const c = cache[d.koleksi] || (cache[d.koleksi] = {});
        if (d.dihapus) delete c[d.id]; else c[d.id] = d.data;
        ubah.add(d.koleksi);
        sejak = Math.max(sejak, d.diubah);
      }
      if (!siap) { siap = true; Object.keys(pendengar).forEach(kabari); } else ubah.forEach(kabari);
      tanda('tersambung · ' + new Date().toLocaleTimeString('id-ID'));
    } catch (e) { tanda('penyimpan tidak terjangkau (' + (e.message || e) + ')', true); }
    finally { sibuk = false; }
  }
  const tanda = (t, buruk) => { const s = document.getElementById('webSambung'); if (s) { s.textContent = t; s.style.color = buruk ? '#f08a80' : ''; } };
  const jalan = () => { tarik(); setTimeout(jalan, document.hidden ? 15000 : 4000); };
  const tulis = async (koleksi, id, mode, data) => {
    const j = await panggil({ aksi: 'tulis', koleksi, id, mode, data });
    const h = j.hasil[0];
    const c = cache[koleksi] || (cache[koleksi] = {});
    if (mode === 'delete') delete c[h.id];
    else c[h.id] = mode === 'update' ? { ...(c[h.id] || {}), ...data } : data;
    kabari(koleksi);
    setTimeout(tarik, 300);
    return h;
  };
  const dokumen = (path) => {
    const i = path.indexOf('/'), k = path.slice(0, i), id = path.slice(i + 1);
    return { set: (d) => tulis(k, id, 'set', d), update: (d) => tulis(k, id, 'update', d), delete: () => tulis(k, id, 'delete') };
  };
  const db = {
    collection: (k) => ({
      onSnapshot(cb) { (pendengar[k] || (pendengar[k] = [])).push(cb); if (siap) cb(snap(k)); return () => { pendengar[k] = pendengar[k].filter((f) => f !== cb); }; },
      add: async (d) => { const h = await tulis(k, '', 'add', d); return { id: h.id }; },
      doc: (id) => dokumen(k + '/' + id),
    }),
    doc: dokumen,
  };
  // pusat: nama penyetuju apa adanya (dicatat di acc_oleh); cabang: admin-<cabang>:<nama>
  const uid = HAL === 'pusat' ? nama : HAL === 'pasif' ? 'tim:' + nama : 'admin-' + HAL + ':' + nama;   // tim follow up 24 Nov 2026
  const user = { id: async () => uid, can: async () => true };
  const bacaB64 = (f) => new Promise((ok, gagal) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1]); r.onerror = gagal; r.readAsDataURL(f); });
  const assets = { upload: async (f, o) => {
    if (f.size > 15 * 1024 * 1024) { const e = new Error('besar'); e.code = 'too_large'; throw e; }
    const j = await panggil({ aksi: 'unggah', tipe: (o && o.type) || f.type, nama: (o && o.nama) || f.name, folder: (o && o.folder) || '', b64: await bacaB64(f) });
    return { url: j.url, id: j.id };
  } };
  const layanan = { db, user, assets, mcp: null };
  window.claude = { use: async (n) => (n in layanan ? layanan[n] : null) };
  jalan();
}
