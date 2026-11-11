---
title: "Audit Repo Sendiri dari Secret yang Bocor: Panduan Praktis Gitleaks dan TruffleHog"
date: 2026-11-11
tags: [hands-on, secrets, gitleaks, git-security]
excerpt: "GitGuardian menghitung 28,65 juta secret hardcoded baru di GitHub publik sepanjang 2025, dan penyerang kini hanya butuh lima menit dari kunci yang bocor sampai menguras cloud vault. Panduan ini memasang Gitleaks dan TruffleHog di repo sendiri — memindai history, memblokir kebocoran berikutnya saat commit, dan tahu persis apa yang harus di-rotate saat satu secret lolos."
cover: /assets/covers/audit-your-repos-for-leaked-secrets.jpg
---

Kode kamu mungkin sedang membocorkan kredensial sekarang, dan kebocorannya bukan di file yang sedang kamu lihat. Ia ada di commit dua tahun lalu, di file `.env` yang sudah dihapus tapi tidak pernah dibersihkan dari history, di konfigurasi MCP yang ikut ter-commit bersama backup dotfile. Pada 13 Oktober 2026, Meta memberi tahu SecurityWeek bahwa mereka memberitahu sekitar 1.500 orang — sebagian besar karyawan mereka sendiri di Amerika Serikat — setelah penyusup memakai kredensial karyawan yang dicuri untuk mengakses repositori GitHub mereka. Repositori itu berisi secret di samping kode, dan Meta me-rotate semuanya. Perusahaan itu tidak dibobol lewat kerentanan produk. Kredensial seseorang membuka pintu depan, dan secret-nya memang sudah duduk di dalam.

Itulah bentuk normal insiden secret. GitGuardian menghitung 28,65 juta [[hardcoded secret]] baru di GitHub publik sepanjang 2025, naik 34% dari tahun sebelumnya, dan lebih dari 64% secret yang mereka konfirmasi valid pada 2022 ternyata masih valid saat diuji ulang pada Januari 2026. Secret yang bocor ke layanan AI naik 81% dari tahun ke tahun, menjadi 1.275.105. Dan jeda antara kebocoran dan penyalahgunaan sudah runtuh: Microsoft mengamati sebuah framework agentic yang hanya butuh lima menit dari pencarian secret di GitHub sampai mengekstfiltrasi Azure Key Vault. Lima menit tidak cukup untuk menyadari sebuah alert, apalagi mengadakan rapat tentangnya. Satu-satunya pertahanan yang bekerja pada kecepatan itu adalah pertahanan yang sudah terpasang sebelum kebocoran terjadi.

Artikel ini membangun pertahanan itu di mesin kamu sendiri, secara praktis: memindai history yang sudah ada, memblokir kebocoran baru saat commit, menangkap sisanya di CI, dan menyiapkan runbook rotasi untuk hari ketika sesuatu lolos. Tool-nya gratis dan open source — [[Gitleaks]] v8.30.1 dan [[TruffleHog]] v3.99.3, versi yang diverifikasi pada 20 Oktober 2026 — dan seluruh setup memakan waktu sekitar satu jam.

## Mengapa `grep` bukan audit

Kesalahan pertama adalah meraih `grep -r "API_KEY" .`. Perintah itu hanya mencari file yang ada sekarang. Secret yang di-commit pada 2023 dan dihapus pada 2024 tidak terlihat olehnya — tapi ia masih duduk di git history, hanya sejauh `git log -p` dari siapa pun yang meng-clone repositori. Audit apa pun yang tidak menelusuri setiap commit adalah pertunjukan, bukan pemeriksaan.

Dua scanner dalam panduan ini menyerang masalah dari arah berlawanan, dan karena itulah mereka bekerja baik bersama. Gitleaks berbasis regex dan [[entropy]]: ia mencocokkan format kredensial yang dikenal (kunci AWS, token GitHub, kunci Stripe, dan ratusan lainnya) serta menandai string ber-entropi tinggi yang terlihat cukup acak untuk menjadi secret. Ia cepat, bekerja offline, dan ideal untuk hook yang berjalan di setiap commit. TruffleHog mengklasifikasikan lebih dari 800 jenis secret dan, yang terpenting, bisa *memverifikasi* kandidat dengan memanggil API penyedianya — mengubah "ini terlihat seperti kunci Stripe" menjadi "ini adalah kunci Stripe yang masih aktif". Verifikasi itulah yang membuatnya berguna di CI, tempat kamu menginginkan sedikit alert dan setiap alert benar-benar nyata.

## Langkah 1: Instal tool-nya

Di macOS atau Linux dengan Homebrew, satu perintah menginstal semuanya, termasuk dua tool yang nanti dibutuhkan untuk membersihkan history:

```bash
brew install gitleaks trufflehog pre-commit git-filter-repo

gitleaks version        # expect: 8.30.1
trufflehog --version    # expect: trufflehog 3.99.3
pre-commit --version    # expect: pre-commit 4.7.0
git filter-repo --version
```

Tool Python-nya juga tersedia lewat pipx (`pipx install pre-commit==4.7.0` dan `pipx install git-filter-repo==2.47.0`). Pin versinya di CI nanti; di laptop, formula Homebrew terbaru sudah cukup.

## Langkah 2: Pindai history yang sudah ada

Sebelum menambahkan hook apa pun, cari tahu apa yang sudah ada di repositori. Kalau tidak, run CI pertama akan gagal karena kunci yang di-commit bertahun-tahun lalu dan seseorang akan menonaktifkan job-nya. Jalankan kedua scanner ke seluruh history:

```bash
cd your-repo

# Gitleaks: pindai setiap commit yang terjangkau dari semua ref, redact secret di output
gitleaks git --redact -v --log-opts="--all" --report-path gitleaks-report.json .

# TruffleHog: pindai seluruh history, tampilkan hanya kredensial yang terverifikasi masih aktif
trufflehog git file://. --results=verified,unknown
```

Selalu sertakan `--redact` untuk Gitleaks: tanpanya, secret itu sendiri mendarat di scrollback terminal dan di file laporan. Jauhkan laporan dari git (`echo "gitleaks-report.json" >> .gitignore`) — ia bisa berisi secret sebagian.

Sebuah temuan Gitleaks terlihat seperti ini, dipangkas dan di-redact:

```
Finding:     aws_secret_access_key = REDACTED
Secret:      REDACTED
RuleID:      aws-access-token
File:        deploy/old-config.env
Line:        4
Commit:      9f2c1e7...
Fingerprint: 9f2c1e7...:deploy/old-config.env:aws-access-token:4
```

Perhatikan exit code-nya, karena CI akan bergantung padanya: Gitleaks keluar dengan kode `1` saat menemukan kebocoran; TruffleHog keluar dengan kode `183` saat ada hasil dan `--fail` dipakai. Opsi TruffleHog `--results=verified,unknown` adalah default yang tepat untuk triase — temuan yang terverifikasi adalah kredensial aktif, bisa dieksploitasi sekarang juga, dan mereka didahulukan.

Untuk setiap temuan nyata, lompat ke runbook rotasi di Langkah 6 *sebelum* menyentuh history. Lalu putuskan apakah temuan lama harus memblokir pemindaian berikutnya: Gitleaks mendukung baseline, jadi kamu bisa merekam temuan lama dan hanya gagal pada temuan baru:

```bash
gitleaks git --baseline-path gitleaks-report.json --report-path findings.json .
```

## Langkah 3: Blokir kebocoran berikutnya saat commit

Hook yang berjalan sebelum commit terbentuk adalah lapisan termurah yang pernah kamu bangun. Buat `.pre-commit-config.yaml` di root repositori:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks          # runs: gitleaks git --pre-commit --redact --staged --verbose
  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.99.3
    hooks:
      - id: trufflehog        # runs: trufflehog git file://. --since-commit HEAD --results=verified --fail
```

Lalu instal dan jalankan sekali ke semua file:

```bash
pre-commit install            # writes .git/hooks/pre-commit
pre-commit run --all-files    # first run builds both Go hooks, so it is slow once
```

Uji dengan token palsu yang cocok dengan format asli (acak, bukan kredensial):

```bash
echo 'token = "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"' > leak-test.py
git add leak-test.py
git commit -m "test"
```

Commit itu harus ditolak dengan `Detect hardcoded secrets... Failed`, `RuleID: github-pat`, dan exit code 1. Bersihkan dengan `git rm --cached leak-test.py && rm leak-test.py`. Hook TruffleHog akan diam terhadap token palsu ini, karena ia hanya melaporkan hasil terverifikasi dan token itu tidak aktif. Itu memang disengaja — Gitleaks-lah yang memblokir secara lokal.

Jujurlah tentang apa itu hook: sabuk pengaman, bukan gembok. Siapa pun bisa melewatinya dengan `git commit --no-verify`, dan clone baru tidak punya hook sampai seseorang menjalankan `pre-commit install`. Karena itulah dua lapisan berikutnya ada.

## Langkah 4: Tangani false positive tanpa mematikan scanner

Cara tercepat membunuh sebuah security tool adalah membiarkannya berteriak palsu sampai seseorang mematikannya. Kamu punya tiga cara untuk false positive, dari yang paling sempit sampai paling luas. Komentar inline untuk nilai tes yang sudah diketahui, pada satu baris:

```python
STRIPE_TEST_KEY = "sk_test_placeholder_not_real"  # gitleaks:allow
```

Entri `.gitleaksignore` untuk satu temuan spesifik, disalin berdasarkan fingerprint dari laporan (`commit:file:rule:line` untuk pemindaian history):

```
9f2c1e7d4b1a0c8e6f3d2b1a09f8e7d6c5b4a3f2:tests/fixtures/jwt.txt:jwt:12
```

Dan `.gitleaks.toml` untuk memperluas aturan default dengan allowlist path — perhatikan perubahan sintaks v8.25.0 menjadi `[[allowlists]]`:

```toml
# .gitleaks.toml (picked up automatically from the repo root)
title = "repo gitleaks config"

[extend]
useDefault = true                 # keep all built-in rules

[[allowlists]]
description = "test fixtures and lockfiles"
paths = [
  '''tests/fixtures/.*''',
  '''(.*?)package-lock\.json$''',
]
```

Pelitlah dengan allowlist path. Pengecualian `tests/` adalah tempat seseorang menempel kunci staging asli "hanya untuk tes ini". Dan pindai juga konfigurasi tool AI kamu: GitGuardian menemukan 24.008 secret unik di file konfigurasi terkait MCP sepanjang 2025. Direktori seperti `.cursor/`, `.claude/`, dan file konfigurasi MCP seharusnya masuk ke dalam pemindaian, bukan keluar darinya.

## Langkah 5: Push protection dan CI — lapisan yang tak bisa dilewati siapa pun

[[Push protection]] adalah pemeriksaan di sisi server GitHub: ia menolak push yang berisi secret yang dikenali sebelum push itu mendarat. Push protection tingkat pengguna aktif secara default untuk push ke repositori publik; perlindungan tingkat repositori pada repositori privat membutuhkan GitHub Secret Protection, seharga $19 per active committer per bulan. Aktifkan dengan GitHub CLI:

```bash
OWNER=your-org REPO=your-repo
gh api -X PATCH "repos/$OWNER/$REPO" \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'

# Confirm
gh api "repos/$OWNER/$REPO" --jq '.security_and_analysis'
```

Push yang diblokir terlihat seperti `remote: error: GH013: Repository rule violations found` diikuti "Push cannot contain secrets". Siapa pun dengan akses tulis bisa melewatinya dengan alasan, dan setiap bypass tercatat di audit log serta dikirim lewat email ke admin repositori — tinjau itu setiap minggu, dan aktifkan delegated bypass kalau kamu ingin hanya staf keamanan yang bisa menyetujuinya.

CI adalah lapisan yang dilalui semua orang, karena hook bisa dilewati dan push protection hanya mengenal format token penyedia. Workflow minimal menjalankan kedua scanner di setiap pull request, dengan setiap third-party action di-pin ke commit SHA penuh:

```yaml
# .github/workflows/secret-scan.yml
name: secret-scan
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  gitleaks:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7.0.1
        with:
          fetch-depth: 0
      - name: Install gitleaks 8.30.1 (checksum verified)
        run: |
          V=8.30.1
          curl -sSLO "https://github.com/gitleaks/gitleaks/releases/download/v${V}/gitleaks_${V}_linux_x64.tar.gz"
          curl -sSLO "https://github.com/gitleaks/gitleaks/releases/download/v${V}/gitleaks_${V}_checksums.txt"
          grep "gitleaks_${V}_linux_x64.tar.gz" "gitleaks_${V}_checksums.txt" | sha256sum -c -
          tar -xzf "gitleaks_${V}_linux_x64.tar.gz" gitleaks
      - name: Scan commits in this PR or push
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            RANGE="${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }}"
          else
            RANGE="${{ github.event.before }}..${{ github.sha }}"
          fi
          ./gitleaks git --redact -v --log-opts="$RANGE" .
  trufflehog:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7.0.1
        with:
          fetch-depth: 0
      - uses: trufflesecurity/trufflehog@v3.99.3
        with:
          version: 3.99.3
          extra_args: --results=verified,unknown
```

Jadikan kedua job itu required status checks di branch protection atau ruleset — kalau tidak, check merah hanya jadi saran. Satu detail yang layak diketahui: GitHub Action resmi gitleaks membutuhkan `GITLEAKS_LICENSE` gratis untuk repositori milik organisasi, dan karena itulah workflow di atas menjalankan binary secara langsung.

## Langkah 6: Sebuah secret bocor. Rotate dulu.

Panduan GitHub sendiri tegas: cabut atau rotate kredensial sebelum hal lain, karena begitu kredensial itu tidak bisa dipakai, kamu mungkin tidak perlu menulis ulang history sama sekali. Anggap secret di repositori publik sudah di-scrape dalam hitungan menit — kisah Key Vault lima menit di atas adalah buktinya — dan ingat bahwa npm worm tahun lalu memanen kredensial langsung dari mesin developer dan runner CI, bukan hanya dari repositori.

Untuk access key pengguna IAM AWS, urutannya adalah buat, deploy, nonaktifkan, selidiki, hapus:

```bash
USER=ci-deployer
OLD=AKIA...LEAKED   # the leaked access key ID
# 1. Create the replacement (an IAM user can have at most two keys)
aws iam create-access-key --user-name "$USER"
# 2. Deploy the new key to your secret manager and consumers, then:
aws iam update-access-key --user-name "$USER" --access-key-id "$OLD" --status Inactive
# 3. See what the leaked key did (CloudTrail event history covers 90 days)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue="$OLD" \
  --max-results 50 --query 'Events[].[EventTime,EventName,Username]' --output table
# 4. Once nothing breaks, delete it
aws iam delete-access-key --user-name "$USER" --access-key-id "$OLD"
```

Pola yang sama berlaku di mana-mana: token GitHub dicabut dari Developer settings, kunci Stripe dan OpenAI di-roll dari dashboard mereka, password database diganti dan connection string di-deploy ulang. Lebih baik lagi, hilangkan kunci berumur panjang itu sepenuhnya — workload identity federation memungkinkan CI mengautentikasi ke AWS, GCP, dan Azure tanpa secret tersimpan yang bisa bocor.

Baru setelah rotasi kamu boleh menghapus secret dari git history, dengan `git filter-repo`. Menulis ulang history mengubah setiap hash commit setelah kebocoran, merusak pull request yang terbuka, dan membatalkan signature, jadi itu adalah operasi yang disengaja dan diumumkan — bukan langkah pertama, dan bukan pengganti rotasi. Secret yang sudah di-rotate di history lama hanyalah string mati. Secret yang belum di-rotate dengan history yang bersih tetaplah kredensial aktif.

## Versi tiga puluh menit

Kalau kamu hanya melakukan satu hal hari ini, lakukan Langkah 2: pindai history repositori terpentingmu. Butuh beberapa menit, dan hasilnya entah melegakan atau menjadi temuan paling berharga minggu ini. Kalau kamu melakukan dua hal, tambahkan pre-commit hook — biayanya satu file dan ia menghentikan kebocoran berikutnya di keyboard tempat ia bermula. Stack lengkap — hook, push protection, CI, runbook — adalah pembeda antara Oktober-nya Meta dan Oktober yang lebih tenang: secret tetap bocor, tapi ia sudah mati sebelum sempat dipakai siapa pun, dan kebocoran berikutnya tidak pernah sampai ke repositori.

Secret tidak bocor karena developer ceroboh. Mereka bocor karena tempat yang nyaman untuk menaruh kunci dan tempat yang aman untuk menaruh kunci tidak pernah sama, dan setiap workflow diam-diam mendorong ke arah yang nyaman. Bangun tempat yang aman lebih dulu, jadikan ia default, dan biarkan scanner menjaga celahnya. Dirimu di masa depan — yang tidak perlu memberitahu 1.500 orang — akan berterima kasih.

*Sumber: GitGuardian State of Secrets Sprawl 2026; SecurityWeek, 13 Oktober 2026 (akses repositori GitHub Meta); Ajay Kumar, "How to Stop Secrets Leaking Into Git" (versi tool diverifikasi 20 Oktober 2026); dokumentasi GitHub tentang secret scanning dan push protection.*
