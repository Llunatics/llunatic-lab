---
title: "Satu Tool Diretas, 178 Brand Kena: Serangan Supply-Chain Optimizely"
date: 2026-11-20
tags: [supply-chain, optimizely, web-security, incident]
excerpt: "Pada 16 November 2026, pengunjung Zoom, BBC, HSBC, IKEA, dan 174 situs besar lainnya disuguhi malware — bukan karena perusahaan-perusahaan itu diretas, melainkan karena satu tool A/B testing yang mereka semua percayai berhasil dibobol. Begini cara satu script beracun menjangkau jutaan browser dalam 19 jam."
cover: /assets/covers/optimizely-supply-chain-attack-178-sites.jpg
---

Pada Senin, 16 November 2026, kamu bisa membuka Zoom, BBC, CNN, HSBC, Salesforce, IKEA, GitLab, Equifax, Air France-KLM, Ledger, atau Peacock — dan disuguhi [[malware]]. Tidak ada satu pun server perusahaan itu yang diretas. Kode jahatnya datang lewat tool yang mereka semua percayai: Optimizely Web Experimentation, platform A/B testing yang snippet JavaScript-nya berjalan di halaman mereka. Seorang penyerang menemukan cara untuk menulis JavaScript-nya sendiri ke dalam project pelanggan Optimizely, dan karena setiap situs memuat snippet itu dari server Optimizely lalu menjalankannya tanpa bertanya, kode tersebut berjalan di browser pengunjung seolah-olah bagian dari situs itu sendiri.

Itulah seluruh cerita [[supply chain attack]] dalam satu kalimat: bobol satu supplier tepercaya, dan kepercayaannya membawa kodemu ke mana-mana.

## Bagaimana serangan ini ketahuan

Serangan ini diungkap oleh peneliti keamanan Scott Helme dan tim Report URI. Saat serangan masih berjalan, para peneliti memindai platform tersebut dan memeriksa **1.611 snippet Optimizely**. Mereka menemukan **188 snippet terinfeksi milik 178 organisasi** di seluruh dunia — dan angka sebenarnya kemungkinan lebih besar, karena mereka hanya bisa memeriksa snippet yang mereka temukan selama serangan berlangsung. Bahkan situs dan halaman login Optimizely sendiri ikut terdampak.

Ke-178 organisasi itu mencakup hampir semua sektor yang menangani uang atau data pribadi: 32 di perbankan dan keuangan, 23 di teknologi dan SaaS, 20 di retail dan fashion, 12 di streaming dan hiburan, 10 di berita dan media, 9 di maskapai dan travel, masing-masing 8 di kesehatan dan farmasi serta industri dan manufaktur, dan 7 di telekomunikasi — ditambah jumlah lebih kecil di kripto, asuransi, properti, makanan, nonprofit, perjudian, logistik, otomotif, dan pendidikan.

Masuk daftar itu artinya snippet Optimizely sebuah organisasi mengandung kode jahat di satu titik pada 16 November. Itu **tidak** dengan sendirinya berarti data pelanggan dicuri. Setiap organisasi masih harus mencari tahu sendiri apa yang dialami pengunjungnya.

## Apa yang dilakukan kode jahat itu

Kode yang disuntikkan diperbarui berkali-kali sepanjang hari, dan terus bertambah fiturnya. Pada akhirnya, kode itu bisa:

- **Menukar alamat kripto.** Kode itu mengganti alamat wallet Bitcoin, Ethereum, Solana, TRON, dan lainnya di halaman, di form, dan di clipboard dengan alamat milik penyerang — sehingga pembayaran masuk ke wallet yang salah.
- **Mencuri kartu pembayaran.** Mulai pukul 13:43 UTC, kode itu menangkap nomor kartu, tanggal kedaluwarsa, dan kode keamanan yang diketik ke form milik situs itu sendiri. Kartu yang dimasukkan lewat kotak pembayaran terpisah yang di-host oleh payment processor berada di luar jangkauan — detail yang penting, seperti akan kita lihat.
- **Mencuri data browser.** Kode itu mengirim alamat halaman, cookie yang bisa dibaca, dan screenshot ke server penyerang setiap kali menemukan konten wallet atau pembayaran.
- **Menyerang iPhone.** Kode itu mengarahkan pengunjung iPhone dan iPad dengan iOS versi lama ke [[exploit kit]] iOS yang mencoba mengambil alih perangkat. Perangkat dengan iOS 18.7.3 atau lebih baru, atau iOS 26.3 atau lebih baru, sudah ditambal terhadap serangan itu.

Sekitar **US$7.000** dalam bentuk kripto sampai ke wallet penyerang, yang dikosongkan pada awal 17 November. Belum ada yang tahu berapa banyak kartu atau sesi browser yang berhasil ditangkap. Tujuh ribu dolar terdengar kecil untuk serangan sebesar ini — tapi wallet itu hanya bagian yang terlihat. Data kartu, cookie, dan screenshot adalah hasil rampasan yang tidak bisa dihitung dari blockchain explorer.

## Linimasanya

- **16 November, 04:21 UTC:** perubahan jahat pertama terlihat, pada snippet BBC.
- **16 November, 11:20 UTC:** snippet Zoom dimodifikasi.
- **16 November, 13:43 UTC:** kode pencuri kartu ditambahkan — payload-nya naik kelas dari pencurian kripto menjadi perilaku [[web skimmer]] penuh.
- **16 November, 20:40–21:10 UTC:** pembersihan massal snippet yang terinfeksi.
- **16 November, 23:11 UTC:** para peneliti mengonfirmasi semua file Optimizely yang terinfeksi sudah bersih.
- **17 November, 01:02 UTC:** Optimizely mempublikasikan pemberitahuan insiden keamanannya.

Secara total, kode itu aktif di sebagian situs selama sekitar **17 sampai 19 jam**. Domain utama penyerang ditangguhkan atau berhenti merespons pada 17 November.

## Bagaimana perusahaan-perusahaan itu merespons

Optimizely mengatakan pihak tak berwenang mengeksploitasi kerentanan di produk Experimentation-nya untuk menambahkan JavaScript berbahaya ke beberapa project pelanggan. Menurut mereka, kerentanan itu sudah diperbaiki, kode yang disuntikkan sudah dihapus, akun pengguna yang terdampak sudah diamankan, dan perlindungan tambahan sudah ditambahkan untuk mencegah pengiriman kode tak berwenang. Mereka juga sudah menghubungi pelanggan yang terdampak secara langsung. Halaman status mereka mencantumkan insiden itu sebagai "Monitoring". Optimizely belum mengatakan secara publik apa kerentanannya atau berapa banyak pelanggan yang terdampak.

Zoom mengatakan di Trust Center-nya bahwa mereka menyadari insiden ini dan telah menonaktifkan Optimizely di seluruh production environment mereka sebagai tindakan pencegahan, dan mereka belum menemukan dampak terhadap data pelanggan. Salesforce mempublikasikan advisory yang menyatakan mereka sedang menyelidiki perubahan tak berwenang pada script Optimizely yang dipakai di situs-situs Salesforce tertentu, dan telah menonaktifkan script tersebut sebagai pencegahan. Equifax meluncurkan investigasi dan berhenti memakai Optimizely, sambil menyatakan tidak menemukan bukti pelanggaran terhadap sistemnya sendiri. IKEA dan sebagian besar brand lain yang disebut belum mempublikasikan pernyataan resmi saat insiden itu pertama kali dilaporkan.

## Kenapa serangan ini penting

Serangan Optimizely adalah contoh textbook karena mengekspos titik buta kebanyakan situs web. Sebuah situs modern bukan satu codebase — melainkan kumpulan script dari puluhan vendor: analytics, chat widget, A/B testing, tag manager, banner consent, session replay. Setiap script itu berjalan dengan kekuatan yang sama seperti kode milik situs itu sendiri. Kalau salah satunya dibobol, penyerang mewarisi kepercayaan dari setiap situs yang memuatnya.

Tiga hal membuat serangan ini luar biasa efektif:

1. **Jalur pengirimannya memang dipercaya secara desain.** Snippet Optimizely *memang seharusnya* menjalankan JavaScript sembarangan — itulah fungsi A/B testing. Script jahat yang tersembunyi di project pelanggan terlihat seperti eksperimen yang sah.
2. **Payload-nya berevolusi di tempat.** Kode itu diperbarui berkali-kali sepanjang hari, menambahkan pencurian kartu berjam-jam setelah infeksi pertama. Situs yang memeriksa snippet-nya di pagi hari dan tidak menemukan apa-apa bisa saja sudah menyajikan skimmer di sore hari.
3. **Jaring pengamannya sebagian besar tidak ada.** Dari organisasi terdampak yang diperiksa para peneliti, hanya sekitar **15%** yang memiliki [[Content Security Policy]] yang sepenuhnya memblokir serangan itu. CSP yang ketat — yang membatasi dari mana script boleh dimuat dan ke mana data boleh dikirim — adalah satu kontrol yang bisa menghentikan script pihak ketiga yang sudah diracuni, bahkan setelah vendor-nya dibobol. Kebanyakan situs tidak memilikinya dengan cukup ketat.

Detail soal pencurian kartu itu layak diingat: kartu yang diketik ke form milik situs itu sendiri terekspos, sementara kartu yang dimasukkan lewat kotak pembayaran yang di-host payment processor tidak. Menyimpan field pembayaran di dalam iframe payment provider bukan sekadar checkbox kepatuhan PCI — itu batas blast radius yang nyata. Pada 16 November, itulah perbedaan antara terekspos dan aman.

## Kalau kamu mengunjungi salah satu situs itu pada 16 November

- **Perbarui iPhone atau iPad kamu** ke iOS 18.7.3 atau lebih baru, atau iOS 26.3 atau lebih baru. Kalau tidak bisa diperbarui, aktifkan Lockdown Mode.
- **Periksa mutasi kartu kamu** untuk transaksi yang tidak kamu kenali, dan segera beri tahu bank kalau ada tagihan aneh. Kalau kamu mengetik kartu ke form sebuah situs pada 16 November, pertimbangkan untuk meminta kartu baru ke bank.
- **Periksa transaksi kripto** yang kamu lakukan pada 16 November. Selalu bandingkan alamat wallet lengkap, karakter demi karakter, sebelum mengirim uang.
- **Keluar lalu masuk lagi** ke akun yang kamu pakai hari itu, dan ganti password yang kamu masukkan di situs yang terdampak.
- **Waspada terhadap penipuan susulan.** Akan ada email dan pesan palsu "akun kamu dibobol" yang memanfaatkan berita ini. Buka situs perusahaan langsung, bukan lewat tautan di pesan.

## Kalau kamu mengelola sebuah situs web

- **Periksa Project JavaScript Optimizely kamu** dan custom code setiap eksperimen untuk mencari script yang bukan kamu tulis — terutama yang memuat kode dari domain tak dikenal atau memakai `atob(` atau `eval(`.
- **Periksa change history Optimizely** untuk edit yang dibuat pada atau sekitar 16 November.
- **Rotasi kredensial dan API token Optimizely**, beserta token sesi atau secret apa pun yang mungkin bisa dibaca dari browser.
- **Anggap detail kartu yang diketik ke form milikmu sendiri pada 16 November mungkin sudah terekspos**, dan bicarakan dengan payment provider kamu.
- **Terapkan Content Security Policy yang ketat** yang membatasi dari mana script boleh dimuat dan ke mana data boleh dikirim — dan sebisa mungkin jauhkan script pihak ketiga dari halaman pembayaran.

## Pelajarannya

Penyerang tidak pernah perlu membobol Zoom, IKEA, atau satu bank pun. Mereka membobol satu layanan yang dipercayai semua pihak itu, lalu membiarkan kepercayaan itu membawa kode jahat ke jutaan pengunjung. Keamanan situs web kamu bukan hanya kode yang kamu tulis — melainkan setiap script yang kamu izinkan dijalankan orang lain di halamanmu. Ketahui script pihak ketiga apa saja yang berjalan di situs kamu, jauhkan dari halaman pembayaran, dan batasi apa yang boleh mereka muat serta ke mana mereka boleh mengirim data. Kontrol yang bisa menghentikan serangan ini adalah kontrol yang sama yang menghentikan serangan berikutnya — dan kebanyakan situs masih belum menerapkannya.

---

*Sumber: [Malware targets crypto and iPhone users on 178 popular sites (PYMNTS, 17 November 2026)](https://www.pymnts.com/cybersecurity/2026/malware-targets-crypto-and-iphone-users-on-178-popular-sites/); [One hacked tool, 178 brands (Reef Sentinel, 17 November 2026)](https://www.reef-sentinel.net/n/271); [BBC, CNN, Zoom among 178 organisations targeted in crypto-stealing malware attack (Storyboard18, 17 November 2026)](https://www.storyboard18.com/digital/bbc-cnn-zoom-among-178-organisations-targeted-in-crypto-stealing-malware-attack-114914.htm). Laporan tambahan: Report URI (Scott Helme) dan pemberitahuan status layanan Optimizely, 17 November 2026.*
