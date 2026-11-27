---
title: "Shirudo: Perisai eBPF dari OpenAI dan Cisco untuk Menutup Celah Patch"
date: 2026-11-27
tags: [tools, ebpf, shirudo, openai]
excerpt: "Kerentanan kritis bocor di hari Jumat. Patch-nya baru datang berminggu-minggu kemudian. Pada 23 November 2026, OpenAI dan Cisco merilis Shirudo sebagai open-source — runtime eBPF yang membiarkan AI agent menulis perisai sementara untuk celah itu dan memasangnya ke sistem Linux yang sedang berjalan, tanpa reboot."
cover: /assets/covers/shirudo-openai-cisco-ebpf-shields.jpg
---

Setiap defender kenal betul celah ini. Sebuah [[vulnerability]] kritis diumumkan di hari Jumat, kode [[exploit]]-nya sudah beredar hari Senin, sementara patch vendor — setelah pengujian, persetujuan change, dan jendela maintenance — baru mendarat bulan depan. Jendela antara disclosure dan patch inilah tempat breach terjadi. Ini real estate paling berbahaya di dunia keamanan, dan selama bertahun-tahun satu-satunya jawaban adalah buru-buru dan berharap.

Pada 23 November 2026, Cisco dan OpenAI mengumumkan jawaban yang berbeda: [[Shirudo]], bahasa Jepang untuk "perisai". Ini runtime open-source berbasis [[eBPF]] yang memasang perlindungan sementara yang tertarget langsung ke sistem Linux yang sedang berjalan — tanpa reboot, tanpa restart layanan — selagi tim menyiapkan patch permanen. Ini rilis pertama dari Secure Infrastructure Project, proyek gabungan kedua perusahaan, dan sasarannya tepat di patch gap.

## Sebenarnya shield itu apa?

Shield Shirudo adalah program kecil yang fokus, yang menempel pada operasi persis yang dibutuhkan sebuah [[exploit]] — dan tidak pada yang lain. Pilihan desain kuncinya adalah presisi. Mematikan satu fungsi berisiko secara keseluruhan bisa merusak traffic yang sah, karena penyerang dan pengguna normal sering memanggil kode yang sama. Shield justru mencegat satu perilaku spesifik: input yang malformed, code path yang berbahaya, satu panggilan yang menjadi tumpuan exploit. Request yang sah tetap mengalir; serangan tidak.

Presisi itu dimungkinkan oleh [[eBPF]], teknologi kernel Linux yang memungkinkan program kecil yang terverifikasi berjalan di hook dalam kernel tanpa mengubah source kernel. Isovalent, perusahaan milik Cisco di balik Shirudo, suka membandingkan eBPF dengan apa yang dilakukan JavaScript untuk browser: eBPF membuat kernel yang sedang berjalan bisa diprogram dengan aman secara on the fly. Shirudo adalah penulisan ulang [[Tetragon]], platform keamanan runtime eBPF open-source yang dirilis Isovalent pada 2022, yang sudah menjadi mesin di balik fitur Live Protect milik Cisco untuk memitigasi celah di produk mereka sendiri. Kalau Tetragon mengamati dan menegakkan policy yang ditulis manusia, Shirudo dibangun ulang di sekitar aktor baru: AI agent.

Alur kerja yang didemokan OpenAI berjalan seperti ini. Sebuah [[vulnerability]] teridentifikasi. Sebuah agentic control plane — OpenAI memakai agent Codex untuk demo ini — mereproduksi celah itu di dalam [[sandbox]], mencari titik tempat shield bisa menempel, menulis kode mitigasi, dan mengujinya terhadap reproducer [[exploit]] yang hidup. Operator meninjau bukti-buktinya dan menyetujui shield sebelum apa pun ditayangkan. Agent mengerjakan pekerjaan yang cepat dan repetitif; manusia tetap memegang keputusan akhir.

## Empat pilar, satu masalah trust

OpenAI dan Cisco menyusun Shirudo di sekitar empat kebutuhan arsitektur, dan yang paling menarik bukan AI-nya — melainkan model trust-nya.

**Live protection.** Shield mencegat atau memblokir code path yang rentan tanpa me-restart layanan, dan operator bisa mengamati dampak nyata sebuah shield sebelum mengaktifkan enforcement. Tujuannya: perlindungan yang mulai berjalan di hari celah diumumkan, bukan di hari patch dikirim.

**AI-assisted defense.** Agent menyelidiki celah, membangun shield, dan memvalidasinya terhadap traffic nyata. Intinya kecepatan: celah yang ditemukan AI kini datang lebih cepat daripada kemampuan tim manusia men-triase-nya, jadi pertahanan juga harus bergerak secepat mesin.

**Trusted deployment.** Setiap shield ditandatangani secara kriptografis dan diverifikasi sebelum bisa dimuat — bahkan jika penyerang sudah mendapatkan akses administrator di host tersebut. Inilah bagian yang membedakan Shirudo dari sekadar hack pintar: pipeline shield dirancang supaya admin yang sudah terkompromi tidak bisa diam-diam menyelipkan "shield" berbahaya atau mencabut shield yang asli.

**Hardware-backed verification.** Chip [[TPM]] 2.0 menyimpan measurement log yang berakar di hardware atas setiap shield yang dimuat atau dicabut. Tim mendapatkan audit trail yang benar-benar bisa dipercaya — bukti tentang apa yang aktif di sebuah sistem, dicatat oleh hardware, bukan oleh software yang bisa ditulis ulang penyerang.

Rantai trust inilah yang mengubah program kernel yang ditulis AI — ide yang terdengar menakutkan — menjadi sesuatu yang bisa di-deploy. Tanpa shield yang ditandatangani dan atestasi TPM, membiarkan agent menyuntikkan kode ke kernel adalah kegilaan. Dengan keduanya, risikonya setidaknya terkendali.

## Uji Java4Shell — dan kenapa ini relevan di sini

Proof of concept-nya sengaja dipilih dekat dengan pembaca blog ini. Dalam satu uji terkontrol, shield yang ditulis Codex menyisipkan validasi ke dalam routine decoding [[Base64]] milik Java — primitif yang persis berada di balik [[Java4Shell]] (CVE-2026-114938), celah [[OpenJDK]] yang kita bahas minggu lalu. Ditempelkan ke instance Elasticsearch yang sudah berjalan, shield itu menghentikan percobaan [[exploit]] Java4Shell sementara aplikasinya tetap online. Cisco melaporkan pendekatan yang sama juga memblokir percobaan terhadap sebuah celah PHP dalam pengujian.

Dua catatan jujur perlu disampaikan di sini. Pertama, ini adalah uji yang dirancang dan dijalankan oleh pembuat proyek itu sendiri, bukan evaluasi independen — Isovalent sendiri menyebut mitigasi itu "appears to be effective". Anggap ini demo yang menjanjikan, bukan benchmark. Kedua, Shirudo tidak bisa melindungi segalanya. Engineer Isovalent John Fastabend mencatat di sebuah Linux kernel summit pada 2026 bahwa timnya sering menemui kerentanan yang tidak punya titik penempelan yang cocok di kernel. Beberapa celah memang tidak punya hook yang bersih.

Ada juga syarat yang berat untuk saat ini. Proyek ini masih pre-release, dan pemakaian produksi membutuhkan kernel Linux yang membawa patch kernel khusus Shirudo plus chip [[TPM]] 2.0. Ini khusus Linux, dan shield adalah perban, bukan obat — ia membeli waktu; ia tidak memperbaiki bug yang mendasarinya. OpenAI mengatakan berharap suatu hari nanti bisa merilis shield yang sudah teruji bersamaan dengan saat celah diumumkan, dengan policy [[least privilege]] yang dibuat otomatis sebagai target jangka panjang.

## Apa yang harus dilakukan sekarang

Shirudo bukan sesuatu yang bisa di-rollout ke produksi minggu ini. Ini sesuatu yang layak mulai dievaluasi — karena arah yang ditujunya adalah arah pertahanan ke depan. Proyek ini open-source di bawah lisensi BSD 2-Clause (program BPF-nya berlisensi ganda BSD dan GPL), kodenya ada di github.com/shirudo-dev/shirudo, dan Isovalent menyediakan quickstart virtual machine serta lab interaktif untuk mencobanya. OpenAI juga mengumumkan webinar deep-dive teknis pada 15 Desember 2026.

Kalau kamu menjalankan infrastruktur Linux, ini cara praktis untuk mendekatinya:

1. **Coba lab-nya, bukan fleet-mu.** Jalankan VM quickstart, reproduksi demo shield Java4Shell, dan amati bagaimana shield menempel, mengamati, lalu menegakkan aturan. Tujuannya memahami alur kerja, bukan melindungi apa pun dulu.
2. **Petakan eksposur patch-gap-mu.** Layanan mana yang paling lama dari disclosure sampai ter-patch — dan kenapa? Nilai Shirudo sebanding dengan besarnya gap itu. Fleet yang patch dalam hitungan jam tidak banyak terbantu; fleet yang butuh change window dan reboot sangat terbantu.
3. **Awasi katalog shield.** Nilai sebenarnya proyek ini akan datang saat shield yang sudah teruji dikirim bersamaan dengan disclosure. Sampai saat itu, setiap shield adalah pekerjaan custom — dan kode kernel custom yang ditulis agent adalah hal yang persis membutuhkan pipeline bertanda tangan dan teratestasi TPM yang sedang dibangun Shirudo.
4. **Terus patch.** Shield adalah sabuk pengaman, bukan perbaikan. Ia membuatmu tetap hidup selagi perbaikan dibangun; ia bukan alasan untuk melewatkan perbaikan itu.

Greg Brockman, presiden dan co-founder OpenAI, menyatakannya dengan lugas saat peluncuran: "Finding a bug today doesn't mean you can patch every system tomorrow." Kalimat itu adalah tesis keseluruhannya. Patch gap bukan kegagalan penjadwalan — ini fakta struktural tentang bagaimana software dikirim. Shirudo adalah upaya serius pertama untuk bertahan di dalam gap itu, bukan sekadar meminta maaf karenanya. Apakah ini bekerja dalam skala besar masih menjadi pertanyaan terbuka, dan jawaban jujurnya adalah belum ada yang tahu. Tapi untuk pertama kalinya, ada yang membangun tooling untuk mencari tahu — secara terbuka, dengan kode yang publik, dan dengan model trust yang dirancang sejak awal. Itu saja sudah cukup alasan untuk memperhatikannya.
