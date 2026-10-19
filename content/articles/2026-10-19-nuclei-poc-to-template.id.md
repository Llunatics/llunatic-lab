---
title: "Dari PoC ke Deteksi dalam Hitungan Menit: Template Nuclei Pertamamu"
date: 2026-10-19
tags: [nuclei, vulnerability-scanning, hands-on, tools]
excerpt: "Saat CVE kritis muncul, PoC exploit beredar di GitHub dalam hitungan jam — dan pemindaian massal menyusul. Nuclei memungkinkanmu memindai infrastrukturmu sendiri secepat itu, dengan mengubah proof of concept menjadi template YAML yang bisa dibagikan. Ini cara kerja tool-nya, cara menulis template pertamamu, dan pagar pengaman agar tidak berbalik menyerangmu."
cover: /assets/covers/nuclei-poc-to-template.jpg
---

Sebuah [[CVE]] kritis muncul di Selasa pagi. Menjelang siang, seseorang sudah mempublikasikan [[proof of concept]] exploit yang berfungsi. Menjelang malam, botnet sudah memindai internet secara massal untuk mencari korban. Di antara "dipublikasikan" dan "dibobol" ada jendela waktu yang dihitung dalam jam — dan satu-satunya pertanyaan yang penting adalah siapa yang memindai infrastrukturmu *lebih dulu*: kamu, atau mereka.

Perlombaan itulah alasan [[Nuclei]] ada. Dibuat oleh ProjectDiscovery sebagai scanner open-source yang ditulis dalam Go, ia tidak datang dengan daftar pemeriksaan yang kaku. Ia datang dengan sebuah engine — dan pemeriksaannya sendiri berupa file YAML polos yang disebut template. Komunitas memelihara lebih dari 12.000 template yang mencakup CVE, miskonfigurasi, file yang terekspos, dan kredensial default, dan proyek ini meraih puluhan ribu bintang di GitHub justru karena modelnya berhasil: begitu sebuah [[vulnerability|kerentanan]] dipahami, siapa pun bisa mengenkripsinya menjadi template dan membagikannya.

## Idenya: kerentanan sebagai kode

Template adalah deskripsi [[vulnerability|kerentanan]] yang bisa dieksekusi mesin. Ia berkata: kirim request *ini*, cari *itu* di responsnya, dan laporkan sebagai temuan jika cocok. Formatnya YAML, kurva belajarnya satu sore, dan hasilnya adalah logika deteksimu bisa berpindah — dari laptop satu analis ke pipeline CI, pemindaian malam hari, dan otomatisasi seluruh tim.

Berikut contoh nyata yang bisa langsung dijalankan. Ia mendeteksi file `.git/HEAD` yang terekspos — kesalahan klasik "repositorinya ikut ke-deploy" yang membocorkan nama branch dan hash commit:

```yaml
id: git-head-exposure

info:
  name: Exposed Git HEAD Detection
  author: llunatic
  severity: medium
  description: Detects publicly accessible .git/HEAD files leaking repository metadata.
  tags: exposure,git,config

http:
  - method: GET
    path:
      - "{{BaseURL}}/.git/HEAD"

    matchers:
      - type: word
        words:
          - "ref: refs/heads"
        condition: and
```

Baca dari atas ke bawah: `id` adalah slug unik, `info` membawa metadata yang dibutuhkan manusia (nama, severity, tags), dan blok `http` adalah bagian mesinnya — satu request GET, satu matcher yang hanya menyala ketika respons benar-benar mengandung `ref: refs/heads`. Disiplin matcher inilah yang membedakan scanner dari mesin penghasil noise: kondisinya harus menggambarkan keadaan yang rentan, bukan sekadar "servernya menjawab."

Matcher punya beberapa rasa — `word`, `regex`, `status`, `binary`, `dsl` — dan bisa digabung dengan `and`/`or`. Rasa DSL adalah senjata pamungkasnya: kamu bisa menulis ekspresi atas respons seperti `contains(body, 'admin') && status_code == 200`, dan begitulah para peneliti mengenkripsi logika halus dari PoC exploit nyata.

## Menjalankannya: setup lima menit

```bash
# install (Go 1.24+)
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# tarik pustaka template komunitas
nuclei -update-templates

# pindai satu target, hanya temuan high dan critical
nuclei -u https://your-target.example -severity high,critical -silent
```

Beberapa flag mengerjakan sebagian besar pekerjaan. `-t` memilih template mana yang dijalankan (direktori seperti `exposures/`, sebuah tag, atau satu file). `-severity` menyaring noise. `-tc` memungkinkanmu menulis kondisi template seperti `"contains(tags, 'xss') && contains(tags, 'cve')"`. Dan `-as` menjalankan pemindaian otomatis yang lebih dulu mem-fingerprint technology stack target — ala Wappalyzer — lalu hanya menembakkan template yang relevan dengan temuannya, jadi kamu tidak menghujani aplikasi Django dengan pemeriksaan WordPress.

Engine-nya cepat secara default — rate limit yang bisa disetel, host paralel, dan template paralel — dan justru karena itulah kamu hanya boleh mengarahkannya ke apa yang kamu miliki. Nuclei mengirim request dan probe sungguhan. Menjalankannya ke infrastruktur yang tidak kamu otorisasi untuk diuji bukanlah "riset"; di kebanyakan yurisdiksi itu masalah hukum. Tentukan scopenya, minta sign-off, catat apa yang kamu pindai.

## Pipeline-nya: recon masuk ke scanning

Nuclei jarang berjalan sendirian. Pola standar komunitas merangkainya di belakang reconnaissance, tiap tool menyuapi tool berikutnya lewat stdin:

```bash
subfinder -d example.com -silent \
  | httpx -silent \
  | nuclei -t exposures/ -severity medium,high,critical -o findings.txt
```

`subfinder` mengenumerasi subdomain, `httpx` hanya menyimpan yang hidup, dan Nuclei memeriksa yang selamat untuk exposure. Jangan pernah memindai daftar subdomain mentah secara langsung — host yang mati hanya membakar waktu dan kuota. Hasilnya tersedia dalam JSON, JSONL, SARIF, atau Markdown, siap di-triase dengan `jq` atau diteruskan ke sistem ticketing.

## Dari PoC ke template: konversinya

Inilah workflow yang memenangkan perlombaan Selasa pagi. Seorang peneliti mempublikasikan PoC untuk CVE baru — misalnya path traversal di mana request ke `/download?file=../../../../etc/passwd` mengembalikan isi file. Mengonversinya bersifat mekanis:

1. **Reproduksi** PoC-nya terhadap target lab dan tangkap request serta respons persisnya.
2. **Identifikasi invarian** — bagian respons yang hanya dihasilkan server yang rentan (misalnya string `root:x:0:0`).
3. **Enkripsi**: satu blok request `http` berisi path payload, satu matcher `word` pada invarian, metadata severity dan CVE di `info`.
4. **Validasi** terhadap target yang diketahui rentan dan yang diketahui sudah di-patch. Template yang menyala di keduanya lebih buruk daripada tidak ada template sama sekali.

Ketika invarian-nya bersifat behavioral bukan tekstual — jeda waktu, callback DNS — integrasi `interactsh` di Nuclei menangani deteksi out-of-band: template menanam URL callback yang unik dan temuan menyala saat target "menelepon pulang".

## Pagar pengamannya (dipelajari dengan cara yang keras)

Dua advisory dari rilis Nuclei v3.8.0 (18 April 2026) layak diperhatikan setiap operator scanner: GHSA-29rg-wmcw-hpf4, di mana template berprotokol JavaScript bisa membaca file lokal di luar sandbox-nya, dan GHSA-jm34-66cf-qpvr, di mana ekspresi yang dievaluasi dari sumber non-template membuka vektor remote-code-execution dari template jahat. Pelajarannya blak-blakan: **template adalah kode, dan kode dari orang asing berjalan dengan hak aksesmu.** Tarik template dari sumber yang kamu percaya, pin versi yang kamu audit, dan upgrade segera — rilis yang sama juga membawa ekspor hasil ke PDF, penganalisis konteks refleksi XSS, dan pendeteksi honeypot, jadi tetap mutakhir membayar dua kali lipat.

Dan pagar pengaman tertua tetap berlaku: scanner memberitahumu *ke mana harus melihat*, bukan *apa yang benar*. Setiap temuan layak diverifikasi manual sebelum menjadi tiket, laporan, atau page jam 2 pagi.

## Yang bisa dibangun minggu ini

Kalau kamu di sisi defensif, langkah dengan leverage tertinggi itu membosankan: pemindaian Nuclei tiap malam terhadap daftar aset eksternalmu, disilangkan dengan feed [[KEV]] terbaru, dengan temuan yang dirutekan ke tempat yang dibaca manusia. Kesenjangan yang membuat organisasi dibobol jarang soal kecanggihan exploit — melainkan soal berminggu-minggu sistem yang diketahui rentan dibiarkan terekspos antara pengungkapan dan seseorang yang benar-benar memeriksa. Scanner yang berjalan tiap malam menutup kesenjangan itu. Yang berjalan tiap kuartal tidak.

Jam exploit mulai berdetak saat PoC dipublikasikan. Dengan template engine di tanganmu, jam deteksimu bisa mulai di saat yang sama. Tulis templatenya, pindai estatemu, patch sebelum makan siang — dan CVE Selasa pagi menjadi sekadar hari Selasa biasa, bukan insiden.
