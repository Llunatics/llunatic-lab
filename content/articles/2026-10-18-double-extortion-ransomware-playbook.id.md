---
title: "Double Extortion: Cara Kerja Ransomware Modern yang Sebenarnya"
date: 2026-10-18
tags: [ransomware, extortion, blue-team, incident-response]
excerpt: "Ransomware modern tidak peduli dengan backup kamu — penyerang mencuri data dulu, baru mengenkripsi, lalu menekanmu dari tiga arah sekaligus. Berikut playbook lengkapnya, dari akses awal sampai leak site, berdasarkan laporan Semperis Oktober 2026 dan kasus-kasus nyata bulan ini."
cover: /assets/covers/double-extortion-ransomware-playbook.jpg
---

Kalau rencana disaster recovery kamu bunyinya "kita punya backup, jadi ransomware bukan masalah kita," berarti kamu sedang berperang dengan peta perang satu dekade lalu. Kru ransomware masa kini tidak butuh backup kamu gagal — mereka hanya butuh sesuatu yang tidak bisa kamu restore dari snapshot: rahasia pelangganmu, email internalmu, private key kamu. Enkripsi itu bagian yang berisik. Bagian yang sunyi — bagian yang benar-benar membuat korban membayar — terjadi berhari-hari sebelumnya, dalam gelap.

Mari kita telusuri playbook lengkapnya, tahap demi tahap, seperti yang dilihat oleh incident responder.

## Tahap 1: masuk ke dalam (initial access)

Setiap kisah ransomware dimulai dari pintu yang tak ada yang menjaga. Favoritnya tak banyak berubah: email phishing berisi lampiran berbahaya, kredensial curian yang dibeli dari broker [[initial access]], atau perangkat edge yang belum di-patch dan menghadap ke internet — concentrator VPN, firewall, server file-transfer. Di beberapa kampanye Oktober 2026, titik masuknya justru pipeline build perangkat lunak: curi satu secret developer, dan seluruh jaringan terbuka seperti kotak hadiah.

Kebenaran yang tidak nyaman: pembobolannya jarang menjadi bagian yang mengesankan. Yang mengesankan adalah betapa lamanya penyerang duduk di dalam sana tanpa terdeteksi.

## Tahap 2: menyebar di dalam (lateral movement dan persistence)

Begitu masuk, kru ransomware tidak langsung mengenkripsi apa pun. Itu berisik, dan yang berisik akan ketahuan. Sebaliknya mereka melakukan dua hal yang sunyi:

- **[[persistence]]** — menanam pijakan yang bertahan walau mesin di-reboot: scheduled task, akun servis gelap, webshell di aplikasi yang menghadap internet, golden ticket yang ditempa dari domain controller yang sudah dikuasai.
- **[[lateral movement]]** — melompat dari satu workstation ke workstation lain, memanen kredensial, sampai mencapai mahkota permata: infrastruktur identitas itu sendiri.

Inilah kenapa [Laporan Risiko Ransomware 2026 dari Semperis](https://www.prnewswire.com/news-releases/semperis-2026-ransomware-report-reveals-increases-in-ai-driven-attacks-and-a-rise-in-physical-threats-against-executives-and-their-families-302907731.html) yang terbit 14 Oktober 2026 begitu menohok: **87% serangan ransomware menargetkan sistem identitas** seperti [[Active Directory]], Entra ID, dan Okta. Kuasai sistem identitas dan kamu kuasai setiap pintu di gedung itu. Namun hanya sekitar separuh perusahaan yang disurvei menyimpan backup identitas khusus, dan 40% rencana disaster recovery bahkan tidak memuat prosedur pemulihan Active Directory. Seperti kata CEO Semperis, Mickey Bresman, begitu backup membuat enkripsi bisa diatasi, penyerang tinggal menambah titik tekan kedua — "[[double extortion]]."

## Tahap 3: pencurian yang sunyi (exfiltration)

Sebelum satu file pun dienkripsi, data sudah keluar lewat pintu belakang. Penyerang menumpuk database, dokumen, dan source code kamu di server yang sudah dikompromikan, lalu melakukan [[exfiltration]] — mengirimkannya ke penyimpanan cloud milik mereka — kadang gigabyte per jam, dibaurkan dengan lalu lintas HTTPS normal sehingga firewall tak berkedip.

Inilah momen yang mengubah backup kamu dari perisai menjadi bahan tertawaan. Kamu bisa me-restore setiap server terenkripsi dari snapshot kemarin dan tetap kehilangan semua yang penting, karena salinan yang duduk di server penyerang tidak peduli dengan rencana pemulihanmu. Tebusannya bukan "bayar atau kehilangan file." Melainkan **"bayar atau kami publikasikan."**

## Tahap 4: enkripsi dan leak site

Kini tibalah bagian yang berisik — deployment yang mengunci ratusan mesin dalam hitungan menit. Oktober ini, pelaku di balik [serangan IDCF Cloud](https://aviatrix.ai/threat-research-center/ransomware-attack-disrupts-japans-idcf-cloud-used-by-govt-clients/) (7 Oktober 2026) mengklaim telah mengenkripsi 225 database berisi 3,6 PB data, menyegel 16.000 disk VM, dan menghapus lebih dari 554.000 snapshot — semuanya dalam sekitar tujuh menit setelah menembus region Jepang Timur. Terlepas dari apakah setiap angka yang diklaim akurat, taktiknya adalah ciri khas 2026: hantam lapisan hypervisor, bukan server satu per satu, dan seluruh region cloud tumbang sekaligus.

Selagi sistemmu terkunci, titik tekan kedua aktif: **[[leak site]]**. Geng ransomware menjalankan portal kebocoran di Tor yang terbaca seperti dashboard kepatuhan yang diputarbalikkan. Satu pendatang baru 2026, AuditTeam, menamai portalnya "DATA EXPOSURE TERMINAL" dan memformat setiap korban sebagai "AUDIT ENTITY" lengkap dengan ID audit heksadesimal dan tanggal penemuan — estetika birokratis yang dirancang agar pemerasan terasa tak terelakkan, seperti inspeksi yang gagal ketimbang kejahatan.

Dan beberapa kru kini menyamarkan nama korban sepenuhnya: listing yang hanya bertuliskan "Paid Victim" dengan sebuah ID, tanpa nama perusahaan. Itu bukan belas kasihan — itu **hitungan mundur dengan radius ledakan yang tak diketahui**, direkayasa agar korban memutuskan lebih cepat daripada listing bernama lengkap.

## Tahap 5: tekanan ganda — termasuk kamu, secara pribadi

Double extortion (enkripsi + publikasi) adalah jawaban dekade 2020-an terhadap backup. Jawaban 2026 adalah **tekanan tiga lapis**: enkripsi, paparan data, dan intimidasi langsung terhadap orang-orangnya.

Angka-angka Semperis layak dibaca dengan perasaan tidak enak:

- **87%** serangan mempersenjatai AI — untuk recon, phishing, dan mempercepat seluruh operasi.
- **40%** serangan melibatkan ancaman psikologis atau fisik terhadap staf atau keluarga mereka; di lebih dari separuh kasus itu, penyerang benar-benar menindaklanjuti ancamannya.
- **Hampir 70%** korban diserang berkali-kali, dan **31% membayar tebusan lebih dari sekali** — membayar sekali menandaimu sebagai orang yang mau membayar.

Jadi playbook modern yang lengkap: masuk diam-diam, kuasai sistem identitas, curi dulu, enkripsi kemudian, ancam publikasi sebagai yang ketiga, dan — semakin sering — ancam manusianya sebagai yang keempat. Chris Inglis, Direktur Cyber Nasional AS pertama, merangkum ekonominya dengan blak-blakan: penyerang ingin biaya untuk *melawan* lebih besar daripada biaya untuk *menyerah*.

## Yang benar-benar membantu (selain "punya backup")

Backup itu perlu — hanya saja tidak lagi cukup. Yang terus diulang para responder di kasus-kasus ini:

1. **Backup yang immutable dan offline.** Tersimpan air-gapped atau write-once, tak terjangkau dan tak bisa dihapus penyerang — karena kru kini memburu server backup lebih dulu. Kasus IDCF menunjukkan penghapusan snapshot sebagai gerakan pembuka standar.
2. **Backup sistem identitas itu sendiri.** Prosedur pemulihan Active Directory yang khusus dan teruji — kebanyakan korban baru sadar mereka tidak memilikinya di tengah krisis.
3. **[[EDR]] di semua endpoint dan ada yang memantaunya.** Minggu-minggu antara intrusi dan enkripsi adalah jendela deteksimu; alert behavioral atas akses file massal dan lalu lintas keluar yang tak biasa menangkap tahap [[exfiltration]].
4. **Segmentasi dan [[least privilege]].** Perlambat [[lateral movement]] sehingga satu workstation yang jebol tak bisa mencapai domain controller.
5. **Patch apa pun yang menghadap internet.** VPN, firewall, appliance file-transfer — pintu depannya. Pantau daftar Known Exploited Vulnerabilities dari CISA ([[KEV]]) seperti itu pekerjaanmu — karena bagi sebagian penyerang, memang begitu.
6. **Rencana [[incident response]] yang sudah dilatih.** Komunikasi out-of-band, peran yang jelas, keputusan soal kebijakan tebusan dibuat *sebelum* krisis — karena bernegosiasi di bawah hitungan mundur dengan listing tersamar adalah resep keputusan buruk.
7. **Jangan bayar kalau bisa dihindari.** Statistiknya bicara jelas: hampir sepertiga pembayar membayar lagi. Pembayaran adalah uang muka untuk serangan berikutnya.

## Penutup

Ransomware sudah lama berhenti menjadi sekadar masalah malware. Kini ia bisnis tekanan — mesin yang mengubah datamu sendiri, infrastruktur identitasmu sendiri, dan ketakutanmu sendiri menjadi daya tawar. Para kru sudah mengindustrikannya: leak site berestetika log audit, listing tersamar sebagai timer hitung mundur, AI yang mengerjakan recon.

Pertahananmu harus sama sistematisnya. Bukan satu peluru perak, melainkan rantai peluru: keraskan pintu depan, awasi lorong-lorongnya, kunci sistem identitas, simpan backup yang tak bisa disentuh penyerang, dan latih hari buruk itu sebelum ia tiba. Karena di 2026, catatan tebusan bukan lagi awal serangan — melainkan *akhir* dari serangan yang dimulai berminggu-minggu sebelum kamu menyadarinya.
