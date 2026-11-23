---
title: "phpAfterShell: Audit Your PHP Fleet Before a Session Becomes a Shell"
date: 2026-11-23
tags: [hands-on, php, vulnerability, patching]
excerpt: "On 19 November 2026, PHP shipped fixes for seven critical flaws rated 9.2 — and two of them turn the language's own session handling into remote code execution. If you patched for PHP2Shell in October, you are still exposed. Here is a hands-on audit you can run today."
cover: /assets/covers/phpaftershell-php-fleet-audit.jpg
---

PHP runs a staggering share of the web — WordPress, Laravel, Drupal, Magento, and millions of custom apps in between. On 19 November 2026, the PHP team released security updates for every supported branch — 8.2.36, 8.3.37, 8.4.28, and 8.5.13 — closing 17 advisories covering 18 [[CVE]] identifiers. Seven of them are rated Critical, each scoring 9.2 under CVSS 4.0. The headline pair, nicknamed [[phpAfterShell]], hides in the most boring part of the language: how it stores your login session.

Here is the part that should make you stop scrolling. The October PHP2Shell fixes do **not** contain the phpAfterShell fixes. If your team patched in October, ticked the box, and moved on, your servers are still vulnerable to these two. And because the flaws live in PHP's default session handling — not in some exotic extension — the blast radius is every PHP app that lets users log in and upload files. Which is to say, nearly all of them.

This article is a hands-on audit. No theory for its own sake: every section below ends in a command you can run or a setting you can check.

## What phpAfterShell actually is

The nickname covers two vulnerabilities in PHP's `ext-session` extension, both rated CVSS 4.0 9.2 and both capable of unauthenticated [[remote code execution]]:

**[[CVE]]-2026-115560 — the session serializer mismatch.** PHP's session upload-progress feature records the progress of a file upload inside the user's session, before any of your application code runs. It builds the session key by appending attacker-controlled values — such as the uploaded file's name — to a fixed prefix. The problem is a format disagreement: upload progress stores that key with one serializer (`php_binary` or `php_serialize`), while another process may read the same session with the incompatible `php` serializer. The `php` serializer uses the pipe character (`|`) to separate a session key from its value, so a `|` smuggled inside the attacker-controlled key makes part of the key get read back as serialized object data. That is [[object injection]] by way of a filename — and with a suitable [[gadget chain]] in the application, it becomes code execution. The upload-progress feature dates back to PHP 5.4.0.

**[[CVE]]-2026-126714 — the partially overwritten session file.** PHP's default `files` session handler writes updated session data into the existing session file without truncating it first. If the write is interrupted, the file ends up holding a mix of new data and a trailing chunk of the old session. When PHP later reads and unserializes that mixture, bytes that were once harmless string content can be reinterpreted as serialized objects — again, [[object injection]], again potentially [[remote code execution]] if the application has a gadget chain. This code has been present since PHP 4.1.0.

A third flaw in the same release deserves a line of its own: **[[CVE]]-2026-129289**, a [[PHP-FPM]] request-smuggling bug. When a front end reuses FastCGI connections and an application does not read the whole request body, leftover bytes from one request can be processed as the start of the next one — letting an unauthenticated attacker bypass front-end routing and run PHP code.

As of 20 November, neither flaw had been seen exploited in the wild, and neither was listed in CISA's [[Known Exploited Vulnerabilities]] catalog. That is the good news. The bad news is that the same was true of Java4Shell for about a day.

## Step 1: find every PHP you run

The CLI binary lies. `php -v` tells you about the command-line interpreter, not the workers serving your website. Inventory all of them:

```bash
# every PHP binary on the box, with versions
for bin in /usr/bin/php* /usr/local/bin/php* /opt/*/bin/php; do
  [ -x "$bin" ] && echo "$bin: $($bin -v 2>/dev/null | head -1)"
done

# every running PHP-FPM worker and its version
ps aux | grep -E 'php-fpm: (pool|master)' | grep -v grep
php-fpm -v 2>/dev/null; php-fpm8.4 -v 2>/dev/null; php-fpm8.3 -v 2>/dev/null
```

Then check the containers and the appliances. PHP hides inside Docker images, third-party products, and vendor appliances that bundle their own runtime — those do not appear in your package manager, and updating the system PHP does not fix them. Vendor appliances need the vendor's patch.

| Branch | Vulnerable | Fixed in |
| --- | --- | --- |
| PHP 8.5 | 8.5.0 – 8.5.12 | **8.5.13** |
| PHP 8.4 | 8.4.0 – 8.4.27 | **8.4.28** |
| PHP 8.3 | 8.3.0 – 8.3.36 | **8.3.37** |
| PHP 8.2 | 8.2.0 – 8.2.35 | **8.2.36** |

PHP 8.6.0, released the same day, also includes the fixes. PHP 8.1 and older receive no patches at all — they are end of life, and PHP 8.2 itself reaches end of life on 31 December 2026, so this is likely one of its last security releases. If you are still on 8.1, the fix is a migration, not a patch.

## Step 2: check the three session settings that matter

Run these against the configuration that actually serves web requests — the FPM pool or `phpinfo()` on a throwaway page you delete afterwards, not the CLI `php.ini`, which often differs:

```bash
php -i | grep -iE 'session\.(upload_progress\.enabled|serialize_handler|save_handler)'
```

What you are looking for:

- **`session.upload_progress.enabled`** — the switch for CVE-2026-115560. If your app does not show upload progress bars, it should be `0`. Note the trap: the fixed releases now ship with upload progress **disabled by default**, but a `php.ini`, distribution package, or hosting panel that turns it on keeps it on. Verify the effective value; do not assume the upgrade flipped it.
- **`session.serialize_handler`** — the mismatch only happens when different processes read the same session data with different serializers. Every FPM pool, virtual host, application, and CLI job that touches shared session storage must agree on one value. The default `php` is fine, as long as it is the *same* everywhere.
- **`session.save_handler`** — `files` is the affected handler for CVE-2026-126714, and it is also the default. Switching to Redis or Memcached for sessions is a legitimate hardening step, but it is a migration, not an emergency patch: patch first.

## Step 3: check PHP-FPM connection reuse

CVE-2026-129289 needs a front end that reuses FastCGI connections. Check yours:

```bash
# nginx: connection reuse to PHP-FPM
grep -rn 'fastcgi_keep_conn' /etc/nginx/ 2>/dev/null

# Apache: connection reuse to PHP-FPM
grep -rn 'enablereuse' /etc/apache2/ /etc/httpd/ 2>/dev/null
```

If either is enabled, that configuration is part of the exposure. Disabling reuse is a valid stopgap while you patch; it is not a substitute for the patch.

## Step 4: patch, restart, and verify the workers — not the binary

Upgrade to the fixed release for your branch, then restart or reload the PHP services. Then verify that the **web-facing workers** are running the new version, because the CLI binary and the FPM workers can disagree after an upgrade:

```bash
sudo systemctl restart php8.4-fpm   # adjust for your branch
php -v                                # the CLI — necessary, not sufficient

# the workers: check the version your web server actually serves
curl -s -D - https://your-site.example.com/ -o /dev/null | grep -i 'x-powered-by'
```

A `phpinfo()` page on a staging host shows the running version directly — create it, read it, delete it. If the header still shows the old version, the old workers are still alive, and the patch has not taken effect where it counts.

## Step 5: the stopgap, if you cannot patch today

If patching has to wait, reduce the exposed surface now — and treat every measure below as temporary, not as a fix:

```ini
; php.ini — or the FPM pool config, where it cannot be overridden
session.upload_progress.enabled = 0
```

```ini
; PHP-FPM pool config
php_admin_flag[session.upload_progress.enabled] = off
```

Set it in `php.ini` or the pool configuration, before any request input is processed — an application-level `ini_set()` call is too late, because upload progress runs during request parsing, before your code executes. Then restart the workers. This closes the easy path for CVE-2026-115560, but it does nothing for CVE-2026-126714: the files-handler flaw does not depend on upload progress at all. If your application genuinely needs upload progress, keep it enabled only where it is used, and make sure every process sharing that session storage uses the same serializer.

After changing serialization formats, consider expiring or migrating existing session data — records written under the old format can still be read back under the new one.

## Step 6: look for signs someone already tried

Patching proves nothing about the past. The NetSPI guidance is blunt on this point: if an unpatched PHP installation was reachable from the internet, treat it as potentially compromised pending investigation. Check for:

- Unusual PHP worker crashes, fatal errors, or unexpected child processes in your FPM and web server logs.
- Session-related errors, or bursts of failed unserialization warnings, around file-upload endpoints.
- Unexplained application behaviour — new files, changed files, or outbound connections from the PHP worker that do not match normal traffic.

A failed exploitation attempt can crash a worker; a successful one rarely announces itself. If anything looks off, investigate before you call the incident closed.

## The lesson that outlives the patch

phpAfterShell is not a story about a weird edge case. It is a story about a feature most developers have never consciously enabled — upload progress — sitting on top of a default — file-based sessions — in a language that powers a huge fraction of the web. The attacker's entry point is a filename in a multipart upload. The victim's defence is a version number.

That is why the audit above is ordered the way it is: inventory first, because you cannot patch a PHP you do not know exists; settings second, because the defaults are the exposure; patch third; and only then the forensics. The October PHP2Shell round taught the same lesson, and the teams that internalised it already had their inventories ready when November's release landed. The ones that did not are now doing the same work under a 9.2.

Run the six steps today. It takes less than an hour — and unlike the session files at the centre of this bug, what you find will not be overwritten by whatever comes next.
