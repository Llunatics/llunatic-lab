---
title: "Zeabur: How Plaintext Secrets Killed a Hosting Platform — A Case Breakdown"
date: 2026-10-23
tags: [case-breakdown, secrets-management, cloud-security]
excerpt: "No zero-day. No nation-state. Just a non-expiring admin token sitting in plaintext in a config repo — and it cost Zeabur 3.2 million secrets, root on 101 customer servers, and eventually the company itself."
cover: /assets/covers/zeabur-plaintext-secrets-breach.jpg
---

A hosting platform died this month, and the murder weapon was a config repository.

Zeabur — a developer platform where you connect a GitHub repo and it handles builds, databases, HTTPS, and servers — published its second breach report in two months on October 19, 2026. Between October 14 and 15, an attacker read the secrets of every service on its shared clusters across nine regions, gained root on 101 customer servers, and dumped the platform database: **321,810 accounts and 3,218,965 environment-variable records**. Days later, Zeabur announced it will shut down on December 31, 2026.

The official report is unusually candid, and it names the root cause in one sentence: *"long-lived admin credentials were stored in plaintext and could be used from the public internet."* That's the whole story. Everything else is just that sentence playing out in slow motion, and it's worth studying frame by frame — because the same habits live in companies that are still alive.

## Act one: the breach they didn't finish fixing

The October intrusion began on August 27. An attacker exploited a customer's NextChat application (v2.16.1, tracked as CVE-2026-7644) running on a Zeabur shared cluster. Weak isolation between tenants let the attacker reach a routing cache holding Zeabur's legacy API keys, then use a team administrator's key to find an AWS root key inside an internal service, then read project environment variables from the production database.

Zeabur learned about it on August 28 from an API-key abuse report — not from its own monitoring. It notified users and rotated keys.

But the rotation missed two things: a shared-cluster admin token created in January 2024 **with no expiry**, and AWS keys. Both had been sitting in plaintext in a private configuration repository since January 2026. For nearly two years, a token that could administer the whole cluster never expired. For nine months, anyone who could read that repo held the keys to the kingdom.

This is the lesson the October incident screams: a partial [[incident response]] is sometimes worse than none, because it creates the belief that the problem is solved. The blast radius was understood, the obvious keys were rotated, and everyone exhaled — while the one credential that mattered most kept working, silently, in a repository.

## Act two: two paths, one plaintext

On October 14 at 01:36 UTC, the attacker returned with the missed credentials and took two paths that eventually met inside Zeabur's internal network.

**Path A: the shared cluster.** The attacker used Zeabur's AWS keys, then — four minutes later — the never-expiring admin token. The crucial detail: **the shared cluster's admin interface was reachable from the public internet**. A stolen token needed no foothold inside the network, no VPN, no pivot. From outside the world, straight into the crown jewels of nine regions.

By 12:39, the attacker was reading the settings and secrets of *all services* on the shared clusters, including environment variables. From 13:40, they ran read commands inside 865 customer database containers. The numbers from the report are staggering: 736 of them were **n8n** instances. Of the 607 n8n instances Zeabur checked, **602 stored their encryption key in an environment variable** — and that key decrypts every third-party credential n8n holds for its workflows. So reading environment variables effectively exposed those downstream logins too, one credential chain tumbling into the next.

The attacker then used an over-privileged cluster key to read a backup of an old cluster, found a key to Zeabur's secrets management service, and read about 53 production secrets — including the internal network's admin credentials, a platform database account, and the GitHub App private key. They also read the key used to sign login credentials and forged sessions as two accounts, one of them a Zeabur employee's.

**Path B: the dedicated servers.** An old GCP key gave the attacker access to server initialization settings, where **root passwords were stored in plaintext**. From October 14 at 13:40, the attacker signed in as root to 101 dedicated servers belonging to 92 users. They added their own SSH keys to 50 of them for [[persistence]], created five virtual machines, and attached copies of 16 customer disks.

On October 15, the paths joined: internal-network credentials taken via Path A let the attacker add their own node to Zeabur's internal network from a compromised server, and between 16:10 and 16:47 UTC, they read the platform database through it — all 29 connections mapped, 8,903 operation records, every environment variable, every account.

There's a detail that deserves a moment of silence. Zeabur began investigating at **13:56 UTC on October 15, after a user report** — again, not from its own alerts. The attacker had been inside for more than 36 hours.

And one more chilling footnote: sometime during the attack, Zeabur's daily backup captured a *newly rotated* key and the attacker read it from the backup and used it at 20:30. Rotating secrets while the attacker can read your backups is like changing the locks while handing out copies of the new keys.

## What the attacker actually wanted

The report's observations on attacker intent are telling. The attacker searched the platform database for API keys, read n8n and new-api/one-api credentials at scale, and tried calling **Amazon Bedrock** with Zeabur's AWS keys. They weren't after user profiles — they were hunting AI service keys.

This is the new credential economy. In 2026, an AI provider API key is as good as cash: it rents someone else's GPU fleet to train models, run inference, or resell access. A hosting platform that collects its customers' most sensitive values — database passwords, cloud keys, AI keys, signing secrets — becomes the highest-value target on the block, because one breach pays out across thousands of victims. That's why [[exfiltration]] of secrets is so much worse than the [[third-party risk]] the Denmark breach taught us about: this isn't a vendor with access to your data, it's a vendor *holding your keys*.

## The mitigation checklist (for everyone, not just Zeabur's customers)

Zeabur's own remediation list is excellent, and the principles generalize to any team that stores secrets:

1. **Rotate everything, then revoke the old values at the provider.** Zeabur's customers were told to revoke keys at AWS, Google Cloud, Stripe, OpenAI, Anthropic first, then issue new ones. Changing a secret only on your side while the old one still works is theater.
2. **Secrets must expire and rotate automatically.** A token created in January 2024 with no expiry is not a credential, it's a permanent spare key. Short-lived credentials, automatic rotation, no exceptions for "internal" tokens.
3. **Never store secrets in plaintext — in repos, in init settings, anywhere.** A private repo is not a secrets store. Environment variables are not encryption. If your secret is readable by anything that isn't a secrets manager with an audit log, it's already leaked in spirit.
4. **Keep admin interfaces off the internet.** If the shared-cluster admin console hadn't been publicly reachable, the stolen token would have been far less useful. Admin planes belong behind network controls, [[MFA]], and ideally mutual TLS — never one bearer token away from the whole world.
5. **Enforce [[least privilege]] on internal keys.** An "over-privileged key" that could read an old cluster backup became the bridge from the cluster to the secrets management service. Every credential should hold the minimum access it needs, so one leak can't cascade into the next.
6. **Monitor like your customers' keys depend on it — because they do.** Both Zeabur incidents were discovered through outside reports. Anomaly detection on credential use (a token from a new network, reads at 01:36 UTC, thousands of secrets in bulk) is table stakes.
7. **Treat dedicated servers as compromised until proven otherwise.** Zeabur told affected users to rebuild from scratch and check `authorized_keys` for the comment `@zeabur-pentest`. With root access and SSH keys added, there is no "cleaned" — only rebuilt.

One structural lesson deserves its own frame: **projects that followed Zeabur's post-August guidance and migrated their environment variables to their own dedicated servers were outside the scope of the platform database read.** Decentralizing secrets — refusing to hand all your keys to one platform — was the single best defense, and it worked. The customers who trusted the platform least were hurt least.

## The closing shot

Zeabur did several things right at the end: a detailed, honest preliminary report, clear victim guidance, and the grim final announcement. But honesty after the fact doesn't resurrect a company whose security model relied on secrets nobody expired, rotated, or protected.

The uncomfortable truth is that most of the failures here were unglamorous: plaintext in a config repo, a token with no expiry, an admin page on the internet, secrets without alarms. No exotic exploit. Just the basics, skipped, for years — until someone came to collect.

So audit your own plaintext today. Search your repos for `AKIA`, for `sk-`, for private keys committed "temporarily" three years ago. Check which tokens in your infrastructure have no expiry date. Because the Zeabur case proves one thing beyond doubt: **the attacker who finds your spare keys doesn't need to pick the lock.** You're already handing them the door.

---

*Sources: [Zeabur's October 2026 security incident report](https://zeabur.com/blogs/october-2026-security-incident) (primary, published October 19, 2026); [August 2026 incident context and shutdown announcement](https://breachhistory.com/blog/zeabur-second-breach-shutdown-october-2026); Exploit Security newsletter, October 16–21, 2026.*
