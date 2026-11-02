---
title: "Sudah Di-patch di Atas Kertas, Masih Rentan di Produksi: Audit Hands-On Node2Shell"
date: 2026-11-02
tags: [hands-on, nodejs, vulnerability, patching]
excerpt: "Node.js memperbaiki Node2Shell pada 21 Oktober, tapi string versi berbohong, runtime bersembunyi di dalam container, dan npm update tidak berpengaruh apa-apa. Audit ini menunjukkan cara membuktikan — bukan sekadar mengasumsikan — bahwa setiap Node.js di estate kamu benar-benar sudah di-patch."
cover: /assets/covers/node2shell-brotli-patch-audit.jpg
---

Ada satu bentuk rasa aman yang palsu, yang baru muncul setelah patch Tuesday yang terasa sudah beres. Kamu membaca advisory, menjalankan upgrade, dashboard berubah hijau — dan di suatu tempat, di dalam container image yang tidak pernah di-rebuild, runtime lama masih melayani traffic. [[CVE]]-2026-111497, yang dijuluki Node2Shell, memang dirancang untuk menghukum rasa percaya diri semacam itu. Perbaikannya rilis pada 21 Oktober 2026. Audit yang membuktikan kamu benar-benar sudah menerapkannya adalah topik artikel ini.

Node2Shell adalah [[out-of-bounds write]] di dalam decoder [[Brotli]] yang dibundel bersama [[Node.js]]. Brotli adalah format kompresi yang dipakai browser dan server berdampingan dengan gzip untuk mengecilkan traffic HTTP, dan Node.js menyertakan decoder Brotli di dalam `node:zlib`. Ketika decoder bertemu stream buatan penyerang dengan block-type switch yang tidak valid, ia salah menangani error tersebut dan terus menulis melewati ujung buffer internal yang kecil. Korupsi memori itu bisa membuat proses crash, membocorkan isi memori, atau — seperti yang didemonstrasikan Red Team Imperva pada 22 Oktober — menjalankan kode buatan penyerang. Proof of concept mereka menjalankan kode di dalam image resmi [[Node.js]] 24.22.0 Linux arm64 tanpa debugger dan tanpa custom build, lewat body request terkompresi maupun response terkompresi. Input yang sama ditolak oleh rilis perbaikan 24.22.1. CNA Google memberi skor CVSS 9.2 untuk celah ini; Node.js sendiri menilainya High. Pada 27 Oktober, [[CISA]] memasukkannya ke katalog [[KEV]], dengan tenggat perbaikan federal 10 November 2026 — sinyal formal bahwa penyerang sudah memanfaatkannya. Firma threat-intel ELLIO melaporkan exploit buatan penyerang mencapai sensor mereka pada 26 Oktober, dan scanner sudah aktif memindai host yang men-decompress body Brotli.

## Kenapa celah ini menjangkau kamu meski kamu tidak pernah menyentuh kompresi

Sebagian besar tim yang menjalankan Node.js tidak pernah menulis satu baris pun kode Brotli, dan justru di situlah masalahnya. Decoder ini dijangkau lewat tiga jalur yang mungkin tidak pernah kamu pilih secara sadar.

Pertama, request masuk. Express 5 dan body-parser 2 men-decompress body request yang dikirim dengan `Content-Encoding: br` secara default, karena opsi `inflate` di body-parser aktif kecuali kamu mematikannya. Aplikasi dengan `app.use(express.json())` yang biasa saja pun bisa dijangkau oleh satu request buatan penyerang, sebelum login apa pun, sebelum kode aplikasimu sendiri berjalan. Aplikasi Koa dan NestJS mewarisi perilaku yang sama lewat parser mereka.

Kedua, request keluar. `fetch()` bawaan Node.js meminta dan men-decompress response Brotli secara otomatis. Server apa pun yang dipanggil kodemu — webhook yang kamu panggil balik, link previewer, scraper, AI agent yang mengambil URL kiriman user — bisa menyodorkan stream berbahaya ke decoder kamu. Penyerang bahkan tidak perlu menyentuh servermu; cukup mengendalikan server yang dihubungi servermu.

Ketiga, pemanggilan langsung. Kode apa pun yang memanggil fungsi Brotli di `node:zlib` atas data dari luar ikut terekspos. Server HTTP Node.js polos yang tidak pernah men-decompress apa pun memang tidak terekspos — decoding harus terjadi agar celah terpicu — tapi begitu middleware atau library melakukannya untukmu, kamu masuk ke dalam scope.

Blast radius-nya tidak berhenti di Node.js. Bug ini hidup di library Brotli C milik Google, sehingga ikut memengaruhi Bun (diperbaiki di 1.4.4), paket Python Brotli (1.2.1) dan brotlicffi (1.2.1.0), serta .NET, yang Microsoft tambal lewat update out-of-band pada 25 Oktober. Tapi audit ini fokus ke Node.js, karena di sanalah jebakan versinya berada.

## Jebakannya: string versi berbohong

Inilah detail yang membuat audit ini layak dilakukan alih-alih mempercayai dashboard. Node.js mengambil perbaikan Brotli lewat cherry-pick tanpa mengubah string versi Brotli yang dibundel. Akibatnya `process.versions.brotli` melaporkan `1.2.0` baik di build yang sudah di-patch maupun yang belum. Script inventaris, scanner, atau cek compliance apa pun yang membaca versi Brotli akan menyebut server rentan sebagai sudah aman. Satu-satunya cek yang bisa diandalkan adalah versi Node.js itu sendiri: 22.23.4, 24.22.1, atau 26.12.1 — atau rilis yang lebih baru di lini yang masih didukung. Dan `npm update` tidak ada gunanya di sini, karena celah ini ada di runtime, bukan di paket. Lini Node.js 20.x dan yang lebih lama tidak mendapat perbaikan sama sekali; mereka sudah end of life, dan satu-satunya jalan adalah migrasi ke lini yang masih didukung.

Lebih parah lagi, runtime ini pandai bersembunyi. `node -v` di laptopmu tidak memberi tahu apa-apa tentang binary Node di dalam container image, CI runner, bundle serverless, atau developer tool yang membawa runtime sendiri. Audit di bawah ini dirancang untuk menemukan salinan-salinan itu.

## Latihan 1: inventarisasi semua Node.js, bukan cuma milikmu

Mulai dari mesin yang kamu kelola, lalu beralih ke artefak yang kamu kirim. Di host mana pun, daftarkan runtime yang terinstal maupun proses yang sedang berjalan:

```bash
# Runtime yang terinstal: version manager, paket sistem, container
which -a node; ls ~/.nvm/versions/node 2>/dev/null; ls /usr/local/bin/node* 2>/dev/null
ps aux | grep -E "node|bun" | grep -v grep
node -v  # bandingkan dengan 22.23.4, 24.22.1, 26.12.1
```

Lalu audit image-nya, karena di sanalah runtime lama bertahan melewati upgrade. Cari base image di setiap Dockerfile dan definisi CI, dan periksa apa isinya sebenarnya:

```bash
grep -rn "FROM node:" --include="Dockerfile*" .
docker run --rm node:24.22.0 node -v  # contoh: membuktikan tag, bukan fleet kamu
```

Aturannya sederhana: base-image tag yang belum di-pull ulang sejak 21 Oktober patut dicurigai, meski kode aplikasimu berubah kemarin. Rebuild image dengan tag yang sudah diperbaiki, deploy ulang, dan restart setiap proses yang masih memakai runtime lama — binary yang sudah di-patch tapi hanya tersimpan di disk tidak melindungi apa pun selama proses lama terus berjalan.

## Latihan 2: temukan jalur eksposur di kodemu

Mengetahui versimu baru setengah audit. Runtime yang sudah di-patch aman apa pun yang terjadi, tapi runtime yang belum di-patch berbahaya sebanding dengan seberapa banyak Brotli tak tepercaya yang ia decode. Petakan permukaan itu dengan dua pencarian di codebase:

```bash
# Decompress body request: default inflate Express 5 / body-parser
grep -rn "express.json\|express.urlencoded\|express.text\|express.raw\|bodyParser" --include="*.js" --include="*.ts" .

# Decoding outbound: fetch() dan pemakaian zlib langsung atas data luar
grep -rn "fetch(\|brotliDecompress\|createBrotliDecompress" --include="*.js" --include="*.ts" . | head -50
```

Setiap hasil dari pencarian pertama adalah route yang bisa dijangkau lewat body request buatan penyerang. Setiap hasil dari pencarian kedua adalah tempat di mana server jahat bisa menjangkau decoder kamu. Prioritaskan layanan yang menghadap internet dulu, lalu apa pun yang mengambil URL kiriman user — kategori kedua inilah yang paling sering dilupakan tim, karena penyerang tidak pernah menyentuh server mereka secara langsung.

## Latihan 3: buru probing yang mungkin sudah terjadi

Eksploitasi meninggalkan bentuk yang khas di log, dan scanner sudah aktif sejak akhir Oktober. Cari tiga sinyal ini di log reverse-proxy dan aplikasi:

1. **Request POST dengan `Content-Encoding: br`** ke API yang tidak pernah menerima body terkompresi secara sah. Kebanyakan API JSON tidak punya alasan menerima body request Brotli sama sekali.
2. **Body terkompresi yang luar biasa besar**, atau ledakan request terkompresi dari satu sumber — traffic exploit publik yang teramati sejauh ini mencakup request sekitar 23 MB yang diarahkan ke Node.js 24.22.0.
3. **Crash atau restart proses yang tidak bisa dijelaskan** di layanan Node.js, terutama yang berkorelasi dengan request terkompresi. Crash adalah dampak pertama yang paling mungkin dari celah ini, dan ia juga sinyal tersendiri: perlakukan crash decoder sebagai kemungkinan serangan, bukan deploy yang flaky, dan periksa apakah core dump sempat menangkap memori proses sebelum di-rotasi.

Tidak satu pun dari ketiganya membuktikan compromise dengan sendirinya. Bersama-sama, mereka memberi tahu apakah ada yang sudah mengetuk pintu — dan apakah tenggat patching kamu dihitung dalam hari atau menit.

## Latihan 4: patch dengan benar, lalu lapisi fallback

Perbaikannya, dalam urutan prioritas:

1. **Upgrade runtime di semua tempat ia berjalan** — 22.23.4, 24.22.1, atau 26.12.1 atau yang lebih baru di linimu — termasuk container image, CI runner, dan runtime yang dibundel. Restart atau deploy ulang setiap proses setelahnya.
2. **Migrasikan lini end-of-life.** Node.js 20.x dan yang lebih lama tidak menerima perbaikan. Pindah ke LTS 22 atau 24 adalah bagian dari patch ini, bukan proyek terpisah.
3. **Perbaiki saudara-saudaranya.** Bun ke 1.4.4, Python Brotli ke 1.2.1, brotlicffi ke 1.2.1.0, dan .NET ke update out-of-band Microsoft 25 Oktober, di mana pun runtime itu ada di estate kamu.
4. **Baru setelah itu, lapisi mitigasi interim untuk apa pun yang belum bisa di-patch.** Set `inflate: false` pada parser Express 5 dan body-parser 2, atau tolak `Content-Encoding: br` di [[reverse proxy]] kamu. Jujurlah soal apa yang dibeli langkah ini: ia hanya menutup jalur inbound, tidak berbuat apa-apa untuk decoding `fetch()` outbound, dan bisa merusak traffic terkompresi yang sah. Ini tourniquet, bukan obat — dan advisory tidak mencantumkan workaround apa pun di dalam Node.js sendiri.

Tutup loop dengan menjalankan ulang Latihan 1 setelah upgrade dan mencatat hasilnya. Audit yang tidak pernah dijalankan ulang setelah patching hanyalah laporan; proses kedua itulah yang mengubahnya menjadi bukti.

## Pelajaran yang layak disimpan

Node2Shell bukan vulnerability paling eksotis di Oktober 2026, dan justru karena itulah ia guru yang baik. Tidak ada yang membutuhkannya: bukan zero-day di kodemu, bukan misconfig yang kamu buat, bukan dependency yang kamu pilih dengan buruk. Yang dibutuhkan hanyalah: kamu menjalankan runtime populer, library yang tidak pernah kamu pikirkan men-decompress data yang tidak pernah kamu periksa, dan inventarismu mempercayai string versi yang tidak berubah saat bug diperbaiki. Celah berikutnya dari keluarga ini akan bersembunyi di tempat yang sama: library yang dibundel, decoder transitif, base image yang tidak pernah di-pull ulang.

Patch runtime-nya. Rebuild image-nya. Restart prosesnya. Lalu periksa — dengan versi yang benar-benar berkata jujur — bahwa kamu sudah melakukannya.

---

*Sources: [Node2Shell: From Brotli Data to Remote Code Execution (Imperva, October 2026)](https://www.imperva.com/blog/node2shell-from-brotli-data-to-remote-code-execution/); [Researchers Demonstrate Node2Shell RCE Exploit on Node.js Build (The Hacker News, October 2026)](https://thehackernews.com/2026/10/researchers-demonstrate-node2shell-rce.html); [Node2Shell puts Microsoft and Node.js on Brotli patch duty (CSO Online, October 2026)](https://www.csoonline.com/article/4241027/node2shell-puts-microsoft-and-node-js-on-brotli-patch-duty.html); [Node2Shell Vulnerability Actively Exploited in the Wild, CISA Warns (CybersecurityNews, October 2026)](https://cybersecuritynews.com/node2shell-vulnerability/); [Node2Shell (CVE-2026-111497): the Brotli flaw reaching Node.js, Python and beyond (Kage Security Lab, October 2026)](https://kagesecuritylab.com/intel/node2shell-cve-2026-111497/).*
