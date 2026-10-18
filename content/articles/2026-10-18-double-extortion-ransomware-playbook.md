---
title: "Double Extortion: How Modern Ransomware Really Works"
date: 2026-10-18
tags: [ransomware, extortion, blue-team, incident-response]
excerpt: "Modern ransomware doesn't care about your backups — attackers steal your data first, then encrypt it, then squeeze you from three directions at once. Here's the full playbook, from initial access to the leak site, grounded in the October 2026 Semperis report and this month's real cases."
cover: /assets/covers/double-extortion-ransomware-playbook.jpg
---

If your disaster recovery plan says "we have backups, so ransomware isn't our problem," you are fighting last decade's war. Today's ransomware crews don't need your backups to fail — they just need something you can't restore from a snapshot: your customers' secrets, your internal emails, your private keys. Encryption is the loud part. The quiet part — the part that actually makes victims pay — happened days earlier, in the dark.

Let's walk the full playbook, stage by stage, the way incident responders see it.

## Stage 1: getting in (initial access)

Every ransomware story starts with a door nobody was watching. The favorites haven't changed much: phishing emails with a weaponized attachment, stolen credentials bought from an [[initial access]] broker, an unpatched edge device facing the internet — a VPN concentrator, a firewall, a file-transfer server. In several of October 2026's campaigns, the entry point was a software build pipeline: steal a developer's secret once, and the whole network opens up like a gift box.

The uncomfortable truth is that the break-in is rarely the impressive part. The impressive part is how long the attackers then sit there, unnoticed.

## Stage 2: spreading inside (lateral movement and persistence)

Once inside, the crew doesn't encrypt anything yet. That would be loud, and loud gets caught. Instead they do two quiet things:

- **[[persistence]]** — planting footholds that survive reboots: scheduled tasks, rogue service accounts, webshells on internet-facing apps, golden tickets minted from a compromised domain controller.
- **[[lateral movement]]** — hopping from workstation to workstation, harvesting credentials, until they reach the crown jewels: the identity infrastructure itself.

This is why Semperis's [2026 Ransomware Risk Report](https://www.prnewswire.com/news-releases/semperis-2026-ransomware-report-reveals-increases-in-ai-driven-attacks-and-a-rise-in-physical-threats-against-executives-and-their-families-302907731.html), published October 14, 2026, hits so hard: **87% of ransomware attacks targeted identity systems** like [[Active Directory]], Entra ID, and Okta. Own the identity system and you own every door in the building. Yet only about half of surveyed companies keep dedicated identity backups, and 40% of disaster recovery plans don't even include procedures for recovering Active Directory. As Semperis CEO Mickey Bresman put it, once backups made encryption survivable, attackers simply added a second pressure point — "double extortion."

## Stage 3: the quiet theft (exfiltration)

Before a single file is encrypted, the data walks out the door. Attackers stage your databases, documents, and source code on a compromised server, — an act called [[exfiltration]] — to cloud storage they control — sometimes gigabytes per hour, blended in with normal HTTPS traffic so the firewall never blinks.

This is the moment that turns your backups from a shield into a shrug. You can restore every encrypted server from yesterday's snapshot and still lose everything that matters, because the copy sitting on the attacker's server doesn't care about your recovery plan. The ransom isn't "pay or lose your files." It's **"pay or we publish."**

## Stage 4: encryption and the leak site

Now comes the loud part — the deployment that locks hundreds of machines in minutes. This October, the threat actors behind the [IDCF Cloud attack](https://aviatrix.ai/threat-research-center/ransomware-attack-disrupts-japans-idcf-cloud-used-by-govt-clients/) (October 7, 2026) claimed to have encrypted 225 databases holding 3.6 PB of data, sealed 16,000 VM disks, and wiped over 554,000 snapshots — all within roughly seven minutes of breaching the East Japan region. Whether or not every claimed number checks out, the tactic is the signature of 2026: hit the hypervisor layer, not the individual servers, and the whole cloud region goes down at once.

While your systems are locked, the second pressure point activates: the **[[leak site]]**. Ransomware gangs run Tor-hosted leak portals that read like twisted compliance dashboards. One 2026 newcomer, AuditTeam, brands its portal as a "DATA EXPOSURE TERMINAL" and formats each victim as an "AUDIT ENTITY" with a hexadecimal audit ID and a discovery date — a bureaucratic aesthetic designed to make extortion feel inevitable, like a failed inspection rather than a crime.

And some crews now mask the victim's name entirely: a listing that says only "Paid Victim" with an ID, no company name. That's not mercy — it's a **countdown with an unknown blast radius**, engineered to push victims to decide faster than a fully named listing would.

## Stage 5: triple pressure — including you, personally

Double extortion (encrypt + publish) was the 2020s answer to backups. The 2026 answer is **triple pressure**: encryption, data exposure, and direct intimidation of people.

The Semperis numbers are grim reading:

- **87%** of attacks weaponized AI — for recon, phishing, and speeding up the whole operation.
- **40%** of attacks involved psychological or physical threats against staff or their families; in more than half of those cases, the attackers followed through.
- **Nearly 70%** of victims were targeted multiple times, and **31% paid multiple ransoms** — paying once marks you as someone who pays.

So the full modern playbook is: break in quietly, own the identity system, steal first, encrypt second, publish threats third, and — increasingly — threaten the human beings fourth. Chris Inglis, the first U.S. National Cyber Director, summarized the economics bluntly: the attacker wants the cost of *resisting* to exceed the cost of *giving in*.

## What actually helps (beyond "have backups")

Backups are necessary — they're just no longer sufficient. What the responders in these cases keep repeating:

1. **Immutable, offline backups.** Air-gapped or write-once storage the attacker can't reach or delete — because crews now hunt backup servers first. The IDCF case shows snapshot deletion as a standard opening move.
2. **Backup the identity system itself.** A dedicated, tested Active Directory recovery procedure — most victims learn they don't have one mid-crisis.
3. **[[EDR]] everywhere and someone watching it.** The weeks between intrusion and encryption are your detection window; behavioral alerts on mass file access and unusual outbound traffic catch the [[exfiltration]] stage.
4. **Segmentation and [[least privilege]].** Slow the [[lateral movement]] so one compromised workstation can't reach the domain controller.
5. **Patch what faces the internet.** VPNs, firewalls, file-transfer appliances — the front door. Track CISA's [[KEV]] list like it's your job, because for some attackers it is.
6. **A rehearsed [[incident response]] plan.** Out-of-band communication, defined roles, a decision on ransom policy made *before* the crisis — because negotiating under a countdown with masked leak listings is exactly how bad decisions happen.
7. **Don't pay if you can avoid it.** The stats say it plainly: nearly a third of payers paid again. Payment is a down payment on the next attack.

## The closing thought

Ransomware stopped being a malware problem years ago. It's a pressure business now — a machine that converts your own data, your own identity infrastructure, and your own fear into leverage. The crews industrialized it: leak sites with audit-log aesthetics, masked listings as countdown timers, AI doing the recon.

Your defense has to be just as systematic. Not one silver bullet, but a chain of them: harden the front door, watch the hallways, lock the identity system, keep backups the attacker can't touch, and rehearse the bad day before it arrives. Because in 2026, the ransom note is no longer the beginning of the attack — it's the *end* of an attack that started weeks before you noticed.
