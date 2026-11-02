---
title: "Patched on Paper, Vulnerable in Production: A Hands-On Node2Shell Audit"
date: 2026-11-02
tags: [hands-on, nodejs, vulnerability, patching]
excerpt: "Node.js fixed Node2Shell on October 21, but the version string lies, the runtime hides in containers, and npm update does nothing. This audit walks you through proving — not assuming — that every Node.js in your estate is actually patched."
cover: /assets/covers/node2shell-brotli-patch-audit.jpg
---

There is a particular kind of false comfort that only appears after a patch Tuesday done right. You read the advisory, you ran the upgrade, the dashboard went green — and somewhere in a container image nobody rebuilt, the old runtime is still serving traffic. [[CVE]]-2026-111497, nicknamed Node2Shell, is built to punish exactly that kind of confidence. The fix shipped on October 21, 2026. The audit that proves you actually applied it is the subject of this article.

Node2Shell is an [[out-of-bounds write]] in the [[Brotli]] decoder bundled with [[Node.js]]. Brotli is a compression format that browsers and servers use alongside gzip to shrink HTTP traffic, and Node.js ships a Brotli decoder inside `node:zlib`. When the decoder meets a crafted stream with an invalid block-type switch, it mishandles the error and keeps writing past the end of a small internal buffer. That memory corruption can crash the process, leak memory contents, or — as Imperva's Red Team demonstrated on October 22 — run attacker-supplied code. Their proof of concept ran code inside the official [[Node.js]] 24.22.0 Linux arm64 image with no debugger and no custom build, through both a compressed request body and a compressed response. The same input was rejected by the fixed release, 24.22.1. Google's CNA rates the flaw CVSS 9.2; Node.js itself rates it High. On October 27, [[CISA]] added it to its [[KEV]] catalog, with a federal remediation deadline of November 10, 2026 — the formal signal that attackers are already using it. Threat-intel firm ELLIO reported a crafted exploit reaching its sensors on October 26, and scanners are already probing for hosts that decompress Brotli bodies.

## Why this reaches you even if you never touch compression

Most teams that run Node.js have never written a line of Brotli code, and that is precisely the point. The decoder is reached through three paths you probably never chose deliberately.

First, incoming requests. Express 5 and body-parser 2 decompress request bodies sent with `Content-Encoding: br` by default, because body-parser's `inflate` option is on unless you turn it off. An app with a plain `app.use(express.json())` can therefore be reached by a single crafted request, before any login, before any of your application code runs. Koa and NestJS applications inherit the same behavior through their parsers.

Second, outgoing requests. Node's built-in `fetch()` asks for and decompresses Brotli responses on its own. Any server your code calls — a webhook you call back, a link previewer, a scraper, an AI agent fetching a user-supplied URL — can hand your decoder a malicious stream. The attacker does not need to reach your server at all; they just need to control a server your server talks to.

Third, direct calls. Any code that calls the Brotli functions in `node:zlib` on outside data is exposed the same way. A plain Node.js HTTP server that never decompresses anything is not exposed — decoding has to happen for the flaw to trigger — but the moment middleware or a library does it for you, you are in scope.

The blast radius does not stop at Node.js. The bug lives in Google's Brotli C library, so it also affects Bun (fixed in 1.4.4), the Python packages Brotli (1.2.1) and brotlicffi (1.2.1.0), and .NET, for which Microsoft shipped out-of-band updates on October 25. But this audit focuses on Node.js, because that is where the version trap lives.

## The trap: the version string lies

Here is the detail that makes this audit worth doing instead of trusting a dashboard. Node.js cherry-picked the Brotli fix without changing the bundled Brotli version string. So `process.versions.brotli` reports `1.2.0` on patched and unpatched builds alike, and any check reading the Brotli version will call a vulnerable server patched. The only reliable check is the Node.js version itself: 22.23.4, 24.22.1, or 26.12.1 — or a newer release in a supported line. And `npm update` does nothing here, because the flaw is in the runtime, not in a package. Node.js 20.x and older lines get no fix at all; they are end of life, and the only move is migration to a supported line.

Worse, the runtime hides: a `node -v` on your laptop says nothing about the Node binary inside a container image, a CI runner, or a tool that ships its own runtime.

## Exercise 1: inventory every Node.js, not just yours

Start with the machines you control, then move to the artifacts you ship. On any host, list both installed runtimes and running processes:

```bash
# Installed runtimes: version managers, system packages, containers
which -a node; ls ~/.nvm/versions/node 2>/dev/null; ls /usr/local/bin/node* 2>/dev/null
ps aux | grep -E "node|bun" | grep -v grep
node -v  # compare against 22.23.4, 24.22.1, 26.12.1
```

Then audit the images, because that is where the old runtime survives an upgrade. Search every Dockerfile and CI definition for its base image, and check what it actually contains:

```bash
grep -rn "FROM node:" --include="Dockerfile*" .
docker run --rm node:24.22.0 node -v  # example: proves the tag, not your fleet
```

A base-image tag not re-pulled since October 21 is suspect, even if your application code changed yesterday. Rebuild on a fixed tag, redeploy, and restart every process on the old runtime — a patched binary on disk protects nothing while the old process keeps running.

## Exercise 2: find the exposure paths in your code

Knowing your version is only half the audit. A patched runtime is safe regardless, but an unpatched one is dangerous in proportion to how much untrusted Brotli it decodes. Map that surface with two searches over your codebase:

```bash
# Request-body decompression: Express 5 / body-parser inflate defaults
grep -rn "express.json\|express.urlencoded\|express.text\|express.raw\|bodyParser" --include="*.js" --include="*.ts" .

# Outbound decoding: fetch() and direct zlib use on outside data
grep -rn "fetch(\|brotliDecompress\|createBrotliDecompress" --include="*.js" --include="*.ts" . | head -50
```

Every hit on the first search is a route reachable by a crafted request body. Every hit on the second is a place where a hostile server can reach your decoder. Prioritize internet-facing services first, then anything that fetches user-supplied URLs — that second category is the one teams most often forget, because the attacker never touches their server directly.

## Exercise 3: hunt for the probing that already happened

Exploitation leaves a distinctive shape in logs, and scanners have been active since late October. Look for three signals in your reverse-proxy and application logs:

1. **POST requests with `Content-Encoding: br`** to APIs that never legitimately receive compressed bodies. Most JSON APIs have no reason to accept Brotli request bodies at all.
2. **Unusually large compressed bodies**, or bursts of compressed requests from a single source — the public exploit traffic observed so far included a request around 23 MB aimed at Node.js 24.22.0.
3. **Unexplained process crashes or restarts** in Node.js services, especially ones correlating with compressed requests. A crash is the most likely first impact of this flaw, and it is also a signal in its own right: treat a decoder crash as a possible attack, not a flaky deploy, and check whether core dumps captured process memory before they are rotated away.

None of these proves compromise alone. Together, they tell you whether anyone has been knocking.

## Exercise 4: patch properly, then layer the fallback

The fix, in priority order:

1. **Upgrade the runtime everywhere it runs** — 22.23.4, 24.22.1, or 26.12.1 or newer in your line — including container images, CI runners, and bundled runtimes. Restart or redeploy every process afterward.
2. **Migrate end-of-life lines.** Node.js 20.x and older receive no fix. Moving to 22 or 24 LTS is part of this patch, not a separate project.
3. **Fix the siblings.** Bun to 1.4.4, Python Brotli to 1.2.1, brotlicffi to 1.2.1.0, and .NET to Microsoft's October 25 out-of-band releases, wherever those runtimes exist in your estate.
4. **Only then, layer interim mitigations for anything you cannot patch yet.** Set `inflate: false` on Express 5 and body-parser 2 parsers, or reject `Content-Encoding: br` at your [[reverse proxy]]. Be honest about what these buy you: they close the inbound path only, they do nothing for outbound `fetch()` decoding, and they can break legitimate compressed traffic. They are a tourniquet, not a cure — and the advisory lists no workaround inside Node.js itself.

Close the loop by re-running Exercise 1 after the upgrade and recording the result. An audit that nobody re-runs after patching is just a report; the second run is what turns it into evidence.

## The lesson worth keeping

Node2Shell is not the most exotic vulnerability of October 2026, and that is why it is a good teacher. It required no zero-day in your code, no misconfiguration, no badly chosen dependency — only a popular runtime, a library you never thought about decompressing data you never inspected, and an inventory trusting a version string that does not change when the bug is fixed. The next flaw in this family will hide in the same places: a bundled library, a transitive decoder, a base image nobody re-pulled.

Patch the runtime. Rebuild the image. Restart the process. Then check — with the version that actually tells the truth — that you did.

---

*Sources: [Node2Shell: From Brotli Data to Remote Code Execution (Imperva, October 2026)](https://www.imperva.com/blog/node2shell-from-brotli-data-to-remote-code-execution/); [Researchers Demonstrate Node2Shell RCE Exploit on Node.js Build (The Hacker News, October 2026)](https://thehackernews.com/2026/10/researchers-demonstrate-node2shell-rce.html); [Node2Shell puts Microsoft and Node.js on Brotli patch duty (CSO Online, October 2026)](https://www.csoonline.com/article/4241027/node2shell-puts-microsoft-and-node-js-on-brotli-patch-duty.html); [Node2Shell Vulnerability Actively Exploited in the Wild, CISA Warns (CybersecurityNews, October 2026)](https://cybersecuritynews.com/node2shell-vulnerability/); [Node2Shell (CVE-2026-111497): the Brotli flaw reaching Node.js, Python and beyond (Kage Security Lab, October 2026)](https://kagesecuritylab.com/intel/node2shell-cve-2026-111497/).*
