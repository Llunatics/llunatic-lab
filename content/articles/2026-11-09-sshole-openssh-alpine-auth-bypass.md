---
title: "sshole: The OpenSSH Bug That Logs You Into Accounts With No Password"
date: 2026-11-09
tags: [threat-intel, openssh, vulnerability, alpine]
excerpt: "On November 5, OpenSSH shipped an emergency fix for CVE-2026-123158 — a logic bug that lets anyone log into a passwordless account on Alpine Linux with a password nobody set. The first exploitation attempts arrived within nine hours."
cover: /assets/covers/sshole-openssh-alpine-auth-bypass.jpg
---

There is a special kind of vulnerability that does not need a stolen credential, a brute-force campaign, or a single line of malware. It needs a password that is deliberately too long — and an account that was never supposed to accept any password at all.

On November 5, 2026, [[OpenSSH]] released Portable OpenSSH 10.6p2, an emergency fix for [[CVE]]-2026-123158, nicknamed "sshole" by its finder, Özgün Kültekin of Wakefield. The flaw scores 8.1 High under CVSS 3.1 and is classified as [[CWE]]-394, an unexpected status code or return value. Threat intelligence firm Previdian told Help Net Security it saw the first exploitation attempt less than nine hours after publication — and confirmed root access on an Alpine Linux honeypot. [[OpenSSH]] developer Damien Miller called it critical and told administrators of affected systems to disable password logins, or SSH altogether, immediately.

The behaviour is simple to state and uncomfortable to read. On an affected system, an attacker who can reach the SSH port can log in to an account that has no password, by sending a password that is deliberately too long. No stolen credential. No key. No brute force. Just a very long string of characters, and a comparison that was never supposed to succeed.

## Three reasonable decisions, fourteen years apart

CVE-2026-123158 is a logic bug, not memory corruption, and it lives in the gap between projects rather than inside any one of them. Three decisions, each defensible on its own, combine into an authentication bypass.

**2012, [[musl]] libc.** The POSIX standard says `crypt()` — the function that hashes passwords — should return a null pointer when hashing fails. Too many callers never checked the return value and crashed, so musl chose to return the literal string `*` instead. A defensive decision, and a defensible one in isolation.

**The same library caps key length.** musl's SHA-based `crypt()` refuses any password longer than 256 bytes, as protection against wasting CPU on absurd inputs. Past that limit, it fails — and failure now means returning `*`.

**2016, OpenSSH.** To fix CVE-2016-6210, a timing side channel that let attackers enumerate valid usernames by measuring whether [[sshd]] bothered to hash anything, OpenSSH 7.3 added salt borrowing. For an account with no real hash, sshd now takes a `$5$` or `$6$` salt from another local account and hashes the submitted password anyway, so valid and invalid usernames take the same time. A sound fix for a real problem.

**A long-standing Unix convention.** A single `*` in the password field of `/etc/shadow` marks an account that must never authenticate by password. Key-only accounts, service accounts, LDAP-mapped users — and root on Alpine — commonly carry it.

Put those together. An attacker offers a 300-byte password for an account whose shadow field is a single asterisk. Because of the 2016 change, sshd does not short-circuit: it borrows a salt from another account and calls `crypt()`. Because of the 2012 change and the 256-byte cap, musl returns the string asterisk. sshd compares that return value against the stored field, finds two identical asterisks, and treats the comparison as a successful authentication.

```text
attacker password : "AAAA…" (257 to 1024 bytes)
stored shadow field : *
sshd borrows salt  : $6$<salt from another account>$
musl crypt() returns: *   <- failure token, not a hash
sshd compares       : * == *  <- match, login accepted
```

The upper bound exists because sshd discards passwords over 1024 bytes, which is why the working range is roughly 257 to 1024. The fix in 10.6p2 is correspondingly narrow: sshd now rejects any stored hash shorter than four characters, whatever `crypt()` hands back.

## Who is exposed, precisely

This one has unusually tight preconditions, which is good news if you check them and bad news if you assume them. Every condition below has to hold at once.

- **sshd is linked against musl libc.** [[Alpine Linux]] is the common case; OpenWrt, Buildroot, and Yocto builds are also named in reporting.
- **[[PAM]] is not in use.** With PAM handling authentication, sshd never performs the `crypt()` comparison that fails open. Alpine's default OpenSSH server configuration does not use PAM.
- **Password authentication is enabled.** This is the OpenSSH default, so it holds unless someone deliberately turned it off.
- **A target account has a bare asterisk in its shadow field.** The account the attacker wants — commonly root or a service account.
- **Another local account has a real `$5$` or `$6$` hash.** The salt has to be borrowed from somewhere, so a system where no account has a usable password hash does not present the condition.

Equally important is what is *not* affected. Systems built on glibc — Debian, Ubuntu, RHEL and their derivatives — return a null pointer or the token `*0` on failure, neither of which can equal a stored asterisk, and sshd already rejects those. Systems using PAM are out of scope. Dropbear is reported as unaffected.

## Why this lands hardest on containers

Reading the conditions above as a server problem will understate the exposure badly. Alpine is the default small base image across most container ecosystems, chosen precisely because it is minimal — and minimal is the reason PAM is absent.

Three consequences follow, and each one breaks a different assumption.

First, **the count is higher than your server inventory suggests.** An organisation with no Alpine servers can still run thousands of Alpine containers. The question is not how many hosts run musl, it is how many images do.

Second, **most of those containers should not be running sshd at all** — and many do, inherited from a base image or added for debugging and never removed. An sshd in a container that nobody remembers enabling is both the exposure and the finding.

Third, **the fix travels by rebuild, not by upgrade.** Patching the host does nothing for an image built before November 5. Alpine published fixed OpenSSH packages across its supported branches — 3.24 ships `10.3_p1-r2`, 3.23 `10.2_p1-r1`, 3.22 `10.0_p1-r11`, 3.21 `9.9_p2-r1`, and 3.16–3.20 are also patched — so the action is to rebuild on a patched base and redeploy, a different workflow from a package upgrade and a slower one.

The practical exposure question for a platform team is therefore narrow and answerable: which running containers have an sshd listening, and of those, which are musl-based and reachable from anywhere an attacker sits. In most estates the honest answer to the first part is not known without checking.

```bash
# containers with a listening SSH port
kubectl get pods -A -o json | jq -r '.items[] | select(.spec.containers[].ports[]? | .containerPort == 22) | "\(.metadata.namespace)/\(.metadata.name)"'

# on a host, confirm the libc and whether PAM is compiled in
ldd /usr/sbin/sshd | grep -E 'musl|libc'
sshd -T 2>/dev/null | grep -E 'usepam|passwordauthentication'
```

## Detection: the gift this bug gives defenders

Memory-corruption bugs are hard to detect because failure looks like instability. This one is the opposite, and the [[SOC]] should take the gift. Successful exploitation produces a specific, logged event that has no legitimate counterpart: a password authentication succeeds for an account whose password field says it can never accept one.

The detection is a join between an authentication event and account state:

```text
rule:     ssh_password_login_to_locked_account
source:   sshd auth log
match:    "Accepted password for <user>"
where:    <user> shadow field is "*" or "!" at the time of login
and:      host libc is musl
severity: critical, no tuning expected
```

Supporting signals worth collecting alongside it, each weaker on its own and useful for confirming a case:

1. **"Accepted password for root"** on any Alpine host or container. Root on Alpine commonly carries the asterisk field, so this is close to decisive in that environment.
2. **Authentication on a container that should have no interactive access.** Any successful SSH login to a workload container is worth an alert on its own merits, independent of this CVE.
3. **Unusually large SSH authentication requests.** The attack requires a password of at least 257 bytes. Where network telemetry allows it, an anomalous request size at the auth stage is a direct indicator of an attempt rather than a success.
4. **Repeat attempts across accounts.** An operator will try root and then service accounts in sequence from the same source, which forms the usual spray pattern and gives a strong correlation key.

## What to do, in order

1. **Hunt retrospectively before anything else.** Exploitation was reported within nine hours of publication, so the question is whether it already happened. Run the detection above against stored authentication logs back to November 5, rather than only forward from today.
2. **Disable password authentication where it is not needed.** Setting `PasswordAuthentication no` removes the precondition entirely and is a reversible configuration change rather than a rebuild. For container images that should never accept interactive logins, removing sshd is better still.
3. **Rebuild and redeploy Alpine-based images** on patched packages, treating this as a distinct workstream from host patching, with its own completion tracking.
4. **Check reachability rather than assuming it.** A vulnerable container that no attacker can reach is a different priority from one behind a load balancer. Confirm which SSH ports are exposed outside the cluster rather than inferring it from network policy intent.

One honest caveat on the reporting: Previdian's observation of attempts within nine hours and root on a honeypot is specific and credited, but other vendor write-ups published on November 6 describe no confirmed in-the-wild exploitation, and at the time of writing the flaw is not listed in CISA's [[KEV]] catalog. Both statements can be true at once — honeypot compromise and confirmed victim organisations are different evidentiary bars. Treat it as being exploited, and verify the KEV position at publication. The [[EPSS]] score stood at 0.98% on November 6, which says the models do not expect mass exploitation — but models do not patch your containers.

Ownership of the defect is also disputed. OpenSSH shipped the fix, and musl's maintainer has described the problem as incorrect use of `crypt()` by the caller rather than a musl defect, while indicating the error behaviour is likely to change in a future release. That disagreement does not change what you have to do.

The lesson of sshole is not that Alpine is unsafe or that musl is broken. It is that the boundary between "an account that can never log in" and "an account that just did" was a single character — `*` — and two separate projects each had a good reason to treat that character as a harmless placeholder. Audit your assumptions the way you audit your packages: check what your locked accounts actually are, check which of your images run sshd, and check your logs back to November 5.

*Sources: OpenSSH 10.6p2 release (5 Nov 2026); Help Net Security via Previdian; Alpine Linux security advisory; hawk-eye.io analysis; zerohunt.ai; walterstein.eu.*
