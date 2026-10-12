---
title: "Kepercayaan Adalah Celahnya: Pelajaran dari Pembobolan Terbesar Denmark tentang Risiko Pihak Ketiga"
date: 2026-10-12
tags: [supply-chain, third-party-risk, data-breach]
excerpt: "Basis data identitas nasional Denmark kehilangan catatan 8,8 juta penduduk — bukan karena zero-day, melainkan lewat akses sah sebuah perusahaan vendor yang disalahgunakan. Inilah mengapa setiap relasi pihak ketiga adalah jalur serangan, dan cara menutup yang paling penting."
cover: /assets/covers/third-party-trust-denmark-breach.jpg
---

Sebagian besar kisah pembobolan dimulai dari sebuah celah: patch yang terlewat, password yang lemah, exploit yang cerdik. Kisah yang satu ini dimulai dari sebuah izin. Basis data identitas nasional Denmark — Central Person Register, satu-satunya sumber kebenaran data setiap warga Denmark — kehilangan catatan pribadi sekitar 8,8 juta orang. Tidak perlu zero-day. Penyerang cukup berjalan masuk lewat pintu yang memang sengaja dibuka Denmark: akses sah sebuah perusahaan ke sistem register tersebut.

Pemerintah Denmark mengumumkan pembobolan ini pada 5 Oktober 2026. Akses ilegalnya berlangsung sekitar sepuluh hari di bulan September sebelum penyelidikan internal — yang dipicu oleh lonjakan query otomatis — menghentikannya. Data yang dicuri meliputi nama, alamat, dan nomor jaminan sosial Denmark — nomor CPR yang dipakai untuk pajak dan layanan publik. Register itu menyimpan catatan sekitar 11 juta orang, jauh melampaui 6 juta penduduk Denmark saat ini, karena ia juga menyimpan data historis warga yang tinggal di luar negeri maupun yang sudah meninggal. Itulah yang membuat ini menjadi pembobolan terbesar dalam sejarah negara itu: yang tersapu bukan hanya yang hidup, melainkan juga yang pindah dan yang telah tiada.

Pemerintah, lewat menteri Christina Egelund, menyebut insiden ini sebagai "insiden serius". Namun detail yang paling penting bagi para defender adalah vektor serangannya. Menurut pernyataan pemerintah, akses ilegal itu diperoleh dengan menyalahgunakan akses sah sebuah perusahaan Denmark untuk mencari informasi di sistem CPR. Perusahaan-perusahaan Denmark memang diizinkan memverifikasi data warga lewat register tersebut. Seseorang mengubah kanal tepercaya itu menjadi pipa pencurian data.

## Perimeter Anda lebih besar dari yang Anda kira

Inilah inti konsep [[third-party risk]]: setiap organisasi yang punya akses ke sistem atau data Anda otomatis menjadi bagian dari [[attack surface]] Anda. Anda bisa mengeraskan jaringan sendiri sampai level militer, tapi tetap kehilangan segalanya lewat vendor yang kredensialnya lebih lemah dari milik Anda.

Pola ini lebih tua dari kebanyakan engineer yang membaca artikel ini. Target kehilangan 40 juta nomor kartu pada 2013 karena penyerang masuk lewat kontraktor AC (HVAC). SolarWinds, pada 2020, mengubah update software tepercaya menjadi kampanye spionase global — [[supply chain attack]] yang jadi acuan buku teks. Di tiap kasus, pertahanan korban sendiri bertahan; penyerang hanya memilih tetangga yang kuncinya lebih murah.

Yang membuat kasus Denmark begitu tajam adalah legitimasi aksesnya. Ini bukan laptop vendor yang diretas atau akun helpdesk yang kena phishing. Jalur aksesnya memang dirancang demikian: register negara yang sengaja dibuka untuk perusahaan swasta demi keperluan verifikasi sehari-hari. Model keamanannya adalah "kami mempercayai perusahaan ini" — dan kepercayaan, begitu diberikan, sangat sulit diawasi.

## Mengapa akses tepercaya begitu sulit diamankan

[[Least privilege]] — prinsip bahwa setiap akun hanya boleh memegang akses minimum yang dibutuhkannya — terdengar jelas sampai Anda menerapkannya ke relasi vendor. Perusahaan yang memverifikasi catatan identitas ke register nasional bisa dibilang memang membutuhkan tepat akses yang diberikan Denmark itu. Anda tidak bisa mencabut hak akses tanpa merusak proses bisnisnya. Jadi pertanyaan sebenarnya bukan apakah akses diberikan, melainkan bagaimana memastikan akses yang diberikan itu tidak diam-diam diubah menjadi pencurian massal.

Penyalahgunaan akses sah hampir tidak meninggalkan jejak forensik tradisional. Tidak ada malware yang bisa dideteksi, tidak ada exploit yang perlu di-patch, tidak ada login mencurigakan dari negara asing — query-query itu datang dari akun sah yang melakukan hal yang memang diotorisasi untuknya, hanya dalam skala industri. Satu-satunya anomali adalah volumenya: lonjakan query otomatis itulah yang akhirnya memicu penyelidikan. Itu pola deteksi — anomali tingkat penggunaan pada akun istimewa — yang bisa diterapkan organisasi mana pun.

Ada pelajaran kedua yang tersembunyi di desain register itu. Basis data CPR menyimpan sekitar 11 juta catatan untuk negara berpenduduk 6 juta. Setiap catatan yang dipertahankan adalah liabilitas: data lama milik orang yang pindah atau meninggal tidak bisa dilindungi siapa pun, tidak bisa diawasi siapa pun, dan tetap punya nilai seumur hidup untuk penipuan identitas. Data yang Anda simpan adalah data yang wajib Anda bela. Data yang tidak lagi Anda butuhkan hanyalah [[attack surface]].

## Menutup pintu vendor yang penting

Anda tidak perlu punya register nasional untuk menerapkan pelajaran ini. Dinamika yang sama berlaku untuk setiap vendor dengan API key, setiap kontraktor dengan akun VPN, setiap integrasi SaaS dengan akses baca ke basis data pelanggan Anda. Berikut program praktisnya:

**Inventarisasi setiap pihak ketiga yang punya akses.** Kalau tidak bisa mendaftarnya, Anda tidak bisa mengamankannya. Setiap akun vendor wajib punya pemilik, alasan bisnis, dan tanggal kedaluwarsa. Akses yang bukan tanggung jawab siapa pun adalah akses yang tidak akan disadari siapapun ketika disalahgunakan.

**Batasi apa yang bisa dilakukan akses tepercaya, bukan cuma siapa yang memilikinya.** Rate limit, kontrol query massal, dan baseline perilaku pada akun vendor mengubah "penyalahgunaan skala besar" dari tak terlihat menjadi mencolok. Penyelidikan di Denmark bermula karena seseorang menyadari lonjakan query otomatis — bangun alerting itu sebelum Anda membutuhkannya.

**Awasi yang sah, bukan cuma yang jahat.** Pipeline [[SIEM]] dan [[threat intelligence]] biasanya disetel untuk indikator yang sudah dikenal jahat: hash malware, domain berbahaya, IP mencurigakan. Penyalahgunaan oleh vendor sah butuh lensa berbeda: deteksi anomali pada perilaku yang diotorisasi. Kalau akun vendor tiba-tiba mengquery sepuluh ribu catatan padahal baselinenya empat puluh, itu harusnya membangunkan seseorang.

**Minimalkan data itu sendiri.** Retensi adalah risiko. Hapus catatan yang sudah tidak punya alasan hukum atau bisnis untuk disimpan, dan ketika harus menyimpan, pangkas ke field minimum. Delapan juta catatan yang diretas itu menyakitkan; 8 juta catatan yang sebenarnya tidak perlu Anda simpan itu lebih menyakitkan lagi.

**Rencanakan skenario vendor yang diretas, bukan cuma diri sendiri.** Playbook respons insiden biasanya mengasumsikan penyerang masuk lewat infrastruktur Anda. Tambahkan satu skenario: "kredensial vendor kami disalahgunakan." Siapa yang Anda hubungi? Bisakah akses mereka dicabut dalam hitungan menit? Pemerintah Denmark menangguhkan akses perusahaan yang terlibat sebagai bagian dari respons — pastikan Anda bisa melakukan hal yang sama jam 2 pagi di hari Minggu.

## Intinya

Firewall terkuat di dunia tidak bisa melindungi Anda dari pintu yang Anda buka sendiri. Pembobolan Denmark adalah pengingat bahwa keamanan bukan properti sistem Anda semata — ia adalah properti dari setiap relasi yang Anda jaga. Kepercayaan, dalam istilah keamanan, bukanlah kebajikan. Ia adalah [[attack surface]], dan ia harus dianggarkan, diawasi, dan dicabut seperti halnya yang lain.

Penyerang dalam kisah ini tidak merusak apa pun. Itulah bagian yang tidak nyaman. Mereka memahami sesuatu yang masih kurang diinvestasikan para defender: cara termudah melewati tembok adalah lewat gerbang yang Anda biarkan terbuka untuk teman-teman Anda.
