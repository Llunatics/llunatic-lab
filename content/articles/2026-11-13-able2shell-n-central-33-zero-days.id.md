---
title: "Able2Shell: Bagaimana 33 Zero-Day Melumpuhkan N-central — dan Patch yang Tak Bertahan"
date: 2026-11-13
tags: [threat-intel, rmm, zero-day, n-central]
excerpt: "Di hari Minggu bulan November, seorang peneliti mempublikasikan 33 zero-day di N-able N-central beserta exploit yang bisa langsung dipakai. Senin platform itu offline di seluruh dunia; Kamis, cryptominer sudah berjalan di server yang sudah di-patch. Inilah anatomi disclosure yang melanggar semua aturan — dan minggu yang mengikutinya."
cover: /assets/covers/able2shell-n-central-33-zero-days.jpg
---

Pada hari Minggu, 8 November 2026, seorang peneliti keamanan ofensif bernama Sean Bales melakukan sesuatu yang selama bertahun-tahun coba dicegah industri: ia mempublikasikan lebih dari 30 kerentanan [[zero-day]] di platform N-able N-central, lengkap dengan [[proof of concept]] exploit yang bisa langsung dijalankan, tanpa memberi peringatan lebih dulu kepada vendor. Celah-celah itu diunggah ke GitHub lewat akun "Oracle-Security" dengan nama kolektif **Able2Shell**. Senin siangnya, N-able mematikan lingkungan N-central hosted-nya di seluruh Amerika, Eropa, dan Asia-Pasifik, dan meminta pelanggan yang menjalankan server sendiri untuk mematikannya sampai ada pemberitahuan lebih lanjut. Kamisnya, patch sudah rilis — dan exploit tetap bekerja melawannya.

Ini bukan cerita tentang satu bug yang buruk. Ini cerita tentang apa yang terjadi ketika perangkat lunak yang mengelola komputer orang lain menjadi target, dan tentang disclosure yang melewati semua aturan yang ada.

## Apa itu N-central, dan kenapa ia target yang sempurna

N-central adalah platform [[remote monitoring and management]] (RMM). [[Managed service provider]] (MSP) memakainya untuk mengawasi, menambal, dan mengendalikan ribuan mesin klien dari satu konsol. Itulah fungsi produknya — dan itulah masalahnya. Server RMM bisa menjalankan script, menyebarkan perangkat lunak, dan membuka sesi remote ke setiap endpoint yang dikelolanya, sering kali mencakup ribuan mesin milik banyak perusahaan berbeda. Seperti kata Gene Moody, field CTO di Action1, kepada Dark Reading: platform semacam ini memegang "hak istimewa luar biasa" karena memang dibutuhkan untuk bekerja — "dan itu juga membuatnya menjadi target yang sangat menarik."

Sekali server N-central dikompromikan, yang didapat bukan satu perusahaan. Penyerang mendapat pijakan ke setiap perusahaan yang dilayani MSP itu, lengkap dengan mekanisme penyebaran bawaan untuk apa pun yang datang berikutnya. Huntress, yang menyelidiki insiden N-central sebelumnya, memperingatkan bahwa penyerang pada kampanye terdahulu terlihat "menyemprotkan" script dan tool tak sah ke lingkungan downstream begitu platform jatuh.

## Linimasanya: lima hari, tiga babak

**Minggu, 8 November — dump-nya.** Bales mempublikasikan 33 celah yang diduga ada beserta kode exploit, diuji terhadap N-central Appliance 2026.4.0.31, sebuah build pra-rilis, dan ia meyakini sebagian besar atau semuanya juga ada di versi sebelumnya. Ia kemudian mengonfirmasi penemuan itu dibantu AI. Daftarnya mencakup pencurian kredensial anonim, pembuatan akun administrator, dan [[remote code execution]] sebagai root. Firma keamanan watchTowr mengamati probing terhadap celah-celah itu dalam 12 jam setelah publikasi.

**Senin, 9 November — shutdown.** Pukul 15:15 UTC, N-able menyatakan insiden keamanan kritis dan mematikan lingkungan N-central hosted-nya di seluruh dunia "sebagai langkah pencegahan." Pelanggan on-premises didesak mematikan server mereka. Saat itu N-able mengatakan belum melihat eksploitasi aktif — tapi kode exploit sudah publik, dan jam terus berjalan.

**Selasa, 10 November — hotfix.** N-able merilis N-central 2026.4 Hotfix 2 (build 2026.4.1.26), yang memperbaiki tujuh CVE dari disclosure tersebut: CVE-2026-125883 (beberapa kerentanan [[XXE]]), CVE-2026-125878 (beberapa celah injeksi OGNL), CVE-2026-125879 ([[privilege escalation]] lokal), CVE-2026-125880 (stored XSS lewat metadata patch MMS3), CVE-2026-125881 (celah validasi skema), CVE-2026-125882 ([[remote code execution]] lewat path traversal pada upload repositori file, ditemukan oleh Nate Fair dari Sprocket Security), dan CVE-2026-91000 (privilege escalation lokal lewat IPC channel yang tidak aman). Lingkungan hosted di-upgrade; pelanggan on-premises diminta menambal sebelum memulihkan akses.

Tim riset Tenable, yang menganalisis rilis itu, menghitung ada empat rantai exploit di antara 33 celah tersebut. Yang paling signifikan adalah rantai XXE, yang Tenable gambarkan sebagai tanpa kredensial: celah XXE tanpa autentikasi pada fungsi service-import N-central yang mengubah satu request jaringan menjadi kompromi penuh atas sistem manajemen IT pusat. Catatan N-able sendiri untuk CVE-2026-125883 menyatakan tidak butuh hak istimewa maupun interaksi pengguna.

**Kamis, 12 November — sekuelnya.** Dua hari setelah hotfix, Bales mempublikasikan dua set exploit lagi, **4EverAble2Shell** dan **Agent2Shell**, keduanya diuji terhadap build Hotfix 2 itu sendiri. 4EverAble2Shell memberi penyerang tanpa autentikasi akses root di server N-central. Agent2Shell merangkai lebih dari sepuluh zero-day untuk menjalankan perintah sebagai NT AUTHORITY\SYSTEM — hak tertinggi di mesin Windows — pada agen Windows yang dikelola.

Babak kedua ini bergerak cepat. Firma threat intelligence Previdian melihat probing terhadap [[honeypot]] N-central-nya sekitar pukul 08:30 UTC, dan percobaan exploit lengkap dari alamat IP 157.20.241.16 mulai pukul 09:16 UTC. Pukul 12:50 UTC, peneliti di Huntback menghitung 21 miner [[XMRig]] aktif berjalan di server N-central produksi — 19 di antaranya memakai build Hotfix 2 — di tujuh negara: Amerika Serikat, Kanada, Afrika Selatan, Britania Raya, Jerman, Prancis, dan Swedia. Miner-miner itu dikonfigurasi memakai sekitar separuh core CPU yang tersedia, mungkin agar tidak ketahuan. Empat jam, dari proof-of-concept sampai payday.

## Rantainya, dan satu switch yang menentukan

Rantai 4EverAble2Shell dimulai dari CVE-2026-90436, celah bernilai 9.8 di pustaka Apache Axis 1.x yang sudah end-of-life, yang patch-nya dirilis 6 November. Penyerang memakainya untuk eksekusi kode awal, lalu menaikkan hak akses ke root lewat celah N-central yang baru — yang dilacak Previdian sebagai VULN-2026-0009 — dan akhirnya mengunduh serta mengeksekusi shell script dari server penyerang dengan `curl`. Ini adalah percobaan eksploitasi pertama yang terdokumentasi terhadap CVE-2026-90436.

Ada satu syarat, dan syarat ini penting: rantai di sisi server hanya bekerja ketika **Legacy API** N-central diaktifkan dan terekspos ke internet publik. Legacy API mati secara default, dan N-able mengatakan penggunaannya tidak disarankan. Setiap dari 21 server yang terkompromi mengaktifkannya — instalasi lama yang menyalakannya bertahun-tahun lalu untuk integrasi dan tak pernah mematikannya. Itulah seluruh pertahanan sampai N-able merilis perbaikan berikutnya: matikan Legacy API. Belum ada patch untuk 4EverAble2Shell maupun Agent2Shell.

Advisory N-able pada 12 November menyatakan mereka membatasi sejumlah fitur dan integrasi N-central selagi mengerjakan perbaikan lanjutan, menonaktifkan integrasi Intune sebagai pencegahan, dan mengatakan belum melihat tanda kompromi lewat celah baru itu. Ke-21 miner itu, yang dihitung secara publik lengkap dengan timestamp, adalah bantahannya.

## Perdebatan soal disclosure

Separuh lain cerita ini adalah bagaimana celah-celah itu keluar. Bales mengatakan ia mempublikasikan tanpa peringatan karena N-able mengabaikan laporan-laporan sebelumnya. N-able membantahnya, mengatakan celah-celah itu tidak pernah dilaporkan lewat kanal resmi mereka. Bales juga mengatakan N-able belum menambal dua celah remote code execution yang tidak terkait di produk N-able lain, yang ia laporkan ke perusahaan itu pada Juli.

Coordinated disclosure ada karena satu alasan: memberi defender waktu menambal sebelum penyerang mendapat exploit-nya. Disclosure penuh tanpa pemberitahuan, lengkap dengan kode yang bisa dipakai, adalah opsi nuklir — dan persis itulah yang terjadi di sini, dua kali dalam seminggu. Entah kamu menganggap Bales beralasan atau ceroboh, dampak praktisnya sama: jeda antara "exploit dipublikasikan" dan "exploit dipakai" menyusut menjadi hitungan jam. Miner-miner itu tiba empat jam setelah disclosure kedua. Itu tidak cukup waktu untuk mengadakan rapat soal patching. Bahkan untuk membaca advisory pun nyaris tidak cukup.

## Ini bukan kali pertama N-central

Pengulangannya adalah bagian dari cerita. Pada Agustus 2025, CISA menambahkan dua kerentanan N-central, CVE-2025-8875 dan CVE-2025-8876, ke katalog Known Exploited Vulnerabilities setelah keduanya dieksploitasi di lapangan. Pada Agustus 2026, penyerang mengeksploitasi celah authentication-bypass, CVE-2026-18556, lalu menemukan jalan memutar perbaikan awal N-able lewat kerentanan terkait, CVE-2026-18577, memperoleh akses administratif dan memakai fitur Take Control platform itu untuk menjangkau sistem yang dikelola.

Tiga insiden besar dalam lima belas bulan, di platform yang sama, dengan pola yang sama: celah di lapisan manajemen, perbaikan, lalu bypass. Pertanyaan yang diajukan Moody — seberapa besar otoritas yang dikonsentrasikan platform manajemen endpoint di satu tempat — tidak punya jawaban yang nyaman. MFA dan role-based access, katanya, "tidak bisa menahan setiap kompromi platform." Sarannya melampaui saran vendor: simpan secret kritis dan signing key di luar platform sepenuhnya, dan buat endpoint memverifikasi persetujuan yang ditandatangani secara kriptografis untuk operasi berdampak tinggi. "Mencuri kredensial, atau bahkan mengendalikan konsol, seharusnya tidak otomatis memberi otoritas itu. Login saja tidak lagi cukup untuk mengesahkan operasi yang dilindungi."

## Apa yang harus dilakukan kalau kamu bersentuhan dengan N-central

Kalau kamu MSP, admin IT, atau pelanggan yang provider-nya memakai N-central, lakukan ini secara berurutan:

1. **Matikan Legacy API sekarang, kalau aktif.** Ini satu-satunya tindakan paling efektif melawan 4EverAble2Shell. Fitur ini mati secara default — verifikasi, jangan berasumsi.
2. **Terapkan Hotfix 2 (build 2026.4.1.26) kalau belum.** Hotfix ini memperbaiki celah tanpa autentikasi dari batch pertama. N-able mengatakan setiap bug tanpa autentikasi dari disclosure pertama kini sudah diperbaiki. Biarkan server tetap offline atau terisolasi dari internet sampai ditambal.
3. **Tinjau log autentikasi dan administrasi sejak 8 November** — saran Huntress — dan jendela yang lebih lebar menurut Moody, sejak awal November. Cari akun admin yang tak dikenal, sesi remote access yang aneh, dan script baru yang disebar ke endpoint. Kalau menemukan salah satunya, perlakukan sebagai insiden dan libatkan incident response.
4. **Periksa miner.** Penggunaan CPU tinggi yang berkelanjutan sekitar 50% di server N-central, koneksi keluar yang tak wajar — terutama ke 157.20.241.16 — dan unduhan shell script lewat `curl` adalah indikatornya. Anggap server N-central yang terkompromi berarti setiap endpoint yang dikelola berada dalam cakupan sampai terbukti sebaliknya.
5. **Jangan pulihkan akses normal sampai N-able mengeluarkan panduan pemulihan yang aman**, dan simpan log sebelum melakukan perubahan. N-able mengatakan akan memposting update setiap empat jam selama insiden.

Kalau kamu pelanggan dan bukan operatornya, tanyakan tiga hal ke provider-mu: apakah hotfix sudah diterapkan, apakah Legacy API mati, dan apa hasil tinjauan log-nya. Jawabannya harus spesifik, bukan sekadar menenangkan.

## Pelajarannya

Able2Shell adalah studi kasus soal risiko yang terkonsentrasi. Satu platform, satu konsol, ribuan endpoint, dan disclosure yang menyerahkan kunci ke semua orang sekaligus. Hotfix itu membeli waktu sekitar dua hari. Miner-miner itu membeli sisanya. Pertahanan yang berhasil bukanlah patch — melainkan switch konfigurasi, yang mati secara default, yang dihidupkan seseorang bertahun-tahun lalu lalu dilupakan. Audit platform manajemenmu seperti kamu mengaudit aset mahkotamu, karena memang itulah mereka: perangkat lunak yang bisa menyentuh segalanya adalah perangkat lunak yang paling diinginkan penyerang, dan disclosure berikutnya mungkin tidak memberimu dua hari.

*Sumber: Dark Reading, 11 November 2026 (N-able takes N-central offline); The Hacker News, 12 November 2026 (new N-central exploits work against patched servers); security update N-able via uptime.n-able.com; Tenable Research Special Operations; blog Huntress, November 2026; Previdian via The Hacker News; hitungan miner Huntback via Ongoing Ideas, 12 November 2026.*
