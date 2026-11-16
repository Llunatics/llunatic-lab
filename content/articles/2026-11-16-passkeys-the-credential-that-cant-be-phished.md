---
title: "Passkeys: The Credential That Can't Be Phished — and Why November 2026 Is the Tipping Point"
date: 2026-11-16
tags: [concept, passkeys, authentication, phishing]
excerpt: "Passwords are a shared secret, so they can be phished, guessed, and leaked. Passkeys replace them with a private key that never leaves your device — and in November 2026, Microsoft made them the first step of sign-in, not an optional extra."
cover: /assets/covers/passkeys-the-credential-that-cant-be-phished.jpg
---

Every [[phishing]] campaign you have ever seen exploits the same structural flaw: the password is a secret that both you and the server know. Anything two parties know can be tricked out of one of them. A convincing fake login page asks for it, you type it, and the attacker now knows it too. [[MFA]] codes help, but [[AitM]] phishing proxies your browser to the real site and relays the code in real time — the code was never meant to prove *which* site you are talking to.

[[Passkey]]s fix the flaw instead of patching around it. They replace the shared secret with a key pair, and the private half never leaves your device. There is nothing to type into a fake page, nothing to reuse across sites, and nothing for a breached database to leak. The idea is not new — the standards are years old — but November 2026 is the month the world's largest identity provider stopped treating passkeys as an optional upgrade and made them the default front door. This is how they work, why phishing cannot steal them, and what is still missing before you can delete your passwords.

## What a passkey actually is

A passkey is a login credential built on [[FIDO2]], the open standard from the [[FIDO Alliance]]: [[WebAuthn]], the web API browsers implement, and CTAP, the protocol for talking to an [[authenticator]] such as your phone, your laptop's fingerprint reader, or a hardware security key. The FIDO Alliance introduced the "passkey" name in 2022 to unify these standards into one consumer-facing concept.

The core idea is [[public-key cryptography]], the same technology behind TLS certificates. When you create a passkey for a site, your device generates a unique key pair scoped to that site's domain. The private key stays locked in the device — ideally in a [[secure element]] or trusted execution environment — and is released only after you unlock it with your face, fingerprint, or PIN. The site receives only the public key, which is useless without its private half. A database breach at the vendor hands attackers a pile of public keys they cannot use to log in as you.

This is also why a passkey counts as [[MFA]] in a single step. It combines something you have (the device holding the private key) with something you are or know (your biometric or PIN). Microsoft classes passkeys as phishing-resistant and lets them satisfy MFA on their own — no second factor, no SMS code, no authenticator app tap.

## The two ceremonies: registration and sign-in

WebAuthn has two flows, and both are challenge-response. Understanding them is understanding why the whole thing holds together.

**Registration** — creating the passkey — goes like this: the site (the [[relying party]]) generates a random [[challenge-response]] and sends it to your browser. The browser calls the WebAuthn API, which asks you to verify yourself with a biometric or PIN. The authenticator generates a fresh key pair bound to the site's domain, signs the challenge with the private key, and returns the public key to the site. The site stores the public key against your account. The private key never crosses the network at any point.

**Authentication** — signing in — is the same dance, minus the key generation. The site issues a fresh, single-use challenge. Your browser prompts for your biometric or PIN, the authenticator signs the challenge with the stored private key, and the site verifies the signature against the public key it holds. The challenge is single-use, which kills replay attacks: an intercepted signature is worthless five minutes later.

The cryptography underneath is deliberately boring and standard: ES256, ECDSA signatures over the P-256 elliptic curve with SHA-256 hashing, roughly 128 bits of security. Nothing exotic, nothing proprietary — which is exactly the point. Boring, standardized cryptography is what survives audit.

## Why phishing fails — structurally, not behaviorally

The phishing resistance of passkeys is not a matter of being careful. A careful person can still be fooled by a pixel-perfect fake login page. A passkey, by design, has nothing useful to hand over to that page.

The mechanism is [[origin]] binding. A passkey is cryptographically scoped to one domain — the [[relying party]] ID recorded at registration. When you try to sign in, the browser checks that the page you are on matches that domain before the authenticator will sign anything. On a look-alike domain, there is simply no matching credential, so nothing happens. The fake page can ask all it wants; the private key will not answer a stranger.

That single property kills three attack classes at once:

- **[[Phishing]] and [[AitM]] relay.** There is no password to type and no code to relay. The credential only works for the genuine domain, so a proxy to the real site cannot borrow it — the origin check happens in the browser, before any signature is produced.
- **[[credential stuffing]].** Every passkey is unique to one service, so a credential leaked from one breach cannot be tried against your other accounts. There is no reused password to stuff.
- **Server breaches.** Services store only public keys. A full database dump exposes nothing an attacker can replay into a login.

This is why the numbers matter more than the theory. Phishing is not a shrinking problem: Hong Kong's CERT recorded 4,404 security incidents in the third quarter of 2026, and phishing made up 2,672 of them — about 61%. Training people to spot fake pages is a losing arms race against attackers who now generate convincing lures at scale. Removing the thing that can be phished is the only move that ends the game.

## November 2026: the month the default flipped

Passkeys have existed for years, but until recently they were buried three menus deep. In 2026 they became the default. Google made passkeys the default sign-in option for personal accounts back in 2023. Microsoft made passkeys the default for new consumer accounts in May 2025, and through 2026 it has been moving existing users off text-message codes.

Then came the enterprise push. On September 1, 2026, Microsoft began rolling out passkeys as the default authentication method in Entra ID, auto-enabling them for users on Microsoft-provided SMS or voice authentication. On November 6, 2026, it went further: passkey or passwordless registration as the *first* [[MFA]] method reached general availability (Message Center post MC1450133), removing the old requirement to register a weaker method before going passwordless. The rollout runs in two phases through late February 2027. The practical consequence is blunt — a new employee can now register a passkey straight away, with no SMS detour that an attacker could hijack during onboarding. Microsoft has also announced it will retire Microsoft-provided SMS and voice authentication on February 1, 2027 for most users, and July 1, 2027 for Global Administrators and external users.

The adoption figures now back the shift. The FIDO Alliance's Passkey Index 2026, published in October 2026, found passkey sign-ins succeeded 93% of the time, against 78% for traditional [[MFA]], and that passkeys accounted for 36% of successful sign-ins at participating services — up from 26% in 2025. The FIDO Alliance's State of Passkeys report estimates around 5 billion passkeys are now in use, with 90% consumer awareness and roughly three in four people having enabled a passkey on at least one account. Dashlane's Passkey Power 20 report, published during Cybersecurity Awareness Month, found 57% of its users now store at least one passkey, up from 40% a year earlier, and that monthly passkey authentications among its users had nearly doubled to 2.5 million. Passkeys appeared in 28% of measured Google logins, 23% at GitHub, and 21% at HubSpot.

Even the standards bodies have caught up: NIST SP 800-63-4, published in July 2025, classifies synced authenticators at Authenticator Assurance Level 2 — the formal recognition that a synced passkey is a serious credential, not a convenience toy.

## Synced vs. device-bound: know which one you have

Not all passkeys are the same, and the distinction matters for your threat model.

A **[[device-bound passkey]]** lives on one piece of hardware — a security key, or a platform authenticator that never exports the key. It cannot be copied off the device, which makes it the strongest option and the right choice for admin accounts, code-signing identities, and anything where losing the device is acceptable but losing the credential is not. The cost is obvious: lose the device and the passkey is gone with it, so you need a second registered credential as a spare.

A **[[synced passkey]]** is stored in a credential manager — iCloud Keychain, Google Password Manager, 1Password, Bitwarden — and copied to your other devices through end-to-end encrypted sync. It survives a lost phone, which is why most people will use it. The tradeoff is that the credential now lives wherever the sync provider can reach it, so the security of your passkeys is the security of that provider's account. Protect the sync account with its own strong authentication, and treat it as the crown jewel it is.

Neither type is "the wrong one." The mistake is not knowing which you have, and having no recovery plan for either.

## The honest caveats

Passkeys are the strongest sign-in available to most people today, but they are not a magic eraser, and three gaps deserve honesty.

**First, you cannot go passkey-only yet.** Many banking apps, government services, and smaller tools still do not support passkeys. A community directory at passkeys.directory keeps an up-to-date list of which services do. Expect a hybrid life — passkeys where offered, passwords plus a hardware key elsewhere — for at least another year or two.

**Second, attackers move to the fallback.** A passkey cannot be typed into a fake site, so attackers turn to account recovery, fallback methods, and people. If your account still offers "reset by SMS code" as a fallback, that SMS code is now the weakest link in the chain — and the attacker knows it. When you enable passkeys, audit the recovery options on the same account and remove the weak ones.

**Third, portability is still maturing.** Moving passkeys between providers used to mean re-registering everywhere by hand. FIDO's Credential Exchange Protocol (CXP) is the standard that fixes this, with platform support expanding through 2026, but it is not yet universal. Before you commit a hundred accounts to one sync provider, check whether it can export.

None of these caveats weakens the core claim. They define the edges of it.

## What to do this week

For individuals: open the security settings of your email, your password manager, and your cloud account, and create a passkey on each. Start with the account that can reset all the others — usually your email. Register a second passkey on a different device or a hardware key, so a lost phone is an inconvenience, not a lockout. Then, on each account, look at the recovery options and remove any SMS fallback you no longer need.

For teams: the November 2026 Entra changes are the template. Make passkeys the first MFA method new users register, not the upgrade they get around to. Require phishing-resistant authentication for admin and privileged roles first — that is where AitM phishing pays off — and set a date to retire SMS-based sign-in, the way Microsoft has. And write down the recovery procedure before anyone needs it: a passkey rollout without a tested account-recovery path is a lockout waiting for a lost phone.

## The password's long goodbye

Passwords survived for sixty years because every replacement was either weaker, harder to use, or both. Passkeys are the first replacement that is stronger *and* easier: a fingerprint instead of a memorized secret, a signature instead of a shared one. The tipping point was never a better algorithm — the cryptography is old. It was the defaults flipping: Google in 2023, Microsoft for consumers in 2025, and now Microsoft Entra for the enterprise in November 2026, with SMS retirement already on the calendar.

The password will not die in a single announcement. It will fade the way it arrived — one default at a time, one account at a time. The question is not whether your accounts will offer passkeys. It is whether you will have created yours before the next phishing email arrives.

---

*Sources: [Passkeys for Small Business: Move Your Team Off Passwords (ExactReads, November 2026)](https://exactreads.com/passkeys-for-small-business/); [Passwordless Authentication: A 2026 Guide to Passkeys (Medium, November 2026)](https://medium.com/@auravenisolutions/passwordless-authentication-a-2026-guide-to-passkeys-111296bf64dd); [Phishing-Resistant MFA in Entra: 13 Steps [2026] (Tech Insider, November 2026)](https://tech-insider.org/phishing-resistant-mfa-entra-passkey-first-13-steps-2026/); [Entra lets passkeys be the first MFA method, GA rollout begins (Kira AI, November 2026)](https://kira-ai.de/blog/entra-lets-passkeys-be-the-first-mfa-method-ga-rollout-begins/); [MC1450133 — Microsoft Entra: Users can register a passkey or passwordless sign-in as their first multifactor authentication method (Microsoft 365 Message Center Archive)](https://message.cengizyilmaz.net/message/mc1450133-microsoft-entra-users-can-register-a-passkey-or-passwordless-signin-as-their-first-multifactor-authentication-method); [What Is a Passkey? 2026 Guide for HK Businesses (UD, November 2026)](https://www.ud.hk/en-US/resources/security/what-is-passkey-2026-11-10); [Passkeys Are Quietly Ending the Password (NewsXphere, November 2026)](https://www.newsxphere.com/tech/passkeys-are-replacing-passwords/); [Passkeys: A WebAuthn Implementation Guide (Veduis, 2026)](https://veduis.com/blog/passkeys-passwordless-authentication-webauthn/); [What really stops the move to passkeys in Microsoft 365, and what changes by July 2027 (Griffin31, November 2026)](https://www.griffin31.com/blog/passkeys-microsoft-365-what-stops-the-move/).*
