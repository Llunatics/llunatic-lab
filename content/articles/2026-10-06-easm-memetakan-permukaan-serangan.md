---
title: "EASM: Mapping Your Attack Surface Before Attackers Do"
date: 2026-10-06
tags: [easm, attack-surface, blue-team]
excerpt: "Most organizations aren't breached through the front door, but through assets they didn't even know existed. EASM is the discipline of finding them first."
cover: /assets/covers/easm-attack-surface.jpg
---

Imagine you're hired to guard a building. You lock the front door, install CCTV, hire guards. But the building has a back door missing from the blueprints, a warehouse window that's never locked, and a service corridor nobody has used in years. Attackers won't knock on the front door — they'll slip in through gaps you didn't even know existed.

That's the most honest picture of most organizations' cybersecurity today. And the discipline born to answer it is called [[EASM]].

## The problem: you can't protect what you don't know

Every modern company has a digital footprint far larger than it realizes: [[subdomain]]s created for a project three years ago and never shut down, cloud storage buckets accidentally left public, dev servers forgotten unpatched, SSL certificates for services nobody uses anymore, even employee accounts on third-party services.

All of it is part of the [[attack surface]] — and attackers hold one fundamental advantage: they only need to find **one** gap, while defenders must close **every** one.

That's why reactive security ("wait for an incident, then act") always loses. [[EASM]] flips the logic: **think like an attacker, but move first.**

## What does EASM actually do?

Simply put, [[EASM]] is the continuous process of discovering, inventorying, and monitoring every internet-exposed digital asset of an organization — from an outsider's perspective.

There are four core stages:

**1. Discovery — find everything.**
This is the foundation. The techniques mirror what attackers use during reconnaissance: [[subdomain]] enumeration, SSL certificate scanning (every certificate logs domain names — an incredible source of intel), special-purpose search engines like [[Shodan]] and [[Censys]], and classic [[OSINT]] techniques. Tools like [[Amass]] automate most of this work.

**2. Inventory — record and classify.**
Discovered assets get logged: what service is running, what software version, who owns it internally, how critical it is. Without a tidy inventory, discovery findings are just a long list nobody can act on.

**3. Assessment — evaluate the risk.**
Each asset gets scored: any known [[vulnerability]]s? Outdated services? Unpatched critical [[CVE]]s? This stage usually connects to [[threat intelligence]] so the risk assessment tracks threats that are actually active in the wild.

**4. Monitoring — watch continuously.**
The attack surface never sits still. Every new deploy, every cloud service trial, every company acquisition expands it. Good [[EASM]] runs continuously — not as a once-a-year audit.

## Why this matters to everyone, not just corporations

The same principle scales down. Got a personal blog? Check for unused subdomains. Got a VPS? Make sure no management ports are wide open to the internet. The principle is one: **shrink what's visible from the outside, and know exactly what remains visible.**

Even for individuals, the [[EASM]] mindset helps: forgotten old accounts, services still connected to your main email, apps still holding access to your Google account — all of it is personal "attack surface".

## Where to start?

You don't need an enterprise budget to start thinking in [[EASM]] terms. The simplest steps anyone can take today:

- Find out what subdomains your domain has (plenty of free tools for this).
- Check the SSL certificates ever issued for your domain — there are often surprises.
- Search your name or organization on [[Shodan]] — see what's visible from the outside.
- List it all, then close or secure whatever doesn't need to be exposed.

Attackers do exactly this every day, automatically, at massive scale. The only question is: who finds your assets first — you, or them?

---

*This article opens the attack surface series on llunatic-lab. Next up: hands-on subdomain enumeration from zero, with free tools.*
