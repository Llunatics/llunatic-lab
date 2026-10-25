---
title: "Dari Read-Only Jadi Superuser: Zero-Day VeloCloud Arista dan Serangan Ketiga ke Control Plane SD-WAN"
date: 2026-10-25
tags: [threat-intel, zero-day, sd-wan, privilege-escalation]
excerpt: "Advisory Arista 22 Oktober menggambarkan celah SQL injection yang mengubah akun VeloCloud paling rendah haknya menjadi operator penuh — celah Orchestrator ketiga yang dieksploitasi sejak Juli, dan yang pertama hanya membutuhkan login."
cover: /assets/covers/arista-velocloud-zero-day-read-only-to-superuser.jpg
---

Ada jenis ketakutan khusus yang hanya muncul pada kerentanan yang bahkan tidak perlu membobol masuk. Pada 22 Oktober 2026, Arista Networks mengungkapkan bahwa penyerang sudah mengeksploitasi [[zero-day]] di VeloCloud Orchestrator miliknya — dan tiket masuknya bukan kata sandi admin yang dicuri atau rangkaian exploit yang eksotis. Tiketnya adalah login valid apa pun, termasuk akun dengan hak paling rendah yang ditawarkan sistem: Enterprise Read Only.

Baca sekali lagi. Akun yang dirancang hanya untuk *melihat* jaringan kini bisa *menjalankan* jaringan itu.

## Apa yang sebenarnya dikendalikan VeloCloud Orchestrator

Untuk memahami mengapa ini penting, pahami dulu apa itu orchestrator. VeloCloud [[SD-WAN]] (software-defined wide-area networking) menggantikan model lama — di mana setiap kantor cabang membutuhkan router yang dikonfigurasi manual dengan teliti — dengan fabric yang dikelola terpusat. Kantor cabang terhubung lewat perangkat Edge, lalu lintas diarahkan secara cerdas lewat internet dan jalur privat, dan semuanya dikonfigurasi, dipantau, dan diperbarui dari satu tempat: VeloCloud Orchestrator (VCO).

Sentralisasi itu adalah nilai jual utamanya, dan juga risiko utamanya. Siapa pun yang mengendalikan orchestrator mengendalikan kebijakan jaringan setiap site yang dikelolanya: lalu lintas mana yang lewat mana, tunnel apa yang ada, perangkat mana yang dipercaya. Operator membuat akun customer dan partner dari sini, dan setiap partner bisa mengelola sekelompok customer. Jadi celah yang menaikkan satu akun customer read-only menjadi hak operator bukan sekadar bug izin kecil — ini kunci utama ke control plane yang berpotensi mencakup banyak organisasi sekaligus.

Arista mengakuisisi lini produk VeloCloud SD-WAN dari Broadcom, dengan kesepakatan yang diumumkan pada Juli 2025. Produk-produk ini sebelumnya dikenal sebagai VMware SD-WAN by VeloCloud. Silsilah itu penting saat inventarisasi: jika daftar asetmu masih menulis "VMware SD-WAN" atau "VeloCloud", advisory ini ditujukan untukmu.

## Celahnya: CVE-2026-114625

Kerentanan ini dilacak sebagai [[CVE]]-2026-114625 dan diberi skor 9,9 pada skala CVSS — hampir setinggi mungkin. Ini adalah celah [[SQL injection]] di orchestrator: input yang seharusnya diperlakukan sebagai data justru ditafsirkan sebagai perintah database, sehingga penyerang bisa membengkokkan database aplikasi itu sendiri sesuai kehendaknya. Hasil praktisnya di sini adalah [[privilege escalation]] dari Enterprise Read Only — peran bawaan paling rendah untuk pengguna customer — ke hak operator, yang secara efektif berperan sebagai superuser lokal dengan akses penuh ke orchestrator.

Tiga detail dari advisory Arista membuat celah ini lebih buruk daripada bug privilege escalation biasa:

1. **Hanya butuh login, bukan admin.** Kredensial read-only apa pun yang bocor, dipakai bersama, atau usang sudah cukup. Organisasi rutin memberikan akses read-only kepada kontraktor, auditor, mitra managed-service, dan mantan staf yang akunnya masih menggantung. Setiap akun itu kini berpotensi menjadi superuser.
2. **Orchestrator terekspos secara default.** Arista menyatakan dengan jelas bahwa VCO terekspos secara default dan tidak ada setelan VCO yang mencegahnya. Tidak ada tombol untuk menyembunyikannya; eksposur harus dikendalikan di lapisan jaringan, dengan membatasi jaringan mana saja yang bisa mencapai antarmuka webnya.
3. **Dampaknya bisa melampaui orchestrator itu sendiri.** Arista menyebut celah ini bisa memungkinkan penyerang memengaruhi host VCO itu sendiri serta mengekspos, mengubah, atau mengganggu orchestrator dan data yang dikelolanya. Untuk celah Juli dan September, Arista memperingatkan bahwa orchestrator yang dikompromikan juga bisa memberi akses ke perangkat VeloCloud Edge; untuk celah ini, advisory tidak menyatakan apakah risiko itu berlaku — ketidakpastian yang harus diperlakukan sebagai alasan untuk menyelidiki, bukan sebagai penenang.

## Serangan ketiga sejak Juli

Bagian inilah yang seharusnya mengubah cara pandangmu terhadap profil risiko produk ini. CVE-2026-114625 adalah celah VeloCloud Orchestrator ketiga yang dilaporkan Arista telah dieksploitasi sejak akhir Juli 2026:

- **Juli:** CVE-2026-16812, dieksploitasi tanpa autentikasi.
- **September:** CVE-2026-93952, juga dieksploitasi tanpa autentikasi.
- **Oktober:** CVE-2026-114625, dieksploitasi dengan login valid apa pun.

Perhatikan polanya. Dua celah pertama tidak membutuhkan kredensial sama sekali; celah ketiga hanya membutuhkan kredensial terlemah. Penyerang kini sudah membuktikan, tiga kali dalam tiga bulan, bahwa mereka bisa menjangkau dan menyalahgunakan control plane orchestrator. Ini bukan lagi rangkaian nasib buruk — ini bukti bahwa orchestrator adalah target yang aktif diburu, dan menambal satu celah sambil menunda yang berikutnya adalah strategi yang kalah. Perlu dicatat, orchestrator yang menjalankan rilis perbaikan celah Juli dan September *masih* rentan terhadap celah ini, karena rilis perbaikan itu lebih tua daripada perbaikan baru. "Bulan lalu sudah kami patch" bukan pembelaan di sini; hanya build baru yang spesifik yang dihitung.

## Siapa yang terdampak, dan apa perbaikannya

Untuk orchestrator on-premises, perbaikannya spesifik per lini rilis:

| Lini rilis | Diperbaiki di |
| --- | --- |
| 5.2 | 5.2.3.18 dan yang lebih baru |
| 6.1 | 6.1.3.10 dan yang lebih baru |
| 6.4 | 6.4.2.12 dan yang lebih baru |

Orchestrator Hosted dan Dedicated sudah ditambal oleh Arista, jadi customer pada model deployment itu tetap harus memverifikasi statusnya, bukan sekadar mengasumsikannya. Perangkat VeloCloud Gateway dan VeloCloud Edge tidak terdampak celah ini, dan lini rilis 7.0 tidak ada dalam daftar rentan — Arista menyatakan rilis apa pun yang tidak ada dalam daftar berarti tidak rentan. Satu catatan: Arista belum memeriksa rilis yang sudah mencapai akhir dukungan, jadi customer pada lini yang tidak didukung sebaiknya menghubungi Technical Assistance Center Arista tentang opsi upgrade, bukan menebak-nebak.

Ada satu ujung longgar yang patut diperhatikan: per 22 Oktober, celah September hanya diperbaiki di lini 5.2 dan 6.4, dan pada 6.1 celah itu memengaruhi rilis hingga 6.1.3.7 tanpa rilis perbaikan yang terdaftar. Tidak ada advisory yang menyatakan apakah 6.1.3.10 juga memperbaiki celah September. Jika kamu menjalankan 6.1, kejar jawaban itu secara eksplisit ke Arista — jangan berasumsi satu patch menutup kedua lubang.

## Memburu jejak kompromi

Arista telah mempublikasikan dua alamat IP yang teramati melakukan serangan. Blokir keduanya, dan cari jejaknya di log-mu:

- `74.82.197.86`
- `38.54.50.151`

Di luar indikator itu, Arista menyarankan untuk memeriksa log akses web VCO untuk permintaan dengan komponen path yang menyerupai URL secara tidak biasa, karakter yang di-encode, referensi ke layanan lokal atau internal, atau laju permintaan yang abnormal. Sampai rilis perbaikan terpasang, Arista juga merekomendasikan membatasi akses ke antarmuka web VCO hanya ke jaringan administratif tepercaya, memantau aktivitas outbound yang tak terduga dari host VCO, memblokir port outbound yang tidak dibutuhkan operasi normal, mewaspadai backdoor daemon dan webshell, serta meninjau aktivitas administrator terbaru untuk perubahan yang tak terduga.

Jika kamu mencurigai adanya kompromi, amankan bukti sebelum memperbaiki apa pun, bila memungkinkan: log akses web VCO, log aplikasi backend, log sistem dan database, serta timestamp filesystem yang relevan. Poin terakhir ini penting karena satu ketidaknyamanan yang belum terjawab: advisory Arista tidak menyatakan apakah upgrade menghilangkan akses yang sudah didapat penyerang. Menambal menutup pintu; ia tidak mengusir seseorang yang sudah masuk dan menanam persistence. Perlakukan orchestrator yang berpotensi dikompromikan sebagai insiden, bukan sekadar tiket patch: rotasi kredensial, tinjau setiap akun dan perubahan yang dilakukan lewat orchestrator, dan periksa perangkat Edge di hilirnya.

## Checklist mitigasi

1. **Segera upgrade orchestrator on-premises** ke 5.2.3.18, 6.1.3.10, atau 6.4.2.12 sesuai linimu — dan konfirmasi status celah September pada 6.1 secara terpisah.
2. **Letakkan orchestrator di balik kontrol jaringan.** Karena VCO terekspos secara default dan tidak ada setelan yang mengubahnya, batasi antarmuka webnya hanya ke jaringan administratif tepercaya di lapisan firewall atau VPN.
3. **Audit akun read-only seperti akun istimewa.** Celah ini menghapus pembeda keamanan antara "bisa melihat" dan "bisa mengendalikan." Hapus akun usang, tinjau akses partner dan kontraktor, dan terapkan [[MFA]] pada setiap login orchestrator.
4. **Berburu dengan indikator yang dipublikasikan.** Cari dua IP penyerang dan pola log mencurigakan di atas, dalam jendela waktu yang luas — Arista tidak menyatakan kapan serangan dimulai, jadi jangan persempit cakupan perburuanmu.
5. **Asumsikan persistence sampai terbukti sebaliknya.** Jika kompromi mungkin terjadi, amankan log dulu, lalu selidiki akun, perubahan terjadwal, dan akses perangkat Edge sebelum menyatakan insiden selesai.

## Penutup

Industri keamanan suka berkata "assume breach." Kisah VeloCloud memberi frasa itu sisi yang lebih tajam: asumsikan juga bahwa akun dengan hak paling rendah adalah vektor breach. Pengguna read-only seharusnya adalah akun yang aman — akun yang bisa dibagikan bebas karena tidak *bisa* melakukan apa-apa. Tiga celah yang dieksploitasi dalam tiga bulan kini telah menghancurkan asumsi itu dua kali lipat: pertama dengan tidak membutuhkan login sama sekali, lalu dengan hanya membutuhkan login terlemah.

Orchestrator adalah otak dari WAN. Ketika otak itu punya celah yang mengubah pengamat menjadi operator, penambalan bukan jendela pemeliharaan — melainkan keadaan darurat. Periksa versimu, batasi akses ke antarmuka, dan buru log-mu. Para penyerang, kata Arista, sudah melakukannya.

---

*Sumber: [Advisory Arista, 22 Oktober 2026, via The Hacker News](https://thehackernews.com/2026/10/arista-warns-of-critical-velocloud-sql.html); [Arista patches exploited VeloCloud zero-day (Cryptopolitan, Oktober 2026)](https://www.cryptopolitan.com/arista-patches-exploited-velocloud-zero-day-as-sd-wan-risks-mount/).*
