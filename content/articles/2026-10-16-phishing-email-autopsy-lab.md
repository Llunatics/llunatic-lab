---
title: "Dissect a Phishing Email Like an Analyst: A Hands-On Lab on the Fake Calendar Invite Wave"
date: 2026-10-16
tags: [phishing, blue-team, hands-on, email-security]
excerpt: "Fake meeting invites just became one of 2026's largest phishing waves — more than 740,000 emails in the first two weeks of October alone, says Check Point. In this hands-on lab you'll autopsy a suspicious invite with stdlib-only Python: headers, SPF/DKIM/DMARC verdicts, hidden URLs, and the malicious .ics attachment."
cover: /assets/covers/phishing-email-autopsy-lab.jpg
---

You know what the most trusted message in your inbox is? It's not the one from your bank. It's the calendar invite. It arrives with zero suspicion, gets one distracted glance, and — click — you're on the "login" page. Attackers figured this out long ago, and this month they industrialized it.

Check Point's email researchers [reported](https://blog.checkpoint.com/securing-user-and-access/fake-calendar-invites-target-thousands-of-organizations-in-microsoft-credential-phishing-campaign/) that fake calendar invites surged starting September 25, 2026. Their new detection layer flagged **more than 302,386 unique phishing emails sent to over 40,000 organizations**, averaging 8,319 emails per active day, from 33,890 sender domains and 247,270 unique sender addresses. The growth curve is the scary part: a few thousand emails a month in April, 118,000 in September, and **more than 740,000 in just the first two weeks of October**. The busiest single day — October 8 — saw almost 200,000 emails. The campaign was still active on October 15, the day before this article.

Two variants are in circulation. One arrives as an **[[ICS]] attachment**: a perfectly valid calendar file — no exploit, no vulnerability, just event data that abuses the trust your mail client places in calendar formats. The other is a fake Microsoft Teams invite where hovering over the "Join" button reveals the real destination: a credential-harvesting page dressed up to look like a Microsoft login.

Today you'll stop reading about phishing and start dissecting it. Below is a real analyst-style autopsy lab using nothing but Python's standard library. Grab a suspicious `.eml` file (export it from your mail client with "Save as"), and let's open it up.

## Step 0: the ground rule

Never do this on your work laptop with the attachment open in a client that auto-renders HTML. Save the message as `.eml`, move to an isolated machine or VM, and **do not click anything**. Our lab reads the raw bytes — no rendering, no fetching, no risk.

## Step 1: who is this really from?

The `From:` header is a lie you are allowed to write. It's display text — anyone can type "Microsoft Teams" into it. What actually matters are the routing headers: `Return-Path`, `Reply-To`, and the chain of `Received:` headers that record every server the message touched.

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

**What to look for:** the `From:` says `Microsoft Teams <no-reply@teams.microsoft.com>`, but `Return-Path` points to a disposable domain, and the first `Received:` hop shows a server that has nothing to do with Microsoft's mail infrastructure. In the calendar-invite wave, Check Point observed senders rotating through **33,890 different domains** — the infrastructure is deliberately disposable, because defenders block domains fast.

## Step 2: the three authentication verdicts

Modern email has three built-in lie detectors, and your mail server stamps its verdict into a header called `Authentication-Results`:

- **[[SPF]]** — did this server have permission to send mail for the claimed domain?
- **[[DKIM]]** — is the message cryptographically signed by the domain, and did the content survive the trip unmodified?
- **[[DMARC]]** — when the first two fail, what policy did the domain owner publish: deliver anyway (`none`), quarantine, or reject?

```python
auth = msg["Authentication-Results"]
if auth:
    import re
    for verdict in re.split(r";\s*", str(auth)):
        if verdict.strip():
            print(" *", verdict.strip()[:90])
else:
    print("(missing — no SPF/DKIM/DMARC verdict at all. Treat as suspicious.)")
```

Typical output for a phish:

```
 * spf=fail (sender IP is 185.220.xx.xx) smtp.mailfrom=invites-calendar-365.com
 * dkim=none (no signature)
 * dmarc=fail (p=quarantine) header.from=teams.microsoft.com
```

That last line is the kill shot: `header.from` claims `teams.microsoft.com`, but [[DMARC]] alignment fails because the real sender is `invites-calendar-365.com` — a domain registered last week. Note the phisher's trick: the envelope domain *passes* its own SPF, so a lazy check on "did SPF pass" is not enough. **Alignment** — the From domain matching the authenticated domain — is what matters.

## Step 3: the URLs that don't match their clothes

Now the body. Phishing lives in the gap between what a link *shows* and where it *goes*:

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
                print(f"  MISMATCH  display={shown_text[:60]!r} -> href={href[:90]}")
```

In the Teams-invite variant, this is exactly where the trap springs: the anchor text shows `teams.microsoft.com/l/meetup-join/...` while the `href` points to a lookalike domain hosting a fake login page. Hovering revealed it in Check Point's screenshots — but most victims never hover. Also watch for `xn--` (punycode) domains, where `microsоft.com` hides a Cyrillic "о".

## Step 4: open the .ics — the actual payload

For the attachment variant, the malicious content lives inside the calendar file. An [[ICS]] file is plain text — no rendering needed, just read it:

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

A real one from this wave looks something like this (synthetic example, same shape):

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

Valid calendar data. No exploit. No malware signature. Just a trusted format carrying an untrusted link — which is precisely why Check Point notes the campaign **abuses calendar features and user trust rather than a software vulnerability**. Signature-based defenses see a legitimate file type; the danger is entirely semantic.

## Step 5: render the verdict, like an analyst

A blue-team analyst scores the message, not the vibe. Here's the decision table this lab produces:

| Signal | Legitimate invite | This wave's phish |
|---|---|---|
| `From` vs `Return-Path` | same domain | mismatch |
| [[SPF]]/[[DKIM]] | pass, aligned | fail or none |
| [[DMARC]] policy | pass | fail |
| `Received` chain | known mail infra | throwaway VPS/relay |
| Link display vs `href` | identical | mismatch |
| `.ics` content | meeting details | login/verify URL |

Two or more red flags: treat it as confirmed [[phishing]], preserve the `.eml`, and report it — don't just delete it. Your security team's detection rules can only learn from samples they receive.

## The uncomfortable escalation: stolen sessions, not just passwords

One more reason this lab matters more than it used to. Proofpoint's October 1, 2026 report on the **TA419** campaign documented an [[AitM]] (adversary-in-the-middle) kit built on Evilginx: instead of cloning the Microsoft login page, it proxies the victim's browser to the *real* Microsoft 365 login and intercepts the credentials **and the session tokens** — with automation that selects "Keep me signed in" and auto-submits OTP codes. Code-based [[MFA]] does not stop that. Only phishing-resistant authentication — FIDO2 security keys or passkeys, which cryptographically bind the login to the real domain — breaks the proxy.

The calendar-invite wave harvests passwords today. The AitM kits harvest the session itself. Your defense has to assume the credential *will* leak and make the session unstealable.

## What to do Monday morning

1. **Report, don't just delete.** Use your mail client's phishing-report button or forward to your SOC. Every sample trains the filters.
2. **Make "hover before you click" a reflex** — and for calendar invites, an even stricter one: invites from outside your organization that contain login or "verify" links deserve a report, not a click.
3. **Enforce [[DMARC]] on your own domain** with `p=quarantine`, then `p=reject`. If your domain can't be spoofed, your brand can't star in someone else's phish.
4. **Ask your mail gateway to flag external `.ics` attachments containing URLs** in `DESCRIPTION` or `LOCATION`. It's a cheap rule that directly targets this wave's technique.
5. **Move high-value accounts to phishing-resistant [[MFA]]** (FIDO2/passkeys). The TA419 report is the proof that codes alone are no longer enough.
6. **Verify out-of-band.** Any "urgent" invite that demands credentials gets a second channel: message the supposed organizer in Teams or Slack before touching the link.

## Closing

The cleverest thing about the fake calendar invite wave is how little cleverness it needs. No zero-day. No exploit. Just a file format your mail client has trusted since the 1990s and a human reflex — *a meeting invite, must be important* — that bypasses every security awareness poster ever printed.

That's also why the autopsy matters. Phishing isn't fought with sharper eyes; it's fought with headers, authentication verdicts, and link inspection — evidence a script can check in milliseconds while your attention is still deciding whether the meeting is real. Save this lab. Run it on the next suspicious invite. The attackers are counting on you not to.
