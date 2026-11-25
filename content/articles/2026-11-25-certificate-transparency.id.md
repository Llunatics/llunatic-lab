---
title: "Certificate Transparency: Buku Besar Publik yang Menangkap Sertifikat Nakal"
date: 2026-11-25
tags: [concept, certificate-transparency, pki, tls]
excerpt: "Setiap sertifikat TLS yang dipercaya browser-mu wajib ditulis ke dalam log publik yang hanya bisa ditambah, sebelum sertifikat itu diterbitkan. Certificate Transparency mengubah penerbitan sertifikat dari jabat tangan privat menjadi catatan publik — dan pada 2026, aturannya menjadi lebih ketat dari sebelumnya."
cover: /assets/covers/certificate-transparency.jpg
---

Bayangkan orang asing masuk ke bank, menunjukkan KTP dengan namamu, lalu keluar membawa uangmu. Sekarang bayangkan bank itu tidak pernah memberitahumu — karena bank itu memang tidak pernah memeriksa apakah KTP tersebut asli. Begitulah kondisi [[public-key cryptography]] web selama bertahun-tahun: [[certificate authority]] mana pun bisa menerbitkan sertifikat untuk domain mana pun, dan pemilik domain baru tahu setelah kerusakannya sudah terjadi.

[[Certificate Transparency]] (CT) adalah solusinya, dan idenya indah dalam kesederhanaannya: jadikan penerbitan itu publik. Setiap sertifikat TLS yang dipercaya publik wajib ditulis ke dalam log publik yang hanya bisa ditambah, sebelum browser mau menerimanya. Sertifikat nakal tetap bisa diterbitkan — tapi tidak bisa lagi diterbitkan *secara diam-diam*. Kredensial palsu penyerang disiarkan ke seluruh dunia dalam hitungan detik, secara permanen, tanpa cara untuk menariknya kembali. Dan pada 2026, sistem ini mengalami guncangan terbesar sejak diciptakan.

## Insiden yang memaksa web membuka bukunya

CT ada karena web belajar dengan cara yang pahit bahwa mempercayai certificate authority secara diam-diam tidak berhasil. Pada 2011, CA asal Belanda DigiNotar dibobol, dan penyerang menerbitkan sertifikat palsu untuk Google dan domain besar lainnya — sertifikat yang dipercaya browser, yang bisa memungkinkan penyadapan lalu lintas pengguna dalam skala besar. Pemilik domain adalah pihak terakhir yang mengetahuinya.

Jawabannya, yang diusulkan Ben Laurie dari Google dan rekan-rekannya lalu distandarkan sebagai RFC 6962 pada 2013, adalah membalik modelnya: alih-alih meminta pemilik domain memercayai CA secara buta, paksa CA untuk mempublikasikan semua yang mereka terbitkan. Kalau setiap sertifikat bersifat publik, siapa pun bisa mengawasi log untuk domain mereka sendiri dan menangkap sertifikat yang tidak pernah mereka minta. Standar penerusnya, RFC 9162 (CT versi 2.0), menyusul pada Desember 2021.

Skalanya hari ini sungguh luar biasa. Log CT publik menyimpan miliaran sertifikat — satu indeks independen menghitung hampir 8 miliar sertifikat yang masih berlaku sekarang atau sudah kedaluwarsa sejak Desember 2025 saja. Log Argon 2026h2 milik Google saja mencapai ukuran tree akhir sekitar 3,5 miliar entri sebelum berhenti menerima tulisan baru. CT bukan lagi eksperimen. Ia adalah tulang punggung PKI web.

## Bagaimana sertifikat mendapatkan tanda terimanya

Mekanismenya adalah rantai janji yang singkat, dan setiap mata rantainya penting:

1. **CA membangun sebuah [[precertificate]].** Sebelum menerbitkan sertifikat asli, CA membuat salinannya dengan ekstensi khusus "poison" yang menandainya sebagai belum valid. Objek inilah yang dicatat ke log.
2. **Log mengembalikan sebuah [[Signed Certificate Timestamp]] (SCT).** CA mengirimkan precertificate ke satu atau beberapa log CT. Setiap log langsung membalas dengan SCT — janji yang ditandatangani untuk menambahkan entri itu ke log dalam [[Maximum Merge Delay]], biasanya 24 jam.
3. **SCT disematkan ke dalam sertifikat final.** CA menerbitkan sertifikat asli dengan SCT yang sudah tertanam di dalamnya. Browser memverifikasi SCT tersebut sebelum memercayai koneksi. Sertifikat tanpa SCT yang valid langsung ditolak.

Log itu sendiri adalah [[Merkle tree]] — struktur yang hanya bisa ditambah, di mana setiap batch sertifikat baru menghasilkan hash root baru yang ditandatangani, dipublikasikan sebagai signed tree head. Entri bisa ditambah tapi tidak pernah bisa diubah atau dihapus, dan siapa pun bisa memverifikasi secara kriptografis bahwa sebuah log tidak pernah dimanipulasi, atau menghasilkan bukti ringkas bahwa suatu sertifikat memang ada di dalamnya. Kamu tidak perlu memercayai operator log. Kamu bisa memeriksa matematikanya.

Browser menegakkan semua ini. Chrome mewajibkan CT sejak 2018: dua SCT dari log yang berbeda untuk sertifikat yang berlaku 180 hari atau kurang, tiga untuk yang lebih lama. Apple menerapkan pembagian yang sama. Firefox adalah yang terakhir dari ketiganya yang mengaktifkan penegakan, di desktop sejak versi 135 pada Februari 2025 dan di Android sejak versi 145. Sertifikat yang gagal memenuhi kebijakan CT diblokir tanpa opsi pengecualian dari pengguna.

## 2026: tahun ketika aturannya diperketat — dua kali

CT sudah wajib secara diam-diam selama bertahun-tahun, tapi 2026 membawa dua perubahan yang membuatnya lebih ketat dan membentuk ulang infrastruktur di bawahnya.

**Pertama, mandat pra-penerbitan.** Berdasarkan Chrome Root Program Policy versi 1.8, yang berlaku 15 Juni 2026, CA wajib mencatat setiap precertificate TLS ke setidaknya satu log CT yang diakui Chrome sebagai Usable atau Qualified *sebelum* menerbitkan sertifikat yang bersangkutan. Sebelum tanggal itu, pencatatan hanya "SHOULD" dengan jendela 24 jam. Sekarang ia adalah "MUST" yang keras, dan harus terjadi sebelum penerbitan. Sertifikat final tetap hanya membawa SHOULD dalam 24 jam — mandatnya menargetkan precertificate secara spesifik, karena di situlah catatan publik dibuat.

**Kedua, Google memensiunkan log klasiknya.** Pada 12 November 2026, empat log RFC 6962 produksi milik Google — Argon 2026h2, Argon 2027h1, Xenon 2026h2, dan Xenon 2027h1 — berhenti menerima tulisan baru. Keempatnya bersama-sama menyimpan sekitar 8,4 miliar entri. Google menyebut makin besarnya upaya manual yang dibutuhkan untuk menjaga log protokol lama tetap berjalan, dan penerbitan pun bergeser ke log static-ct-api milik Google yang lebih baru serta log operator lain. Kebijakan CT Apple sudah menerima log static-ct-api sejak 5 November 2026. Log lama tetap bisa dibaca selama proses pengarsipan — catatannya tidak hilang hanya karena pintu masuknya pindah.

Dan pengetatan terus berlanjut. Pada 17 November 2026, tim CT Chrome mengumumkan bahwa log hanya boleh menerima root RSA dan ECDSA, dan mulai 15 Desember 2026 harus menolak submission apa pun yang rantainya memakai kunci atau algoritma tanda tangan lain — termasuk kunci pasca-kuantum seperti ML-DSA. Alasan yang diberikan adalah beban: sertifikat yang tidak diandalkan Chrome menambah penyimpanan, bandwidth, dan pekerjaan verifikasi tanpa manfaat keamanan bagi pengguna Chrome. Era pasca-kuantum akan membutuhkan pengaturan CT-nya sendiri; log yang ada sekarang bukan tempatnya.

Perubahan-perubahan ini berada di dalam tekanan yang lebih luas terhadap masa berlaku sertifikat. Masa berlaku maksimum sertifikat TLS yang dipercaya publik turun menjadi 200 hari pada 15 Maret 2026, dan jatuh menjadi 100 hari pada 15 Maret 2027 — tanggal yang sama ketika Chrome mewajibkan sertifikat subscriber baru hanya menyatakan server authentication, dan menghapus extended key usage clientAuth. Sertifikat yang lebih pendek umurnya berarti lebih banyak penerbitan, lebih banyak pencatatan, dan makin banyak alasan untuk mengawasi log secara otomatis, bukan manual.

## Apa yang bisa — dan tidak bisa — dilakukan CT untukmu

Kesalahpahaman paling umum tentang CT adalah bahwa ia mencegah sertifikat buruk. Tidak. CT adalah kamera, bukan gembok. Sertifikat yang salah terbit tetap berfungsi di browser sampai seseorang mencabutnya. Yang dijamin CT adalah bahwa kesalahan penerbitan itu tidak bisa tetap tersembunyi.

Jaminan itu hanya berguna kalau ada yang mengawasi. CT memberikan tiga kemampuan praktis bagi setiap pemilik domain:

- **Mendeteksi sertifikat yang tidak pernah kamu minta.** Sertifikat untuk domainmu yang muncul di log padahal kamu tidak pernah memintanya adalah tanda khas kesalahan CA, akun DNS atau registrar yang dibajak, atau serangan yang ditargetkan. Ini adalah peringatan paling dini yang akan didapat kebanyakan organisasi.
- **Memetakan [[attack surface]]-mu sendiri.** CT menunjukkan setiap subdomain yang pernah mendapatkan sertifikat — termasuk server staging yang dibuat developer lalu dilupakan, dan layanan lawas yang tidak ada lagi pemiliknya. Ini salah satu inventaris eksternal gratis terbaik untuk jejak digitalmu sendiri.
- **Melengkapi gambaran [[CAA]].** Record DNS CAA memberi tahu CA mana saja yang boleh menerbitkan untuk domainmu. Itu pencegahan. CT adalah deteksi — ia menunjukkan apa yang tetap lolos.

Tooling-nya gratis dan butuh beberapa menit untuk disiapkan. Cari domain apa pun di **crt.sh** untuk melihat setiap sertifikat yang pernah dicatat untuknya. Jalankan **certspotter** sebagai daemon yang memberi peringatan saat sertifikat baru muncul. Atau sambungkan ke firehose **certstream** untuk melihat penerbitan secara real-time saat terjadi. False positive memang ada — CDN dan penyedia hosting secara sah memperoleh sertifikat untuk domainmu — tapi menyaringnya adalah pekerjaan satu kali, dan alternatifnya adalah tidak tahu sama sekali.

## Awasi buku besarnya

Certificate Transparency adalah salah satu kontrol keamanan langka yang tidak membutuhkan biaya, tidak membutuhkan agen, dan bekerja untuk domain segala ukuran — tapi hanya kalau ada yang melihatnya. Log-nya publik. Tanda terimanya kriptografis. Perubahan aturan 2026 berarti lebih banyak sertifikat dicatat lebih awal dan lebih andal dari sebelumnya, dan log itu sendiri kini berada di tengah pergantian generasi dari infrastruktur RFC 6962 lama ke static CT.

Siapkan pemantauan untuk domainmu hari ini: pencarian di crt.sh, peringatan certspotter, atau sekilas mingguan pada entri terbaru. Lain kali sebuah certificate authority membuat kesalahan — atau penyerang yang membuatnya untuk mereka — kamulah yang pertama tahu, bukan yang terakhir. Buku besarnya terbuka. Gunakanlah.
