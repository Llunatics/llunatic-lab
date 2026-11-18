---
title: "Codex Security CLI: Pemindai Open-Source OpenAI yang Menemukan, Memvalidasi, dan Memperbaiki Bug"
date: 2026-11-18
tags: [tools, ai-security, code-audit, openai]
excerpt: "Codex Security CLI dari OpenAI memindai repo kamu, memperdebatkan temuannya sendiri sampai hanya yang asli yang tersisa, lalu menyusun patch dan memeriksanya ulang. Versi 0.10.0 baru saja membuatnya bisa dilanjutkan, dibatasi biayanya, dan siap CI — begini cara menjalankannya, plus dua hal yang tidak boleh dilewatkan."
cover: /assets/covers/codex-security-cli.jpg
---

Sebagian besar AI code reviewer punya kelemahan yang sama: mereka tidak pernah meragukan diri sendiri. Arahkan satu ke sebuah repository dan ia akan mengembalikan daftar [[vulnerability]] yang meyakinkan, separuhnya langsung menguap begitu manusia membaca source-nya. Jawaban OpenAI atas masalah itu adalah `codex-security` — sebuah command-line scanner yang memperlakukan temuannya sendiri sebagai tersangka, bukan vonis. Ia menemukan kandidat bug, mencoba membantah masing-masing, menyusun patch untuk yang bertahan, lalu memeriksa ulang perbaikannya. Tool ini sudah publik sejak akhir Juli 2026, tapi versi 0.10.0 yang dirilis 12 November-lah yang mendorongnya ke halaman trending GitHub dan melewati 13.000 star dalam hitungan hari.

## Sebenarnya ini apa

Codex Security adalah CLI dan TypeScript SDK dari OpenAI untuk menemukan, memvalidasi, dan memperbaiki [[vulnerability]] keamanan di kode kamu sendiri. Ia dikirim sebagai paket npm `@openai/codex-security`, berlisensi Apache-2.0, dengan source di `github.com/openai/codex-security`. Kamu bisa memakainya dengan tiga cara: sebagai plugin di dalam Codex, dari terminal dengan perintah `cs`, atau dalam otomatisasi lewat SDK atau GitHub Action.

Repository-nya dibuat pada 13 Juli 2026 dan di-open-source pada akhir Juli, dengan rilis npm pertama, 0.1.0, mendarat pada 31 Juli. Selama tiga bulan ia tumbuh dengan tenang. Lalu rilis 0.10.0 pada 12 November bertepatan dengan keynote OpenAI "Cyber at the Frontier" — hari yang sama perusahaan itu mengumumkan Daybreak Red Team dan Defense Factory, produk agen ofensif dan defensif terkelola mereka. Codex Security adalah blok bangunan yang terbuka dan bisa di-host sendiri di bawah cerita itu: bagian yang bisa kamu install dan jalankan sendiri, bukan dibeli sebagai layanan.

Jumlah star menceritakan lonjakannya: sekitar 12.900 star pada 13 November, kira-kira 13.350 keesokan harinya, dan mendekati 13.900 pada 17 November — lebih dari 2.000 star baru dalam satu minggu.

## Cara kerja sebuah scan: temukan, validasi, patch, periksa ulang

Alurnya punya empat tahap, dan tahap kedua adalah inti dari semuanya:

1. **Find (temukan).** Scanner membaca repository kamu — satu tree penuh, satu path tertentu, atau hanya perubahan dalam sebuah git diff — lalu mengusulkan kandidat [[vulnerability]].
2. **Validate (validasi).** Setiap kandidat diperiksa terhadap source sebelum dilaporkan. Tujuan desainnya eksplisit: temuan dari source belum tentu sebuah exploit yang bisa direproduksi, dan kecurigaan yang belum terkonfirmasi tidak seharusnya sampai ke kamu dengan menyamar sebagai fakta. Ini langkah yang dilewati sebagian besar AI reviewer, dan inilah alasan output tool ini dimaksudkan lebih pendek dan lebih bisa dipercaya daripada muntahan mentah sebuah model.
3. **Patch.** Untuk temuan yang tervalidasi, ia menyusun draft perbaikan.
4. **Re-check (periksa ulang).** Ia memverifikasi bahwa perbaikan itu benar-benar menyelesaikan temuan tersebut, bukan sekadar mengasumsikan patch-nya berhasil.

Deep scan mengulang Standard scan dan mengembalikan temuan yang sudah dideduplikasi, jadi pass kedua dimaksudkan untuk menangkap yang terlewat pass pertama, bukan mengulanginya. Scanner ini mencakup Python, JavaScript, TypeScript, Go, Java, C, C++, Rust, Ruby, dan PHP.

Ia juga akur dengan tool yang sudah kamu jalankan. Temuan dari scanner lain bisa diimpor — importer untuk AWS dan CrowdStrike tiba pada minggu sebelum 0.10.0, dan 0.10.0 sendiri menambahkan impor [[SAST]] ArmorCode — dan hasilnya diekspor sebagai [[SARIF]], JSON, atau CSV, dengan pelacakan ke Linear, Jira, atau GitHub. Penggunaan yang paling masuk akal adalah sebuah langkah keamanan di [[CI/CD]] yang bisa ditindaklanjuti coding agent, bukan PDF yang tidak dibaca siapa pun.

## Install dan jalankan

Syaratnya Node.js 22.13.0 atau lebih baru dalam lini 22.x, atau 24.x atau 26.x, plus Python 3.10 atau lebih baru. Install secara global lalu sign in:

```bash
npm install --global @openai/codex-security
cs login
```

Lalu scan dari dalam repository:

```bash
cs scan .
```

`cs` dan `codex-security` adalah perintah yang sama — pakai bentuk panjangnya kalau nama pendeknya bentrok dengan sesuatu di sistem kamu, atau `npx @openai/codex-security` untuk melewati install global sepenuhnya. Batasi cakupan scan dengan flag:

```bash
# Hanya satu direktori
cs scan . --path src/auth/

# Hanya yang berubah terhadap main — alur kerja pull request
cs scan . --diff origin/main

# Batasi biaya dan gagalkan CI pada temuan high-severity
cs scan . --max-cost 5.00 --fail-on-severity high
```

Di CI, lewati login interaktif dan set `OPENAI_API_KEY` atau `CODEX_API_KEY` sebagai gantinya. Contoh GitHub Action-nya membatasi setiap scan pada estimasi $5 — sebuah batas, bukan harga, tapi default yang layak ditiru. Untuk pekerjaan massal di banyak repository, repo ini menyediakan konfigurasi Docker Compose yang dibangun di atas image `ghcr.io/openai/codex-security`. Dan kalau kamu menginginkannya di dalam kode, bukan di command line, SDK-nya tinggal satu import:

```typescript
import { CodexSecurity } from "@openai/codex-security";
```

## Apa yang baru di 0.10.0

Tiga perubahan yang penting dalam praktik:

- **Scan yang bisa dilanjutkan (resumable scan).** Standard scan yang terputus bisa dilanjutkan dari titik berhentinya dengan `cs scans resume SCAN_ID`, bukan mulai dari nol dan membayar dua kali.
- **Budget biaya bersama.** `--max-total-cost` memasang satu budget untuk satu batch scan, persis yang kamu butuhkan saat job malam menyapu puluhan repository.
- **Penjelasan pemblokiran patch yang lebih jelas.** Saat sebuah perbaikan tidak bisa diterapkan, tool ini sekarang menjelaskan alasannya, bukan gagal diam-diam — perbedaan antara jalan buntu dan langkah berikutnya.

Semua ini tidak mengubah apa yang ditemukan scanner. Yang berubah adalah apakah kamu bisa menjalankannya sebagai pipeline yang bisa diulang, bukan eksperimen sekali jalan — arah yang sama dengan seluruh kategori ini. Skill security-audit open-source Cloudflare, yang dibahas di sini dua minggu lalu, bertaruh pada hal yang sama: nilainya ada pada validasi dan orkestrasi, bukan pada tebakan pertama model.

## Dua hal yang perlu diwaspadai

Pertama, biaya dan akses. Codex Security memang open source, tapi bukan scanner gratis yang berdiri sendiri. Scan yang memakai inferensi OpenAI membutuhkan akses Codex Security atau API key, dan kode kamu dikirim ke server OpenAI untuk dianalisis. Beberapa permintaan keamanan siber juga membutuhkan program Trusted Access for Cyber dari OpenAI, jalur akses yang dibatasi — tidak semua fitur tersedia untuk semua pengguna secara default. README juga mencatat penyedia inferensi alternatif, termasuk Amazon Bedrock, OpenRouter, dan Fireworks. Anggarkan token seperti kamu menganggarkan tool berbasis [[LLM]] lainnya, dan periksa ketentuan penanganan datanya sebelum mengarahkannya ke kode proprietary.

Kedua, hal yang sama berlaku untuk semua scanner: temuan yang tervalidasi tetap membutuhkan manusia untuk memutuskan apakah ia penting. Versi 0.10.0, menurut penomorannya sendiri, belum produk jadi. Validasi memangkas [[false positive]]; ia tidak menghilangkan penilaian. Bug asli di code path yang mati dan bug asli di halaman login kamu sama-sama "terkonfirmasi" — hanya satu yang pantas mendapatkan sore harimu.

## Yang bisa dilakukan minggu ini

1. **Install dan scan repo yang kamu miliki** — mulai dengan `--diff origin/main` pada sebuah pull request, di mana blast radius-nya kecil dan temuannya segar.
2. **Set `--max-cost` sebelum scan repo penuh pertama.** Pelajari berapa biaya sebuah scan di codebase kamu sebelum ia berjalan tanpa pengawasan.
3. **Baca temuan yang tervalidasi, lalu baca source trace di balik salah satunya.** Kepercayaan diperoleh per temuan, bukan per tool.
4. **Pasang GitHub Action di satu repository** dengan batas contoh $5, mengekspor SARIF supaya temuan mendarat di tempat tim kamu sudah men-triase issue.
5. **Jangan auto-merge patch-nya.** Biarkan perbaikan itu duduk di pull request bersama hasil re-check-nya, dan review seperti diff lainnya.

Pola di seluruh rilis open-source bulan ini sulit dilewatkan: uangnya sudah berpindah dari generasi ke verifikasi. Chrome mengajari coding agent soal web modern sebelum mereka menulis, sebuah tool 10.000 star kini menempatkan manusia di antara agen dan merge, dan scanner OpenAI berdebat dengan dirinya sendiri sebelum berdebat dengan kamu. Tool yang bertahan dari pergeseran ini bukan yang menemukan bug terbanyak. Melainkan yang temuannya bisa kamu percaya — dan yang patch-nya bisa kamu merge tanpa menahan napas.

---

*Sumber: [Open Source Radar — November 14: OpenAI's Codex Security CLI (siliconnoon.com, 14 November 2026)](https://siliconnoon.com/open-source-radar-november-14-openais-codex-security-cli/); [OpenAI's Codex Security Hits 12,500 Stars (inoryva.blogspot.com, 13 November 2026)](http://inoryva.blogspot.com/2026/11/openais-codex-security-hits-12500-stars.html); [Codex Security: OpenAI's vulnerability scanner, explained (systemdesign.academy, November 2026)](https://www.systemdesign.academy/explained/codex-security); [openai/codex-security (GitHub)](https://github.com/openai/codex-security).*
