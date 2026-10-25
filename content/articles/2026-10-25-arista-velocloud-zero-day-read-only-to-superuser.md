---
title: "Read-Only to Superuser: Arista's VeloCloud Zero-Day and the Third Strike on SD-WAN's Control Plane"
date: 2026-10-25
tags: [threat-intel, zero-day, sd-wan, privilege-escalation]
excerpt: "Arista's October 22 advisory describes a SQL injection flaw that turns the lowest-privilege VeloCloud account into a full operator — the third exploited VeloCloud Orchestrator flaw since July, and the first that only needs a login."
cover: /assets/covers/arista-velocloud-zero-day-read-only-to-superuser.jpg
---

There is a special kind of dread reserved for the vulnerability that doesn't need to break in. On October 22, 2026, Arista Networks disclosed that attackers are already exploiting a [[zero-day]] in its VeloCloud Orchestrator — and the entry ticket is not a stolen admin password or an exotic exploit chain. It is any valid login, including the lowest-privilege account the system offers: Enterprise Read Only.

Read that again. The account designed to *look* at the network can now *run* it.

## What VeloCloud Orchestrator actually controls

To understand why this matters, you need to understand what the orchestrator is. VeloCloud [[SD-WAN]] (software-defined wide-area networking) replaces the old model — where every branch office needed its own carefully hand-configured router — with a centrally managed fabric. Branch sites connect through Edge devices, traffic is steered intelligently across internet and private links, and everything is configured, monitored, and updated from one place: the VeloCloud Orchestrator (VCO).

That centralization is the whole selling point, and it is also the whole risk. Whoever controls the orchestrator controls the network policy of every site it manages: which traffic goes where, which tunnels exist, which devices are trusted. Operators create customer and partner accounts from it, and each partner can manage a group of customers. So a flaw that elevates a single read-only customer account to operator privileges is not a minor permission bug — it is a skeleton key to the control plane of potentially many organizations at once.

Arista acquired the VeloCloud SD-WAN product line from Broadcom, with the deal announced in July 2025. The products were previously known as VMware SD-WAN by VeloCloud. That lineage matters for defenders doing inventory: if your estate still lists "VMware SD-WAN" or "VeloCloud" in an asset register, this advisory is about you.

## The flaw: CVE-2026-114625

The vulnerability is tracked as [[CVE]]-2026-114625 and rated 9.9 on the CVSS scale — about as severe as ratings get. It is a [[SQL injection]] flaw in the orchestrator: crafted input that is supposed to be treated as data is instead interpreted as a database command, letting the attacker bend the application's own database to their will. In this case, the practical result is [[privilege escalation]] from Enterprise Read Only — the lowest built-in role for customer users — to operator privileges, effectively acting as a local superuser with full access to the orchestrator.

Three details from Arista's advisory make this worse than a typical privilege-escalation bug:

1. **It only needs a login, not an admin.** Any compromised, shared, or stale read-only credential is enough. Organizations routinely hand read-only access to contractors, auditors, managed-service partners, and former staff whose accounts linger. Every one of those is now a potential superuser.
2. **The orchestrator is exposed by default.** Arista states plainly that VCO is exposed by default and that no VCO setting prevents that exposure. There is no toggle to hide it; exposure must be controlled at the network layer, by restricting which networks can reach the web interface at all.
3. **The blast radius may extend past the orchestrator itself.** Arista says the flaw may allow an attacker to affect the VCO host itself and to expose, modify, or disrupt the orchestrator and the data it manages. For the July and September flaws, Arista warned that a compromised orchestrator could also grant access to VeloCloud Edge devices; for this flaw, the advisory does not say whether that risk applies — an uncertainty defenders should treat as a reason to investigate, not as reassurance.

## Third strike since July

This is the part that should change how you think about the product's risk profile. CVE-2026-114625 is the third VeloCloud Orchestrator flaw Arista has reported as exploited since late July 2026:

- **July:** CVE-2026-16812, exploited without authentication.
- **September:** CVE-2026-93952, also exploited without authentication.
- **October:** CVE-2026-114625, exploited with any valid login.

Notice the pattern. The first two flaws needed no credentials at all; the third needs only the weakest credential. Attackers have now demonstrated, three times in three months, that they can reach and abuse the orchestrator's control plane. That is no longer a run of bad luck — it is evidence that the orchestrator is an actively hunted target, and that patching one flaw while deferring the next is a losing strategy. Notably, orchestrators running the releases that fixed the July and September flaws are *still* affected by this one, because those fixed releases are older than the new fixes. "We patched last month" is not a defense here; only the specific new builds count.

## Who is affected, and what fixes it

For on-premises orchestrators, the fixes are build-specific per release train:

| Release train | Fixed in |
| --- | --- |
| 5.2 | 5.2.3.18 and later |
| 6.1 | 6.1.3.10 and later |
| 6.4 | 6.4.2.12 and later |

Hosted and Dedicated orchestrators have already been patched by Arista, so customers on those deployment models should still verify their status rather than assume it. VeloCloud Gateway and VeloCloud Edge devices are not affected by this flaw, and the 7.0 release train is not on the vulnerable list — Arista says any release not on the list is not vulnerable. One caveat: Arista has not checked releases that have reached end of support, so customers on unsupported trains should contact Arista's Technical Assistance Center about upgrade options rather than guessing.

A related loose end deserves attention: as of October 22, the September flaw is fixed only in the 5.2 and 6.4 trains, and on 6.1 it affects releases up to 6.1.3.7 with no fixed release listed. Neither advisory says whether 6.1.3.10 also fixes the September flaw. If you run 6.1, chase that answer explicitly with Arista — do not assume one patch closes both holes.

## Hunting for compromise

Arista has published two IP addresses observed carrying out the attacks. Block them, and search your logs for any trace of them:

- `74.82.197.86`
- `38.54.50.151`

Beyond those indicators, Arista advises checking VCO web access logs for requests with unusual URL-like path components, encoded characters, references to local or internal services, or abnormally high request rates. Until the fixed release is installed, it also recommends limiting access to the VCO web interface to trusted administrative networks, monitoring for unexpected outbound activity from the VCO host, blocking outbound ports that normal operation does not need, watching for backdoor daemons and webshells, and reviewing recent administrator activity for unexpected changes.

If you suspect compromise, preserve evidence before you fix anything, where possible: VCO web access logs, backend application logs, system and database logs, and relevant filesystem timestamps. That last point matters because of an uncomfortable unknown: Arista's advisory does not say whether upgrading removes access an attacker has already gained. Patching closes the door; it does not evict someone who already walked through it and planted persistence. Treat a potentially compromised orchestrator as an incident, not a patch ticket: rotate credentials, review every account and change made through the orchestrator, and check downstream Edge devices.

## The mitigation checklist

1. **Upgrade on-premises orchestrators now** to 5.2.3.18, 6.1.3.10, or 6.4.2.12 for your train — and confirm the September flaw's status on 6.1 separately.
2. **Put the orchestrator behind network controls.** Since VCO is exposed by default and no setting changes that, restrict its web interface to trusted administrative networks at the firewall or VPN layer.
3. **Audit read-only accounts like privileged ones.** This flaw erases the safety distinction between "can view" and "can control." Remove stale accounts, review partner and contractor access, and enforce [[MFA]] on every orchestrator login.
4. **Hunt with the published indicators.** Search for the two attacker IPs and the suspicious log patterns above, across the full window — Arista has not said when the attacks began, so do not scope your hunt narrowly.
5. **Assume persistence until proven otherwise.** If compromise is possible, preserve logs first, then investigate accounts, scheduled changes, and Edge device access before declaring the incident closed.

## The closing shot

The security industry loves to say "assume breach." The VeloCloud story gives that phrase a sharper edge: assume that your lowest-privilege accounts are breach vectors too. A read-only user was supposed to be the safe account — the one you could hand out freely because it couldn't *do* anything. Three exploited flaws in three months have now demolished that assumption twice over: first by needing no login at all, then by needing only the weakest one.

The orchestrator is the brain of the WAN. When the brain has a flaw that turns observers into operators, patching is not a maintenance window — it is an emergency. Check your version, restrict access to the interface, and hunt your logs. The attackers, Arista tells us, are already doing the same.

---

*Sources: [Arista advisory, October 22, 2026, via The Hacker News](https://thehackernews.com/2026/10/arista-warns-of-critical-velocloud-sql.html); [Arista patches exploited VeloCloud zero-day (Cryptopolitan, October 2026)](https://www.cryptopolitan.com/arista-patches-exploited-velocloud-zero-day-as-sd-wan-risks-mount/).*
