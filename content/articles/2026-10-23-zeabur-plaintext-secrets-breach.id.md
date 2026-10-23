---
title: "Zeabur: Ketika Secret Plaintext Membunuh Sebuah Hosting Platform — Bedah Kasus"
date: 2026-10-23
tags: [case-breakdown, secrets-management, cloud-security]
excerpt: "Bukan zero-day. Bukan nation-state. Hanya token admin tanpa masa kedaluwarsa yang disimpan plaintext di config repo — dan itu merenggut 3,2 juta secret, root di 101 server pelanggan, dan akhirnya perusahaan itu sendiri."
cover: /assets/covers/zeabur-plaintext-secrets-breach.jpg
---

Sebuah hosting platform tumbang bulan ini, dan senjata pembunuhnya adalah sebuah configuration repository.

Zeabur — platform developer tempat kamu sambungkan repo GitHub lalu ia yang mengurus build, database, HTTPS, dan server — menerbitkan laporan pembobolan keduanya dalam dua bulan pada 19 Oktober 2026. Antara 14 dan 15 Oktober, penyerang membaca secret dari setiap layanan di shared cluster-nya di sembilan region, menguasai root di 101 server pelanggan, dan menguras database platform: **321.810 akun dan 3.218.965 record environment variable**. Tak lama kemudian, Zeabur mengumumkan akan tutup pada 31 Desember 2026.

Laporan resminya luar biasa jujur, dan ia menyebut akar masalah dalam satu kalimat: *"kredensial admin berumur panjang disimpan dalam plaintext dan bisa dipakai dari internet publik."* Itulah seluruh ceritanya. Selebihnya hanyalah kalimat itu yang terurai dalam slow motion, dan layak dipelajari bingkai demi bingkai — karena kebiasaan yang sama masih hidup di perusahaan-perusahaan yang belum tumbang.

## Babak satu: pembobolan yang tidak selesai diperbaiki

Intrusi Oktober sebenarnya dimulai pada 27 Agustus. Penyerang mengeksploitasi aplikasi NextChat milik pelanggan (v2.16.1, tercatat sebagai CVE-2026-7644) yang berjalan di shared cluster Zeabur. Isolasi antar-tenant yang lemah memungkinkan penyerang menjangkau routing cache berisi API key lawas Zeabur, lalu memakai kunci administrator tim untuk menemukan AWS root key di dalam sebuah layanan internal, lalu membaca environment variable proyek dari database produksi.

Zeabur mengetahuinya pada 28 Agustus dari laporan penyalahgunaan API key — bukan dari monitoring-nya sendiri. Mereka memberitahu pengguna dan merotasi key.

Tapi rotasi itu melewatkan dua hal: sebuah admin token shared-cluster yang dibuat Januari 2024 **tanpa masa kedaluwarsa**, dan AWS key. Keduanya duduk dalam plaintext di sebuah configuration repository privat sejak Januari 2026. Selama hampir dua tahun, token yang bisa mengadministrasikan seluruh cluster tidak pernah kedaluwarsa. Selama sembilan bulan, siapa pun yang bisa membaca repo itu memegang kunci kerajaan.

Inilah pelajaran yang diteriakkan insiden Oktober: [[incident response]] yang setengah-setengah kadang lebih buruk daripada tidak sama sekali, karena menciptakan keyakinan bahwa masalah sudah selesai. Blast radius sudah dipahami, key yang terlihat sudah dirotasi, semua orang menghela napas — sementara satu kredensial yang paling menentukan terus bekerja, diam-diam, di sebuah repository.

## Babak dua: dua jalur, satu plaintext

Pada 14 Oktober pukul 01:36 UTC, penyerang kembali dengan kredensial yang terlewat dan menempuh dua jalur yang akhirnya bertemu di jaringan internal Zeabur.

**Jalur A: shared cluster.** Penyerang memakai AWS key Zeabur, lalu — empat menit kemudian — admin token yang tak pernah kedaluwarsa itu. Detail krusialnya: **antarmuka admin shared cluster bisa diakses dari internet publik**. Token curian tidak butuh pijakan di dalam jaringan, tidak butuh VPN, tidak butuh pivot. Dari luar dunia, langsung ke mahkota sembilan region.

Pukul 12:39, penyerang sudah membaca pengaturan dan secret dari *seluruh layanan* di shared cluster, termasuk environment variable. Mulai 13:40, mereka menjalankan perintah baca di dalam 865 container database pelanggan. Angka dari laporannya mencengangkan: 736 di antaranya adalah instance **n8n**. Dari 607 instance n8n yang diperiksa Zeabur, **602 menyimpan encryption key-nya di environment variable** — dan key itu mendekripsi setiap kredensial pihak ketiga yang disimpan n8n untuk workflow-nya. Jadi membaca environment variable praktis juga membongkar login-login downstream itu, satu rantai kredensial meruntuhkan rantai berikutnya.

Penyerang lalu memakai cluster key yang terlalu berkuasa untuk membaca backup dari cluster lama, menemukan kunci menuju layanan [[secrets management]] Zeabur, dan membaca sekitar 53 production secret — termasuk kredensial admin jaringan internal, akun database platform, dan GitHub App private key. Mereka juga membaca kunci penanda login dan memalsukan sesi sebagai dua akun, salah satunya milik karyawan Zeabur.

**Jalur B: dedicated server.** Sebuah GCP key lama memberi penyerang akses ke pengaturan inisialisasi server, tempat **password root disimpan dalam plaintext**. Mulai 14 Oktober pukul 13:40, penyerang masuk sebagai root ke 101 dedicated server milik 92 pengguna. Mereka menambahkan SSH key milik mereka di 50 server untuk [[persistence]], membuat lima virtual machine, dan menyalin 16 disk pelanggan.

Pada 15 Oktober kedua jalur menyatu: kredensial admin jaringan internal dari Jalur A memungkinkan penyerang menambahkan node miliknya ke jaringan internal Zeabur dari server yang sudah dikuasai, dan antara pukul 16:10–16:47 UTC, mereka membaca database platform lewat node itu — 29 koneksi terpetakan, 8.903 record operasi, seluruh environment variable, seluruh akun.

Ada satu detail yang layak diheningkan sejenak. Zeabur mulai menyelidiki pukul **13:56 UTC pada 15 Oktober, setelah laporan pengguna** — lagi-lagi, bukan dari alarmnya sendiri. Penyerang sudah berada di dalam selama lebih dari 36 jam.

Dan satu catatan kaki yang mengerikan: di tengah serangan, backup harian Zeabur menangkap sebuah *key yang baru saja dirotasi* dan penyerang membacanya dari backup lalu memakainya pukul 20:30. Merotasi secret selagi penyerang bisa membaca backup kamu itu seperti mengganti gembok sambil membagikan salinan kunci baru.

## Apa yang sebenarnya diincar penyerang

Pengamatan laporan tentang niat penyerang sangat revealing. Penyerang mencari API key di database platform, membaca kredensial n8n dan new-api/one-api dalam skala besar, dan mencoba memanggil **Amazon Bedrock** dengan AWS key milik Zeabur. Mereka tidak mengincar profil pengguna — mereka memburu AI service key.

Inilah ekonomi kredensial yang baru. Pada 2026, API key penyedia AI sama berharganya dengan uang tunai: ia menyewa armada GPU orang lain untuk melatih model, menjalankan inferensi, atau menjual ulang akses. Platform hosting yang mengumpulkan nilai paling sensitif pelanggannya — password database, cloud key, AI key, signing secret — menjadi target paling berharga, karena satu pembobolan membayar ke ribuan korban. Itu sebabnya [[exfiltration]] secret jauh lebih buruk daripada [[third-party risk]] yang diajarkan kasus Denmark: ini bukan vendor yang punya akses ke datamu, ini vendor *yang memegang kuncimu*.

## Checklist mitigasi (untuk semua orang, bukan cuma pelanggan Zeabur)

Daftar remidiasi Zeabur sendiri sangat bagus, dan prinsipnya berlaku umum untuk setiap tim yang menyimpan secret:

1. **Rotasi semuanya, lalu cabut nilai lama di penyedianya.** Pelanggan Zeabur diminta mencabut key di AWS, Google Cloud, Stripe, OpenAI, Anthropic dulu, baru menerbitkan yang baru. Mengganti secret hanya di sisimu sementara yang lama masih berfungsi itu teater.
2. **Secret harus kedaluwarsa dan berotasi otomatis.** Token yang dibuat Januari 2024 tanpa kedaluwarsa itu bukan kredensial, itu kunci serep permanen. Kredensial berumur pendek, rotasi otomatis, tanpa pengecualian untuk token "internal".
3. **Jangan pernah menyimpan secret dalam plaintext — di repo, di pengaturan inisialisasi, di mana pun.** Repo privat bukan secrets store. Environment variable bukan enkripsi. Kalau secret-mu bisa dibaca oleh apa pun selain secrets manager dengan audit log, ia sudah bocor secara rohani.
4. **Jauhkan antarmuka admin dari internet.** Seandainya konsol admin shared cluster tidak bisa diakses publik, token curian itu jauh kurang berguna. Admin plane harus di balik kontrol jaringan, [[MFA]], idealnya mutual TLS — bukan satu bearer token dari seluruh dunia.
5. **Terapkan [[least privilege]] pada key internal.** Sebuah key "terlalu berkuasa" yang bisa membaca backup cluster lama menjadi jembatan dari cluster ke layanan secrets management. Setiap kredensial harus memegang akses minimum, supaya satu kebocoran tidak merembet ke berikutnya.
6. **Monitoring seperti kunci pelanggan bergantung padanya — karena memang begitu.** Kedua insiden Zeabur ditemukan lewat laporan pihak luar. Deteksi anomali pemakaian kredensial (token dari jaringan baru, pembacaan massal pukul 01:36 UTC, ribuan secret dibaca sekaligus) adalah kebutuhan dasar.
7. **Perlakukan dedicated server sebagai sudah dikuasai sampai terbukti sebaliknya.** Zeabur menyuruh pengguna terdampak membangun ulang dari nol dan memeriksa `authorized_keys` untuk komentar `@zeabur-pentest`. Dengan akses root dan SSH key yang ditambahkan, tidak ada kata "dibersihkan" — hanya dibangun ulang.

Satu pelajaran struktural layak dapat bingkainya sendiri: **proyek yang mengikuti panduan pasca-Agustus Zeabur dan memindahkan environment variable ke dedicated server milik sendiri berada di luar jangkauan pembacaan database platform.** Desentralisasi secret — menolak menyerahkan semua kunci ke satu platform — adalah pertahanan terbaik, dan ia berhasil. Pelanggan yang paling sedikit mempercayai platform justru paling sedikit terluka.

## Tembakan penutup

Zeabur melakukan beberapa hal dengan benar di akhir: laporan pendahuluan yang detail dan jujur, panduan jelas untuk korban, dan pengumuman terakhir yang suram. Tapi kejujuran setelah kejadian tidak membangkitkan perusahaan yang model keamanannya bergantung pada secret yang tidak pernah kedaluwarsa, tidak pernah dirotasi, dan tidak pernah dilindungi.

Kebenaran yang tidak nyaman adalah bahwa kegagalan-kegagalan di sini semuanya tidak glamor: plaintext di config repo, token tanpa kedaluwarsa, halaman admin di internet, secret tanpa alarm. Tidak ada exploit eksotis. Hanya hal-hal dasar, yang dilewatkan, selama bertahun-tahun — sampai seseorang datang menagih.

Jadi audit plaintext-mu hari ini. Cari di repo-mu untuk `AKIA`, untuk `sk-`, untuk private key yang di-commit "sementara" tiga tahun lalu. Cek token mana di infrastrukturmu yang tidak punya tanggal kedaluwarsa. Karena kasus Zeabur membuktikan satu hal tanpa keraguan: **penyerang yang menemukan kunci serep-mu tidak perlu membobol gembok.** Kamu sudah menyerahkan pintunya.

---

*Sumber: [Laporan insiden keamanan Zeabur Oktober 2026](https://zeabur.com/blogs/october-2026-security-incident) (primer, diterbitkan 19 Oktober 2026); [konteks insiden Agustus dan pengumuman penutupan](https://breachhistory.com/blog/zeabur-second-breach-shutdown-october-2026); buletin Exploit Security, 16–21 Oktober 2026.*
