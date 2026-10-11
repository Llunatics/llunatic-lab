---
title: "Hunting Stealth Cryptominers: A Hands-On Lab From the AhsayCBS XMRig Campaign"
date: 2026-10-11
tags: [blue-team, threat-hunting, cryptojacking, hands-on]
excerpt: "Attackers chained two AhsayCBS zero-days, dropped an XMRig miner disguised as Microsoft Edge, and deployed an AI-assisted script that kills Task Manager the moment it opens. Here is how to hunt every stage of that campaign on your own network."
cover: /assets/covers/hunting-ahsaycbs-xmrig-campaign.jpg
---

Imagine this: a server's CPU is pegged at 90 percent around the clock, the electricity bill quietly climbs — and every time someone opens Task Manager to investigate, the spike vanishes. Task Manager itself closes. Reopen it, and it's gone again. The culprit is not haunted hardware. It is a cryptominer that watches you watching it.

That is not a hypothetical. On October 7, 2026, attackers began exploiting two flaws in AhsayCBS — the backup management platform used by MSPs and system integrators — and turned compromised backup servers into [[Monero]] mines. The payload, dubbed the "edge.exe" campaign by researchers at Huntress, packs four layers of evasion that read like a checklist of every stealth trick in the [[cryptojacking]] playbook. Let's take it apart, piece by piece, and turn each trick into something you can hunt for.

## The 30-second campaign brief

The two vulnerabilities are tracked as [[CVE]]-2026-105133 (an improper authentication flaw in the `checkSysPwd()` function, scored 5.5) and [[CVE]]-2026-105134 (an operating system command injection bug in the Replication Receiver, scored 9.3). Chained together, they let a remote, unauthenticated attacker execute commands with SYSTEM privileges. The CVE identifiers were only published on October 4, 2026 — and the first exploitation attempts hit at 11:20 p.m. UTC on October 7. At least five organizations were affected within a day.

Here is the twist that makes this a [[zero-day]] story: the NVD lists the flaws as fixed in AhsayCBS 10.3.4, but Huntress confirmed the latest version is also vulnerable. No real patch existed at the time of writing — treat every version as exposed.

Post-exploitation, Huntress observed the attackers running reconnaissance, dropping Java Server Pages [[webshell]]s, and then pulling payloads from an Alibaba Cloud object storage host. The files landed in `%TEMP%` or `AppData/Local/Temp`, spawned as child processes of the AhsayCBS service binary `cbssvcX64.exe`: `edge.exe`, `msedge.exe`, `config.json`, and a PowerShell script called `Taskgmr.ps1`. That process tree — a backup service spawning random binaries from Temp — is the first thing we will hunt.

## Trick 1: name masquerade

The XMRig miner — a legitimate open-source [[Monero]] miner frequently abused by criminals — arrived renamed as `edge.exe`, impersonating Microsoft Edge. When an analyst glances at a process list, a process called Edge barely registers. This is [[MITRE ATT&CK]] technique T1036.004, "masquerade task or service," and its cousin T1036.005, "match legitimate resource name."

Names lie. Paths and signatures don't. A real Edge browser binary lives under `C:\Program Files (x86)\Microsoft\Edge\Application` and is signed by Microsoft. The attacker's copy ran from a Temp folder with no valid signature. Your hunt:

```powershell
# Find every "edge.exe" running from a suspicious location
Get-CimInstance Win32_Process -Filter "Name = 'edge.exe'" |
  Select-Object Name, ProcessId, ExecutablePath, CommandLine

# Verify digital signatures — unsigned or wrong-signer binaries stick out
Get-ChildItem C:\Users\*\AppData\Local\Temp\*.exe -ErrorAction SilentlyContinue |
  Get-AuthenticodeSignature | Where-Object { $_.Status -ne 'Valid' }
```

In a [[SIEM]], the equivalent detection is simple: alert on any process whose name matches a well-known application but whose image path sits in a Temp directory or whose signature status is not Microsoft. Huntress published four [[Sigma]] rules covering exactly this pattern, including edge-named binaries carrying XMRig's tell-tale daemon flags.

## Trick 2: persistence that mimics the real updater

Killing the miner is not enough — you have to kill its [[persistence]] mechanism. The attackers installed a Windows service named `MicrosoftEdgeUpdateSvc`, deliberately close to the legitimate Edge update service (`edgeupdate`). The service ran `msedge.exe`, which Huntress identified as a modified copy of the Non-Sucking Service Manager ([[NSSM]]) — a legitimate open-source utility that runs any program as a Windows service and restarts it after crashes or reboots.

So the chain is: NSSM wrapper (SYSTEM privileges) → restarts `edge.exe` forever. Remove the service, the miner dies. Leave it, and it respawns on every boot. Your hunt:

```powershell
# List services with suspicious display-name / binary-path mismatches
Get-Service | Where-Object { $_.Name -like '*Edge*' -or $_.Name -like '*Update*' } |
  ForEach-Object { Get-CimInstance Win32_Service -Filter "Name = '$($_.Name)'" } |
  Select-Object Name, DisplayName, PathName, StartMode

# Flag services whose binaries live in Temp or user-writable folders
Get-CimInstance Win32_Service |
  Where-Object { $_.PathName -match '(?i)(temp|appdata)' } |
  Select-Object Name, DisplayName, PathName
```

Also compare the service list against a known-good baseline. The fake `MicrosoftEdgeUpdateSvc` differs from the real Edge updater by name, binary path (Temp instead of `Program Files`), and publisher metadata. On a fleet, any one of those mismatches is a hunt hit.

## Trick 3: the script that watches you back

This is the campaign's signature move. `Taskgmr.ps1` — fetched over `curl` — monitored Windows Task Manager and took action when an analyst got curious: if Task Manager opened, the script stopped the mining service to hide the CPU spike, then restarted it when Task Manager closed. Worse, it force-killed Task Manager at 6:00 p.m. local time, and again if Task Manager stayed open for more than an hour overnight. Huntress suspects the script was AI-assisted, based on its heavily commented code style — an unsettling sign of where commodity attacker tooling is headed.

Your hunt for this one has two halves. First, find the script's footprint: PowerShell execution events that poll for processes or call `Stop-Service`/`Stop-Process` on `taskmgr`:

```powershell
# Search PowerShell script-block logging (Event ID 4104) for Task Manager tampering
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational'; Id=4104} |
  Where-Object { $_.Message -match '(?i)(taskmgr|Stop-Service|Stop-Process)' } |
  Select-Object TimeCreated, @{n='Snippet';e={$_.Message.Substring(0,120)}}
```

Second, check for the persistence that keeps the script alive — scheduled tasks or registry Run keys pointing at `Taskgmr.ps1` or similar oddly named scripts. And remember the meta-lesson: when a machine's Task Manager keeps closing itself, don't dismiss it as a glitch. It is one of the most reliable user-visible indicators of anti-analysis [[malware]] on a box.

## Trick 4: the kernel driver shortcut

In at least one intrusion, the attackers used `certutil.exe` — the built-in Windows certificate utility, a classic [[LOLBin]] — to download `WinRing0x64.sys` to the Temp folder. This is a legitimate but vulnerable kernel driver. Attackers routinely abuse such drivers to disable endpoint security tools or, in this case, to gain low-level hardware access and squeeze more hashes out of the CPU.

Any download via `certutil` deserves scrutiny, but a `.sys` file written to Temp by `certutil.exe` and then loaded is a five-alarm hunt hit:

```powershell
# certutil downloading executables or drivers = investigate immediately
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688} |
  Where-Object { $_.Message -match '(?i)certutil.*(urlcache|download)' -and $_.Message -match '(?i)\.(exe|sys|dll)' } |
  Select-Object TimeCreated, @{n='Detail';e={$_.Message.Substring(0,150)}}
```

Also audit the driver store for unsigned or nonstandard drivers with `sigverif` or `driverquery /si`, and consider blocking known-vulnerable drivers with Microsoft's vulnerable-driver blocklist.

## The full hunt checklist

If you run AhsayCBS — or just want a practical exercise — work through this list in order. Treat it as a lab: each step maps to one evasion trick above.

1. **Scope exposure**: is the AhsayCBS management web interface reachable from the internet? Huntress's core advice: restrict it to trusted IPs or require VPN, immediately. Remember 10.3.4 is also vulnerable — this is a [[zero-day]] with no complete fix.
2. **Child processes**: hunt for unexpected children of `cbssvcX64.exe` or `cbssvcX86.exe` in your EDR or Sysmon logs (process creation, Event ID 1/4688).
3. **Name masquerade**: find Edge/Chrome-looking binaries running from Temp, unsigned or with mismatched signatures.
4. **Fake services**: diff your services against baseline; flag anything whose binary lives in a user-writable path.
5. **Anti-analysis scripts**: search PowerShell 4104 logs for `taskmgr` references; audit scheduled tasks and Run keys.
6. **LOLBin downloads**: look for `certutil` or `curl` pulling executables, and `.sys` files landing in Temp.
7. **Network**: watch for outbound connections to Monero pools — the campaign used `xmr.kryptex.network:8029` and `51.195.127.124:8029`.
8. **Assume breach depth**: if you find anything, Huntress recommends re-imaging the host from a trusted backup. Webshells and backdoors may be hiding alongside the miner.

## Closing: the miner is the least of your problems

Here is the part defenders sometimes miss. Cryptojacking feels like a nuisance — stolen electricity, slow servers. But this campaign started with a webshell on a backup server. Backup servers hold the keys to everything: credentials, repositories, storage systems for every customer an MSP protects. A miner that announces itself with 90 percent CPU is, perversely, a loud intruder. The quiet ones — the webshells, the stolen sessions, the backup data copied off in the background — are the real payload. Hunt the miner, but patch the assumption that mining is all they did.

Sources: Huntress blog (primary, including published Sigma rules and IoCs), The Hacker News (Oct 9, 2026), BleepingComputer (Oct 9, 2026), Threadlinqs TL-2026-3109.
