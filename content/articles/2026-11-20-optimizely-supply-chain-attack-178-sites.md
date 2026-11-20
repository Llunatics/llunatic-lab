---
title: "One Hacked Tool, 178 Brands: The Optimizely Supply-Chain Attack"
date: 2026-11-20
tags: [supply-chain, optimizely, web-security, incident]
excerpt: "On 16 November 2026, visitors to Zoom, the BBC, HSBC, IKEA, and 174 other major sites were served malware — not because any of those companies were hacked, but because a single A/B testing tool they all trusted was. Here's how one poisoned script reached millions of browsers in 19 hours."
cover: /assets/covers/optimizely-supply-chain-attack-178-sites.jpg
---

On Monday 16 November 2026, you could visit Zoom, the BBC, CNN, HSBC, Salesforce, IKEA, GitLab, Equifax, Air France-KLM, Ledger, or Peacock — and be served [[malware]]. None of those companies' servers were hacked. The malicious code arrived through a tool they all trust: Optimizely Web Experimentation, the A/B testing platform whose JavaScript snippet runs on their pages. An attacker found a way to write their own JavaScript into Optimizely customer projects, and because every site loads that snippet from Optimizely's servers and runs it, the code ran in visitors' browsers as if it were part of the site itself.

That is the entire story of a [[supply chain attack]] in one sentence: compromise one trusted supplier, and its trust carries your code everywhere.

## How it was found

The attack was uncovered by security researcher Scott Helme and the team at Report URI. While it was still running, they scanned the platform and checked **1,611 Optimizely snippets**, finding **188 infected ones belonging to 178 organisations** worldwide — and the real number is probably higher, since they could only check snippets they found during the attack. Even Optimizely's own website and login page were affected.

The 178 organisations span almost every sector that handles money or personal data: 32 in banking and finance, 23 in tech and SaaS, 20 in retail and fashion, 12 in streaming, 10 in news and media, 9 in airlines and travel, 8 each in healthcare/pharma and industry, and 7 in telecoms — plus smaller numbers in crypto, insurance, property, food, nonprofits, gambling, logistics, automotive, and education.

Being on that list means an organisation's Optimizely snippet contained the malicious code at some point on 16 November. It does **not** by itself mean any customer data was taken. Each organisation still has to work out what its own visitors were exposed to.

## What the code did

The injected code was updated many times during the day, gaining features as it went. By the end, it could:

- **Swap cryptocurrency addresses.** It replaced Bitcoin, Ethereum, Solana, TRON, and other wallet addresses on the page, in forms, and in the clipboard with the attacker's own — so payments went to the wrong wallet.
- **Steal payment cards.** From 13:43 UTC it captured card numbers, expiry dates, and security codes typed into a site's own form fields. Cards entered in separate hosted payment boxes, such as those provided by payment processors, were out of reach — a detail that matters, as we'll see.
- **Steal browser data.** It sent page addresses, readable cookies, and screenshots to the attacker's server whenever it found wallet or payment content.
- **Attack iPhones.** It sent iPhone and iPad visitors on older iOS versions to known iOS [[exploit kit]]s that try to take over the device. Devices on iOS 18.7.3 or later, or iOS 26.3 or later, are patched against them.

Around **US$7,000** in cryptocurrency reached the attacker's wallets, which were emptied early on 17 November. Nobody yet knows how many cards or browser sessions were captured. Seven thousand dollars sounds small for an attack of this scale — but the wallets were only the visible part. The card data, cookies, and screenshots are the haul that can't be counted.

## The timeline

- **16 November, 04:21 UTC:** first malicious change seen, on the BBC's snippet.
- **16 November, 11:20 UTC:** Zoom's snippet is modified.
- **16 November, 13:43 UTC:** card-stealing code is added — the payload escalates from crypto theft to full [[web skimmer]] behaviour.
- **16 November, 20:40–21:10 UTC:** mass clean-up of infected snippets.
- **16 November, 23:11 UTC:** researchers confirm all infected Optimizely files are clean.
- **17 November, 01:02 UTC:** Optimizely posts its security incident notice.

In total, the code was live on some sites for about **17 to 19 hours**. The attacker's main domains were suspended or stopped responding on 17 November.

## How the companies responded

Optimizely said an unauthorised party exploited a vulnerability in its Experimentation product to add malicious JavaScript to some customer projects. It says it has fixed the vulnerability, removed the injected code, secured the affected accounts, and added protections to stop unauthorised code being delivered. Its status page listed the incident as "Monitoring". Optimizely has not yet said publicly what the vulnerability was or how many customers were affected.

Zoom said on its Trust Center that it has disabled Optimizely across its production environments as a precaution, and has not identified any impact to customer data. Salesforce posted an advisory saying it is investigating unauthorised changes to Optimizely scripts on certain Salesforce websites, and has disabled them as a precaution. Equifax launched an investigation and stopped using Optimizely, while stating it found no evidence of a breach of its own systems. IKEA and most of the other named brands had not published an official statement when the incident was first reported.

## Why this one matters

The Optimizely attack is a textbook case because it exposes the blind spot most websites live with. A modern website is not one codebase — it is a bundle of scripts from dozens of vendors: analytics, chat, A/B testing, tag managers, consent banners. Each of those scripts runs with the same power as the website's own code. If any one of them is compromised, the attacker inherits the trust of every site that loads it.

Three things made this attack unusually effective:

1. **The delivery channel was trusted by design.** Optimizely snippets are *supposed* to run arbitrary JavaScript — that is literally what A/B testing does. A malicious script hidden in a customer project looked like a legitimate experiment.
2. **The payload evolved in place.** The code was updated many times during the day, adding card theft hours after the first infection — a site that checked its snippet in the morning could have been serving a skimmer by the afternoon.
3. **The safety net mostly wasn't there.** Of the affected organisations the researchers checked, only about **15%** had a [[Content Security Policy]] that fully blocked the attack. A strict CSP — one that limits where scripts can load from and where data can be sent — is the one control that can stop a poisoned third-party script even after the vendor is compromised.

The card-theft detail is worth remembering: cards typed into a site's own form fields were exposed, while cards entered in hosted payment boxes were not. Keeping payment fields inside an iframe served by your payment provider is not just a PCI checkbox — it is a real blast-radius boundary. On 16 November, it was the difference between exposed and safe.

## If you visited one of those sites on 16 November

- **Update your iPhone or iPad** to iOS 18.7.3 or later, or iOS 26.3 or later. If you cannot update, turn on Lockdown Mode.
- **Check your card statements** for anything you don't recognise, and tell your bank straight away. If you typed a card into a website form on 16 November, consider asking your bank for a new card.
- **Check crypto transactions** you made on 16 November. Always compare the full wallet address, character by character, before you send money.
- **Sign out and back in** on accounts you used that day, and change passwords you entered on affected sites.
- **Be wary of follow-up scams.** Expect fake "your account was compromised" emails that use this news. Go to companies' websites directly, not through links in messages.

## If you run a website

- **Review your Optimizely Project JavaScript** and every experiment's custom code for scripts you did not write — especially anything that loads code from an unknown domain or uses `atob(` or `eval(`.
- **Check Optimizely's change history** for edits made on or around 16 November.
- **Rotate Optimizely credentials and API tokens**, and any session tokens or secrets that could have been readable in the browser.
- **Treat card details typed into your own form fields on 16 November as possibly exposed**, and talk to your payment provider.
- **Deploy a strict Content Security Policy** that limits where scripts can load from and where data can be sent — and keep third-party scripts off payment pages.

## The lesson

The attacker never needed to break into Zoom, IKEA, or a single bank. They compromised one service that all of them trust, and let that trust carry malicious code to millions of visitors. Your website's security is not just the code you wrote — it is every script you let someone else run on your pages. Know which third-party scripts run on your site, keep them off payment pages, and limit what they may load and where they may send data. The controls that would have stopped this one are the same controls that stop the next one — and most sites still haven't deployed them.

---

*Sources: [Malware targets crypto and iPhone users on 178 popular sites (PYMNTS, 17 November 2026)](https://www.pymnts.com/cybersecurity/2026/malware-targets-crypto-and-iphone-users-on-178-popular-sites/); [One hacked tool, 178 brands (Reef Sentinel, 17 November 2026)](https://www.reef-sentinel.net/n/271); [BBC, CNN, Zoom among 178 organisations targeted in crypto-stealing malware attack (Storyboard18, 17 November 2026)](https://www.storyboard18.com/digital/bbc-cnn-zoom-among-178-organisations-targeted-in-crypto-stealing-malware-attack-114914.htm). Additional reporting: Report URI (Scott Helme) and Optimizely's service status notice, 17 November 2026.*
