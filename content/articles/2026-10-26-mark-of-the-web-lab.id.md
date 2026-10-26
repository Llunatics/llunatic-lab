---
title: "Stiker Tak Kasat Mata yang Menjaga Windows: Lab Hands-On Mark of the Web"
date: 2026-10-26
tags: [hands-on, windows-security, mark-of-the-web, phishing]
excerpt: "CVE-2026-96951, yang sudah dieksploitasi di lapangan, menghapus tanda tak kasat mata yang ditempel Windows pada file unduhan internet — dan bersamanya, SmartScreen, Protected View, dan pemblokir macro ikut diam. Lab ini menunjukkan cara melihat tanda itu, menguji apa yang dikendalikannya, dan memburu file yang kehilangan tanda tersebut."
cover: /assets/covers/mark-of-the-web-lab.jpg
---

Bayangkan mengunduh sebuah file lalu mengklik dua kali — dan Windows tidak berkata apa-apa. Tanpa peringatan, tanpa banner kuning, tanpa peringatan "file ini berasal dari internet". File itu langsung terbuka, seolah-olah kamu sendiri yang membuatnya lima menit lalu. Keheningan itulah yang dibeli penyerang lewat [[CVE]]-2026-96951.

Microsoft menambal celah ini dalam Patch Tuesday 13 Oktober 2026, memberinya skor CVSS 8.8 dan mengonfirmasi bahwa celah ini sudah dieksploitasi di lapangan. CISA memasukkannya ke katalog [[KEV]] pada hari yang sama, dengan tenggat perbaikan untuk instansi federal pada 16 Oktober. Celah ini adalah bug command-injection di Windows Shell yang menembus [[Mark of the Web]] — tanda yang ditempel Windows pada file yang diunduh dari internet. Ini adalah celah bypass MotW ketiga di Windows Shell yang dieksploitasi di lapangan hanya pada 2026, setelah CVE-2026-21510 pada Februari dan CVE-2026-32202 pada April. Penyerang terus menghantam komponen yang sama persis ini karena ia adalah sakelar utama: satu bypass diam-diam mematikan beberapa pertahanan sekaligus.

Artikel ini bukan panduan exploit. Ini adalah lab yang bisa kamu jalankan di mesin virtual Windows yang terisolasi, memakai file tidak berbahaya yang kamu buat sendiri, supaya kamu bisa melihat mekanismenya dengan mata kepala sendiri — dan belajar cara mempertahankannya.

## Tanda yang tak pernah kamu lihat

Ketika browser atau klien email menyimpan file dari internet, Windows menulis sedikit metadata di samping file itu memakai [[alternate data stream]] — aliran data tersembunyi yang menempel pada file di volume [[NTFS]], tak terlihat di File Explorer. Aliran itu bernama [[Zone.Identifier]], dan untuk unduhan dari internet isinya biasanya seperti ini:

```text
[ZoneTransfer]
ZoneId=3
```

ZoneId=3 berarti "zona internet." Hanya itu isi tandanya: beberapa byte, tanpa konten, tanpa kode. Dan inilah perbedaan penting yang sering terlewat — tanda itu sendiri tidak melindungi apa-apa. Ia hanya label. Pertahanan yang sesungguhnya adalah kontrol-kontrol yang *membaca* label itu:

- **[[SmartScreen]]** memeriksa executable yang diunduh terhadap data reputasinya dan memberi peringatan sebelum menjalankan file yang tak dikenal.
- **Office Protected View** membuka dokumen dari internet dalam mode hanya-baca, di balik banner kuning "Enable Editing".
- **Pemblokir macro internet** menghentikan macro di file Office yang ditandai berasal dari internet.
- **Smart App Control** di Windows 11 memblokir aplikasi yang tak tepercaya.
- **Attachment Manager** menampilkan prompt "apakah kamu ingin membuka file ini?".

Anggap MotW sebagai stiker pada paket yang diperiksa setiap penjaga di gedung itu. CVE-2026-96951 mengantarkan paket tanpa stiker — sehingga semua penjaga meloloskannya begitu saja. Penyerang tetap butuh kamu membuka file itu; Microsoft menegaskan tidak ada yang bisa memaksamu melihat konten yang dikendalikan penyerang. Tapi [[phishing]] ada justru karena selalu ada yang mengklik dua kali, dan bug ini menghilangkan peringatan yang seharusnya menyambut klik tersebut.

## Persiapan lab: lima menit, nol risiko

Jalankan semua langkah di bawah ini di VM Windows tanpa data penting, terpisah dari dokumen aslimu — snapshot yang bisa di-rollback adalah pilihan ideal. Kamu hanya memakai file yang kamu buat sendiri: tanpa malware unduhan, tanpa kode exploit, tanpa payload serangan sungguhan. Yang kamu butuhkan hanyalah PowerShell dan satu dokumen Office kosong atau file teks yang kamu buat di VM.

## Latihan 1: Melihat tandanya

Unduh file kecil apa pun di browser VM — manual PDF, gambar, apa saja yang tidak berbahaya — lalu periksa di PowerShell:

```powershell
Get-Item .\Downloads\example.pdf -Stream *
Get-Content .\Downloads\example.pdf -Stream Zone.Identifier
```

Perintah pertama menampilkan semua stream yang menempel pada file, termasuk `:$DATA` (file itu sendiri) dan `Zone.Identifier`. Perintah kedua mencetak isi tandanya: `[ZoneTransfer]` dan `ZoneId=3`. Sekarang buat file lokal di folder yang sama — klik kanan, New, Text Document — dan jalankan perintah yang sama pada file itu. Tidak ada stream `Zone.Identifier` yang muncul. Perbedaan itu, yang tak terlihat di File Explorer, adalah dasar seluruh pertahanan unduhan Windows.

Sekarang salin file unduhan itu ke flashdisk atau volume non-NTFS lain, lalu salin kembali. Periksa stream-nya lagi: tandanya hilang, karena alternate data stream hanya ada di NTFS. Itulah keterbatasan jujur pertama MotW — ia adalah label yang bisa lepas dalam perjalanan, dan ketiadaannya tidak membuktikan apa-apa soal keamanan sebuah file.

## Latihan 2: Menyaksikan tanda mengubah perilaku file

Buat dokumen Word kosong di VM, lalu beri ia tanda internet sendiri:

```powershell
Copy-Item .\lab.docx .\lab-internet.docx
Set-Content -Path .\lab-internet.docx -Stream Zone.Identifier -Value "[ZoneTransfer]`nZoneId=3"
```

Buka kedua file itu. Salinan lokal terbuka normal. Salinan bertanda terbuka di Protected View, hanya-baca, di balik banner kuning — padahal isi kedua file identik. Kamu baru saja mereproduksi, dengan dokumen tidak berbahaya, mekanisme persis yang ditembus zero-day Oktober itu: kontennya sama, tapi tandanya yang menentukan pertahanan mana yang aktif.

Sekarang hapus tanda itu dengan cara yang sah:

```powershell
Unblock-File -Path .\lab-internet.docx
Get-Item .\lab-internet.docx -Stream *
```

Stream `Zone.Identifier` hilang, dan file terbuka normal lagi. Inilah cara yang benar untuk membuka blokir file yang benar-benar kamu percayai — per file, secara sadar, lewat Properties atau `Unblock-File`. Yang tidak boleh kamu lakukan adalah membuka blokir seluruh folder Downloads sekaligus "supaya peringatannya berhenti." Setiap unblock adalah keputusan untuk mempercayai sebuah file; skrip yang membuat keputusan itu untuk ratusan file sekaligus sedang mengerjakan tugas penyerang untuk mereka.

## Latihan 3: Memburu file yang kehilangan tandanya

Penyerang tidak selalu butuh zero-day. Sebagian kanal unduhan tidak pernah menempelkan MotW, dan sebagian metode arsip dan transfer menghapusnya. Maka kebiasaan defensif yang berguna adalah memburu file executable dan skrip di lokasi unduhan pengguna yang *tidak* membawa tanda sama sekali — file yang mungkin diperlakukan pertahananmu sebagai file lokal. Di PowerShell, dari folder Downloads:

```powershell
Get-ChildItem -File -Recurse |
  Where-Object { $_.Extension -match '\.(exe|msi|ps1|bat|scr|js)$' } |
  ForEach-Object {
    $streams = Get-Item $_.FullName -Stream * -ErrorAction SilentlyContinue
    if (-not ($streams.Stream -contains 'Zone.Identifier')) {
      $_.FullName
    }
  }
```

Apa pun yang muncul dalam daftar ini layak diperiksa kedua kalinya: dari mana asalnya, siapa yang menaruhnya di sana, dan apakah kehadirannya memang diharapkan? Di mesin yang bersih, daftarnya seharusnya pendek. Di mesin tempat sesuatu tiba lewat kanal yang tidak menempelkan tanda, daftar ini adalah peringatan dini. Perhatikan catatan jujur dari Latihan 1: tanda yang hilang saja bukan bukti kejahatan — file yang kamu buat sendiri secara sah memang tidak memilikinya. Perburuan ini adalah daftar triase, bukan vonis.

## Latihan 4: Daftar periksa pertahanan

Tutup lab dengan kontrol yang benar-benar penting, urut berdasarkan prioritas:

1. **Pasang patch.** Update Oktober 2026 menutup CVE-2026-96951. Jika kamu mengelola mesin Windows, celah ini mengalahkan label "Important" CVSS 8.8-nya: status eksploitasi mengalahkan skor keparahan dalam triase, setiap saat.
2. **Biarkan pemblokir macro dan Protected View aktif.** Inilah kontrol yang diberi makan oleh MotW. Menonaktifkannya "supaya tidak ribet" justru menghilangkan pertahanan yang memang dirancang untuk dibungkam oleh bypass MotW.
3. **Biarkan SmartScreen dan Smart App Control aktif.** Mereka adalah peringatan terakhir yang didapat pengguna sebelum executable tak dikenal berjalan.
4. **Ajarkan aturan satu klik.** Bug ini butuh pengguna membuka file rekayasa yang dikirim lewat email atau pesan. Pertahanan yang tidak pernah kedaluwarsa adalah pengguna yang berhenti sejenak pada lampiran tak terduga — terutama yang datang bersama rasa urgensi.
5. **Perlakukan "tanpa peringatan" sebagai sinyal, bukan kenyamanan.** Jika file yang seharusnya berasal dari internet terbuka tanpa banner dan tanpa prompt, tanyakan dulu alasannya sebelum kamu mempercayainya. Ketiadaan peringatan adalah persis apa yang dihasilkan oleh celah sekelas ini.

## Mengapa penyerang terus kembali ke stiker ini

Tiga bypass MotW yang dieksploitasi dalam satu tahun bukanlah kebetulan. MotW adalah satu titik kegagalan sejak dari desainnya: satu tanda, dibaca banyak kontrol, tanpa opini kedua. Saat ia bekerja, ia elegan — beberapa byte yang mengoordinasikan seluruh postur pertahanan. Saat ia gagal, ia gagal di semua tempat sekaligus, secara diam-diam. Karena itulah patch Oktober penting, dan karena itulah lab ini lebih penting lagi: begitu kamu pernah melihat tandanya, menyaksikan ia mengubah perilaku dokumen, dan memburu file yang tidak memilikinya, kamu tidak akan pernah lagi mengira klik dua kali yang hening sebagai klik yang aman.

Stikernya tak terlihat. Pertahanan yang dipicunya tidak. Belajarlah memeriksa keduanya.

---

*Sumber: [Liputan Microsoft October 2026 Patch Tuesday (SecurityWeek, Oktober 2026)](https://www.securityweek.com/microsoft-patches-record-1413-vulnerabilities-including-exploited-windows-zero-day/amp/); [Analisis October 2026 Patch Tuesday (Tenable, Oktober 2026)](https://www.tenable.com/blog/microsofts-october-2026-patch-tuesday-addresses-1407-cves-cve-2026-96951); [Patch Tuesday Oktober 2026: analisis CVE (Automox, Oktober 2026)](https://www.automox.com/blog/patch-fix-tuesday-october-2026); [Mark of the Web dari sudut pandang red team (Outflank, 2020)](https://www.outflank.nl/blog/2020/03/30/mark-of-the-web-from-a-red-teams-perspective/?ref=0idea.dev).*
