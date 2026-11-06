---
title: "Ubah Agen Coding-mu Menjadi Auditor Keamanan: Mengenal Security-Audit Skill Open-Source dari Cloudflare"
date: 2026-11-06
tags: [tools, ai-security, code-audit, cloudflare]
excerpt: "Cloudflare membuka kode skill yang menjadi benih sistem penemuan kerentanan di seluruh armadanya: alur audit enam fase di mana agen baru mencoba membantah setiap temuan sebelum temuan itu dihitung. Begini cara kerjanya, biayanya, dan aturan sandbox yang tidak boleh dilewati."
cover: /assets/covers/cloudflare-security-audit-skill.jpg
---

Minta agen coding untuk "periksa kode ini dari sisi keamanan" dan kamu akan mendapat jawaban. Minta dua kali dan kamu akan mendapat dua jawaban yang berbeda. Minta dia membuktikan bug itu benar-benar ada, dan biasanya dia hanya akan mengulang jawabannya dengan lebih percaya diri. Itulah celah yang dihadapi tim keamanan Cloudflare ketika mereka mencoba mengubah code review berbasis AI menjadi sesuatu yang bisa dijalankan di seluruh armada mereka — dan celah itulah yang coba ditutup oleh `security-audit-skill` yang baru mereka open-source-kan.

Repositorinya, `cloudflare/security-audit-skill`, berlisensi MIT dan meraih puluhan ribu bintang GitHub dalam hitungan minggu setelah rilis. Tapi jumlah bintang bukan hal yang paling menarik. Yang penting adalah desainnya: skill ini tidak mempercayai model yang menemukan bug. Setiap kandidat temuan diserahkan ke agen baru yang tugasnya hanya satu — membantahnya — dan hanya temuan yang selamat dari serangan itu yang dicatat sebagai terkonfirmasi.

## Asal-usulnya

Pada Juni 2026, Cloudflare menerbitkan postingan blog berjudul "Build your own vulnerability harness" yang menceritakan bagaimana tim mereka berangkat dari satu skill menuju sistem multi-tahap. Titik awalnya adalah sebuah [[agent skill]] sepanjang sekitar 450 baris yang dijalankan pada satu repositori, disetel sampai benar-benar menemukan bug. Dari perintah slash-command pertama sampai pemindai yang mencakup 128 repositori, butuh waktu sekitar enam minggu. Di perjalanan, tim itu menabrak tiga tembok yang tidak bisa dipecahkan oleh satu skill saja: kehabisan konteks, tidak ada persistensi setelah crash, dan tidak ada penalaran lintas repositori. Repo open-source ini adalah titik awal single-repo itu — benih tempat harness tumbuh, bukan harness itu sendiri. Satu detail dari postingan itu menjelaskan sebagian besar desainnya: Cloudflare memakai satu model untuk discovery dan model yang berbeda untuk validasi, supaya keduanya saling memeriksa.

## Enam fase

Audit penuh berjalan sebagai pipeline, dan setiap tahap menyerahkan state terstruktur ke tahap berikutnya, bukan sekadar prosa:

1. **Reconnaissance.** Memetakan arsitektur, trust boundary, permukaan input, dan bukti sebelumnya ke dalam `architecture.md` dan sebuah [[coverage ledger]] (`coverage-ledger.json`) — catatan deterministik tentang apa saja yang ada, dan karena itu apa saja yang harus diperiksa.
2. **Coverage-led hunting.** Agen hunter yang terisolasi ditugaskan pada unit-unit dari ledger, mencatat setiap pemeriksaan yang mereka lakukan, dan coverage critic memburu celah yang terlewat oleh para hunter.
3. **Candidate validation.** Setiap kandidat unik diserahkan ke verifier baru yang instruksinya adalah membantahnya.
4. **Structured output.** Temuan ditulis sebagai record `confirmed`, `needs_validation`, atau `rejected` di `findings.json`, divalidasi terhadap JSON schema (`report-schema.json`).
5. **Independent record verification.** Agen baru memeriksa ulang klaim sumber final, dan penggantian material apa pun mendapat verifier independen tambahan.
6. **Target-neutral reporting.** `REPORT.md`, `FINDINGS-DETAIL.md`, dan `NEEDS-VALIDATION.md` yang mudah dibaca manusia diturunkan dari record terverifikasi dan coverage ledger.

Dua skrip kecil menegakkan struktur itu alih-alih mempercayakan format pada ingatan model: `validate-coverage-ledger.cjs` berjalan setelah ledger dibuat dan setelah setiap pembaruan, dan `validate-findings.cjs` berjalan di fase 4 dan setelah setiap penggantian di fase 5. Keduanya adalah skrip Node tanpa dependensi, jadi kedisiplinannya tidak bergantung pada ingatan model.

Skill ini dilengkapi sebelas matriks serangan per domain — memory safety dan binary, target AI dan LLM, protokol web dan auth, kode client-side, [[supply chain attack]] dan rilis, cloud dan deployment, RPC dan messaging, resource exhaustion, isolasi data, serta desktop, mobile, dan IPC lokal. Skill memilih kelas yang cocok dengan targetnya, jadi aplikasi web TypeScript tidak akan mendapat prompt kernel-fuzzing.

## Tiga verdict — dan mengapa yang di tengah paling penting

| Verdict | Artinya |
|---|---|
| `confirmed` | Jejak sumber lengkap dan hasil observasi yang terbatas |
| `needs_validation` | Ada satu fakta yang belum terjawab, dan tidak ada severity yang ditetapkan |
| `rejected` | Kandidat yang berhasil dibantah |

Kategori tengah itulah yang paling berguna. Kebanyakan tool audit AI menyajikan setiap kecurigaan sebagai temuan. Di sini, lead yang tidak bisa dibuktikan tetap berlabel belum terbukti, lengkap dengan pertanyaan spesifik yang menghalanginya. Satu pengujian lapangan independen terhadap skill ini melaporkan 46 record dari satu codebase: 10 terkonfirmasi dan 36 ditahan di `needs_validation`, masing-masing dengan fakta persis yang dibutuhkan manusia untuk menyelesaikannya.

Lima prinsip desain berada di balik alur kerja ini, dan semuanya terbaca seperti checklist untuk review agentic apa pun:

- **Hanya konfirmasi kegagalan boundary yang sudah terbukti.** Lead yang terblokir tapi berakar pada sumber tetap berstatus `needs_validation`.
- **[[Adversarial validation]].** Agen yang memeriksa temuan tidak pernah menjadi agen yang menemukannya.
- **Severity membutuhkan impact.** Likelihood dikali impact, bukan penyimpangan dari checklist.
- **Celah defense-in-depth bukan kerentanan.** Jika layer A mencegah serangan, layer B yang hilang hanyalah catatan hardening.
- **Run berulang meningkatkan coverage.** Cloudflare menyebut satu run hanya menemukan sekitar setengah dari total yang ditemukan run berulang.

## Cara menginstal dan menjalankannya

Instal dengan Skills CLI:

```bash
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit
```

Tambahkan `--global` untuk instalasi di level pengguna. Lalu jalankan coding agent kamu — Claude Code, Codex, Cursor, atau agen lain yang mendukung tool use dan sub-agent paralel — di codebase target dan minta dengan bahasa biasa:

```text
security audit this codebase
find security vulnerabilities in ./src
do a security review, output to ~/audits/my-project
```

Permintaan audit langsung memakai full audit mode; pertanyaan keamanan dan pekerjaan [[vulnerability]] yang terfokus memakai guidance mode yang lebih ringan kecuali kamu meminta artefak laporan. Dalam full mode, direktori output yang tidak ditentukan akan default ke `~/security-audit-skill/<repo-name>/run-<N>`, dan alur kerja hanya menulis di dalam repositori target jika kamu secara eksplisit memilih direktori di sana. Run berulang bersifat aditif: mereka memakai ulang ledger sebelumnya untuk menyasar celah dan memvalidasi ulang sumber yang berubah, alih-alih mulai dari nol.

## Persyaratan yang sering dilewati: sandbox

README-nya eksplisit tentang apa yang kamu butuhkan: coding agent yang modelnya mendukung tool use dan sub-agent paralel, Node.js untuk validator, dan [[sandbox]] yang ditegakkan OS untuk apa pun yang dikendalikan target — build, test, proses, browser, emulator, fuzzer, fixture. Sandbox itu harus menonaktifkan jaringan eksternal, memakai environment yang disanitasi dan di-allowlist, menegakkan batas resource, dan hanya mengizinkan penulisan ke scratch path yang ditetapkan. Tanpa kontrol itu, alur kerja akan menahan lead sebagai `needs_validation` alih-alih mengeksekusi kode target.

Mengapa ini penting: untuk memvalidasi bug, skill mungkin perlu membangun dan menjalankan kode yang diaudit, dan repositori yang tidak tepercaya bisa mengeksekusi apa saja di dalam build script-nya. Jika kamu mengarahkan skill ini ke kode yang bukan kamu tulis, anggap sandbox sebagai wajib. Ini adalah kelas risiko yang sama dengan [[prompt injection]] dan [[tool poisoning]] di server [[MCP]] — hanya saja di sini skill itu sendiri yang menjalankan kodenya. Container atau VM dengan jaringan yang dimatikan adalah batas minimum; checkout telanjang di host bukanlah tempat menjalankan ini.

## Biayanya, dan apa yang tidak dijanjikan

Bagian jujur dari cerita ini adalah biayanya. Cloudflare tidak menerbitkan angka token per run di README. Satu komentator Hacker News melaporkan menghabiskan sekitar 1 juta token pada codebase berukuran sedang tanpa hasil yang bisa ditunjukkan — laporan satu komentator, bukan pengukuran terverifikasi, tapi konsisten dengan biaya audit multi-agent dan multi-fase. Jawaban yang adil untuk skeptis yang menyebutnya "cuma file markdown" adalah bahwa nilainya terletak pada orkestrasi dan validator, bukan pada satu prompt mana pun — merekalah yang membuat output bisa diperiksa mesin, sesuatu yang tidak dimiliki prompt code-review biasa.

Cloudflare juga belum menerbitkan tingkat presisi atau false-positive untuk skill open-source ini, dan berapa banyak kerentanan nyata yang sudah ditemukannya di luar armada Cloudflare sendiri masih belum diketahui. Perlakukan ia sebagaimana adanya: titik awal yang kuat untuk audit terstruktur, bukan scanner yang punya benchmark.

## Yang bisa dilakukan minggu ini

1. **Jalankan di repo milikmu sendiri**, di dalam container atau VM dengan jaringan yang dimatikan.
2. **Jalankan setidaknya dua kali.** Run berulang menemukan lebih banyak, dan skill memakai ledger sebelumnya untuk menyasar celah.
3. **Baca `NEEDS-VALIDATION.md` dulu.** Lead yang belum terselesaikan menunjukkan di mana agen tidak bisa membuktikan sesuatu — dan fakta apa yang hilang.
4. **Jangan mengajukan laporan bug dari record `confirmed` tanpa membaca sendiri jejak sumbernya.** Jejak yang terverifikasi tetaplah klaim sampai manusia membacanya.
5. **Lacak biaya token per run** sebelum menjadwalkannya di CI.

Pola yang lebih besar di sini layak disebut. Lab dan vendor sedang bergerak dari "bisakah model menemukan bug" menuju "bagaimana menjalankan ini sebagai pipeline yang bisa diulang" — Frontier Red Team Anthropic menerbitkan riset exploit yang dibuat AI, OpenAI meluncurkan GPT-6 Cyber ke pelanggan terverifikasi, Trail of Bits menerbitkan plugin agen untuk patching. Kontribusi Cloudflare adalah yang paling tidak glamor dan mungkin paling berguna: alur kerja yang menganggap penemu salah sampai orang asing membuktikan dia benar. Begitulah cara kerja audit yang seharusnya.

---

*Sumber: [Cloudflare security-audit-skill: 6 Phases, 25.6k Stars (explainx.ai, November 2026)](https://explainx.ai/blog/cloudflare-security-audit-skill-open-source-agent-vulnerability-hunting-2026); [Cloudflare Security Audit Skill for Claude Code (devpik.com)](https://www.devpik.com/open-source/security-audit-skill); [Who Audits the Agent? Security Review Is a Category (dev.to, November 2026)](https://dev.to/max_quimby/who-audits-the-agent-security-review-is-a-category-g4e); [Field notes: running Cloudflare's open-source security-audit-skill on a real codebase (norforge.com)](https://norforge.com/blog/field-notes-cloudflare-security-audit-skill); [cloudflare/security-audit-skill (GitHub)](https://github.com/cloudflare/security-audit-skill).*
