---
title: "Terinstal tapi Tak Pernah Diimpor — dan Kunci Anda Tetap Dicuri: Memburu Stealer .pth LiteLLM"
date: 2026-10-30
tags: [supply-chain, python-security, tools, incident-response]
excerpt: "Pada 21 Oktober 2026, rilis LiteLLM 1.107.0 yang diracuni menyembunyikan pencuri kredensial di dalam file startup Python — sehingga ia berjalan di setiap proses Python di host tersebut, bahkan yang tak pernah menyentuh LiteLLM. Inilah cara memeriksa apakah ia menyentuh Anda, dan cara membersihkannya dengan benar."
cover: /assets/covers/litellm-pth-stealer-audit.jpg
---

Ada asumsi menenangkan yang dibawa setiap developer Python: menginstal sebuah package itu tidak berbahaya sampai Anda mengimpornya. Anda bisa `pip install` sesuatu, mencobanya nanti, menghapusnya kalau berubah pikiran — dan tidak ada yang berjalan di antaranya. Pada 21 Oktober 2026, sebuah rilis LiteLLM yang diracuni membuktikan asumsi itu salah dengan cara terburuk.

Pagi itu, versi berbahaya dari `litellm` 1.107.0 muncul di [[PyPI]] — ketujuh wheel-nya, mencakup Linux, macOS, dan Windows — dan di image container LiteLLM di Docker Hub dan GHCR dengan tag `v1.107.0`, `latest`, `main-latest`, dan `main-stable`. Ia membawa pencuri kredensial yang tidak menunggu ada yang mengimpor LiteLLM. Ia berjalan begitu proses Python apa pun dimulai di host itu. "Kami hanya menginstalnya, tidak pernah memakainya" bukan pembelaan di sini. Kalau rilis beracun itu mendarat di environment Anda, kalimat itulah yang justru diandalkan penyerang.

## Apa yang sebenarnya terjadi

LiteLLM adalah gateway open-source populer yang memungkinkan aplikasi berbicara ke banyak penyedia model bahasa besar lewat satu antarmuka — yang berarti mesin yang menjalankannya cenderung menyimpan persis rahasia yang diinginkan penyerang: kredensial cloud dan API key penyedia AI. Komprominya bukan pada kode sumber publik LiteLLM. Advisory proyek itu sendiri mencatat bahwa git tag resmi v1.107.0 tidak mengandung file berbahaya; wheel yang diracuni dibangun dari repositori yang dikuasai penyerang. Ini adalah [[supply chain attack]] terhadap pipeline rilis, bukan commit jahat yang bisa terlihat saat code review.

Cara penyerang masuk ke pipeline itu adalah pelajarannya sendiri. Analisis atas insiden itu melaporkan bahwa sebuah master key telah terekspos di repositori publik sejak 27 Mei 2026, dan penyerang sempat mengujinya pada 10 Oktober sebelum memakainya untuk menerbitkan rilis beracun pada 21 Oktober. Sebuah rahasia yang dibiarkan di tempat publik selama hampir lima bulan, lalu dipersenjatai dalam satu pagi. Jendela paparan di [[PyPI]] sendiri singkat — wheel diunggah antara pukul 11:39 dan 11:40 UTC dan PyPI menghapus rilis itu pada 13:23 UTC, kurang dari dua jam kemudian — tetapi dua jam adalah waktu yang sangat lama bagi installer otomatis. Pipeline CI, build Docker, dan bot dependensi tidak tidur, dan tag container yang mengambang membawa image berbahaya lebih lama, antara pukul 11:46 dan 14:20 UTC.

Dan ini adalah kedua kalinya bagi LiteLLM. Pada Maret 2026, kelompok yang dilacak sebagai TeamPCP mengompromikan `litellm` 1.82.7 dan 1.82.8 memakai token [[PyPI]] yang dicuri lewat Trivy, dengan teknik `.pth` yang serupa. Aktor berbeda, titik lemah yang sama: pipeline rilis adalah bagian dari attack surface, dan ia terus membuktikannya.

## Triknya: file startup, bukan import

Mekanismenyalah yang membuat insiden ini layak dipelajari, karena ia berlaku jauh melampaui LiteLLM. Wheel yang diracuni menaruh tiga file ke `site-packages`: `cook.pth`, `cook.py`, dan `sitecustomize.py`. File pertama adalah kuncinya.

Python memproses setiap file `.pth` di `site-packages` saat interpreter dimulai, dan baris apa pun yang diawali `import` akan dieksekusi. Itu fitur yang terdokumentasi, dimaksudkan untuk menambahkan direktori ke jalur pencarian modul — tetapi itu berarti file `.pth` adalah primitif eksekusi kode yang menyala sebelum kode Anda, sebelum aplikasi Anda, sebelum apa pun yang Anda tulis. `cook.pth` mengimpor `cook.py`, sehingga stealer berjalan di dalam setiap proses Python di host itu: aplikasi Anda, test suite Anda, language server IDE Anda, job CI Anda, bahkan `pip` itu sendiri.

Detail terakhir itu penting untuk incident response, dan merupakan jebakan pertama dalam kisah ini: menjalankan `pip show litellm` di environment yang dicurigai untuk memeriksa versi justru akan memicu stealer sekali lagi. Pada mesin yang Anda curigai, periksa file-nya dari shell dulu, tanpa memulai Python sama sekali.

Apa yang dicuri `cook.py` terbaca seperti inventaris semua yang dimiliki host engineering modern: kredensial cloud untuk AWS, GCP, dan Azure, API key penyedia AI, kunci SSH dan GPG, rahasia CI/CD, kata sandi browser, variabel environment proses, dan — bila `DATABASE_URL` proxy LiteLLM disetel — baris dari tabel kredensial proxy, termasuk provider key yang tersimpan di sana. Hasil curian dienkripsi dan dikirim ke `www.litellm.dev`, domain tiruan yang tidak terkait dengan `litellm.ai` yang resmi. Perlakukan setiap rahasia yang bisa dibaca oleh host yang terdampak sebagai sudah terekspos, bukan hanya yang terbukti diambil.

Payload kedua, `sitecustomize.py`, adalah lapisan persistensinya: ia memulai daemon latar yang, setiap jam, membaca alamat server dari file yang dihosting di GitHub, menjalankan ulang stealer, dan mengunduh serta mengeksekusi kode lanjutan. Akun GitHub di baliknya mengembalikan 404 pada pukul 13:40 UTC, kira-kira dua jam setelah rilis, sehingga loader itu cepat kehilangan server perintahnya — tetapi host apa pun yang menjalankan daemon itu sebelum titik tersebut bisa saja menerima kode tahap kedua yang alamatnya tak lagi bisa dipulihkan peneliti.

## Auditnya: lima pemeriksaan, sesuai urutan

Kalau Anda menjalankan Python di mana pun — dan terutama kalau Anda menjalankan LiteLLM, gateway AI, atau container apa pun yang dibangun dari tag yang mengambang — kerjakan ini sesuai urutan. Lakukan pemeriksaan file sebelum Anda menjalankan tool Python apa pun di environment yang dicurigai.

**1. Periksa rilis beracun di lockfile dan cache Anda.** Cari `litellm==1.107.0` di lockfile dependensi, log build, dan cache. Versi yang bersih adalah 1.106.2 dan release candidate 1.107.0 (1.107.0rc1 dan 1.107.0rc2). Lockfile yang mengunci 1.107.0, atau entri cache untuknya, berarti environment itu menarik rilis yang buruk — bahkan bila rilis itu kemudian dihapus dari [[PyPI]].

**2. Cari file implan di disk.** Dari shell, bukan lewat Python:

```bash
find / \( -name 'litellm-1.107.0.dist-info' -o -name 'cook.pth' \
  -o -name 'cook.py' -o -name 'sitecustomize.py' \) 2>/dev/null
ls -la /tmp/.pc_once_* /tmp/remote_code_loader.lock 2>/dev/null
```

Menemukan `cook.pth` atau direktori `litellm-1.107.0.dist-info` berarti rilis buruk itu pernah terinstal. Perlu dicatat bahwa `sitecustomize.py` bisa jadi sah di beberapa build Python, jadi perlakukan ia sebagai mencurigakan terutama bila ia berada di samping `cook.pth`.

**3. Periksa file marker — dan pahami apa yang tidak dibuktikannya.** Stealer menulis `/tmp/.pc_once_72129118c59f5636c0bb` hanya setelah data curian terkirim, jadi menemukannya memastikan eksfiltrasi pernah terjadi. Tidak menemukannya tidak membuktikan apa-apa: restart container atau pembersihan `/tmp` menghapusnya, dan pencurian itu mungkin tetap terjadi.

**4. Periksa image container berdasarkan digest, bukan tag.** Tag berpindah; digest tidak. Bandingkan image yang benar-benar Anda jalankan:

```bash
docker images --digests | grep -i -E 'berriai|litellm'
```

Di Kubernetes, periksa image ID di status container setiap pod — itulah digest yang benar-benar berjalan, dan hanya itulah yang penting. Image apa pun yang ditarik saat tag mengambang menyajikan build beracun harus diperlakukan sebagai terkompromi.

**5. Periksa egress dan log cloud.** Cari koneksi keluar ke `litellm.dev` di sekitar jendela instalasi, dan aktivitas cloud — misalnya panggilan `GetCallerIdentity` dari role yang ada di host terdampak — yang datang dari luar jaringan Anda. Bila sebuah role bisa dipakai dari host itu, anggap saja role itu sudah dipakai.

## Pembersihannya: uninstall saja tidak cukup

Ini jebakan kedua dalam kisah ini, dan jebakan yang paling mungkin menelan kebanyakan tim. Menghapus instalasi `litellm` 1.107.0 tidak menghilangkan implan, karena `cook.pth`, `cook.py`, dan `sitecustomize.py` berada di root `site-packages`, di luar direktori package — mereka bertahan setelah package dihapus, dan loader yang sedang berjalan terus berjalan. Pembersihan yang benar punya empat langkah:

1. **Hapus file implan dengan tangan** dari setiap environment yang terdampak, dan matikan proses loader yang sedang berjalan.
2. **Bangun ulang, jangan ditambal.** Bangun ulang image container dari base yang bersih lalu deploy ulang; jangan mencoba membersihkan container yang sedang berjalan secara bedah lalu menyebutnya tepercaya.
3. **Rotasi semua yang bisa dibaca host itu.** Role cloud, setiap provider key di database proxy, master key dan virtual key, kata sandi `DATABASE_URL`, dan setiap rahasia di environment proses apa pun. Rotasi adalah remediasinya — penghapusan file hanyalah kebersihan.
4. **Kunci dan verifikasi ke depannya.** Kunci `litellm` ke versi bersih berdasarkan hash, kunci image container berdasarkan digest alih-alih tag yang mengambang, dan wajibkan instalasi terverifikasi hash (`pip install --require-hashes`) untuk build produksi. Tag yang mengambang adalah instruksi untuk menerima apa pun yang disajikan penerbit berikutnya — dan pada 21 Oktober, itu adalah malware.

## Pelajaran yang bertahan lebih lama dari insiden ini

Lepaskan detail LiteLLM-nya dan bentuk serangannya terasa tidak nyaman karena begitu umum. Pipeline rilis sebuah proyek open-source tepercaya dikompromikan lewat rahasia yang sudah lama terekspos. Payload memakai fitur interpreter yang sah, bukan kerentanan, sehingga tidak ada scanner yang menandai CVE yang diketahui akan menangkapnya. Ia berjalan tanpa import, sehingga "kami tidak pernah memakainya" tidak berarti apa-apa. Ia bertahan di luar direktori package, sehingga uninstall tidak berarti apa-apa. Dan ia menargetkan persis kelas host — gateway AI — yang memusatkan kredensial paling berharga di satu tempat.

Itulah mengapa audit di atas layak dijalankan bahkan bila Anda cukup yakin tidak terdampak. Pemeriksaannya murah: grep lockfile, pencarian filesystem, perbandingan digest. Dan ia melatih kebiasaan yang penting melampaui minggu ini: perlakukan dependency tree dan tag container Anda sebagai keputusan trust yang hidup, bukan sebagai plumbing latar. Setiap instalasi adalah tindakan kecil percaya pada pipeline rilis orang lain. Pada 21 Oktober, kepercayaan itu disalahgunakan selama kurang dari dua jam — dan itu sudah cukup.

Periksa environment Anda. Rotasi yang perlu dirotasi. Dan lain kali seseorang berkata sebuah package aman karena tidak pernah diimpor, Anda sudah tahu yang sebenarnya.

---

*Sumber: [Compromised LiteLLM 1.107.0 on PyPI Installs a Credential Stealer and Backdoor (SafeDep, 21 Oktober 2026)](https://safedep.io/litellm-pypi-compromise-credential-stealer-backdoor/); [LiteLLM Supply Chain Attack: IOCs and Runbook (Kodem)](https://www.kodemsecurity.com/resources/litellm-supply-chain-attack-litellm-1-107-0-affected-versions-iocs-and-first-hour-response-runbook); [LiteLLM 1.107.0 Backdoored: How the .pth Key Stealer Worked (PlayCISO)](https://playciso.com/blog/litellm-1-107-0-supply-chain-compromise-credential-stealer); [LiteLLM 1.107.0 Compromised: Check, Clean Up, Rotate Keys (Tecyfy)](https://tecyfy.com/blog/litellm-compromised-check-and-clean); [Black October: How a Week of Cybersecurity Failures Exposed the Limits of Traditional Patching (29 Oktober 2026)](https://beatsinbrief.com/2026/10/29/black-october-2026-ai-patch-window-php2shell/).*
