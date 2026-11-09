---
title: "sshole: Bug OpenSSH yang Membuatmu Login ke Akun Tanpa Password"
date: 2026-11-09
tags: [threat-intel, openssh, vulnerability, alpine]
excerpt: "Pada 5 November, OpenSSH merilis perbaikan darurat untuk CVE-2026-123158 — bug logika yang memungkinkan siapa pun login ke akun tanpa password di Alpine Linux dengan password yang tidak pernah diatur. Upaya eksploitasi pertama muncul kurang dari sembilan jam kemudian."
cover: /assets/covers/sshole-openssh-alpine-auth-bypass.jpg
---

Ada jenis kerentanan khusus yang tidak butuh kredensial curian, kampanye brute-force, atau satu baris malware pun. Yang dibutuhkan hanya sebuah password yang sengaja dibuat terlalu panjang — dan sebuah akun yang seharusnya tidak pernah menerima password apa pun.

Pada 5 November 2026, [[OpenSSH]] merilis Portable OpenSSH 10.6p2, perbaikan darurat untuk [[CVE]]-2026-123158, yang dijuluki "sshole" oleh penemunya, Özgün Kültekin dari Wakefield. Celah ini mendapat skor 8.1 High di CVSS 3.1 dan diklasifikasikan sebagai [[CWE]]-394, status code atau return value yang tidak terduga. Firma threat intelligence Previdian mengatakan kepada Help Net Security bahwa mereka melihat upaya eksploitasi pertama kurang dari sembilan jam setelah publikasi — dan mengonfirmasi akses root pada sebuah honeypot Alpine Linux. Developer [[OpenSSH]] Damien Miller menyebutnya kritis dan meminta administrator sistem yang terdampak untuk segera menonaktifkan login password, atau SSH sepenuhnya.

Perilakunya sederhana untuk dijelaskan dan tidak nyaman untuk dibaca. Pada sistem yang terdampak, penyerang yang bisa menjangkau port SSH dapat login ke akun yang tidak punya password, dengan mengirimkan password yang sengaja dibuat terlalu panjang. Tanpa kredensial curian. Tanpa key. Tanpa brute force. Hanya deretan karakter yang sangat panjang, dan sebuah perbandingan yang seharusnya tidak pernah berhasil.

## Tiga keputusan yang masuk akal, empat belas tahun terpisah

CVE-2026-123158 adalah bug logika, bukan kerusakan memori, dan ia hidup di celah antar proyek, bukan di dalam satu proyek saja. Tiga keputusan, masing-masing bisa dibenarkan sendiri-sendiri, bergabung menjadi sebuah authentication bypass.

**2012, [[musl]] libc.** Standar POSIX mengatakan `crypt()` — fungsi yang melakukan hashing password — harus mengembalikan null pointer saat hashing gagal. Terlalu banyak program pemanggil yang tidak pernah memeriksa nilai kembaliannya lalu crash, sehingga musl memilih mengembalikan string literal `*`. Keputusan defensif, dan bisa dibenarkan jika dilihat sendiri.

**Library yang sama membatasi panjang key.** `crypt()` berbasis SHA milik musl menolak password yang lebih panjang dari 256 byte, sebagai perlindungan agar CPU tidak terbuang untuk input yang absurd. Melewati batas itu berarti gagal — dan kegagalan kini berarti mengembalikan `*`.

**2016, OpenSSH.** Untuk memperbaiki CVE-2016-6210, sebuah side channel timing yang memungkinkan penyerang mengenali username yang valid dengan mengukur apakah [[sshd]] sempat melakukan hashing, OpenSSH 7.3 menambahkan salt borrowing. Untuk akun tanpa hash asli, sshd kini mengambil salt `$5$` atau `$6$` dari akun lokal lain dan tetap melakukan hashing terhadap password yang dikirim, sehingga username valid dan tidak valid memakan waktu yang sama. Juga perbaikan yang masuk akal untuk masalah nyata.

**Konvensi Unix yang sudah lama ada.** Satu karakter `*` di field password pada `/etc/shadow` menandai akun yang tidak boleh autentikasi dengan password. Akun key-only, service account, pengguna yang dipetakan dari LDAP — dan root di Alpine — umumnya membawa tanda itu.

Gabungkan semuanya. Penyerang menawarkan password sepanjang 300 byte untuk akun yang field shadow-nya berupa satu asterisk. Karena perubahan 2016, sshd tidak melakukan short-circuit: ia meminjam salt dari akun lain dan memanggil `crypt()`. Karena perubahan 2012 dan batas 256 byte, musl mengembalikan string asterisk. sshd membandingkan nilai kembalian itu dengan field yang tersimpan, menemukan dua asterisk yang identik, dan menganggap perbandingan itu sebagai autentikasi yang berhasil.

```text
password penyerang : "AAAA…" (257 sampai 1024 byte)
field shadow tersimpan : *
sshd meminjam salt  : $6$<salt dari akun lain>$
musl crypt() mengembalikan: *   <- token kegagalan, bukan hash
sshd membandingkan       : * == *  <- cocok, login diterima
```

Batas atasnya ada karena sshd membuang password yang lebih panjang dari 1024 byte, sehingga rentang yang bekerja kira-kira 257 sampai 1024. Perbaikan di 10.6p2 pun sesempit itu: sshd kini menolak hash tersimpan yang lebih pendek dari empat karakter, apa pun yang dikembalikan `crypt()`.

## Siapa yang sebenarnya terpapar

Celah ini punya prasyarat yang luar biasa ketat — kabar baik kalau kamu memeriksanya, kabar buruk kalau kamu hanya mengasumsikannya. Semua kondisi di bawah ini harus terpenuhi sekaligus.

- **sshd ter-link ke musl libc.** [[Alpine Linux]] adalah kasus yang paling umum; build OpenWrt, Buildroot, dan Yocto juga disebut dalam laporan.
- **[[PAM]] tidak digunakan.** Dengan PAM yang menangani autentikasi, sshd tidak pernah melakukan perbandingan `crypt()` yang gagal terbuka itu. Konfigurasi server OpenSSH default di Alpine tidak memakai PAM.
- **Password authentication aktif.** Ini adalah default OpenSSH, jadi kondisinya berlaku kecuali seseorang sengaja mematikannya.
- **Akun target punya asterisk tunggal di field shadow-nya.** Akun yang diincar penyerang — umumnya root atau service account.
- **Ada akun lokal lain dengan hash `$5$` atau `$6$` yang asli.** Salt harus dipinjam dari suatu tempat, jadi sistem yang tidak punya akun dengan password hash yang bisa dipakai tidak menghadirkan kondisi ini.

Sama pentingnya untuk tahu apa yang *tidak* terdampak. Sistem yang dibangun di atas glibc — Debian, Ubuntu, RHEL dan turunannya — mengembalikan null pointer atau token `*0` saat gagal, dan keduanya tidak bisa sama dengan asterisk yang tersimpan, serta sshd sudah menolak keduanya. Sistem yang memakai PAM berada di luar cakupan. Dropbear dilaporkan tidak terdampak.

## Kenapa dampaknya paling keras di container

Membaca kondisi di atas sebagai masalah server akan sangat meremehkan paparannya. Alpine adalah base image kecil yang menjadi default di hampir semua ekosistem container, dipilih justru karena ia minimal — dan minimal itulah alasan PAM tidak ada.

Tiga konsekuensi mengikutinya, dan masing-masing mematahkan asumsi yang berbeda.

Pertama, **jumlahnya lebih besar dari yang ditunjukkan inventaris server-mu.** Organisasi tanpa satu pun server Alpine tetap bisa menjalankan ribuan container Alpine. Pertanyaannya bukan berapa host yang menjalankan musl, melainkan berapa image yang menjalankannya.

Kedua, **sebagian besar container itu seharusnya tidak menjalankan sshd sama sekali** — dan banyak yang tetap menjalankannya, diwarisi dari base image atau ditambahkan untuk debugging lalu tidak pernah dihapus. Sebuah sshd di dalam container yang tidak ada yang ingat mengaktifkannya adalah paparan sekaligus temuan.

Ketiga, **perbaikan ini datang lewat rebuild, bukan lewat upgrade.** Melakukan patch pada host tidak berpengaruh apa-apa terhadap image yang dibangun sebelum 5 November. Alpine telah menerbitkan paket OpenSSH yang diperbaiki di semua branch yang didukung — 3.24 membawa `10.3_p1-r2`, 3.23 `10.2_p1-r1`, 3.22 `10.0_p1-r11`, 3.21 `9.9_p2-r1`, dan 3.16–3.20 juga sudah di-patch — jadi aksinya adalah rebuild di atas base yang sudah diperbaiki lalu redeploy, sebuah workflow yang berbeda dari upgrade paket dan lebih lambat.

Pertanyaan paparan yang praktis bagi tim platform karenanya sempit dan bisa dijawab: container mana yang sedang berjalan dan punya sshd yang listening, dan dari semua itu, mana yang berbasis musl dan bisa dijangkau dari mana pun penyerang berada. Di sebagian besar estate, jawaban jujur untuk bagian pertama tidak diketahui tanpa pengecekan.

```bash
# container dengan port SSH yang listening
kubectl get pods -A -o json | jq -r '.items[] | select(.spec.containers[].ports[]? | .containerPort == 22) | "\(.metadata.namespace)/\(.metadata.name)"'

# di host, konfirmasi libc dan apakah PAM ter-compile
ldd /usr/sbin/sshd | grep -E 'musl|libc'
sshd -T 2>/dev/null | grep -E 'usepam|passwordauthentication'
```

## Deteksi: hadiah yang diberikan bug ini kepada defender

Bug kerusakan memori sulit dideteksi karena kegagalan terlihat seperti ketidakstabilan. Yang ini justru sebaliknya, dan [[SOC]] sebaiknya memanfaatkan hadiah itu. Eksploitasi yang berhasil menghasilkan event spesifik yang tercatat di log dan tidak punya padanan yang sah: autentikasi password berhasil untuk akun yang field password-nya menyatakan ia tidak akan pernah menerima password.

Deteksinya adalah join antara event autentikasi dan state akun:

```text
rule:     ssh_password_login_to_locked_account
source:   sshd auth log
match:    "Accepted password for <user>"
where:    field shadow <user> adalah "*" atau "!" saat login
and:      libc host adalah musl
severity: critical, no tuning expected
```

Sinyal pendukung yang layak dikumpulkan bersamanya, masing-masing lebih lemah sendiri-sendiri namun berguna untuk mengonfirmasi sebuah kasus:

1. **"Accepted password for root"** di host atau container Alpine mana pun. Root di Alpine umumnya membawa field asterisk, jadi ini hampir bisa dipastikan sebagai bukti di lingkungan itu.
2. **Autentikasi pada container yang seharusnya tidak punya akses interaktif.** Login SSH yang berhasil ke container workload layak mendapat alert atas dasarnya sendiri, terlepas dari CVE ini.
3. **Request autentikasi SSH yang ukurannya tidak biasa.** Serangan ini membutuhkan password minimal 257 byte. Ukuran paket saat autentikasi bukan sesuatu yang kebanyakan tim catat, tetapi di mana telemetri jaringan memungkinkannya, ukuran request yang anomali pada tahap auth adalah indikator langsung dari upaya, bukan keberhasilan.
4. **Upaya berulang lintas akun.** Seorang operator akan mencoba root lalu service account secara berurutan dari sumber yang sama, membentuk pola spray yang biasa dan memberikan kunci korelasi yang kuat.

## Apa yang harus dilakukan, berurutan

1. **Hunt secara retrospektif sebelum apa pun.** Eksploitasi dilaporkan dalam sembilan jam setelah publikasi, jadi pertanyaannya adalah apakah itu sudah terjadi. Jalankan deteksi di atas terhadap log autentikasi yang tersimpan hingga 5 November, bukan hanya ke depan dari hari ini.
2. **Nonaktifkan password authentication di tempat yang tidak dibutuhkan.** Mengatur `PasswordAuthentication no` menghilangkan prasyarat itu sepenuhnya dan merupakan perubahan konfigurasi yang bisa dibalik, bukan rebuild. Untuk image container yang seharusnya tidak pernah menerima login interaktif, menghapus sshd sepenuhnya lebih baik lagi.
3. **Rebuild dan redeploy image berbasis Alpine** di atas paket yang sudah diperbaiki, perlakukan ini sebagai workstream yang terpisah dari patching host, dengan pelacakan penyelesaiannya sendiri.
4. **Periksa reachability, bukan mengasumsikannya.** Container rentan yang tidak bisa dijangkau penyerang adalah prioritas yang berbeda dari yang berada di belakang load balancer. Konfirmasi port SSH mana yang terekspos ke luar cluster, bukan menyimpulkannya dari niat network policy.

Satu catatan jujur soal pelaporan: observasi Previdian tentang upaya dalam sembilan jam dan root pada honeypot bersifat spesifik dan bisa dipercaya, tetapi write-up vendor lain yang diterbitkan 6 November tidak menggambarkan eksploitasi in-the-wild yang terkonfirmasi, dan saat tulisan ini dibuat celah tersebut belum tercantum di katalog [[KEV]] CISA. Kedua pernyataan itu bisa benar sekaligus — kompromi honeypot dan organisasi korban yang terkonfirmasi adalah standar bukti yang berbeda. Perlakukan seolah-olah ia sedang dieksploitasi, dan verifikasi posisi KEV saat publikasi. Skor [[EPSS]] berada di 0.98% pada 6 November, yang berarti model tidak mengharapkan eksploitasi massal — tetapi model tidak melakukan patch pada container-mu.

Kepemilikan atas cacat ini juga diperdebatkan. OpenSSH merilis perbaikan, dan maintainer musl menggambarkan masalah ini sebagai penggunaan `crypt()` yang salah oleh pemanggil, bukan cacat musl, sambil mengindikasikan perilaku error itu kemungkinan akan berubah di rilis mendatang. Perdebatan itu tidak mengubah apa yang harus kamu lakukan, dan menjadi pengingat yang berguna: cacat yang hidup di antara dua komponen yang masing-masing berperilaku benar bukan milik siapa-siapa sampai seseorang dikompromikan karenanya.

Pelajaran sshole bukan bahwa Alpine tidak aman atau musl rusak. Pelajarannya adalah batas antara "akun yang tidak akan pernah bisa login" dan "akun yang baru saja login" ternyata hanya satu karakter — `*` — dan dua proyek yang terpisah masing-masing punya alasan yang bagus untuk memperlakukan karakter itu sebagai placeholder yang tidak berbahaya. Audit asumsimu seperti kamu mengaudit paketmu: periksa apa sebenarnya locked account-mu, periksa image mana yang menjalankan sshd, dan periksa log-mu hingga 5 November. Penyerang hanya butuh satu asterisk yang sejajar.

*Sumber: rilis OpenSSH 10.6p2 (5 Nov 2026); Help Net Security via Previdian; advisory keamanan Alpine Linux; analisis hawk-eye.io; zerohunt.ai; walterstein.eu.*
