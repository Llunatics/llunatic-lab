---
title: "phpAfterShell: Audit Armada PHP-mu Sebelum Session Berubah Jadi Shell"
date: 2026-11-23
tags: [hands-on, php, vulnerability, patching]
excerpt: "Pada 19 November 2026, PHP merilis perbaikan untuk tujuh celah kritis bernilai 9.2 — dan dua di antaranya mengubah penanganan session PHP sendiri menjadi remote code execution. Kalau kamu sudah menambal PHP2Shell di bulan Oktober, kamu masih rentan. Ini audit hands-on yang bisa kamu jalankan hari ini."
cover: /assets/covers/phpaftershell-php-fleet-audit.jpg
---

PHP menjalankan sebagian besar web — WordPress, Laravel, Drupal, Magento, dan jutaan aplikasi custom di antaranya. Pada 19 November 2026, tim PHP merilis security update untuk semua branch yang masih didukung — 8.2.36, 8.3.37, 8.4.28, dan 8.5.13 — menutup 17 advisory yang mencakup 18 identifier [[CVE]]. Tujuh di antaranya dinilai Critical, masing-masing 9.2 di bawah CVSS 4.0. Pasangan yang jadi headline, dijuluki [[phpAfterShell]], bersembunyi di bagian paling membosankan dari bahasa ini: cara PHP menyimpan session login kamu.

Dan ini bagian yang harus membuatmu berhenti scroll. Perbaikan PHP2Shell bulan Oktober **tidak** mencakup perbaikan phpAfterShell. Kalau timmu sudah menambal di bulan Oktober, mencentang kotaknya, lalu move on, server kamu masih rentan terhadap dua celah ini. Dan karena celahnya ada di penanganan session bawaan PHP — bukan di ekstensi eksotis — jangkauannya adalah semua aplikasi PHP yang mengizinkan user login dan mengunggah file. Alias, hampir semuanya.

Artikel ini adalah audit hands-on. Tanpa teori demi teori: setiap bagian di bawah berakhir dengan perintah yang bisa kamu jalankan atau pengaturan yang bisa kamu periksa.

## Sebenarnya phpAfterShell itu apa

Julukan ini mencakup dua kerentanan di ekstensi `ext-session` PHP, keduanya dinilai CVSS 4.0 9.2 dan keduanya bisa berujung pada [[remote code execution]] tanpa autentikasi:

**[[CVE]]-2026-115560 — ketidakcocokan session serializer.** Fitur session upload progress PHP mencatat progres unggahan file di dalam session user, sebelum satu baris pun kode aplikasimu berjalan. Fitur ini membangun session key dengan menempelkan nilai yang dikendalikan penyerang — misalnya nama file yang diunggah — ke sebuah prefix tetap. Masalahnya adalah perbedaan format: upload progress menyimpan key itu dengan satu serializer (`php_binary` atau `php_serialize`), sementara proses lain bisa membaca session yang sama dengan serializer `php` yang tidak kompatibel. Serializer `php` memakai karakter pipe (`|`) untuk memisahkan session key dari valuenya, jadi sebuah `|` yang diselundupkan di dalam key yang dikendalikan penyerang membuat sebagian key dibaca kembali sebagai data objek yang ter-serialize. Itu [[object injection]] lewat nama file — dan dengan [[gadget chain]] yang cocok di aplikasi, itu berubah menjadi eksekusi kode. Fitur upload progress ini sudah ada sejak PHP 5.4.0.

**[[CVE]]-2026-126714 — file session yang tertimpa sebagian.** Handler session `files` bawaan PHP menulis data session yang diperbarui ke file session yang sudah ada tanpa memotongnya (truncate) terlebih dahulu. Kalau penulisan itu terinterupsi, file tersebut akhirnya berisi campuran data baru dan sisa potongan session lama. Saat PHP kemudian membaca dan melakukan unserialize pada campuran itu, byte yang tadinya sekadar konten string biasa bisa ditafsirkan ulang sebagai objek yang ter-serialize — lagi-lagi [[object injection]], lagi-lagi berpotensi [[remote code execution]] kalau aplikasi punya gadget chain. Kode ini sudah ada sejak PHP 4.1.0.

Ada satu celah ketiga di rilis yang sama yang layak disebut: **[[CVE]]-2026-129289**, bug request smuggling di [[PHP-FPM]]. Saat front end memakai ulang koneksi FastCGI dan aplikasi tidak membaca seluruh request body, sisa byte dari satu request bisa diproses sebagai awal request berikutnya — memungkinkan penyerang tanpa autentikasi melewati routing front end dan menjalankan kode PHP.

Per 20 November, tidak ada satu pun celah ini yang terlihat dieksploitasi di alam liar, dan tidak ada yang terdaftar di katalog [[Known Exploited Vulnerabilities]] milik CISA. Itu kabar baiknya. Kabar buruknya: hal yang sama juga berlaku untuk Java4Shell — selama sekitar satu hari.

## Langkah 1: temukan semua PHP yang kamu jalankan

Binary CLI itu berbohong. `php -v` hanya memberi tahu tentang interpreter command-line, bukan worker yang melayani websitemu. Inventarisasi semuanya:

```bash
# semua binary PHP di mesin ini, beserta versinya
for bin in /usr/bin/php* /usr/local/bin/php* /opt/*/bin/php; do
  [ -x "$bin" ] && echo "$bin: $($bin -v 2>/dev/null | head -1)"
done

# semua worker PHP-FPM yang sedang berjalan beserta versinya
ps aux | grep -E 'php-fpm: (pool|master)' | grep -v grep
php-fpm -v 2>/dev/null; php-fpm8.4 -v 2>/dev/null; php-fpm8.3 -v 2>/dev/null
```

Lalu periksa container dan appliance. PHP bersembunyi di dalam Docker image, produk pihak ketiga, dan appliance vendor yang membundel runtime sendiri — semua itu tidak muncul di package manager kamu, dan memperbarui PHP sistem tidak memperbaikinya. Appliance vendor butuh patch dari vendornya.

| Branch | Rentan | Diperbaiki di |
| --- | --- | --- |
| PHP 8.5 | 8.5.0 – 8.5.12 | **8.5.13** |
| PHP 8.4 | 8.4.0 – 8.4.27 | **8.4.28** |
| PHP 8.3 | 8.3.0 – 8.3.36 | **8.3.37** |
| PHP 8.2 | 8.2.0 – 8.2.35 | **8.2.36** |

PHP 8.6.0, yang dirilis di hari yang sama, juga sudah berisi perbaikan ini. PHP 8.1 dan yang lebih lama tidak menerima patch sama sekali — mereka sudah end of life, dan PHP 8.2 sendiri mencapai end of life pada 31 Desember 2026, jadi ini kemungkinan salah satu rilis keamanan terakhirnya. Kalau kamu masih di 8.1, perbaikannya adalah migrasi, bukan patch.

## Langkah 2: periksa tiga pengaturan session yang penting

Jalankan ini terhadap konfigurasi yang benar-benar melayani request web — pool FPM atau `phpinfo()` di halaman sekali pakai yang kamu hapus setelahnya, bukan `php.ini` milik CLI, yang sering berbeda:

```bash
php -i | grep -iE 'session\.(upload_progress\.enabled|serialize_handler|save_handler)'
```

Yang kamu cari:

- **`session.upload_progress.enabled`** — saklar untuk CVE-2026-115560. Kalau aplikasimu tidak menampilkan progress bar unggahan, nilainya harus `0`. Perhatikan jebakannya: rilis yang sudah diperbaiki kini memang mengirim upload progress dalam keadaan **nonaktif secara default**, tapi `php.ini`, paket distribusi, atau panel hosting yang mengaktifkannya akan tetap mengaktifkannya. Verifikasi nilai efektifnya; jangan berasumsi upgrade sudah membaliknya.
- **`session.serialize_handler`** — ketidakcocokan hanya terjadi ketika proses yang berbeda membaca data session yang sama dengan serializer yang berbeda. Setiap pool FPM, virtual host, aplikasi, dan job CLI yang menyentuh penyimpanan session bersama harus sepakat pada satu nilai. Default `php` tidak masalah, selama nilainya *sama* di mana-mana.
- **`session.save_handler`** — `files` adalah handler yang terdampak CVE-2026-126714, dan itu juga default-nya. Beralih ke Redis atau Memcached untuk session adalah langkah hardening yang sah, tapi itu migrasi, bukan patch darurat: patch dulu.

## Langkah 3: periksa pemakaian ulang koneksi PHP-FPM

CVE-2026-129289 membutuhkan front end yang memakai ulang koneksi FastCGI. Periksa milikmu:

```bash
# nginx: pemakaian ulang koneksi ke PHP-FPM
grep -rn 'fastcgi_keep_conn' /etc/nginx/ 2>/dev/null

# Apache: pemakaian ulang koneksi ke PHP-FPM
grep -rn 'enablereuse' /etc/apache2/ /etc/httpd/ 2>/dev/null
```

Kalau salah satunya aktif, konfigurasi itu adalah bagian dari eksposur. Menonaktifkan reuse adalah stopgap yang valid selagi kamu menambal; itu bukan pengganti patch.

## Langkah 4: patch, restart, dan verifikasi worker-nya — bukan binary-nya

Upgrade ke rilis perbaikan untuk branch kamu, lalu restart atau reload layanan PHP. Kemudian verifikasi bahwa **worker yang melayani web** sudah menjalankan versi baru, karena binary CLI dan worker FPM bisa berbeda setelah upgrade:

```bash
sudo systemctl restart php8.4-fpm   # sesuaikan dengan branch kamu
php -v                                # CLI — perlu, tapi tidak cukup

# worker-nya: periksa versi yang benar-benar dilayani web server kamu
curl -s -D - https://situs-kamu.example.com/ -o /dev/null | grep -i 'x-powered-by'
```

Halaman `phpinfo()` di host staging menunjukkan versi yang sedang berjalan secara langsung — buat, baca, lalu hapus. Kalau header masih menunjukkan versi lama, worker lama masih hidup, dan patch belum berlaku di tempat yang penting.

## Langkah 5: stopgap, kalau kamu belum bisa menambal hari ini

Kalau penambalan harus menunggu, kecilkan permukaan yang terekspos sekarang — dan perlakukan semua langkah di bawah sebagai sementara, bukan perbaikan:

```ini
; php.ini — atau konfigurasi pool FPM, tempat nilainya tidak bisa di-override
session.upload_progress.enabled = 0
```

```ini
; konfigurasi pool PHP-FPM
php_admin_flag[session.upload_progress.enabled] = off
```

Atur di `php.ini` atau konfigurasi pool, sebelum ada input request yang diproses — panggilan `ini_set()` di level aplikasi sudah terlambat, karena upload progress berjalan saat request parsing, sebelum kode kamu dieksekusi. Lalu restart worker-nya. Ini menutup jalur mudah untuk CVE-2026-115560, tapi tidak berpengaruh apa-apa terhadap CVE-2026-126714: celah file handler tidak bergantung pada upload progress sama sekali. Kalau aplikasimu memang membutuhkan upload progress, aktifkan hanya di tempat ia dipakai, dan pastikan semua proses yang berbagi penyimpanan session itu memakai serializer yang sama.

Setelah mengubah format serialisasi, pertimbangkan untuk mengakhiri masa berlaku atau memigrasikan data session yang sudah ada — record yang ditulis dengan format lama masih bisa dibaca kembali dengan format baru.

## Langkah 6: cari tanda-tanda seseorang sudah mencoba

Menambal tidak membuktikan apa pun tentang masa lalu. Panduan NetSPI blak-blakan soal ini: kalau instalasi PHP yang belum ditambal bisa dijangkau dari internet, perlakukan sebagai berpotensi sudah dikompromikan sampai investigasi selesai. Periksa:

- Crash worker PHP yang tidak biasa, fatal error, atau child process tak terduga di log FPM dan web server kamu.
- Error terkait session, atau ledakan warning unserialization yang gagal, di sekitar endpoint unggahan file.
- Perilaku aplikasi yang tidak bisa dijelaskan — file baru, file yang berubah, atau koneksi outbound dari worker PHP yang tidak cocok dengan traffic normal.

Upaya eksploitasi yang gagal bisa membuat worker crash; yang berhasil jarang mengumumkan dirinya. Kalau ada yang terlihat janggal, selidiki sebelum kamu menyatakan insiden selesai.

## Pelajaran yang bertahan lebih lama dari patch

phpAfterShell bukan cerita tentang edge case yang aneh. Ini cerita tentang fitur yang kebanyakan developer tidak pernah sadar mereka aktifkan — upload progress — di atas sebuah default — session berbasis file — dalam bahasa yang menggerakkan sebagian besar web. Titik masuk penyerangnya adalah nama file dalam unggahan multipart. Pertahanan korbannya adalah sebuah nomor versi.

Itulah mengapa audit di atas diurutkan seperti itu: inventarisasi dulu, karena kamu tidak bisa menambal PHP yang tidak kamu ketahui keberadaannya; pengaturan kedua, karena default adalah eksposurnya; patch ketiga; dan baru kemudian forensiknya. Putaran PHP2Shell di bulan Oktober mengajarkan pelajaran yang sama, dan tim yang menginternalisasinya sudah punya inventaris yang siap saat rilis November tiba. Yang tidak, kini mengerjakan pekerjaan yang sama di bawah bayang-bayang nilai 9.2.

Jalankan enam langkah itu hari ini. Tidak sampai satu jam — dan tidak seperti file session yang menjadi pusat bug ini, apa yang kamu temukan tidak akan tertimpa oleh apa pun yang datang berikutnya.
