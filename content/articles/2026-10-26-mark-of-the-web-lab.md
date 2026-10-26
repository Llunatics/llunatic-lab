---
title: "The Invisible Sticker That Guards Windows: A Hands-On Mark of the Web Lab"
date: 2026-10-26
tags: [hands-on, windows-security, mark-of-the-web, phishing]
excerpt: "CVE-2026-96951, exploited in the wild, strips the invisible tag Windows puts on internet downloads — and with it, SmartScreen, Protected View, and the macro block all go quiet. This lab shows you how to see that tag, test what it controls, and hunt files that lost it."
cover: /assets/covers/mark-of-the-web-lab.jpg
---

Imagine downloading a file and double-clicking it — and Windows says nothing. No warning, no yellow banner, no "this file came from the internet" caution. It just opens, as if you had created it yourself five minutes ago. That silence is exactly what attackers bought with [[CVE]]-2026-96951.

Microsoft patched the flaw in its October 13, 2026 Patch Tuesday release, rating it CVSS 8.8 and confirming it was already exploited in the wild. CISA added it to its [[KEV]] catalog the same day, with federal agencies told to remediate by October 16. The flaw is a command-injection bug in Windows Shell that defeats [[Mark of the Web]] — the tag Windows stamps on files downloaded from the internet. It is the third Windows Shell MotW-bypass flaw exploited in the wild in 2026 alone, after CVE-2026-21510 in February and CVE-2026-32202 in April. Attackers keep hammering this exact component because it is a master switch: one bypass quietly disables several defenses at once.

This article is not a walkthrough of the exploit. It is a lab you can run on an isolated Windows virtual machine with harmless files you create yourself, so you can see the mechanism with your own eyes — and learn to defend it.

## The tag you never see

When a browser or mail client saves a file from the internet, Windows writes a tiny piece of metadata alongside it using an [[alternate data stream]] — a hidden stream of data attached to the file on an [[NTFS]] volume, invisible in File Explorer. The stream is called [[Zone.Identifier]], and for an internet download it typically reads:

```text
[ZoneTransfer]
ZoneId=3
```

ZoneId=3 means "internet zone." That is the whole tag: a few bytes, no content, no code. And here is the crucial distinction most people miss — the tag itself protects nothing. It is only a label. The protections are the controls that *read* the label:

- **[[SmartScreen]]** checks downloaded executables against its reputation data and warns before running unknown ones.
- **Office Protected View** opens internet documents read-only, behind the yellow "Enable Editing" banner.
- **The internet macro block** stops macros in Office files flagged as coming from the internet.
- **Smart App Control** on Windows 11 blocks untrusted apps.
- **The Attachment Manager** shows the "do you want to open this file?" prompt.

Think of MotW as the sticker on a package that every guard in the building checks. CVE-2026-96951 delivers the package with no sticker attached — so every guard waves it through. The attacker still needs you to open the file; Microsoft is explicit that no one can force you to view attacker-controlled content. But phishing exists precisely because somebody always double-clicks, and this bug removes the warning that was supposed to greet that click.

## Lab setup: five minutes, zero risk

Run everything below in a Windows VM with no important data, disconnected from your real documents — a snapshot you can roll back is ideal. You will use only files you create yourself: no downloaded malware, no exploit code, no real attack payload. All you need is PowerShell and a blank Office document or text file you make in the VM.

## Exercise 1: See the tag

Download any small file in the VM's browser — a PDF manual, an image, anything benign — then inspect it in PowerShell:

```powershell
Get-Item .\Downloads\example.pdf -Stream *
Get-Content .\Downloads\example.pdf -Stream Zone.Identifier
```

The first command lists every stream attached to the file, including `:$DATA` (the file itself) and `Zone.Identifier`. The second prints the tag's contents: `[ZoneTransfer]` and `ZoneId=3`. Now create a file locally in the same folder — right-click, New, Text Document — and run the same commands on it. No `Zone.Identifier` stream appears. That difference, invisible in File Explorer, is the entire basis of Windows' download defenses.

Now copy the downloaded file to a USB stick or another non-NTFS volume and copy it back. Check the streams again: the tag is gone, because alternate data streams only exist on NTFS. That is MotW's first honest limitation — it is a label that can fall off in transit, and its absence proves nothing about a file's safety.

## Exercise 2: Watch the tag change behavior

Create a blank Word document in the VM, then give it an internet tag yourself:

```powershell
Copy-Item .\lab.docx .\lab-internet.docx
Set-Content -Path .\lab-internet.docx -Stream Zone.Identifier -Value "[ZoneTransfer]`nZoneId=3"
```

Open both files. The local copy opens normally. The tagged copy opens in Protected View, read-only, behind the yellow banner — even though the two files have identical content. You have just reproduced, with a harmless document, the exact mechanism the October zero-day defeats: content is identical, but the tag decides which defenses engage.

Now remove the tag the legitimate way:

```powershell
Unblock-File -Path .\lab-internet.docx
Get-Item .\lab-internet.docx -Stream *
```

The `Zone.Identifier` stream is gone, and the file opens normally again. This is also the correct way to unblock a file you genuinely trust — per file, deliberately, through Properties or `Unblock-File`. What you must never do is bulk-unblock a whole Downloads folder "to stop the warnings." Each unblock is a decision to trust a file; a script that makes that decision for hundreds of files at once is doing an attacker's job for them.

## Exercise 3: Hunt for files that lost their tag

Attackers do not always need a zero-day. Some download channels never stamp MotW at all, and some archives and transfer methods strip it. So a useful defensive habit is hunting for executable and script files in user download locations that carry *no* tag at all — files your defenses may treat as local. In PowerShell, from a Downloads folder:

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

Anything this lists deserves a second look: where did it come from, who put it there, and was it expected? On a clean machine the list should be short. On a machine where something arrived through an unstamping channel, it is your early warning. Note the honest caveat from Exercise 1: a missing tag alone is not proof of malice — files you created locally legitimately have none. The hunt is a triage list, not a verdict.

## Exercise 4: The defense checklist

Close the lab with the controls that actually matter, in priority order:

1. **Patch.** The October 2026 update closes CVE-2026-96951. If you manage Windows machines, this one outranks its CVSS 8.8 "Important" label: exploitation status beats severity scores in triage, every time.
2. **Keep the macro block and Protected View on.** These are the controls MotW feeds. Disabling them to "reduce friction" removes the very defenses a MotW bypass is designed to silence.
3. **Keep SmartScreen and Smart App Control on.** They are the last warnings a user gets before an unknown executable runs.
4. **Teach the one-click rule.** The bug needs a user to open a crafted file delivered by email or message. The defense that never patches out of date is a user who pauses on unexpected attachments — especially ones that arrive with urgency attached.
5. **Treat "no warning" as a signal, not a comfort.** If a file that should have come from the internet opens with no banner and no prompt, ask why before you trust it. The absence of a warning is exactly what this class of bug produces.

## Why attackers keep coming back to this sticker

Three exploited MotW bypasses in one year is not coincidence. MotW is a single point of failure by design: one tag, read by many controls, with no second opinion. When it works, it is elegant — a few bytes that coordinate an entire defensive posture. When it fails, it fails everywhere at once, silently. That is why the October patch matters, and why the lab matters more: once you have seen the tag, watched it change a document's behavior, and hunted for files that lack it, you will never again mistake a quiet double-click for a safe one.

The sticker is invisible. The defenses it triggers are not. Learn to check both.

---

*Sources: [Microsoft October 2026 Patch Tuesday coverage (SecurityWeek, October 2026)](https://www.securityweek.com/microsoft-patches-record-1413-vulnerabilities-including-exploited-windows-zero-day/amp/); [October 2026 Patch Tuesday analysis (Tenable, October 2026)](https://www.tenable.com/blog/microsofts-october-2026-patch-tuesday-addresses-1407-cves-cve-2026-96951); [Patch Tuesday October 2026: CVE analysis (Automox, October 2026)](https://www.automox.com/blog/patch-fix-tuesday-october-2026); [Mark of the Web from a red team's perspective (Outflank, 2020)](https://www.outflank.nl/blog/2020/03/30/mark-of-the-web-from-a-red-teams-perspective/?ref=0idea.dev).*
