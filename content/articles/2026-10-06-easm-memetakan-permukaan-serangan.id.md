---
title: "EASM: Memetakan Attack Surface Sebelum Penyerang Melakukannya"
date: 2026-10-06
tags: [easm, attack-surface, blue-team]
excerpt: "Kebanyakan organisasi kebobolan bukan lewat pintu depan, melainkan lewat aset yang bahkan tidak mereka sadari ada. EASM adalah disiplin untuk menemukan semuanya lebih dulu."
cover: /assets/covers/easm-attack-surface.jpg
---

Bayangkan kamu disewa untuk menjaga sebuah gedung. Kamu kunci pintu depan, pasang CCTV, sewa satpam. Tapi ternyata gedung itu punya pintu belakang yang tidak tercatat di denah, jendela gudang yang tidak pernah dikunci, dan lorong servis yang sudah lama tidak dipakai siapa pun. Penyerang tidak akan mengetuk pintu depan — mereka akan menyelinap lewat celah yang bahkan tidak kamu tahu ada.

Itulah gambaran paling jujur tentang keamanan siber kebanyakan organisasi hari ini. Dan disiplin ilmu yang lahir untuk menjawabnya namanya [[EASM]].

## Masalahnya: kamu tidak bisa menjaga yang tidak kamu ketahui

Setiap perusahaan modern punya jejak digital yang jauh lebih besar dari yang mereka kira: [[subdomain]] yang dibuat untuk proyek tiga tahun lalu dan tidak pernah dimatikan, bucket penyimpanan cloud yang tidak sengaja terbuka publik, server pengembangan yang lupa di-patch, sertifikat SSL untuk layanan yang sudah tidak dipakai, hingga akun karyawan di layanan pihak ketiga.

Semua itu adalah bagian dari [[attack surface]] — dan penyerang punya satu keunggulan fundamental: mereka hanya butuh menemukan **satu** celah, sementara tim bertahan harus menutup **semuanya**.

Itulah kenapa keamanan yang reaktif ("tunggu ada insiden, baru bertindak") selalu kalah. [[EASM]] membalik logikanya: **berpikir seperti penyerang, tapi bergerak lebih dulu.**

## Apa sebenarnya yang dilakukan EASM?

Secara sederhana, [[EASM]] adalah proses berkelanjutan untuk menemukan, menginventarisasi, dan memantau seluruh aset digital organisasi yang terekspos ke internet — dari sudut pandang orang luar.

Ada empat tahapan intinya:

**1. Discovery — menemukan semuanya.**
Ini fondasinya. Tekniknya mirip dengan yang dipakai penyerang saat fase reconnaissance: enumerasi [[subdomain]], pemindaian sertifikat SSL (setiap sertifikat mencatat nama domain — sumber informasi yang luar biasa), mesin pencari khusus seperti [[Shodan]] dan [[Censys]], sampai teknik [[OSINT]] klasik. Tool seperti [[Amass]] mengotomatiskan sebagian besar pekerjaan ini.

**2. Inventory — mencatat dan mengklasifikasikan.**
Aset yang ditemukan dicatat: layanannya apa, versi software apa yang berjalan, siapa pemiliknya di internal, seberapa kritis. Tanpa inventaris yang rapi, temuan discovery hanya jadi daftar panjang yang tidak bisa ditindaklanjuti.

**3. Assessment — menilai risikonya.**
Setiap aset dinilai: apakah ada [[vulnerability]] yang diketahui? Apakah layanannya sudah usang? Apakah ada [[CVE]] kritis yang belum di-patch? Tahap ini biasanya terhubung dengan [[threat intelligence]] agar penilaian risikonya mengikuti ancaman yang sedang aktif di dunia nyata.

**4. Monitoring — mengawasi terus-menerus.**
Attack surface tidak pernah diam. Setiap deploy baru, setiap uji coba layanan cloud, setiap akuisisi perusahaan menambah permukaan serangan. [[EASM]] yang baik berjalan kontinu, bukan audit setahun sekali.

## Kenapa ini relevan untuk semua orang, bukan cuma korporat?

Prinsip yang sama berlaku dalam skala kecil. Punya blog pribadi? Cek subdomain yang tidak terpakai. Punya VPS? Pastikan tidak ada port manajemen yang terbuka ke seluruh internet. Prinsipnya satu: **kurangi apa yang terlihat dari luar, dan ketahui persis apa yang masih terlihat.**

Bahkan untuk individu, pola pikir [[EASM]] berguna: akun-akun lama yang terlupakan, layanan yang masih terhubung ke email utama, aplikasi yang masih punya akses ke akun Google — semuanya adalah "attack surface" pribadi.

## Mulai dari mana?

Kamu tidak butuh budget enterprise untuk mulai berpikir ala [[EASM]]. Langkah paling sederhana yang bisa dilakukan siapa pun hari ini:

- Cari tahu subdomain apa saja yang dimiliki domainmu (banyak tool gratis untuk ini).
- Cek sertifikat SSL yang pernah diterbitkan untuk domainmu — sering ada kejutan di sana.
- Cari namamu atau nama organisasimu di [[Shodan]] — lihat apa yang terlihat dari luar.
- Buat daftarnya, lalu tutup atau amankan yang tidak perlu terekspos.

Penyerang melakukan hal yang persis sama setiap hari, secara otomatis, dalam skala masif. Satu-satunya pertanyaan adalah: siapa yang menemukan asetmu lebih dulu — kamu, atau mereka?

---

*Artikel ini adalah pembuka seri attack surface di llunatic-lab. Berikutnya kita akan praktik langsung: enumerasi subdomain dari nol dengan tool gratis.*
