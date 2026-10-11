---
title: "Berburu Cryptominer Siluman: Lab Praktis dari Kampanye XMRig AhsayCBS"
date: 2026-10-11
tags: [blue-team, threat-hunting, cryptojacking, hands-on]
excerpt: "Penyerang merangkai dua zero-day AhsayCBS, menanam miner XMRig yang menyamar sebagai Microsoft Edge, lalu menyebar script berbantuan AI yang langsung mematikan Task Manager begitu dibuka. Berikut cara memburu setiap tahap kampanye itu di jaringan Anda sendiri."
cover: /assets/covers/hunting-ahsaycbs-xmrig-campaign.jpg
---

Bayangkan ini: CPU sebuah server terpaku di angka 90 persen sepanjang hari, tagihan listrik diam-diam naik — dan setiap kali seseorang membuka Task Manager untuk menyelidiki, lonjakannya lenyap. Task Manager-nya sendiri ikut tertutup. Buka lagi, tertutup lagi. Pelakunya bukan hardware berhantu. Ia adalah cryptominer yang mengawasi Anda balik mengawasinya.

Itu bukan skenario hipotetis. Pada 7 Oktober 2026, penyerang mulai mengeksploitasi dua celah di AhsayCBS — platform manajemen backup yang dipakai MSP dan integrator sistem — dan mengubah server backup yang diretas menjadi tambang [[Monero]]. Payload-nya, yang oleh peneliti Huntress disebut kampanye "edge.exe", membawa empat lapis teknik pengelakan yang seperti checklist lengkap trik-trik siluman ala [[cryptojacking]]. Mari kita bongkar satu per satu, dan ubah setiap trik menjadi sesuatu yang bisa Anda buru.

## Ringkasan kampanye 30 detik

Dua kerentanan tersebut tercatat sebagai [[CVE]]-2026-105133 (cacat autentikasi di fungsi `checkSysPwd()`, skor 5,5) dan [[CVE]]-2026-105134 (bug injeksi perintah OS di komponen Replication Receiver, skor 9,3). Dirangkai, keduanya memungkinkan penyerang jarak jauh tanpa autentikasi mengeksekusi perintah dengan hak SYSTEM. Nomor CVE-nya baru dipublikasikan pada 4 Oktober 2026 — dan upaya eksploitasi pertama tercatat pukul 11:20 malam UTC tanggal 7 Oktober. Setidaknya lima organisasi terdampak dalam sehari.

Ada kejutan yang menjadikan ini kisah [[zero-day]]: NVD menyatakan celah ini sudah diperbaiki di AhsayCBS 10.3.4, tetapi Huntress mengonfirmasi versi terbaru pun masih rentan. Saat tulisan ini dibuat, belum ada patch yang benar-benar menutup celah — anggap semua versi sebagai terpapar.

Setelah masuk, menurut Huntress, penyerang melakukan reconnaissance, menanam [[webshell]] Java Server Pages, lalu mengunduh payload dari object storage Alibaba Cloud. File-file itu mendarat di `%TEMP%` atau `AppData/Local/Temp`, dijalankan sebagai child process dari biner service AhsayCBS `cbssvcX64.exe`: `edge.exe`, `msedge.exe`, `config.json`, dan sebuah script PowerShell bernama `Taskgmr.ps1`. Pohon proses itu — service backup yang tiba-tiba melahirkan biner asing dari folder Temp — adalah hal pertama yang akan kita buru.

## Trik 1: penyamaran nama

Miner XMRig — penambang [[Monero]] open-source yang sah tapi sering disalahgunakan kriminal — datang dengan nama `edge.exe`, menyamar sebagai Microsoft Edge. Bagi analis yang sekilas melirik daftar proses, proses bernama Edge hampir tak menimbulkan kecurigaan. Ini adalah teknik [[MITRE ATT&CK]] T1036.004, "masquerade task or service," dan sepupunya T1036.005, "match legitimate resource name."

Nama bisa berbohong. Path dan signature tidak. Biner Edge asli tinggal di `C:\Program Files (x86)\Microsoft\Edge\Application` dan ditandatangani Microsoft. Salinan milik penyerang berjalan dari folder Temp tanpa signature yang valid. Cara berburu:

```powershell
# Temukan semua "edge.exe" yang berjalan dari lokasi mencurigakan
Get-CimInstance Win32_Process -Filter "Name = 'edge.exe'" |
  Select-Object Name, ProcessId, ExecutablePath, CommandLine

# Verifikasi signature digital — biner tak bertanda atau salah penanda langsung menonjol
Get-ChildItem C:\Users\*\AppData\Local\Temp\*.exe -ErrorAction SilentlyContinue |
  Get-AuthenticodeSignature | Where-Object { $_.Status -ne 'Valid' }
```

Di [[SIEM]], deteksi padanannya sederhana: buat alert untuk setiap proses yang namanya menyerupai aplikasi terkenal tetapi image path-nya berada di direktori Temp atau status signature-nya bukan Microsoft. Huntress merilis empat rule [[Sigma]] yang mencakup persis pola ini, termasuk biner bernama Edge yang membawa flag daemon khas XMRig.

## Trik 2: persistence yang meniru updater asli

Sekadar membunuh miner tidak cukup — Anda harus membunuh mekanisme [[persistence]]-nya. Penyerang memasang Windows service bernama `MicrosoftEdgeUpdateSvc`, yang disengaja mirip dengan service update Edge yang asli (`edgeupdate`). Service itu menjalankan `msedge.exe`, yang menurut Huntress adalah salinan [[NSSM]] (Non-Sucking Service Manager) yang dimodifikasi — utilitas open-source yang sah untuk menjalankan program apa pun sebagai Windows service dan me-restart-nya setelah crash atau reboot.

Jadi rantainya: pembungkus NSSM (hak SYSTEM) → me-restart `edge.exe` selamanya. Hapus service-nya, miner mati. Biarkan, dan ia bangkit di setiap boot. Cara berburu:

```powershell
# Daftar service dengan ketidakcocokan nama tampilan vs path biner
Get-Service | Where-Object { $_.Name -like '*Edge*' -or $_.Name -like '*Update*' } |
  ForEach-Object { Get-CimInstance Win32_Service -Filter "Name = '$($_.Name)'" } |
  Select-Object Name, DisplayName, PathName, StartMode

# Tandai service yang binernya tinggal di Temp atau folder yang bisa ditulis user
Get-CimInstance Win32_Service |
  Where-Object { $_.PathName -match '(?i)(temp|appdata)' } |
  Select-Object Name, DisplayName, PathName
```

Bandingkan juga daftar service dengan baseline yang sudah diketahui baik. `MicrosoftEdgeUpdateSvc` palsu berbeda dari updater Edge asli dalam nama, path biner (Temp, bukan `Program Files`), dan metadata publisher. Di satu fleet, satu saja ketidakcocokan itu sudah layak jadi temuan.

## Trik 3: script yang mengawasi balik

Ini adalah jurus khas kampanye ini. `Taskgmr.ps1` — diambil lewat `curl` — memantau Windows Task Manager dan bertindak begitu ada analis yang penasaran: jika Task Manager dibuka, script menghentikan service mining agar lonjakan CPU hilang, lalu menjalankannya lagi saat Task Manager ditutup. Lebih parah: script mematikan paksa Task Manager setiap pukul 18:00 waktu lokal, dan lagi jika Task Manager dibiarkan terbuka lebih dari satu jam di malam hari. Huntress menduga script ini dibantu AI, dilihat dari gaya kodenya yang penuh komentar — pertanda yang meresahkan tentang arah tooling penyerang komoditas.

Perburuannya punya dua sisi. Pertama, temukan jejak script: event eksekusi PowerShell yang memantau proses atau memanggil `Stop-Service`/`Stop-Process` terhadap `taskmgr`:

```powershell
# Cari di PowerShell script-block logging (Event ID 4104) untuk manipulasi Task Manager
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational'; Id=4104} |
  Where-Object { $_.Message -match '(?i)(taskmgr|Stop-Service|Stop-Process)' } |
  Select-Object TimeCreated, @{n='Snippet';e={$_.Message.Substring(0,120)}}
```

Kedua, periksa mekanisme persistence yang menjaga script tetap hidup — scheduled task atau registry Run key yang menunjuk ke `Taskgmr.ps1` atau script bernama aneh lainnya. Dan ingat pelajaran meta-nya: ketika Task Manager di sebuah mesin terus menutup sendiri, jangan anggap itu glitch. Itu adalah salah satu indikator paling andal — dan terlihat oleh user — bahwa ada [[malware]] anti-analisis di mesin itu.

## Trik 4: jalan pintas via kernel driver

Dalam setidaknya satu intrusi, penyerang memakai `certutil.exe` — utilitas sertifikat bawaan Windows, [[LOLBin]] klasik — untuk mengunduh `WinRing0x64.sys` ke folder Temp. Ini adalah kernel driver yang sah tetapi rentan. Penyerang rutin menyalahgunakan driver semacam itu untuk melumpuhkan tool keamanan endpoint atau, dalam kasus ini, mendapatkan akses hardware level rendah demi memeras lebih banyak hash dari CPU.

Unduhan apa pun via `certutil` layak dicurigai, tetapi file `.sys` yang mendarat di Temp via `certutil.exe` lalu di-load adalah temuan lima alarm:

```powershell
# certutil mengunduh executable atau driver = segera selidiki
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688} |
  Where-Object { $_.Message -match '(?i)certutil.*(urlcache|download)' -and $_.Message -match '(?i)\.(exe|sys|dll)' } |
  Select-Object TimeCreated, @{n='Detail';e={$_.Message.Substring(0,150)}}
```

Audit juga driver store untuk driver tak bertanda atau nonstandar dengan `sigverif` atau `driverquery /si`, dan pertimbangkan memblokir driver rentan yang sudah dikenal dengan vulnerable-driver blocklist dari Microsoft.

## Checklist berburu lengkap

Jika Anda menjalankan AhsayCBS — atau sekadar ingin latihan praktis — kerjakan daftar ini berurutan. Anggap sebagai lab: setiap langkah memetakan ke satu trik pengelakan di atas.

1. **Batasi eksposur**: apakah web interface manajemen AhsayCBS bisa dijangkau dari internet? Saran inti Huntress: batasi ke IP tepercaya atau wajibkan VPN, segera. Ingat 10.3.4 pun rentan — ini [[zero-day]] tanpa patch lengkap.
2. **Child process**: buru child process tak terduga dari `cbssvcX64.exe` atau `cbssvcX86.exe` di EDR atau log Sysmon (pembuatan proses, Event ID 1/4688).
3. **Penyamaran nama**: temukan biner mirip Edge/Chrome yang berjalan dari Temp, tak bertanda atau signature-nya janggal.
4. **Service palsu**: bandingkan daftar service dengan baseline; tandai yang binernya berada di path yang bisa ditulis user.
5. **Script anti-analisis**: cari referensi `taskmgr` di log PowerShell 4104; audit scheduled task dan Run key.
6. **Unduhan LOLBin**: cari `certutil` atau `curl` yang menarik executable, dan file `.sys` yang mendarat di Temp.
7. **Jaringan**: awasi koneksi keluar ke mining pool Monero — kampanye ini memakai `xmr.kryptex.network:8029` dan `51.195.127.124:8029`.
8. **Asumsikan kedalaman breach**: jika menemukan sesuatu, Huntress menyarankan re-image host dari backup tepercaya. Webshell dan backdoor mungkin bersembunyi di samping miner.

## Penutup: miner adalah masalah terkecil

Ini bagian yang kadang luput dari defender. Cryptojacking terasa seperti gangguan — listrik dicuri, server lambat. Tapi kampanye ini berawal dari webshell di server backup. Server backup menyimpan kunci segalanya: kredensial, repositori, sistem penyimpanan untuk setiap pelanggan yang dilindungi MSP. Miner yang berisik dengan CPU 90 persen justru, ironisnya, adalah penyusup yang lantang. Yang sunyi — webshell, sesi yang dicuri, data backup yang disalin diam-diam — adalah payload sesungguhnya. Buru miner-nya, tapi tambal juga asumsi bahwa mining adalah satu-satunya yang mereka lakukan.

Sumber: blog Huntress (primer, termasuk rule Sigma dan IoC yang dirilis), The Hacker News (9 Okt 2026), BleepingComputer (9 Okt 2026), Threadlinqs TL-2026-3109.
