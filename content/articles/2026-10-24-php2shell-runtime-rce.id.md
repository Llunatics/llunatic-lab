---
title: "PHP2Shell: Saat Runtime-nya Sendiri yang Jadi Celah — Bedah Kasus"
date: 2026-10-24
tags: [case-breakdown, php, vulnerability]
excerpt: "Bukan plugin yang jebol. Bukan password yang ketebak. Dua celah di PHP sendiri memungkinkan penyerang tanpa akun menjalankan kode di server web — dan percobaan eksploitasi pertamanya datang empat hari sebelum patch tersedia."
cover: /assets/covers/php2shell-runtime-rce.jpg
---

Kebanyakan cerita keamanan web dimulai dari bug di kode seseorang. Cerita ini dimulai dari lapisan di bawah semua kode itu.

Pada 21 Oktober 2026, PHP merilis update darurat untuk dua celah kritis di runtime bahasanya sendiri: CVE-2026-109618 dan CVE-2026-109619, yang bersama-sama dijuluki PHP2Shell. Keduanya memungkinkan penyerang tanpa akun mengeksekusi kode di server yang menjalankan PHP, keduanya bernilai CVSS v4.0 9,2, dan keduanya tidak menuntut aplikasi korban ditulis dengan buruk. Situs WordPress dengan kode yang rapi, aplikasi Laravel dengan validasi yang bersih, layanan Symfony tanpa bug yang diketahui — semuanya terekspos, karena celahnya duduk satu lapis di bawah aplikasi, di mesin yang menjalankan aplikasi itu.

Perbedaan itu adalah inti ceritanya. Kamu bisa mengaudit kodemu bertahun-tahun dan tetap melewatkan ini, karena memang tidak ada apa-apa di kodemu yang bisa ditemukan.

## Apa yang sebenarnya rusak

Dua celah ini adalah bug yang berbeda dengan tujuan akhir yang sama.

CVE-2026-109618 terpicu saat PHP kehabisan memori di tengah menyiapkan sebuah request. Sebagian data internal tertinggal dalam keadaan setengah jadi, dan kode pembersih yang berjalan di akhir request tetap mempercayai data yang rusak itu. CVE-2026-109619 soal state yang hidup lebih lama daripada memori yang ditunjuknya: request berikutnya yang diambil oleh worker yang sama bisa bertindak berdasarkan pointer sisa dari request sebelumnya. Dalam kedua kasus, penyerang tidak butuh akun, login, atau akses awal apa pun. Satu request web yang dibuat khusus sudah cukup.

PHP menyatakan semua instalasi yang melayani request web berisiko — PHP-FPM, php-cgi, FrankenPHP, LiteSpeed, dan mod_php Apache. Mod_php menanggung risiko tertinggi, karena di sana [[exploit]] terverifikasi lewat HTTP dengan limit memori dan input bawaan, sebelum kode aplikasi apa pun mulai berjalan. Detail terakhir itu penting: tidak ada middleware, tidak ada aturan firewall di dalam aplikasimu, tidak ada filter input yang kamu tulis yang bisa menghentikannya, karena kodemu belum berjalan sama sekali.

Satu jalur yang terkonfirmasi melewati fitur session upload progress PHP, yang aktif secara default dan memungkinkan aplikasi melacak progres upload file. Fitur itu akan muncul lagi nanti dalam cerita ini, dengan cara yang seharusnya membuat siapa pun yang buru-buru menambal kemarin kembali memperhatikan.

Celah ini dilaporkan oleh peneliti dari Wiz dan Calif, bekerja sama dengan tim keamanan PHP, dan memengaruhi hampir semua versi PHP sampai ke belakang, hingga 5.4. Versi yang sudah diperbaiki adalah PHP 8.5.12, 8.4.27, 8.3.36, dan 8.2.35. Cabang yang lebih tua tidak mendapat rilis bernomor sama sekali: tim PHP menerbitkan backport sumber minimal untuk 7.4, 8.0, dan 8.1, bagi yang membangun dari source atau punya vendor long-term support. Kalau kamu masih di 8.1 atau lebih tua, kalimat "kami sudah update WordPress" tidak pernah jadi jawaban. WordPress tidak membawa PHP. Host-mu, image container-mu, server-mu yang membawa.

## Disclosure yang berantakan di depan publik

PHP2Shell tidak mendapat coordinated disclosure yang rapi. Ia mendapat seminggu penuh kebocoran, patch yang datang lebih awal, dan perdebatan soal siapa yang bergerak duluan.

Rangkaiannya, sejauh yang bisa direkonstruksi dari catatan publik, kira-kira begini. Pada 17 Oktober, jaringan honeypot Amazon merekam percobaan eksploitasi terhadap celah ini — empat hari sebelum patch apa pun ada, selagi kerentanan masih dalam masa embargo. Bagaimana penyerang mendapatkan detailnya masih belum diketahui. Pada 20 Oktober, detail bocor di media sosial menjelang jadwal disclosure 22 Oktober, dan sebuah video [[proof of concept]] keliru dipublikasikan oleh salah satu firma peneliti. Malam itu juga PHP mengumumkan rilis darurat untuk keesokan harinya.

Pada 21 Oktober, Cloudflare mengaktifkan aturan firewall darurat secara default pukul 03:02 UTC, berjam-jam sebelum perbaikan. Pukul 07:41 UTC, vendor container Chainguard menerbitkan image yang sudah berisi patch, sekitar enam jam sebelum rilis terkoordinasi — langkah yang kemudian dikritik PHP Foundation, dan dibela Chainguard dengan alasan mereka bertindak setelah vendor lain melaporkan serangan. Pukul 14:00 UTC, PHP menerbitkan versi yang sudah diperbaiki.

Dalam hitungan jam, watchTowr melaporkan eksploitasi yang teramati di alam liar lewat jaringan honeypot-nya, dan firma lain menggambarkan pemindaian luas yang tidak tertarget. Pada saat yang sama, catatannya lebih berantakan daripada yang ditulis headline. CISA, saat menerbitkan alert-nya, menyatakan belum mengamati eksploitasi. WatchTowr sendiri pada awalnya menggambarkan percobaan, bukan keberhasilan yang terkonfirmasi. PHP Foundation menyatakan [[proof of concept]] yang beredar dan sempat diperiksanya bukan exploit yang berfungsi pada saat rilis. Hingga 22 Oktober, tidak satu pun dari kedua [[CVE]] itu masuk katalog [[KEV]] CISA.

Keberantakan itu bukan catatan kaki. Itu bentuk normal dari seminggu zero-day: sensor yang berbeda melihat hal yang berbeda pada waktu yang berbeda, "exploited in the wild" bisa berarti probe terhadap honeypot dan bukan server yang benar-benar diambil alih, dan belum ada sumber publik yang menyebut satu situs bernama yang terkonfirmasi dibobol lewat PHP2Shell. Menganggap probe sebagai pembobolan melebih-lebihkan kerusakan. Menganggap tidak adanya korban bernama sebagai tanda aman meremehkannya, karena percobaan itu dimulai sebelum patch ada — yang berarti server yang ditambal pada 21 Oktober pun bisa saja sudah diprobe pada 17 Oktober.

Respons praktis di beberapa negara mencerminkan ketidakpastian itu. NSA, CISA, dan FBI menyarankan organisasi yang belum bisa update segera untuk mempertimbangkan menonaktifkan situs webnya. Situs pemerintah dan layanan publik di Belanda, Jerman, Prancis, Belgia, Finlandia, dan Ceko, plus beberapa council di Inggris, padam sebagai pencegahan selagi menambal. Pemadaman itu bukan pengakuan sudah dibobol. Itu wujud kehati-hatian saat runtime di bawah semua yang kamu jalankan berlubang dan perbaikannya belum terpasang.

## Lalu, pada 23 Oktober, advisory kedua

Tepat saat tim-tim menyelesaikan patch darurat, PHP menerbitkan advisory lain pada 23 Oktober — dan gampang disalahpahami, jadi layak dinyatakan dengan presisi.

Isu baru ini, tercatat sebagai CVE-2026-115560, adalah jalur [[remote code execution]] potensial yang melibatkan session upload progress. Tapi ia hanya berlaku dalam kombinasi yang tidak biasa: aplikasi mula-mula mengonfigurasi `session.serialize_handler` sebagai `php_binary` atau `php_serialize`, lalu mengubahnya saat runtime dengan `ini_set()` menjadi `php` sebelum memanggil `session_start()`, selagi session upload progress tetap aktif. Aplikasi yang tidak pernah mengubah serialization handler saat runtime tidak terekspos lewat jalur ini, sekalipun upload progress menyala.

PHP tidak mengeluarkan patch darurat untuknya. Rencananya perbaikan masuk rilis bugfix reguler, dengan advisory lengkap menyertainya, dan pada saat pemberitahuan 23 Oktober itu versi yang terdampak dan skor severity-nya belum dipublikasikan. Mitigasi yang disarankan sederhana:

```ini
session.upload_progress.enabled = 0
```

Kalau kamu sudah menonaktifkan upload progress sebagai respons terhadap advisory 21 Oktober untuk CVE-2026-109619, PHP menyatakan tidak ada tindakan lanjutan yang diperlukan untuk isu ini. Dan menonaktifkan upload progress tidak menggantikan update 21 Oktober. Ia membantu melawan satu jalur dari satu celah. Ia tidak berbuat apa-apa terhadap CVE-2026-109618. Hanya update yang memperbaiki PHP2Shell secara penuh.

Di situlah jebakan advisory kedua ini bagi tim yang sudah lelah: ia tampak seperti darurat lain, dan sekaligus tampak seperti alasan untuk santai. Ia bukan keduanya. Ia isu yang lebih sempit dan membara lebih pelan, menempel pada fitur yang sama, dan ia memberi hadiah tepat kepada orang yang membaca kondisinya, bukan cuma headline-nya.

## Yang benar-benar harus dilakukan

Kalau kamu menjalankan apa pun di atas PHP, checklist-nya pendek dan tidak mengenal ampun:

1. **Periksa runtime-nya, bukan aplikasinya.** Jalankan `php -v` di server yang benar-benar melayani traffic, dan periksa setiap tempat lain PHP bersembunyi: container lain, server staging, VPS lama yang tidak ada yang ingat, appliance vendor. Palo Alto Networks menghitung 22,6 juta instance terekspos yang berpotensi rentan dari telemetrinya sendiri — ekor panjang PHP yang terlupakan itulah attack surface yang sesungguhnya di sini.
2. **Update, lalu restart.** Pindah ke 8.2.35, 8.3.36, 8.4.27, atau 8.5.12 (atau paket vendor yang sudah ditambal), dan restart setiap worker PHP: pool FPM, Apache, worker yang berjalan lama. Binary yang sudah ditambal dan duduk di disk selagi worker lama terus melayani request bukanlah kondisi sudah ditambal.
3. **Jangan percaya setting sebagai pengganti.** Orang-orang PHP sendiri mengatakannya dengan blak-blakan di minggu rilis: perubahan konfigurasi tidak akan menyelamatkanmu. Aturan WAF, termasuk aturan darurat Cloudflare, adalah penahan sementara yang membeli waktu berjam-jam. Menyetel `fatal_error_backtraces = 0` memblokir satu jalur terkonfirmasi kalau kamu benar-benar belum bisa update saat itu juga. Tidak satu pun dari itu adalah perbaikan.
4. **Kalau kamu terekspos sebelum patch, lihat ke belakang, bukan cuma ke depan.** Periksa apakah worker PHP menelurkan shell, interpreter, atau download tool, dan apakah ada proses atau file tak terduga dari jendela 17–21 Oktober. Kalau kamu tidak bisa memastikan sebuah server bersih selama jendela itu, rotasi secret yang dipegang server tersebut. Patch menutup pintu; ia tidak mengusir siapa pun yang sudah lebih dulu masuk.
5. **Untuk isu 23 Oktober, periksa satu hal di kodemu.** Cari pemanggilan `ini_set` yang menyentuh `session.serialize_handler`. Kalau tidak ada yang ketemu, advisory ini bukan daruratmu. Kalau ketemu, nonaktifkan upload progress sampai perbaikan reguler tiba.

Pelajaran yang lebih dalam kurang teknis dan lebih tidak nyaman. Kebanyakan tim punya proses untuk mengupdate dependency dan hampir tidak punya proses untuk mengupdate runtime. Framework mendapat alert Dependabot dan changelog yang dibaca orang. PHP sendiri, benda di bawah framework itu, diupdate saat host melakukannya, atau saat base image container dibangun ulang, atau tidak pernah. PHP2Shell adalah apa yang terjadi saat celah itu bertemu celah yang tidak membutuhkan bug aplikasi apa pun.

Kodemu bisa saja aman. Runtime-mu belum tentu. Sampai kamu bisa menjawab, tanpa menebak, versi PHP apa yang sebenarnya dijalankan setiap servermu saat ini, kalimat itu berlaku untukmu.

---

*Sumber: [FAQ PHP2Shell watchTowr](https://watchtowr.com/intelligence/php-cve-2026-109618-faq/) (linimasa eksploitasi dan versi perbaikan); [The Hacker News, patch darurat PHP](https://thehackernews.com/2026/10/php-issues-emergency-patches-for-two.html) (linimasa disclosure dan peneliti); [Panduan versi PHP2Shell yang sudah ditambal](https://cve.tools/blog/php2shell-cve-2026-109618-cve-2026-109619) (rilis perbaikan, backport, dan setting penahan sementara); [Percobaan honeypot Amazon, 17 Oktober](https://www.siliconreport.com/hackers-attempted-to-exploit-php-flaws-before-patches) (percobaan eksploitasi sebelum disclosure); [Advisory PHP 23 Oktober soal session upload progress](https://www.analyticsinsight.net/news/new-php-security-flaw-raises-concerns-after-emergency-patches) (kondisi CVE-2026-115560 dan mitigasi).*
