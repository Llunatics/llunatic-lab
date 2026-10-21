---
title: "Plugin Agen AI-mu Adalah Attack Surface Baru: Mengaudit MCP Server dengan mcp-scan"
date: 2026-10-21
tags: [mcp, ai-security, tools, prompt-injection]
excerpt: "Agen AI kini menjelajah web, menjalankan kode, dan mengquery database lewat MCP server — dan penyerang sudah menyadarinya. Begini cara kerja tool poisoning, kenapa Oktober 2026 menjadikan MCP headline threat, dan cara mengaudit setup-mu sendiri dengan mcp-scan dari Invariant Labs sebelum sebuah plugin mengauditmu."
cover: /assets/covers/mcp-server-audit-scan.jpg
---

Kamu memasang plugin kalkulator yang kelihatannya tidak berbahaya untuk AI coding agent-mu. Deskripsi tool-nya bilang ia "menjumlahkan dua angka dan mengembalikan hasilnya." Kamu tidak pernah membaca sisanya — karena memang tidak ada "sisanya" sejauh yang ditampilkan UI. Tapi tersembunyi di dalam deskripsi itu, tak terlihat olehmu, ada blok teks yang memerintahkan agen untuk membaca SSH private key dan file konfigurasi MCP-mu dulu, menyelundupkan isinya lewat parameter sampingan, dan tidak pernah menceritakannya kepadamu.

Itulah [[tool poisoning]], yang didemonstrasikan secara publik oleh Invariant Labs pada April 2025. Tanpa authentication bypass. Tanpa exploit memory-corruption. Hanya teks dalam sebuah field JSON yang dibaca agen sebagai konteks tepercaya. Dan satu setengah tahun kemudian, pada Oktober 2026, seluruh kategori ini meledak menjadi salah satu cerita terpanas di dunia keamanan.

## Kenapa MCP jadi target

[[MCP]] — Model Context Protocol — adalah standar terbuka dari Anthropic, diperkenalkan November 2024, yang memungkinkan asisten AI memanggil tool eksternal: filesystem, API, database, utilitas developer seperti Git. MCP server adalah jembatan: model yang memutuskan, server yang mengeksekusi aksi sistem yang nyata.

Jembatan itu menjadi mainstream dengan cepat. Pada Q3 2026, Gartner memperkirakan lebih dari 40% perusahaan yang menjalankan deployment LLM telah mengembangkannya menjadi arsitektur agen otonom — sistem di mana agen menjelajah web, mengeksekusi kode, mengquery database, mengirim email, dan mengorkestrasi sub-agen lain. Setiap kemampuan itu adalah sebuah tool. Setiap tool adalah server yang ditulis seseorang. Dan server yang ditulis orang asing kini duduk di antara agenmu dan infrastrukturmu.

Angka-angka bulan ini menceritakan semuanya. Enterprise MCP Guide 2026, terbit 5 Oktober oleh The Agentics, mencatat **68 CVE MCP server dalam satu bulan** dan menamai enam kelas serangan yang berbeda. Analisis Stingrai terhadap NVD menemukan **141 CVE yang deskripsinya mengandung frasa persis "prompt injection"** — 87 di antaranya terbit pada 2026 saja, dengan 105 berstatus High atau Critical. [[MITRE ATT&CK]] v20, rilis 13 Oktober 2026, menambahkan Direct [[Prompt Injection]], Indirect Prompt Injection, dan AI-Enabled Exfiltration sebagai teknik resmi. Ini bukan lagi sekadar keingintahuan riset; ini attack surface yang terlacak, tertaksonomi, dan sedang dieksploitasi.

## Enam jalan masuknya

Taksonomi dari The Agentics layak dihafal, karena setiap kelas meruntuhkan asumsi yang berbeda:

1. **Tool poisoning** — instruksi jahat disembunyikan dalam deskripsi tool, yang dibaca model di setiap pemanggilan sementara pengguna hanya melihat nama yang ramah.
2. **Schema poisoning** — daftar tool yang tersedia itu sendiri dirusak.
3. **Tool shadowing** — tool jahat diam-diam menimpa tool sah dengan nama yang sama, sehingga agen memanggil kode penyerang sementara dialog persetujuan menampilkan label yang familiar.
4. **Command injection** — instruksi penyerang disematkan dalam konten yang diproses agen (dokumen, halaman web, output tool).
5. **Shadow servers** — MCP server tak resmi ditambahkan ke environment agen tanpa persetujuan.
6. **Context oversharing** — agen mengekspos lebih banyak data daripada yang dibutuhkan tugas, memberi makan kelima serangan di atas.

Dua temuan nyata bulan ini membuatnya konkret. Firma keamanan Signals Corps menemukan hampir **8.000 situs web mengirim pesan ke agen AI lewat HTTP header**, dengan 30 di antaranya mencoba indirect prompt injection yang sesungguhnya. Dan peneliti independen Syed Anas Mohiuddin mendokumentasikan "protocol pivoting" — prompt injection yang diarahkan ke agen individual, bukan ke modelnya, lalu diteruskan menyusuri rantai agent-to-agent — yang berdampak pada organisasi termasuk Google, JP Morgan Chase, dan Rapid7. Kepercayaan antar agen internal, katanya, adalah kerentanannya.

## Praktik: memindai setup-mu sendiri dengan mcp-scan

Mengetahui teorinya baru setengah pekerjaan; separuhnya lagi adalah memeriksa apa yang sebenarnya tercolok ke *agenmu*. Scanner yang paling mapan adalah **mcp-scan** dari Invariant Labs — tim yang sama yang menamai tool poisoning. Ia memindai MCP server yang dikonfigurasi di Claude, Cursor, Windsurf, dan klien MCP berbasis file lainnya, mencari prompt injection dalam deskripsi tool, tool poisoning lewat analisis Guardrails mereka, dan cross-origin escalation ([[tool shadowing]]). Ia juga mendukung **tool pinning**: meng-hash definisi tool tiap server sehingga [[rug pull]] — server yang hasil scannya bersih hari ini lalu berubah jahat besok — ketahuan saat metadata-nya berubah.

Instalasinya satu perintah:

```bash
uvx mcp-scan@latest
```

Untuk benar-benar memeriksa apa yang dilihat agenmu — deskripsi tool selengkapnya, termasuk teks yang tak pernah ditampilkan UI mana pun:

```bash
uvx mcp-scan@latest inspect
```

Dan untuk pemindaian penuh atas semua server yang dikonfigurasi:

```bash
uvx mcp-scan@latest scan
```

Dua hal yang perlu kamu tahu sebelum menjalankannya. Pertama, kecuali kamu memakai flag `--local-only` (yang butuh OpenAI API key dan hasilnya kurang akurat), nama dan deskripsi tool dikirim ke API Invariant untuk dianalisis — tool ini tidak mencatat *pemanggilan* tool atau hasilnya, tapi ia membagikan metadata untuk riset. Tentukan sendiri apakah kamu nyaman dengan itu di mesin kerja. Kedua, ada alternatif komunitas yang lebih baru dan layak dikenal: scanner statis bernama `mcpscan` yang menjalankan dua belas pemeriksaan offline — frasa prompt-injection, command injection, hook berbahaya, secret yang ter-commit — tanpa dependensi sama sekali dan output JSON/SARIF untuk CI. Filosofi berbeda, tujuan sama: baca metadata-nya sebelum model membacanya.

## Caveat yang tidak nyaman

Sekarang bagian yang tidak akan ditulis vendor scanner di landing page mereka. Riset Adversa pada Oktober 2026 membangun dua MCP server jahat yang sepenuhnya berfungsi — satu pencuri kredensial, satu remote code executor — dan **kelima scanner yang mereka uji memberi hasil bersih untuk keduanya**, termasuk mcp-scanner dari Cisco, agent-scan dari Snyk, dan SkillSpector dari NVIDIA. Teknik evasinya: payload disembunyikan di handler code, obfuskasi, file berukuran raksasa, dan fingerprinting terhadap scanner. Kesimpulan mereka blak-blakan dan tepat: *hasil scan yang bersih adalah titik awal, bukan persetujuan.*

Jadi perlakukan mcp-scan sebagai detektor asap, bukan firewall. Ia menangkap yang malas, yang ceroboh, dan yang sudah dikenal — yang, jujur saja, merupakan sebagian besar isi direktori MCP server publik saat ini. Yang canggih butuh kontrol membosankan di bawahnya.

## Checklist yang benar-benar penting

Meminjam dari Enterprise MCP Guide dan para praktisi yang menulis soal ini sepanjang bulan, inilah versi berlapisnya:

- **Perlakukan setiap MCP server pihak ketiga sebagai dependency yang belum direview.** Baca deskripsi tool-nya (pakai `inspect`) sebelum menghubungkan, sama seperti kamu me-review package baru.
- **Least privilege, selalu.** Hubungkan dengan kredensial terlemah yang diizinkan tugas — read-only kalau bisa, dibatasi ke satu database atau direktori, bukan seluruh akun. Matikan grup tool write/execute kecuali workflow memang membutuhkannya.
- **Allowlist per agen.** Setiap agen hanya mendapat tool yang benar-benar dibutuhkannya. Agen penerjemah tidak ada urusannya dengan shell.
- **Catat semuanya lewat gateway.** Gateway MCP terpusat yang merekam setiap pemanggilan tool mengubah "agen melakukan sesuatu yang aneh" menjadi jejak yang bisa diaudit.
- **Persetujuan manusia untuk yang ireversibel.** Menghapus data, mengirim komunikasi, memindahkan uang — agen tidak boleh melakukannya tanpa gerbang manusia.
- **Pin tool-mu.** Hash metadata tool setelah direview; beri peringatan saat berubah. Rug pull itu soal kapan, bukan soal apakah.
- **Pindai ulang terjadwal**, bukan cuma saat instalasi. Server di-update; update bisa bersifat hostile.

## Perimeternya sudah pindah

Inilah model mental yang layak dibawa pulang: di era agen, teks paling berpengaruh dalam sebuah transaksi sering kali adalah teks yang tidak dibaca siapa pun — deskripsi tool yang dilahap model di setiap pemanggilan sementara manusia hanya melihat label yang ramah. Antarmuka yang memperlakukan teks itu sekadar metadata, lalu terkejut saat ternyata ia adalah instruksi, adalah kerentanannya. Angka-angka Oktober 2026 — 68 CVE dalam sebulan, 141 CVE prompt-injection, teknik ATT&CK dengan nama resmi — adalah gambaran ketika penyerang tiba di perimeter baru sebelum para defender.

Jalankan scan-nya. Baca deskripsinya. Pin tool-nya. Direktori plugin adalah software supply chain yang baru — dan tidak seperti npm, kebanyakan orang yang memasang darinya belum pernah sekalipun melihat apa yang mereka pasang.
