---
title: "Installed but Never Imported — and It Still Stole Your Keys: Hunting the LiteLLM .pth Stealer"
date: 2026-10-30
tags: [supply-chain, python-security, tools, incident-response]
excerpt: "On October 21, 2026, a poisoned LiteLLM 1.107.0 release hid a credential stealer in a Python startup file — so it ran in every Python process on the host, even ones that never touched LiteLLM. Here is how to check whether it touched you, and how to clean it up properly."
cover: /assets/covers/litellm-pth-stealer-audit.jpg
---

There is a comforting assumption every Python developer carries around: installing a package is harmless until you import it. You can `pip install` something, poke at it later, remove it if you change your mind — and nothing runs in between. On October 21, 2026, a poisoned release of LiteLLM proved that assumption wrong in the worst possible way.

That morning, a malicious version of `litellm` 1.107.0 appeared on [[PyPI]] — all seven wheels, covering Linux, macOS, and Windows — and in LiteLLM container images on Docker Hub and GHCR under the `v1.107.0`, `latest`, `main-latest`, and `main-stable` tags. It carried a credential stealer that did not wait for anyone to import LiteLLM. It ran the moment any Python process started on the host. "We only installed it, we never used it" is not a defense here. If the poisoned release landed in your environment, that sentence is exactly what the attacker was counting on.

## What actually happened

LiteLLM is a popular open-source gateway that lets applications talk to many large-language-model providers through one interface — which means the machines running it tend to hold exactly the secrets an attacker wants: cloud credentials and AI provider API keys. The compromise was not in LiteLLM's public source code. The project's own advisory notes that the official v1.107.0 git tag does not contain the malicious files; the poisoned wheels were built from an attacker-controlled repository. This was a [[supply chain attack]] against the release pipeline, not a malicious commit anyone could have spotted in code review.

How the attacker got into the pipeline is a lesson of its own. Analyses of the incident report that a master key had been exposed in a public repository on May 27, 2026, and that attackers tested it on October 10 before using it to publish the poisoned release on October 21. A secret left in a public place for nearly five months, then weaponized in a single morning. The window of exposure on [[PyPI]] itself was short — the wheels went up between 11:39 and 11:40 UTC and PyPI removed the release by 13:23 UTC, under two hours later — but two hours is an eternity for automated installers. CI pipelines, Docker builds, and dependency bots do not sleep, and the floating container tags carried the malicious image for longer, between 11:46 and 14:20 UTC.

And this was LiteLLM's second time. In March 2026, a group tracked as TeamPCP compromised `litellm` 1.82.7 and 1.82.8 using a [[PyPI]] token stolen through Trivy, with a similar `.pth` technique. Different actor, same weak point: the release pipeline is part of the attack surface, and it keeps proving it.

## The trick: a startup file, not an import

The mechanism is what makes this incident worth studying, because it generalizes far beyond LiteLLM. The poisoned wheels dropped three files into `site-packages`: `cook.pth`, `cook.py`, and `sitecustomize.py`. The first one is the key.

Python processes every `.pth` file in `site-packages` at interpreter startup, and any line beginning with `import` is executed. That is a documented feature, meant for adding directories to the module search path — but it means a `.pth` file is a code-execution primitive that fires before your code, before your application, before anything you wrote. `cook.pth` imported `cook.py`, so the stealer ran inside every Python process on the host: your app, your test suite, your IDE's language server, your CI jobs, even `pip` itself.

That last detail matters for incident response, and it is the first trap in this story: running `pip show litellm` in a suspect environment to check the version would itself trigger the stealer one more time. On a machine you suspect, check the files from the shell first, without starting Python at all.

What `cook.py` stole reads like an inventory of everything a modern engineering host holds: cloud credentials for AWS, GCP, and Azure, AI provider API keys, SSH and GPG keys, CI/CD secrets, browser passwords, process environment variables, and — where the LiteLLM proxy's `DATABASE_URL` was set — rows from the proxy's credential tables, including the provider keys stored there. The loot was encrypted and sent to `www.litellm.dev`, a look-alike domain unrelated to the official `litellm.ai`. Treat any secret readable by an affected host as exposed, not just the ones you can prove were taken.

The second payload, `sitecustomize.py`, was the persistence layer: it started a background daemon that, every hour, read a server address from a file hosted on GitHub, re-ran the stealer, and downloaded and executed further code. The GitHub account behind it returned a 404 by 13:40 UTC, roughly two hours after the release, so the loader lost its command server quickly — but any host that ran the daemon before that point could have received second-stage code whose address researchers could no longer recover.

## The audit: five checks, in order

If you run Python anywhere — and especially if you run LiteLLM, an AI gateway, or any container built from a floating tag — work through these in order. Do the file checks before you run any Python tooling in the suspect environment.

**1. Check for the poisoned release in your lockfiles and caches.** Search dependency lockfiles, build logs, and caches for `litellm==1.107.0`. The clean versions are 1.106.2 and the 1.107.0 release candidates (1.107.0rc1 and 1.107.0rc2). A lockfile pinning 1.107.0, or a cache entry for it, means the environment pulled the bad release — even if it was later removed from [[PyPI]].

**2. Look for the implant files on disk.** From the shell, not through Python:

```bash
find / \( -name 'litellm-1.107.0.dist-info' -o -name 'cook.pth' \
  -o -name 'cook.py' -o -name 'sitecustomize.py' \) 2>/dev/null
ls -la /tmp/.pc_once_* /tmp/remote_code_loader.lock 2>/dev/null
```

Finding `cook.pth` or the `litellm-1.107.0.dist-info` directory means the bad release was installed. Note that `sitecustomize.py` can be legitimate in some Python builds, so treat it as suspicious mainly when it sits next to `cook.pth`.

**3. Check the marker file — and understand what it does not prove.** The stealer wrote `/tmp/.pc_once_72129118c59f5636c0bb` only after the stolen data had been sent, so finding it confirms exfiltration happened. Not finding it proves nothing: a container restart or a `/tmp` cleanup removes it, and the theft may still have happened.

**4. Check container images by digest, not by tag.** Tags move; digests do not. Compare the images you actually run:

```bash
docker images --digests | grep -i -E 'berriai|litellm'
```

In Kubernetes, check the image ID in each pod's container status — that shows the digest actually running, which is the only one that matters. Any image pulled while the floating tags served the poisoned build must be treated as compromised.

**5. Check egress and cloud logs.** Look for outbound connections to `litellm.dev` around the install window, and for cloud activity — such as `GetCallerIdentity` calls from roles that were present on affected hosts — coming from outside your network. If a role was usable from the host, assume it was used.

## The cleanup: uninstalling is not enough

This is the second trap in the story, and the one most teams would fall into. Uninstalling `litellm` 1.107.0 does not remove the implant, because `cook.pth`, `cook.py`, and `sitecustomize.py` sit at the `site-packages` root, outside the package directory — they survive package removal, and a running loader keeps running. A proper cleanup has four steps:

1. **Remove the implant files by hand** from every affected environment, and kill any running loader process.
2. **Rebuild, don't patch.** Rebuild container images from clean bases and redeploy; do not try to surgically clean a running container and call it trusted.
3. **Rotate everything the host could read.** Cloud roles, every provider key in the proxy database, master and virtual keys, the `DATABASE_URL` password, and every secret in any process's environment. Rotation is the remediation — the file removal is just hygiene.
4. **Pin and verify going forward.** Pin `litellm` to a clean version by hash, pin container images by digest instead of floating tags, and require hash-verified installs (`pip install --require-hashes`) for production builds. A floating tag is an instruction to accept whatever the publisher serves next — and on October 21, that was malware.

## The lesson that outlives this incident

Strip away the LiteLLM specifics and the shape of the attack is uncomfortably general. The release pipeline of a trusted open-source project was compromised through a long-exposed secret. The payload used a legitimate interpreter feature, not a vulnerability, so no scanner flagging known CVEs would have caught it. It ran without an import, so "we never used it" meant nothing. It persisted outside the package directory, so uninstalling meant nothing. And it targeted exactly the class of host — an AI gateway — that concentrates the most valuable credentials in one place.

That is why the audit above is worth running even if you are fairly sure you were not affected. The checks are cheap: a lockfile grep, a filesystem search, a digest comparison. And they teach a habit that matters beyond this week: treat your dependency tree and your container tags as live trust decisions, not as background plumbing. Every install is a small act of faith in someone else's release pipeline. On October 21, that faith was misplaced for under two hours — and that was enough.

Check your environments. Rotate what needs rotating. And the next time someone says a package is safe because it was never imported, you will know better.

---

*Sources: [Compromised LiteLLM 1.107.0 on PyPI Installs a Credential Stealer and Backdoor (SafeDep, October 21, 2026)](https://safedep.io/litellm-pypi-compromise-credential-stealer-backdoor/); [LiteLLM Supply Chain Attack: IOCs and Runbook (Kodem)](https://www.kodemsecurity.com/resources/litellm-supply-chain-attack-litellm-1-107-0-affected-versions-iocs-and-first-hour-response-runbook); [LiteLLM 1.107.0 Backdoored: How the .pth Key Stealer Worked (PlayCISO)](https://playciso.com/blog/litellm-1-107-0-supply-chain-compromise-credential-stealer); [LiteLLM 1.107.0 Compromised: Check, Clean Up, Rotate Keys (Tecyfy)](https://tecyfy.com/blog/litellm-compromised-check-and-clean); [Black October: How a Week of Cybersecurity Failures Exposed the Limits of Traditional Patching (October 29, 2026)](https://beatsinbrief.com/2026/10/29/black-october-2026-ai-patch-window-php2shell/).*
