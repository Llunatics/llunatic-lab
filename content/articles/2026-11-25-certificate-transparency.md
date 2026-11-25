---
title: "Certificate Transparency: The Public Ledger That Catches Rogue Certificates"
date: 2026-11-25
tags: [concept, certificate-transparency, pki, tls]
excerpt: "Every TLS certificate your browser trusts is written into a public, append-only log before it is issued. Certificate Transparency turns certificate issuance from a private handshake into a public record — and in 2026, the rules around it got stricter than ever."
cover: /assets/covers/certificate-transparency.jpg
---

Imagine a stranger walks into a bank, shows an ID card with your name on it, and walks out with your money. Now imagine the bank never tells you it happened — because it never checks whether the ID was real in the first place. That was the state of the web's [[public-key cryptography]] for years: any [[certificate authority]] could issue a certificate for any domain, and the domain owner would only find out when the damage was already done.

[[Certificate Transparency]] (CT) is the fix, and it is beautifully simple: make issuance public. Every publicly trusted TLS certificate must be written into an append-only public log before browsers will accept it. A rogue certificate can still be issued — but it can no longer be issued *quietly*. The attacker's fake credential is broadcast to the world within seconds, permanently, with no way to take it back. And in 2026, the system went through its biggest shake-up since it was created.

## The incident that forced the web to open its books

CT exists because the web learned the hard way that trusting certificate authorities in secret does not work. In 2011, the Dutch CA DigiNotar was breached, and attackers issued fraudulent certificates for Google and other major domains — certificates that browsers trusted, that could have enabled large-scale interception of users' traffic. The owner of the domain was the last to find out.

The answer, proposed by Google's Ben Laurie and colleagues and standardized as RFC 6962 in 2013, was to flip the model: instead of asking domain owners to trust CAs blindly, force CAs to publish everything they issue. If every certificate is public, anyone can watch the logs for their own domains and catch a certificate they never requested. The successor standard, RFC 9162 (CT version 2.0), followed in December 2021.

Today the scale is staggering. Public CT logs hold billions of certificates — one independent index counts nearly 8 billion certificates that are valid now or expired since December 2025 alone. Google's Argon 2026h2 log alone reached a final tree size of about 3.5 billion entries before it stopped accepting writes. CT is no longer an experiment. It is the backbone of the web PKI.

## How a certificate gets its receipt

The mechanics are a short chain of promises, and each link matters:

1. **The CA builds a [[precertificate]].** Before issuing the real certificate, the CA constructs a copy with a special "poison" extension that marks it as not-yet-valid. This is the object that gets logged.
2. **The log returns a [[Signed Certificate Timestamp]] (SCT).** The CA submits the precertificate to one or more CT logs. Each log replies immediately with an SCT — a signed promise to add the entry to the log within the [[Maximum Merge Delay]], usually 24 hours.
3. **The SCTs are embedded in the final certificate.** The CA issues the real certificate with the SCTs baked in. Browsers verify those SCTs before trusting the connection. A certificate with no valid SCTs is rejected outright.

The logs themselves are [[Merkle tree]]s — append-only structures where every new batch of certificates produces a new signed root hash, published as a signed tree head. Entries can be added but never edited or deleted, and anyone can cryptographically verify that a log has not been tampered with, or produce a compact proof that a given certificate is included. You do not have to trust the log operator. You can check the math.

Browsers enforce all of this. Chrome has required CT since 2018: two SCTs from distinct logs for certificates valid 180 days or less, three for longer ones. Apple applies the same split. Firefox was the last of the three to switch on enforcement, on desktop from version 135 in February 2025 and on Android from version 145. A certificate that fails CT policy is blocked with no user override.

## 2026: the year the rules tightened — twice

CT has been quietly mandatory for years, but 2026 brought two changes that made it stricter and reshaped the infrastructure underneath it.

**First, the pre-issuance mandate.** Under Chrome Root Program Policy version 1.8, effective 15 June 2026, CAs must log every TLS precertificate to at least one CT log Chrome recognizes as Usable or Qualified *before* issuing the corresponding certificate. Before that date, logging was a "SHOULD" with a 24-hour window. It is now a hard "MUST", and it must happen pre-issuance. Final certificates still only carry a SHOULD within 24 hours — the mandate targets precertificates specifically, because that is the point where the public record is created.

**Second, Google retired its classic logs.** On 12 November 2026, Google's four production RFC 6962 logs — Argon 2026h2, Argon 2027h1, Xenon 2026h2, and Xenon 2027h1 — stopped accepting writes. Together they held about 8.4 billion entries. Google cited the growing manual effort needed to keep the old protocol's logs running, and issuance shifted to its newer static-ct-api logs and other operators' logs. Apple's CT policy has accepted static-ct-api logs since 5 November 2026. The old logs remain readable while they are archived — the record does not disappear just because the intake moved.

And the tightening continues. On 17 November 2026, Chrome's CT team announced that logs must accept only RSA and ECDSA roots, and from 15 December 2026 must reject any submission whose chain uses another key or signature algorithm — including post-quantum keys such as ML-DSA. The reason given is load: certificates Chrome does not rely on add storage, bandwidth, and verification work with no security benefit to Chrome users. The post-quantum era will need its own CT arrangements; the current logs are not where they will live.

These changes sit inside a broader squeeze on certificate lifetimes. The maximum validity of a publicly trusted TLS certificate dropped to 200 days on 15 March 2026, and falls to 100 days on 15 March 2027 — the same date Chrome requires new subscriber certificates to assert only server authentication, dropping the clientAuth extended key usage. Shorter-lived certificates mean more issuance, more logging, and more reason to watch the logs automatically rather than by hand.

## What CT can — and cannot — do for you

The most common misunderstanding about CT is that it prevents bad certificates. It does not. CT is a camera, not a lock. A misissued certificate still works in a browser until someone revokes it. What CT guarantees is that the misissuance cannot stay hidden.

That guarantee is only useful if someone is watching. CT hands every domain owner three practical capabilities:

- **Detect certificates you never asked for.** A certificate for your domain appearing in the logs that you did not request is the signature of a CA error, a hijacked DNS or registrar account, or a targeted attack. This is the earliest warning most organizations will ever get.
- **Map your own [[attack surface]].** CT shows every subdomain anyone has ever obtained a certificate for — including the staging server a developer spun up and forgot, and the legacy service nobody owns anymore. It is one of the best free external inventories of your own footprint.
- **Complete the [[CAA]] picture.** A CAA DNS record tells CAs which of them may issue for your domain. That is prevention. CT is detection — it shows you what slipped through anyway.

The tooling is free and takes minutes to set up. Search any domain on **crt.sh** to see every certificate ever logged for it. Run **certspotter** as a daemon that alerts you when a new certificate appears. Or tap the **certstream** firehose for real-time issuance as it happens. The false positives are real — CDNs and hosting providers legitimately obtain certificates for your domains — but filtering those out is a one-time exercise, and the alternative is not knowing at all.

## Watch the ledger

Certificate Transparency is one of the rare security controls that costs nothing, requires no agent, and works for domains of every size — but only if someone looks at it. The logs are public. The receipts are cryptographic. The 2026 rule changes mean more certificates are logged earlier and more reliably than ever before, and the logs themselves are now in the middle of a generational handover from the old RFC 6962 infrastructure to static CT.

Set up monitoring for your domains today: a crt.sh search, a certspotter alert, a weekly glance at the newest entries. The next time a certificate authority makes a mistake — or an attacker makes one for them — you want to be the first to know, not the last. The ledger is open. Use it.
