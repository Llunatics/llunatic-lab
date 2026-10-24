---
title: "PHP2Shell: When the Runtime Itself Is the Vulnerability — A Case Breakdown"
date: 2026-10-24
tags: [case-breakdown, php, vulnerability]
excerpt: "No plugin was broken. No password was guessed. Two flaws in PHP itself let an unauthenticated attacker run code on a web server — and the first exploit attempts arrived four days before the patch existed."
cover: /assets/covers/php2shell-runtime-rce.jpg
---

Most web security stories start with a bug in somebody's code. This one starts underneath all of it.

On October 21, 2026, PHP shipped emergency releases fixing two critical flaws in the language runtime itself: CVE-2026-109618 and CVE-2026-109619, collectively nicknamed PHP2Shell. Both allow an unauthenticated attacker to execute code on a server running PHP, both are rated CVSS v4.0 9.2, and neither requires the victim's application to be badly written. A WordPress site with perfect code, a Laravel app with clean validation, a Symfony service with no known bugs — all of them were exposed, because the flaw sat one layer below the application, in the engine that runs it.

That distinction is the whole story. You can audit your own code for years and still miss this, because there was nothing in your code to find.

## What actually broke

The two flaws are different bugs with the same destination.

CVE-2026-109618 fires when PHP runs out of memory partway through setting up a request. Some internal data is left half-built, and the cleanup code that runs at the end of the request trusts that broken data anyway. CVE-2026-109619 is about state that outlives the memory it points to: a later request picked up by the same worker can act on leftover pointers from an earlier one. In both cases the attacker does not need an account, a login, or any prior access. A crafted web request is enough.

The PHP project said every installation serving web requests was at risk — PHP-FPM, php-cgi, FrankenPHP, LiteSpeed, and Apache's mod_php. Mod_php carried the highest risk, because there the [[exploit]] was validated over HTTP with default memory and input limits, before any application code had even started running. That last detail matters: no middleware, no firewall rule inside your app, no input filter you wrote could have stopped it, because your code had not run yet.

One confirmed path ran through PHP's session upload progress feature, which is enabled by default and lets an application track file uploads. That feature will come back later in this story, in a way that should make anyone who patched in a hurry pay attention.

The flaws were reported by researchers at Wiz and Calif, working with the PHP security team, and they affect nearly every PHP version back to 5.4. The fixed releases were PHP 8.5.12, 8.4.27, 8.3.36, and 8.2.35. Older branches got no numbered release at all: the PHP team published minimal source backports for 7.4, 8.0, and 8.1, for people who build from source or have a long-term support vendor. If you are still on 8.1 or older, "we updated WordPress" was never the answer. WordPress does not ship PHP. Your host, your container image, your server does.

## A disclosure that fell apart in public

PHP2Shell did not get a clean coordinated disclosure. It got a week of leaks, early patches, and arguments about who moved first.

The timeline, as best as the public record reconstructs it, goes like this. On October 17, Amazon's honeypot network recorded an exploitation attempt against the flaws — four days before any patch existed, while the vulnerabilities were still under embargo. How the attacker got the details is still unknown. On October 20, details leaked on social media ahead of the planned October 22 disclosure, and a [[proof of concept]] video was mistakenly posted by one of the research firms. That evening PHP announced an emergency release for the next day.

On October 21, Cloudflare switched on emergency firewall rules by default at 03:02 UTC, hours before the fix. At 07:41 UTC, container vendor Chainguard published images containing the patch, about six hours before the coordinated release — a move the PHP Foundation later criticised, and which Chainguard defended by saying it acted after other vendors reported attacks. At 14:00 UTC, PHP published the fixed versions.

Within hours, watchTowr reported exploitation observed in the wild through its honeypot network, and other firms described broad, untargeted scanning. At the same time, the record is messier than the headlines suggest. CISA, when it published its alert, said it had not observed exploitation. WatchTowr itself initially described attempts, not confirmed successes. The PHP Foundation said the circulating proofs of concept it inspected were not functional exploits at release time. As of October 22, neither [[CVE]] had entered CISA's [[KEV]] catalog.

That messiness is not a footnote. It is the normal shape of a zero-day week: different sensors see different things at different times, "exploited in the wild" can mean a probe against a honeypot rather than a server actually taken over, and no public source has yet named a specific website confirmed compromised by PHP2Shell. Treating a probe as a breach overstates the damage. Treating the absence of a named victim as safety understates it, because the attempts began before the patch existed — which means a server patched on October 21 could still have been probed on October 17.

The practical response in several countries reflected that uncertainty. The NSA, CISA, and FBI advised organisations that could not update immediately to consider taking websites offline. Government and public-service sites in the Netherlands, Germany, France, Belgium, Finland, and the Czech Republic, plus councils in the UK, went dark as a precaution while they patched. Those shutdowns were not admissions of compromise. They were what caution looks like when the runtime under everything you run has a hole in it and the fix is not yet installed.

## Then, on October 23, a second advisory

Just as teams were finishing the emergency patch, PHP published another advisory on October 23 — and it is easy to misunderstand, so it is worth stating precisely.

The new issue, tracked as CVE-2026-115560, is a potential [[remote code execution]] path involving session upload progress. But it only applies in an unusual combination: an application first configures `session.serialize_handler` as `php_binary` or `php_serialize`, then changes it at runtime with `ini_set()` to `php` before calling `session_start()`, while session upload progress stays enabled. Applications that never change the serialization handler at runtime are not exposed through this path, even with upload progress on.

PHP did not issue an emergency patch for it. The plan is a fix in a regular bugfix release, with a full advisory alongside it, and at the time of the October 23 notice the affected versions and a severity score had not been published. The recommended mitigation is simple:

```ini
session.upload_progress.enabled = 0
```

If you already disabled upload progress in response to the October 21 advisory for CVE-2026-109619, PHP says no further action is needed for this one. And disabling upload progress does not replace the October 21 update. It helps against one path of one flaw. It does nothing against CVE-2026-109618. Only updating fixes PHP2Shell in full.

That is the trap this second advisory sets for tired teams: it looks like another emergency, and it also looks like a reason to relax. It is neither. It is a narrower, slower-burning issue attached to the same feature, and it rewards exactly the people who read the conditions instead of just the headline.

## What to actually do

If you run anything on PHP, the checklist is short and unforgiving:

1. **Check the runtime, not the app.** Run `php -v` on the server that actually serves traffic, and check every other place PHP hides: other containers, staging servers, that old VPS nobody remembers, vendor appliances. Palo Alto Networks counted 22.6 million potentially vulnerable exposed instances from its own telemetry — the long tail of forgotten PHP is the real attack surface here.
2. **Update, then restart.** Move to 8.2.35, 8.3.36, 8.4.27, or 8.5.12 (or a patched vendor package), and restart every PHP worker: FPM pools, Apache, long-running workers. A patched binary sitting on disk while an old worker keeps serving requests is not patched.
3. **Do not trust settings as a substitute.** PHP's own people put it bluntly during the release week: configuration tweaks will not save you. A WAF rule, including Cloudflare's emergency rules, is a stopgap that buys hours. Setting `fatal_error_backtraces = 0` blocks one confirmed path if you genuinely cannot update at once. None of that is a fix.
4. **If you were exposed before the patch, look backwards, not just forwards.** Check for PHP workers spawning shells, interpreters, or download tools, and for unexpected processes or files from the October 17–21 window. If you cannot be sure a server was clean during that window, rotate the secrets that server held. A patch closes the door; it does not evict anyone who already walked through it.
5. **For the October 23 issue, check one thing in your code.** Search for `ini_set` calls that touch `session.serialize_handler`. If you find none, this advisory is not your emergency. If you find one, disable upload progress until the regular fix lands.

The deeper lesson is less technical and more uncomfortable. Most teams have a process for updating their dependencies and almost no process for updating their runtime. Frameworks get Dependabot alerts and changelogs people read. PHP itself, the thing underneath the framework, gets updated when the host does it, or when a container base image is rebuilt, or never. PHP2Shell is what happens when that gap meets a flaw that needs no application bug at all.

Your code can be secure. Your runtime may not be. Until you can answer, without guessing, which PHP version every one of your servers is actually running right now, that sentence applies to you.

---

*Sources: [watchTowr PHP2Shell FAQ](https://watchtowr.com/intelligence/php-cve-2026-109618-faq/) (exploitation timeline and fixed versions); [The Hacker News, PHP emergency patches](https://thehackernews.com/2026/10/php-issues-emergency-patches-for-two.html) (disclosure timeline and researchers); [PHP2Shell patched versions and guide](https://cve.tools/blog/php2shell-cve-2026-109618-cve-2026-109619) (fixed releases, backports, and stopgap settings); [Amazon honeypot attempt, October 17](https://www.siliconreport.com/hackers-attempted-to-exploit-php-flaws-before-patches) (pre-disclosure exploitation attempt); [PHP October 23 session upload progress advisory](https://www.analyticsinsight.net/news/new-php-security-flaw-raises-concerns-after-emergency-patches) (CVE-2026-115560 conditions and mitigation).*
