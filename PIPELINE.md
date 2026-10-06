# Pipeline artikel otomatis — playbook cron worker

Jadwal: Senin, Rabu, Jumat, Minggu pukul 07:00 WIB (4x/minggu).
Tujuan: riset → tulis → build → push, tanpa campur tangan user.
Repo: `Llunatics/llunatic-lab`. Push via skill `github-push` (pakai konektor
`custom.github`). Vercel auto-deploy setiap push ke branch utama.

## Langkah

1. **Pilih topik.** Baca judul + tag artikel yang sudah ada (`content/articles/`),
   jangan mengulang topik yang sama dalam 8 minggu terakhir. Rotasi kategori:
   threat-intel → tutorial-praktis → bedah-konsep → tools → bedah-kasus → ulangi.
   Prioritaskan yang sedang ramai: CVE kritis baru, breach besar, atau teknik
   yang lagi dibahas komunitas.

2. **Riset (wajib, jangan halusinasi).** Gunakan `browser.search` (vertical `news`
   untuk kabar terbaru) atau `browser.deep_research` untuk topik berat.
   Catat: fakta kunci, angka, nama, tanggal, dan 2–4 URL sumber. JANGAN mengarang
   nomor CVE, nama perusahaan korban, atau tanggal kejadian.

3. **Tulis artikel** ke `content/articles/YYYY-MM-DD-slug.md`:
   - Frontmatter: title, date (hari ini), tags (2–4, huruf kecil, strip),
     excerpt (1–2 kalimat), cover (`/assets/covers/<slug>.jpg`).
   - Bahasa Indonesia, 800–1500 kata, target pembaca campuran.
   - Struktur: hook pembuka → penjelasan → detail teknis → mitigasi/langkah
     praktis → penutup yang nempel di kepala.
   - Istilah teknis dibungkus `[[Istilah]]` saat pertama muncul. Kalau istilah
     belum ada di `content/glossary.json`, tambahkan dengan penjelasan
     Indonesia yang ringkas dan akurat.
   - Code block selalu pakai bahasa (```bash, ```python, dsb).

4. **Generate cover** via `media.generate_image`:
   - `output_dir`: `/home/hatch/workspace/llunatic-lab/assets/covers`
   - `name`: slug artikel, `output_format`: `jpg`
   - Prompt: dark editorial illustration, aksen lime-green, sinematik,
     minimalis, **tanpa teks/huruf/angka sama sekali**. Sesuaikan dengan topik.

5. **Build**: `cd /home/hatch/workspace/llunatic-lab && python3 scripts/build.py`.
   Pastikan tidak error dan artikel baru muncul di `public/`.

6. **Push**: `git add -A && git commit -m "artikel: <slug>"` lalu push via
   skill `github-push`. Jangan push kalau build gagal.

7. **Lapor ke user** via WhatsApp (chat ini): judul artikel + 1 kalimat isi +
   link Vercel (format link inline diikuti teks, JANGAN di akhir pesan).

## Aturan keras

- Tidak ada fakta tanpa sumber yang diverifikasi di langkah 2.
- Tidak ada plagiarisme: tulis ulang dengan gaya llunatic-lab, jangan
  copy-paste sumber.
- Kalau riset buntu (topik tidak cukup sumber), ganti topik — jangan dipaksakan.
- Satu artikel per run. Kalau gagal di tengah, jangan commit setengah jalan.
