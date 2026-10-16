---
title: "Bedah Email Phishing Seperti Analis: Lab Hands-On dari Gelombang Undangan Kalender Palsu"
date: 2026-10-16
tags: [phishing, blue-team, hands-on, email-security]
excerpt: "Undangan meeting palsu baru saja menjadi salah satu gelombang phishing terbesar tahun 2026 — lebih dari 740.000 email hanya dalam dua minggu pertama Oktober, menurut Check Point. Di lab hands-on ini kamu akan membedah undangan mencurigakan dengan Python stdlib: header, hasil verifikasi SPF/DKIM/DMARC, URL tersembunyi, dan lampiran .ics yang berbahaya."
cover: /assets/covers/phishing-email-autopsy-lab.jpg
---

Tahukah kamu pesan apa yang paling dipercaya di inbox? Bukan email dari bank. Melainkan undangan kalender. Ia datang tanpa kecurigaan, dilirik sekilas sambil lalu, dan — klik — kamu sudah mendarat di halaman "login". Para penyerang sudah lama menyadari ini, dan bulan ini mereka mengindustrikan trik tersebut.

Peneliti email Check Point [melaporkan](https://blog.checkpoint.com/securing-user-and-access/fake-calendar-invites-target-thousands-of-organizations-in-microsoft-credential-phishing-campaign/) bahwa undangan kalender palsu melonjak mulai 25 September 2026. Lapisan deteksi baru mereka menandai **lebih dari 302.386 email phishing unik yang dikirim ke 40.000+ organisasi**, rata-rata 8.319 email per hari aktif, dari 33.890 domain pengirim dan 247.270 alamat pengirim unik. Kurva pertumbuhannya yang menakutkan: beberapa ribu email per bulan di bulan April, 118.000 di bulan September, dan **lebih dari 740.000 hanya dalam dua minggu pertama Oktober**. Hari tersibuk — 8 Oktober — mencatat hampir 200.000 email. Kampanye ini masih aktif pada 15 Oktober, sehari sebelum artikel ini ditulis.

Ada dua varian yang beredar. Yang pertama datang sebagai **lampiran [[ICS]]**: file kalender yang sepenuhnya valid — tanpa exploit, tanpa kerentanan, hanya data event yang menyalahgunakan kepercayaan klien email terhadap format kalender. Yang kedua adalah undangan Microsoft Teams palsu, di mana mengarahkan kursor ke tombol "Join" memperlihatkan tujuan sebenarnya: halaman panen kredensial yang didandani menyerupai halaman login Microsoft.

Hari ini kamu berhenti sekadar membaca tentang phishing dan mulai membedahnya. Di bawah ini adalah lab autopsi ala analis sungguhan yang hanya memakai standard library Python. Siapkan file `.eml` yang mencurigakan (ekspor dari klien email dengan "Save as"), lalu kita bedah.

## Langkah 0: aturan dasar

Jangan lakukan ini di laptop kerja dengan lampiran dibuka di klien yang otomatis me-render HTML. Simpan pesan sebagai `.eml`, pindah ke mesin atau VM yang terisolasi, dan **jangan klik apa pun**. Lab kita membaca byte mentah — tanpa rendering, tanpa fetching, tanpa risiko.

## Langkah 1: sebenarnya ini dari siapa?

Header `From:` adalah kebohongan yang boleh ditulis siapa saja. Itu cuma teks tampilan — siapa pun bisa mengetik "Microsoft Teams" di sana. Yang benar-benar penting adalah header routing: `Return-Path`, `Reply-To`, dan rantai header `Received:` yang mencatat setiap server yang dilewati pesan tersebut.

```python
import email
from email import policy

with open("suspicious-invite.eml", "rb") as fh:
    msg = email.message_from_binary_file(fh, policy=policy.default)

print("== Identity headers ==")
for h in ("From", "Reply-To", "Return-Path", "Date"):
    print(f"{h:12} {msg[h]}")

print("\n== Received chain (oldest first) ==")
for h in reversed(msg.get_all("Received", [])):
    print(" *", h.replace("\n", " ")[:110])
```

**Yang perlu diperhatikan:** `From:` tertulis `Microsoft Teams <no-reply@teams.microsoft.com>`, tapi `Return-Path` menunjuk ke domain sekali pakai, dan hop `Received:` pertama menunjukkan server yang sama sekali bukan infrastruktur email Microsoft. Dalam gelombang undangan kalender ini, Check Point mengamati pengirim berputar lewat **33.890 domain berbeda** — infrastrukturnya memang sengaja sekali pakai, karena defender memblokir domain dengan cepat.

## Langkah 2: tiga hasil verifikasi otentikasi

Email modern punya tiga pendeteksi kebohongan bawaan, dan server email kamu mencap hasil pemeriksaannya ke dalam header bernama `Authentication-Results`:

- **[[SPF]]** — apakah server ini berizin mengirim email atas nama domain yang diklaim?
- **[[DKIM]]** — apakah pesan ditandatangani secara kriptografis oleh domain tersebut, dan apakah isinya sampai tanpa diubah?
- **[[DMARC]]** — ketika dua pemeriksaan di atas gagal, kebijakan apa yang dipublikasikan pemilik domain: tetap kirim (`none`), karantina, atau tolak?

```python
auth = msg["Authentication-Results"]
if auth:
    import re
    for verdict in re.split(r";\s*", str(auth)):
        if verdict.strip():
            print(" *", verdict.strip()[:90])
else:
    print("(tidak ada — sama sekali tanpa hasil SPF/DKIM/DMARC. Anggap mencurigakan.)")
```

Contoh keluaran khas untuk phish:

```
 * spf=fail (sender IP is 185.220.xx.xx) smtp.mailfrom=invites-calendar-365.com
 * dkim=none (no signature)
 * dmarc=fail (p=quarantine) header.from=teams.microsoft.com
```

Baris terakhir adalah tembakan mematikannya: `header.from` mengklaim `teams.microsoft.com`, tapi [[DMARC]] gagal karena pengirim aslinya `invites-calendar-365.com` — domain yang didaftarkan minggu lalu. Perhatikan trik phisher: domain amplop *lolos* SPF-nya sendiri, jadi pemeriksaan malas "SPF-nya lolos kan?" tidak cukup. **Alignment** — domain di From harus cocok dengan domain yang terautentikasi — itulah yang penting.

## Langkah 3: URL yang pakaiannya tidak cocok

Sekarang bagian body. Phishing hidup di celah antara apa yang *ditampilkan* sebuah tautan dan ke mana ia *pergi*:

```python
import re

URL_RE = re.compile(r"https?://[^\s<>\"']+")
LINK_RE = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)

for part in msg.walk():
    ctype = part.get_content_type()
    if ctype not in ("text/plain", "text/html"):
        continue
    body = part.get_content()
    for url in dict.fromkeys(URL_RE.findall(body)):
        print("  URL:", url[:100])
    if ctype == "text/html":
        for href, shown in LINK_RE.findall(body):
            shown_text = re.sub(r"<[^>]+>", "", shown).strip()
            if shown_text and shown_text != href.strip():
                print(f"  TIDAK COCOK  display={shown_text[:60]!r} -> href={href[:90]}")
```

Pada varian undangan Teams, di sinilah jebakan terbuka: teks anchor menampilkan `teams.microsoft.com/l/meetup-join/...` sementara `href`-nya menunjuk ke domain mirip-mirip yang menghosting halaman login palsu. Mengarahkan kursor mengungkapkannya di screenshot Check Point — tapi sebagian besar korban tidak pernah mengarahkan kursor. Waspadai juga domain `xn--` (punycode), di mana `microsоft.com` menyembunyikan huruf "о" dari alfabet Cyrillic.

## Langkah 4: buka file .ics — payload sebenarnya

Untuk varian lampiran, konten berbahayanya berada di dalam file kalender. File [[ICS]] adalah teks polos — tidak perlu rendering, cukup dibaca:

```python
for part in msg.iter_attachments():
    name = part.get_filename() or "(unnamed)"
    print(f" * {name} ({part.get_content_type()})")
    if name.lower().endswith(".ics"):
        payload = part.get_content()
        text = payload.decode("utf-8", "replace") if isinstance(payload, bytes) else payload
        for line in text.splitlines():
            if line.startswith(("DESCRIPTION", "LOCATION", "URL", "ATTACH", "SUMMARY")):
                print("   ", line[:120])
```

Contoh nyata dari gelombang ini bentuknya kurang-lebih seperti ini (contoh sintetis, bentuknya sama):

```
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Action Required: Verify Your Teams Account
DESCRIPTION:Your account will be suspended.\nVerify now: https://login-microsoft365-secure.com/verify
LOCATION:Microsoft Teams Meeting
END:VEVENT
END:VCALENDAR
```

Data kalender yang valid. Tanpa exploit. Tanpa signature malware. Hanya format tepercaya yang membawa tautan tak tepercaya — dan tepat karena itulah Check Point mencatat kampanye ini **menyalahgunakan fitur kalender dan kepercayaan pengguna, bukan kerentanan perangkat lunak**. Pertahanan berbasis signature melihat tipe file yang sah; bahayanya sepenuhnya bersifat semantik.

## Langkah 5: buat vonisnya, seperti analis

Analis blue-team menilai pesan berdasarkan skor, bukan firasat. Berikut tabel keputusan yang dihasilkan lab ini:

| Sinyal | Undangan sah | Phish gelombang ini |
|---|---|---|
| `From` vs `Return-Path` | domain sama | tidak cocok |
| [[SPF]]/[[DKIM]] | lolos, selaras | gagal atau tidak ada |
| Kebijakan [[DMARC]] | lolos | gagal |
| Rantai `Received` | infra email dikenal | VPS/relay sekali pakai |
| Tampilan tautan vs `href` | identik | tidak cocok |
| Isi `.ics` | detail meeting | URL login/verifikasi |

Dua atau lebih bendera merah: perlakukan sebagai [[phishing]] terkonfirmasi, simpan file `.eml`-nya, dan laporkan — jangan cuma dihapus. Aturan deteksi tim keamananmu hanya bisa belajar dari sampel yang mereka terima.

## Eskalasi yang tidak nyaman: sesi yang dicuri, bukan sekadar password

Ada satu alasan lagi kenapa lab ini lebih penting dari sebelumnya. Laporan Proofpoint 1 Oktober 2026 tentang kampanye **TA419** mendokumentasikan kit [[AitM]] (adversary-in-the-middle) berbasis Evilginx: alih-alih meniru halaman login Microsoft, kit ini meneruskan browser korban ke login Microsoft 365 yang *asli* lalu mencegat kredensial **beserta token sesinya** — dengan otomasi yang memilih "Keep me signed in" dan mengirimkan kode OTP secara otomatis. [[MFA]] berbasis kode tidak menghentikan itu. Hanya otentikasi anti-phishing — security key FIDO2 atau passkey, yang mengikat login secara kriptografis ke domain aslinya — yang memutus proxy tersebut.

Gelombang undangan kalender memanen password hari ini. Kit AitM memanen sesinya langsung. Pertahananmu harus berasumsi kredensial *akan* bocor dan membuat sesinya tidak bisa dicuri.

## Yang harus dilakukan Senin pagi

1. **Laporkan, jangan cuma hapus.** Gunakan tombol lapor-phishing di klien email atau teruskan ke SOC. Setiap sampel melatih filter.
2. **Jadikan "arahkan kursor sebelum klik" sebagai refleks** — dan untuk undangan kalender, lebih ketat lagi: undangan dari luar organisasi yang berisi tautan login atau "verifikasi" layak dilaporkan, bukan diklik.
3. **Terapkan [[DMARC]] di domainmu sendiri** dengan `p=quarantine`, lalu `p=reject`. Kalau domainmu tidak bisa dipalsukan, brand-mu tidak bisa membintangi phish orang lain.
4. **Minta mail gateway menandai lampiran `.ics` eksternal yang mengandung URL** di `DESCRIPTION` atau `LOCATION`. Aturan murah yang langsung menyasar teknik gelombang ini.
5. **Pindahkan akun bernilai tinggi ke [[MFA]] anti-phishing** (FIDO2/passkey). Laporan TA419 adalah buktinya bahwa kode saja tidak lagi cukup.
6. **Verifikasi lewat kanal lain.** Undangan "mendesak" apa pun yang meminta kredensial dapat kanal kedua: kirim pesan ke pengirim yang diklaim di Teams atau Slack sebelum menyentuh tautannya.

## Penutup

Hal terpintar dari gelombang undangan kalender palsu adalah betapa sedikit kepintaran yang dibutuhkannya. Tanpa zero-day. Tanpa exploit. Hanya format file yang dipercaya klien emailmu sejak era 1990-an dan sebuah refleks manusia — *undangan meeting, pasti penting* — yang melewati semua poster security awareness yang pernah dicetak.

Itu juga alasan kenapa autopsi ini penting. Phishing tidak dilawan dengan mata yang lebih tajam; ia dilawan dengan header, hasil verifikasi otentikasi, dan pemeriksaan tautan — bukti yang bisa dicek skrip dalam hitungan milidetik sementara perhatianmu masih memutuskan apakah meeting-nya nyata. Simpan lab ini. Jalankan pada undangan mencurigakan berikutnya. Para penyerang mengandalkan kamu untuk tidak melakukannya.
