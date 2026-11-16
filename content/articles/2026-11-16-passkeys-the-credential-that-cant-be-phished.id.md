---
title: "Passkey: Kredensial yang Tak Bisa Di-phishing — dan Kenapa November 2026 Jadi Titik Baliknya"
date: 2026-11-16
tags: [concept, passkeys, authentication, phishing]
excerpt: "Password adalah rahasia bersama, jadi ia bisa di-phishing, ditebak, dan bocor. Passkey menggantinya dengan private key yang tak pernah meninggalkan perangkatmu — dan pada November 2026, Microsoft menjadikannya langkah pertama saat sign-in, bukan lagi opsi tambahan."
cover: /assets/covers/passkeys-the-credential-that-cant-be-phished.jpg
---

Setiap kampanye [[phishing]] yang pernah kamu lihat mengeksploitasi kelemahan struktural yang sama: password adalah rahasia yang diketahui oleh kamu dan server. Apa pun yang diketahui dua pihak bisa ditipu keluar dari salah satunya. Halaman login palsu yang meyakinkan memintanya, kamu mengetiknya, dan penyerang kini ikut mengetahuinya. Kode [[MFA]] memang membantu, tapi [[phishing]] [[AitM]] meneruskan browser kamu ke situs asli dan merelay kodenya secara real time — kode itu memang tidak pernah dirancang untuk membuktikan *situs mana* yang sedang kamu ajak bicara.

[[Passkey]] memperbaiki kelemahannya, bukan menambalnya dari luar. Ia mengganti rahasia bersama dengan sepasang kunci, dan separuh privatnya tak pernah meninggalkan perangkatmu. Tidak ada yang bisa diketik ke halaman palsu, tidak ada yang bisa dipakai ulang di situs lain, dan tidak ada yang bisa bocor dari database yang dibobol. Idenya bukan hal baru — standarnya sudah bertahun-tahun — tapi November 2026 adalah bulan ketika penyedia identitas terbesar di dunia berhenti memperlakukan passkey sebagai upgrade opsional dan menjadikannya pintu depan default. Inilah cara kerjanya, kenapa phishing tak bisa mencurinya, dan apa yang masih kurang sebelum kamu bisa menghapus password.

## Apa sebenarnya passkey itu

Passkey adalah kredensial login yang dibangun di atas [[FIDO2]], standar terbuka dari [[FIDO Alliance]]: [[WebAuthn]], API web yang diimplementasikan browser, dan CTAP, protokol untuk berbicara dengan [[authenticator]] seperti ponselmu, pembaca sidik jari laptop, atau security key perangkat keras. FIDO Alliance memperkenalkan nama "passkey" pada 2022 untuk menyatukan standar-standar ini menjadi satu konsep yang ramah pengguna.

Ide intinya adalah [[public-key cryptography]], teknologi yang sama di balik sertifikat TLS. Saat kamu membuat passkey untuk sebuah situs, perangkatmu menghasilkan sepasang kunci unik yang terikat pada domain situs itu. Private key tetap terkunci di perangkat — idealnya di dalam [[secure element]] atau trusted execution environment — dan hanya dilepas setelah kamu membukanya dengan wajah, sidik jari, atau PIN. Situs hanya menerima public key, yang tak berguna tanpa separuh privatnya. Pembobolan database di pihak vendor hanya menyerahkan tumpukan public key yang tak bisa dipakai untuk login sebagai kamu.

Inilah juga alasan kenapa passkey dihitung sebagai [[MFA]] dalam satu langkah. Ia menggabungkan sesuatu yang kamu miliki (perangkat yang menyimpan private key) dengan sesuatu yang melekat padamu atau kamu ketahui (biometrik atau PIN). Microsoft menggolongkan passkey sebagai phishing-resistant dan mengizinkannya memenuhi MFA sendirian — tanpa faktor kedua, tanpa kode SMS, tanpa ketukan di aplikasi authenticator.

## Dua upacara: registrasi dan sign-in

WebAuthn punya dua alur, dan keduanya berbasis challenge-response. Memahami keduanya berarti memahami kenapa seluruh sistem ini kokoh.

**Registrasi** — membuat passkey — berjalan seperti ini: situs ([[relying party]]) menghasilkan [[challenge-response]] acak dan mengirimkannya ke browsermu. Browser memanggil WebAuthn API, yang memintamu memverifikasi diri dengan biometrik atau PIN. Authenticator menghasilkan sepasang kunci baru yang terikat pada domain situs, menandatangani challenge dengan private key, dan mengembalikan public key ke situs. Situs menyimpan public key itu untuk akunmu. Private key tak pernah melintasi jaringan pada titik mana pun.

**Autentikasi** — sign-in — adalah tarian yang sama, tanpa pembuatan kunci. Situs mengeluarkan challenge baru yang sekali pakai. Browser memintamu memverifikasi dengan biometrik atau PIN, authenticator menandatangani challenge dengan private key yang tersimpan, dan situs memverifikasi tanda tangan itu dengan public key yang ia simpan. Challenge yang sekali pakai membunuh serangan replay: tanda tangan yang disadap tak ada nilainya lima menit kemudian.

Kriptografi di bawahnya sengaja membosankan dan standar: ES256, tanda tangan ECDSA pada kurva eliptik P-256 dengan hashing SHA-256, kira-kira 128 bit keamanan. Tidak ada yang eksotis, tidak ada yang proprietary — dan justru itulah intinya. Kriptografi yang membosankan dan terstandarisasi adalah yang lolos audit.

## Kenapa phishing gagal — secara struktural, bukan soal kehati-hatian

Ketahanan passkey terhadap phishing bukan soal berhati-hati. Orang yang hati-hati pun masih bisa tertipu oleh halaman login palsu yang sempurna. Passkey, secara desain, tidak punya apa pun yang berguna untuk diserahkan ke halaman itu.

Mekanismenya adalah pengikatan [[origin]]. Sebuah passkey terikat secara kriptografis pada satu domain — ID [[relying party]] yang dicatat saat registrasi. Saat kamu mencoba sign-in, browser memeriksa bahwa halaman yang kamu buka cocok dengan domain itu sebelum authenticator mau menandatangani apa pun. Di domain tiruan, tidak ada kredensial yang cocok, jadi tidak terjadi apa-apa. Halaman palsu boleh meminta sepuasnya; private key tidak akan menjawab orang asing.

Satu sifat ini membunuh tiga kelas serangan sekaligus:

- **[[Phishing]] dan relay [[AitM]].** Tidak ada password untuk diketik dan tidak ada kode untuk direlay. Kredensial hanya bekerja untuk domain asli, jadi proxy ke situs asli tidak bisa meminjamnya — pemeriksaan origin terjadi di browser, sebelum tanda tangan apa pun dibuat.
- **[[credential stuffing]].** Setiap passkey unik untuk satu layanan, jadi kredensial yang bocor dari satu pembobolan tidak bisa dicoba ke akunmu yang lain. Tidak ada password yang dipakai ulang untuk di-stuff.
- **Pembobolan server.** Layanan hanya menyimpan public key. Dump database lengkap tidak mengekspos apa pun yang bisa di-replay menjadi login.

Inilah kenapa angkanya lebih penting daripada teorinya. Phishing bukan masalah yang mengecil: CERT Hong Kong mencatat 4.404 insiden keamanan pada kuartal ketiga 2026, dan phishing mencakup 2.672 di antaranya — sekitar 61%. Melatih orang untuk mengenali halaman palsu adalah perlombaan senjata yang kalah melawan penyerang yang kini membuat umpan meyakinkan dalam skala besar. Menghapus hal yang bisa di-phishing adalah satu-satunya langkah yang mengakhiri permainan.

## November 2026: bulan ketika default berubah

Passkey sudah ada bertahun-tahun, tapi sampai baru-baru ini ia terkubur tiga menu jauhnya. Pada 2026 ia menjadi default. Google menjadikan passkey opsi sign-in default untuk akun personal sejak 2023. Microsoft menjadikan passkey default untuk akun konsumen baru pada Mei 2025, dan sepanjang 2026 ia terus memindahkan pengguna dari kode SMS.

Lalu datanglah dorongan enterprise. Pada 1 September 2026, Microsoft mulai menggulirkan passkey sebagai metode autentikasi default di Entra ID, mengaktifkannya otomatis untuk pengguna yang memakai SMS atau voice dari Microsoft. Pada 6 November 2026, ia melangkah lebih jauh: registrasi passkey atau passwordless sebagai metode [[MFA]] *pertama* mencapai general availability (pesan Message Center MC1450133), menghapus syarat lama untuk mendaftarkan metode yang lebih lemah dulu sebelum bisa passwordless. Rollout berjalan dua fase hingga akhir Februari 2027. Konsekuensi praktisnya blak-blakan — karyawan baru kini bisa langsung mendaftarkan passkey, tanpa jalan memutar lewat SMS yang bisa dibajak penyerang saat onboarding. Microsoft juga sudah mengumumkan akan mempensiunkan autentikasi SMS dan voice dari Microsoft pada 1 Februari 2027 untuk sebagian besar pengguna, dan 1 Juli 2027 untuk Global Administrator dan pengguna eksternal.

Angka adopsi kini mendukung perubahan itu. Passkey Index 2026 dari FIDO Alliance, terbit Oktober 2026, menemukan sign-in passkey berhasil 93% dari waktu, berbanding 78% untuk [[MFA]] tradisional, dan passkey mencakup 36% dari sign-in yang berhasil di layanan-layanan peserta — naik dari 26% pada 2025. Laporan State of Passkeys dari FIDO Alliance memperkirakan sekitar 5 miliar passkey kini digunakan, dengan kesadaran konsumen 90% dan kira-kira tiga dari empat orang telah mengaktifkan passkey di setidaknya satu akun. Laporan Passkey Power 20 dari Dashlane, terbit saat Cybersecurity Awareness Month, menemukan 57% penggunanya kini menyimpan setidaknya satu passkey, naik dari 40% setahun sebelumnya, dan autentikasi passkey bulanan di antara penggunanya hampir berlipat ganda menjadi 2,5 juta. Passkey muncul di 28% login Google yang diukur, 23% di GitHub, dan 21% di HubSpot.

Bahkan badan standar sudah menyusul: NIST SP 800-63-4, terbit Juli 2025, mengklasifikasikan authenticator yang tersinkronisasi pada Authenticator Assurance Level 2 — pengakuan formal bahwa passkey yang tersinkronisasi adalah kredensial serius, bukan mainan kenyamanan.

## Synced vs. device-bound: kenali mana yang kamu punya

Tidak semua passkey sama, dan perbedaannya penting untuk threat model kamu.

**[[synced passkey]]** disimpan di credential manager — iCloud Keychain, Google Password Manager, 1Password, Bitwarden — dan disalin ke perangkatmu yang lain lewat sinkronisasi terenkripsi end-to-end. Ia selamat dari ponsel yang hilang, dan itulah kenapa kebanyakan orang akan memakainya. Komprominya adalah kredensial itu kini berada di mana pun penyedia sinkronisasi bisa menjangkaunya, jadi keamanan passkey kamu adalah keamanan akun penyedia itu. Lindungi akun sinkronisasi dengan autentikasi yang kuat, dan perlakukan ia sebagai mahkota yang memang ia adalah.

**[[device-bound passkey]]** hidup di satu perangkat keras — security key, atau authenticator platform yang tak pernah mengekspor kunci. Ia tak bisa disalin keluar dari perangkat, yang menjadikannya opsi terkuat dan pilihan tepat untuk akun admin, identitas code-signing, dan apa pun yang kehilangan perangkatnya masih bisa diterima tapi kehilangan kredensialnya tidak. Biayanya jelas: kalau perangkatnya hilang, passkey ikut hilang, jadi kamu butuh kredensial kedua yang terdaftar sebagai cadangan.

Tidak ada tipe yang "salah." Kesalahannya adalah tidak tahu mana yang kamu punya, dan tidak punya rencana pemulihan untuk keduanya.

## Peringatan yang jujur

Passkey adalah sign-in terkuat yang tersedia bagi kebanyakan orang hari ini, tapi ia bukan penghapus ajaib, dan tiga celah pantas disebut dengan jujur.

**Pertama, kamu belum bisa sepenuhnya tanpa password.** Banyak aplikasi perbankan, layanan pemerintah, dan tools kecil yang masih belum mendukung passkey. Direktori komunitas di passkeys.directory menyimpan daftar terbaru layanan mana yang sudah mendukung. Bersiaplah hidup hibrida — passkey di mana ditawarkan, password plus hardware key di tempat lain — setidaknya satu atau dua tahun lagi.

**Kedua, penyerang berpindah ke fallback.** Passkey tidak bisa diketik ke situs palsu, jadi penyerang beralih ke pemulihan akun, metode fallback, dan manusia. Kalau akunmu masih menawarkan "reset lewat kode SMS" sebagai fallback, kode SMS itu kini menjadi tautan terlemah dalam rantai — dan penyerang mengetahuinya. Saat kamu mengaktifkan passkey, audit opsi pemulihan di akun yang sama dan hapus yang lemah.

**Ketiga, portabilitas masih matang.** Memindahkan passkey antar penyedia dulu berarti mendaftar ulang di mana-mana secara manual. Credential Exchange Protocol (CXP) dari FIDO adalah standar yang memperbaikinya, dengan dukungan platform yang meluas sepanjang 2026, tapi belum universal. Sebelum kamu menitipkan seratus akun ke satu penyedia sinkronisasi, periksa apakah ia bisa mengekspor.

Tak satu pun peringatan ini melemahkan klaim intinya. Mereka hanya menentukan batasnya.

## Apa yang harus dilakukan minggu ini

Untuk individu: buka pengaturan keamanan email, password manager, dan akun cloud kamu, lalu buat passkey di masing-masing. Mulai dari akun yang bisa mereset semua akun lain — biasanya emailmu. Daftarkan passkey kedua di perangkat lain atau hardware key, supaya ponsel yang hilang menjadi ketidaknyamanan, bukan lockout. Lalu, di setiap akun, periksa opsi pemulihan dan hapus fallback SMS yang sudah tidak kamu butuhkan.

Untuk tim: perubahan Entra pada November 2026 adalah templatenya. Jadikan passkey metode MFA pertama yang didaftarkan pengguna baru, bukan upgrade yang nanti-nanti. Wajibkan autentikasi phishing-resistant untuk peran admin dan privileged dulu — di sanalah phishing AitM paling menguntungkan — dan tetapkan tanggal untuk mempensiunkan sign-in berbasis SMS, seperti yang sudah dilakukan Microsoft. Dan tuliskan prosedur pemulihan sebelum ada yang membutuhkannya: rollout passkey tanpa jalur pemulihan akun yang teruji adalah lockout yang menunggu ponsel hilang.

## Perpisahan panjang password

Password bertahan enam puluh tahun karena setiap penggantinya lebih lemah, lebih sulit dipakai, atau keduanya. Passkey adalah pengganti pertama yang lebih kuat *dan* lebih mudah: sidik jari alih-alih rahasia yang dihafal, tanda tangan alih-alih rahasia bersama. Titik baliknya tidak pernah berupa algoritma yang lebih baik — kriptografinya sudah tua. Titik baliknya adalah default yang berbalik: Google pada 2023, Microsoft untuk konsumen pada 2025, dan kini Microsoft Entra untuk enterprise pada November 2026, dengan pensiun SMS yang sudah masuk kalender.

Password tidak akan mati dalam satu pengumuman. Ia akan memudar seperti ia datang — satu default demi satu default, satu akun demi satu akun. Pertanyaannya bukan apakah akunmu akan menawarkan passkey. Pertanyaannya adalah apakah kamu sudah membuatnya sebelum email phishing berikutnya tiba.

---

*Sumber: [Passkeys for Small Business: Move Your Team Off Passwords (ExactReads, November 2026)](https://exactreads.com/passkeys-for-small-business/); [Passwordless Authentication: A 2026 Guide to Passkeys (Medium, November 2026)](https://medium.com/@auravenisolutions/passwordless-authentication-a-2026-guide-to-passkeys-111296bf64dd); [Phishing-Resistant MFA in Entra: 13 Steps [2026] (Tech Insider, November 2026)](https://tech-insider.org/phishing-resistant-mfa-entra-passkey-first-13-steps-2026/); [Entra lets passkeys be the first MFA method, GA rollout begins (Kira AI, November 2026)](https://kira-ai.de/blog/entra-lets-passkeys-be-the-first-mfa-method-ga-rollout-begins/); [MC1450133 — Microsoft Entra: Users can register a passkey or passwordless sign-in as their first multifactor authentication method (Microsoft 365 Message Center Archive)](https://message.cengizyilmaz.net/message/mc1450133-microsoft-entra-users-can-register-a-passkey-or-passwordless-signin-as-their-first-multifactor-authentication-method); [What Is a Passkey? 2026 Guide for HK Businesses (UD, November 2026)](https://www.ud.hk/en-US/resources/security/what-is-passkey-2026-11-10); [Passkeys Are Quietly Ending the Password (NewsXphere, November 2026)](https://www.newsxphere.com/tech/passkeys-are-replacing-passwords/); [Passkeys: A WebAuthn Implementation Guide (Veduis, 2026)](https://veduis.com/blog/passkeys-passwordless-authentication-webauthn/); [What really stops the move to passkeys in Microsoft 365, and what changes by July 2027 (Griffin31, November 2026)](https://www.griffin31.com/blog/passkeys-microsoft-365-what-stops-the-move/).*
