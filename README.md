# llunatic-lab

Security notes dari sisi gelap internet — ditulis oleh **kou**.

Static site (tanpa framework, tanpa build step di server). Artikel ditulis dalam
Markdown di `content/articles/`, lalu `scripts/build.py` (stdlib Python saja,
tanpa dependensi) me-render semuanya ke `public/`.

## Struktur

```
content/articles/*.md    artikel (frontmatter: title, date, tags, excerpt, cover)
content/glossary.json    istilah teknis + penjelasan Indonesia (untuk tooltip hover)
assets/css, assets/js    tema noir-editorial (dark default, light toggle)
assets/covers            cover tiap artikel
templates/base.html      kerangka halaman
scripts/build.py         static site generator
public/                  output siap-deploy (di-commit)
```

## Cara nambah artikel

1. Tulis file `content/articles/YYYY-MM-DD-slug.md` dengan frontmatter.
2. Tandai istilah teknis dengan `[[Istilah]]` — otomatis jadi tooltip hover
   kalau istilahnya ada di `glossary.json`. Kalau belum ada, tambahkan dulu.
3. Generate cover 21:9 yang gelap + aksen lime, simpan di `assets/covers/`,
   rujuk sebagai `/assets/covers/nama.jpg`.
4. Jalankan `python3 scripts/build.py`, cek `public/`, commit + push.
   Vercel auto-deploy dari branch utama.

## Standar tulisan

- Bahasa Indonesia, 800–1500 kata, target pembaca campuran.
- Jangan halusinasi nomor CVE / nama breach — verifikasi dulu via riset.
- Istilah teknis selalu dibungkus `[[...]]` saat pertama muncul.
