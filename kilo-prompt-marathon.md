You are operating as a senior full-stack/frontend engineer performing a comprehensive audit remediation, performance optimization, and visual polish pass on **llunatic-lab** (`https://github.com/Llunatics/llunatic-lab`, live at `https://lab.llunaticsys.web.id`).

## Working Environment & Strict Rules

1. **Repository Path**: `/home/kou/Development/llunatic-lab` (currently on the latest `main` branch).
2. **Branching Policy (MANDATORY)**:
   - Immediately create and switch to a new working branch named `overhaul/marathon-2026-11-09` from `main`:
     `git checkout -b overhaul/marathon-2026-11-09`
   - Commit all work exclusively to `overhaul/marathon-2026-11-09`.
   - **DO NOT** merge into `main`.
   - **DO NOT** deploy to production or trigger manual Vercel deployments.
3. **Verify Before Fixing**:
   - Before modifying any file for a finding listed below, inspect the actual code in the repository to confirm the diagnosis. If your local inspection reveals a slightly different root cause or additional context (for example, regarding binary cover assets in git), document the discrepancy clearly in your final report.
4. **Editorial Content Rule**:
   - **DO NOT** alter the editorial prose or wording of any article in `content/articles/*.md`. Only technical fixes that are strictly necessary (or handling syntax in `scripts/build.py` so existing markdown renders properly without touching the articles) are permitted. If any markdown file in `content/articles/` is touched for a proven technical reason, explicitly mark and justify it in your final report. (Note: all markdown rendering issues identified below can and should be fixed in `scripts/build.py` and `content/glossary.json` without modifying `content/articles/*.md` at all!)
5. **Visual Identity Rule**:
   - Preserve the existing noir-editorial visual identity (dark-first `#0a0a0c`, warm-paper light mode `#f5f3ec`, lime acid accent `#bef264` / `#4d7c0f`, Fraunces + Inter + JetBrains Mono typography, film grain overlay, editorial numbering). Do not redesign the site; polish and fix what is broken or rough.

---

## Detailed Audit Findings & Required Remediations

Verify each item against the codebase and implement the fixes cleanly:

### 1. Missing Cover Assets & Raw Media-Generation JSON Leaks (`assets/covers/`, `scripts/build.py`, `.gitignore`, `PIPELINE.md`)
- **Diagnosis**:
  - The 3 newest article pairs (`2026-11-04-when-the-editor-is-the-exploit`, `2026-11-06-cloudflare-security-audit-skill`, `2026-11-08-smbc-consumer-finance-breach`) reference `/assets/covers/when-the-editor-is-the-exploit.jpg`, `/assets/covers/cloudflare-security-audit-skill.jpg`, and `/assets/covers/smbc-consumer-finance-breach.jpg` in their frontmatter.
  - However, in `assets/covers/` (and copied into `public/assets/covers/`), the automated pipeline saved raw tool response files instead of the `.jpg` images:
    - `assets/covers/media-generation-when-the-editor-is-the-exploit-1793750235.json`
    - `assets/covers/media-generation-cloudflare-security-audit-skill-1793923038.json`
    - `assets/covers/media-generation-smbc-consumer-finance-breach-1794095837.json`
  - Because `scripts/build.py` runs `shutil.copytree(ASSETS / "covers", PUBLIC / "assets" / "covers")`, those raw `.json` files are published to production while the 3 `.jpg` covers 404 on the homepage, archive, tag pages, article pages, and OpenGraph `og:image`.
- **Action**:
  1. Check `assets/covers/` in your local clone. Inspect the 3 `media-generation-*.json` files.
  2. Attempt to download the image URLs from inside each of the 3 JSON files (`attachments[0].url`) and convert/save them as high-quality 21:9 JPEGs at:
     - `assets/covers/when-the-editor-is-the-exploit.jpg`
     - `assets/covers/cloudflare-security-audit-skill.jpg`
     - `assets/covers/smbc-consumer-finance-breach.jpg`
     If the signed CDN URLs in those JSON files have expired or fail to download, generate deterministic, high-resolution (e.g. `1470x630`, 21:9 aspect ratio) noir-editorial abstract cybersecurity cover illustrations (dark `#0a0a0c` background, subtle geometric/network/terminal motif, `#bef264` lime accents, zero text/letters/numbers) using Python/Pillow or SVG-to-raster/stdlib tools so that every single article's `cover` file exists as a valid `.jpg` in `assets/covers/`.
  3. Also verify that all other 18 `.jpg` cover files referenced in `content/articles/*.md` exist in `assets/covers/` and are non-empty valid images.
  4. Remove the 3 `media-generation-*.json` files from `assets/covers/` and add `assets/covers/*.json` to `.gitignore`.
  5. In `scripts/build.py`, when copying `assets/covers` to `public/assets/covers`, only copy valid image files (`.jpg`, `.jpeg`, `.png`, `.webp`, `.avif`, `.svg`) — never copy `.json` or hidden/temp files. Additionally, make `build.py` emit a clear warning (or fail if strict) if any article references a `cover` path that does not exist in `PUBLIC`.
  6. In `PIPELINE.md`, update Step 4 (`Generate the cover`) to explicitly instruct the cron worker that if `media.generate_image` writes a `media-generation-*.json` file instead of `<slug>.jpg`, it must download/convert the attachment URL to `assets/covers/<slug>.jpg` and delete the `.json` file before running `build.py`. Also update stale references in `PIPELINE.md` (such as `/home/hatch/workspace/llunatic-lab` or `https://llunatic-lab.vercel.app`) to match the canonical site `https://lab.llunaticsys.web.id`.

### 2. Broken Regression Test Suite (`scripts/test_build.py`)
- **Diagnosis**:
  - `python3 scripts/test_build.py` currently fails at line 67 (`AssertionError: GAGAL: search.json 9 artikel EN, url valid`) and line 76 (`rss.count("<item>") == 9`) because `9` was hardcoded when the repository had only 9 articles (it now has 21 slugs / 42 markdown files).
  - Line 85 hardcodes `"tidak ada id duplikat di 18 halaman artikel"` and only loops over `(pub / "artikel").rglob("index.html")`, skipping `/id/artikel/`.
  - Line 90 (`missing = [a["cover"] for a in sj if a.get("cover")]`) is dead code because `search.json` does not include `"cover"`, and line 96 (`missing = [c for c in covers if not (pub / c).exists()]`) was never reached because the script crashed at line 67.
- **Action**:
  1. Update `scripts/test_build.py` so expected article counts are derived dynamically from `content/articles/*.md` (e.g., `en_count = len([f for f in p.glob("*.md") if not f.name.endswith(".id.md")])`, `id_count = len(list(p.glob("*.id.md")))`, and `min(20, id_count)` for RSS `<item>` count since `build.py` slices `arts[:20]`).
  2. Check duplicate HTML `id` attributes across **both** `(pub / "artikel").rglob("index.html")` and `(pub / "id" / "artikel").rglob("index.html")`.
  3. Keep and strengthen the cover existence assertion so it verifies every article's `cover` exists as a non-empty file in `public/assets/covers/` and that no `.json` files leak into `public/assets/covers/`.
  4. Add unit assertions in `scripts/test_build.py` for the new markdown and glossary fixes below (nested `*italic*` inside `**bold**`, `[[term|alias]]` pipe syntax, hyphen/space glossary matching, and template placeholder collision safety).

### 3. Markdown Parser Bugs & Unmatched Glossary Terms (`scripts/build.py`, `content/glossary.json`)
- **Diagnosis**:
  - **Bug 3A — Bold containing italics fails to parse**: In `scripts/build.py` line 166, `re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)` uses `[^*]+`, which fails whenever a bold span contains `*italic*` inside it. In `content/articles/2026-10-28-kev-patch-by-exploitation-not-score.md` (line 54) and `.id.md` (line 54), `**4. Patch *and* hunt.**` and `**4. Tambal *dan* buru.**` render literally with raw asterisks: `<p>**4. Patch <em>and</em> hunt.** ...`.
  - **Bug 3B — Glossary pipe alias `[[term|label]]` and hyphen/space normalization unsupported**:
    - In `2026-10-19-nuclei-poc-to-template.id.md` (lines 11 and 15), the author wrote `[[vulnerability|kerentanan]]`. Because `gterm()` in `build.py` does not split on `|`, it searches `glossary.json` for `"vulnerability|kerentanan"`, fails to find it, and outputs the raw text `vulnerability|kerentanan` into the published Indonesian article!
    - In `2026-10-09-atlassian-cve-2026-21589-exploited-hours.md` and `.id.md` (line 13), the article uses `[[proof-of-concept]]`, whereas `content/glossary.json` defines `"proof of concept"` (with spaces). Because `gterm()` only compares `k.lower() == term.lower()`, `[[proof-of-concept]]` fails to produce a tooltip.
  - **Bug 3C — 23 Glossary entries lack Indonesian translations**:
    - In `content/glossary.json`, 23 foundational terms (`Amass`, `CVE`, `Censys`, `DDoS`, `EASM`, `MFA`, `OSINT`, `SOC`, `Shodan`, `attack surface`, `blue team`, `encryption`, `exploit`, `firewall`, `malware`, `penetration testing`, `phishing`, `ransomware`, `red team`, `subdomain`, `threat intelligence`, `vulnerability`, `zero-day`) are plain English strings instead of `{"en": "...", "id": "..."}` objects. On `/id/` pages, hovering over these terms displays an English definition instead of Indonesian.
  - **Bug 3D — Template replacement order & TOC stripping in `scripts/build.py`**:
    - In `page()` (lines 306–316), `t.replace("{{content}}", content)` is executed *before* `.replace("{{description}}", ...)`, `.replace("{{extra_head}}", ...)`, and `for k, v in st.items(): t = t.replace("{{s:" + k + "}}", v)`. If an article body contains any of those placeholders inside a code block, `page()` will corrupt the article content.
    - In `md_to_html()` (lines 237 and 240), `toc.append((lvl, hid, re.sub(r"<[^>]+>", "", txt)))` strips HTML tags from the raw markdown heading `txt` rather than stripping HTML tags from `inner` (or stripping markdown tokens like `` ` ``, `**`, `[[term|label]]`). If a heading ever uses inline code or `[[term]]`, raw markdown syntax leaks into the TOC and `slugify()`.
- **Action**:
  1. In `scripts/build.py` `inline_md()`:
     - Support non-greedy bold matching that allows single asterisks inside it: `re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)` before italic replacement `re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)`. Verify that `**4. Patch *and* hunt.**` renders as `<strong>4. Patch <em>and</em> hunt.</strong>` and multiple bold spans on the same line (e.g. `**a** and **b**`) still render as two separate `<strong>` elements.
     - In `gterm(m)`, support optional pipe display syntax `[[term|display_label]]`: split `m.group(1)` on `|` (max 1 split) into `raw_term` and `display_label` (defaulting to `raw_term`). When matching `raw_term` against `glossary`, normalize both `k` and `raw_term` by lowercasing and treating hyphens and spaces as equivalent (`re.sub(r"[\s-]+", " ", s.strip().lower())`). If matched, render `display_label` as the visible text and `key` as `data-term`. If unmatched, return `html.escape(display_label)` (never leave `term|label` raw).
  2. Convert the 23 string-only entries in `content/glossary.json` into `{"en": "<existing English string>", "id": "<accurate, natural Indonesian translation keeping standard English technical terms where appropriate>"}` so all 98 glossary entries have both `"en"` and `"id"` definitions.
  3. In `md_to_html()`, generate `inner = inline_md(txt, glossary, lang)` first, derive clean plain text via `clean_txt = html.unescape(re.sub(r"<[^>]+>", "", inner))`, and use `clean_txt` for both `slugify(clean_txt)` and `toc.append((lvl, hid, clean_txt))`.
  4. In `page()`, perform all template shell replacements (`{{title}}`, `{{description}}`, `{{extra_head}}`, `{{s:...}}`, `lang-toggle`) **before** replacing `{{content}}` last, so article content can never be mutated by template variables.

### 4. Mobile Layout, Navigation & Responsive Polish (`assets/css/style.css`, `templates/base.html`, `scripts/build.py`)
- **Diagnosis**:
  - **Bug 4A — Navigation Links Disappear Completely on Mobile (`<= 640px`)**:
    - In `assets/css/style.css` line 705:
      ```css
      @media (max-width: 640px) {
        .nav-links a:not(.keep) { display: none; }
      ```
    - In `templates/base.html`, **none** of the links in `.nav-links` (`Archive`, `About`, or `.lang-toggle`) have the class `keep`. As a result, on mobile viewports (`<= 640px`), `Archive`, `About`, and the `ID`/`EN` language switcher all disappear completely! Mobile users have no way to switch languages or visit the About page.
  - **Bug 4B — Drop-cap float collision on short opening paragraphs**:
    - `.prose > p:first-of-type::first-letter` has `float: left; font-size: 3.6em; line-height: 0.82;`. When an article's first paragraph is a short 1-liner (such as `2026-10-23-zeabur-plaintext-secrets-breach.md`: *"A hosting platform died this month, and the murder weapon was a config repository."*), the 3.6em floated drop-cap is taller than the first `<p>`, causing the second `<p>` to wrap awkwardly around the bottom of the first paragraph's drop-cap!
  - **Bug 4C — Language-specific RSS link in footer**:
    - `templates/base.html` line 43 hardcodes `<a href="/rss.xml">rss</a>`. On Indonesian pages (`/id/...`), clicking `rss` in the footer sends the user to the English RSS feed `/rss.xml` instead of `/id/rss.xml`. Also, `<link rel="alternate" type="application/rss+xml" ...>` is missing from `<head>`.
  - **Bug 4D — Pager when only one link exists & mobile spacing**:
    - On mobile (`<= 640px`), `.pager` switches to `grid-template-columns: 1fr`. When an article is the newest or oldest article, `build.py` inserts an empty `<span></span>` placeholder inside `.pager`, which in a 1-column grid creates an unnecessary empty grid track + `20px` gap. Also `.pager .next` stays `text-align: right` on stacked mobile cards, which looks slightly unbalanced compared to left-aligned cards, or needs clean styling.
    - On mobile (`<= 640px`), `.wrap` and `.wrap-narrow` have `padding: 0 28px` and `.nav-inner` has `padding: 0 28px`, which is slightly tight on 320px–375px screens when combined with the brand + nav links + 3 action buttons.
- **Action**:
  1. **Fix Mobile Navigation (`style.css` & `base.html`)**:
     - Keep all navigation items (`Archive`/`Arsip`, `About`/`Tentang`, `.lang-toggle`, `.search-toggle`, `.theme-toggle`) accessible and visible on mobile without overflow.
     - Specifically, on `@media (max-width: 640px)`, do **not** hide `.nav-links a` (`Remove .nav-links a:not(.keep) { display: none; }`). Instead, adjust `.nav-inner` padding (e.g. `0 16px` on `<= 640px`), reduce `.brand` font-size slightly (`15px`), reduce `.nav-links` gap (e.g. `gap: 10px` or `12px`), set `.nav-links a` font-size to `11px` with `letter-spacing: 0.1em`, and size `.icon-btn` and `.lang-toggle` to `34px × 34px` on `<= 640px` so that `LLUNATIC_`, `Archive`, `About`, `ID`/`EN`, Search, and Theme buttons all fit comfortably on a `360px`/`375px` mobile screen on a single row with zero horizontal overflow. (Verify width math: at 360px viewport with 32px horizontal padding = 328px available; `LLUNATIC_` ~85px + gap + `ARCHIVE` ~52px + `ABOUT` ~40px + 3×34px buttons = 102px + gaps ~40px = ~319px, fitting cleanly even at 360px!).
  2. **Fix Drop-Cap Float Clearance (`style.css`)**:
     - Add `clear: left;` to `.prose > * + *` (or `display: flow-root;` on `.prose > p:first-of-type`) so the floated `::first-letter` drop-cap is always contained within the first paragraph and never bleeds into the second paragraph on short hooks. (`display: flow-root` on `.prose > p:first-of-type` is especially clean because it contains the float inside the first paragraph!).
  3. **Fix Pager Empty Placeholder on Mobile (`style.css`)**:
     - Hide empty `span:empty` inside `.pager` on `@media (max-width: 640px)` (`.pager > span:empty { display: none; }`) so there is no phantom gap on the newest/oldest article pages on mobile.
  4. **Fix Footer RSS Link & Head RSS Autodiscovery (`base.html`, `build.py`)**:
     - Add `rss_url` (`/{pfx(lang)}rss.xml`) to `st` in `page()` in `scripts/build.py`.
     - Update `templates/base.html` footer to use `<a href="{{s:rss_url}}">rss</a>` and add `<link rel="alternate" type="application/rss+xml" title="llunatic-lab ({{s:lang}})" href="{{s:rss_url}}">` in `<head>`.

### 5. Performance, Zero-Flicker Theme Loading, Smooth Transitions & CLS (`templates/base.html`, `assets/css/style.css`, `assets/js/main.js`, `scripts/build.py`)
- **Diagnosis**:
  - **Bug 5A — Theme FOUC (Flash of Dark Theme) & Page-Load Color Transition Flash**:
    - `templates/base.html` sets `<html lang="{{s:lang}}" data-theme="dark">`, and `style.css` sets `transition: background 0.45s ease, color 0.45s ease;` on `body`.
    - When a user who selected Light Mode navigates between pages, the browser first paints the page in dark mode (`#0a0a0c`), and then when `main.js` executes at the bottom of `<body>`, it switches `data-theme="light"`, triggering a slow 450ms fade from black to warm paper on every single page load!
  - **Bug 5B — Cross-Document Page Transitions & Above-the-Fold Reveal Flicker**:
    - Navigating between pages currently does a hard browser cut without cross-document View Transitions.
    - On the homepage, archive, and tag pages, all `.index-row.rv` items start at `opacity: 0; transform: translateY(26px);` until JS loads and `IntersectionObserver` fires. If JS is delayed by font/stylesheet loading, above-the-fold rows flash invisible then jump in.
  - **Bug 5C — Image Attributes & CLS Prevention**:
    - Cover images (`<img class="cover" ...>`) in `build.py` lack `width`, `height`, `decoding="async"`, and `fetchpriority="high"`.
    - Thumbnail images (`<img class="thumb" ...>`) in `index_row()` lack explicit `width="190" height="128"` and `decoding="async"`, and markdown inline images (`_img`) lack `decoding="async"`.
  - **Bug 5D — Keyboard Accessibility & UX Polish in `main.js` / `style.css`**:
    - Glossary terms (`.gterm`) only respond to `mouseenter`/`mouseleave`/`click` and are `<span>` elements without `tabindex="0"`, so keyboard users cannot tab to them to read definitions.
    - When the search overlay (`.search-overlay`) is open, background page scrolling is not locked (`overflow: hidden` on `body`), and there is no keyboard arrow navigation (`ArrowDown`/`ArrowUp`/`Enter`) in search results.
    - External links inside article prose (`http://` / `https://`) open in the same tab without `rel="noopener noreferrer"` or `target="_blank"`.
    - Missing SEO/social metadata in `page()`: `<link rel="canonical" href="{SITE_URL}{page._cur}">`, `<meta property="og:url" content="{SITE_URL}{page._cur}">`, `<link rel="alternate" hreflang="x-default" href="...">` when `lang_url` is present, and `og:type` is hardcoded to `website` even on article pages.
- **Action**:
  1. **Eliminate Theme FOUC & Page-Load Transition Flash**:
     - Place a tiny synchronous inline `<script>` inside `<head>` in `templates/base.html` (before `<link rel="stylesheet" href="/assets/css/style.css">`):
       ```html
       <script>(function(){try{var t=localStorage.getItem("llunatic-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}catch(e){}})();</script>
       ```
     - In `assets/css/style.css`, remove `transition: background 0.45s ease, color 0.45s ease;` from the default `body` rule so initial page paint never animates background/color. Instead, scope the smooth theme transition to a class `html.theme-transition body { transition: background 0.35s ease, color 0.35s ease; }` (and apply `theme-transition` transiently in `main.js` only when the user clicks `.theme-toggle`).
  2. **Add Smooth Cross-Document View Transitions**:
     - In `assets/css/style.css`, add progressive enhancement for the CSS View Transitions API (wrapped in `@media (prefers-reduced-motion: no-preference)`):
       ```css
       @media (prefers-reduced-motion: no-preference) {
         @view-transition { navigation: auto; }
         ::view-transition-old(root),
         ::view-transition-new(root) {
           animation-duration: 0.22s;
           animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
         }
       }
       ```
     - Ensure that if `IntersectionObserver` is unavailable or before scrolling, `.rv` animations feel snappy (`0.45s` instead of sluggish `0.7s`, smaller `16px` offset) and respect `prefers-reduced-motion: reduce` (where `.rv` must immediately have `opacity: 1; transform: none;`).
  3. **Add Explicit Image Dimensions & Loading Hints (`scripts/build.py`)**:
     - On article hero covers (`<img class="cover" ...>`): add `width="1470" height="630" fetchpriority="high" decoding="async"`.
     - On index row thumbnails (`<img class="thumb" ...>`): add `width="190" height="128" loading="lazy" decoding="async"`.
     - On markdown inline images (`_img` in `inline_md`): keep `loading="lazy"` and add `decoding="async"`.
  4. **Accessibility, Keyboard UX & Active Nav State (`scripts/build.py`, `assets/js/main.js`, `assets/css/style.css`)**:
     - In `inline_md()`, add `tabindex="0" role="button"` to `<span class="gterm" ...>` and in `main.js`, bind `focus` (to `show()`) and `blur` / `Escape` (to `hidePop()`) on `.gterm` elements so keyboard users can access glossary tooltips. Ensure `test_ui.js` assertions still pass!
     - In `style.css`, add subtle, high-craft `:focus-visible` outlines (`outline: 2px solid var(--acid); outline-offset: 3px;`) for interactive elements (`a`, `button`, `.gterm`).
     - Highlight the active navigation link (`Archive` when on `/arsip/` or `/id/arsip/`, `About` when on `/tentang/` or `/id/tentang/`) by adding an `.active` class or `aria-current="page"` so the user has clear location feedback in the navbar.
     - In `main.js`, lock `document.body.style.overflow = "hidden"` when `.search-overlay` opens and restore it on `closeSearch()`.
  5. **Canonical & OpenGraph Polish (`scripts/build.py`, `templates/base.html`)**:
     - Include `<link rel="canonical" href="{SITE_URL}{page._cur}">` and `<meta property="og:url" content="{SITE_URL}{page._cur}">` in `page()`.
     - When `lang_url` is provided in `page()`, also include `<link rel="alternate" hreflang="x-default" href="{SITE_URL}{en_url}">` pointing to the English URL.

---

## Verification & Testing Protocol (MANDATORY)

After implementing the changes, you must run the exact build and verification commands that exist in this repository and ensure every single check is 100% green:

1. **Rebuild the static site into `public/`**:
   ```bash
   python3 scripts/build.py
   ```
   Verify that it builds all 42 pages (21 slugs) cleanly with zero errors.

2. **Run the Python build & regression test suite:**
   ```bash
   python3 scripts/test_build.py
   ```
   Every assertion (existing + newly added assertions for cover files, nested bold/italic, glossary pipe syntax, and glossary translations) must pass.

3. **Run the Node/JSDOM UI interaction test suite:**
   Start a local static HTTP server on port 8125 serving `public/`, run `scripts/test_ui.js`, and stop the server:
   ```bash
   python3 -m http.server 8125 --directory public &
   SERVER_PID=$!
   sleep 1
   LAB_PORT=8125 node scripts/test_ui.js
   kill $SERVER_PID
   ```
   (Note: If `jsdom` is not yet installed in `node_modules` locally, install it with `npm install --no-save jsdom` — since `node_modules/` is already in `.gitignore`, ensure `package.json` / `package-lock.json` are not left untracked unless intentional — and verify all 18+ UI assertions pass.)

4. **Run a sanity audit check via Python one-liner:**
   Verify that:
   - Zero `.json` files exist in `assets/covers/` or `public/assets/covers/`.
   - Every cover referenced by any markdown file in `content/articles/*.md` exists in `public/assets/covers/` and has file size > 0.
   - Zero occurrences of raw `**`, `[[`, `]]`, or `vulnerability|kerentanan` remain outside `<code>`/`<pre>` across all generated HTML files in `public/`.
   - `git status` shows no untracked temporary artifacts.

## Git Commit, Push & Final Report

Stage all source and regenerated `public/` changes (`git add -A`).

Commit on branch `overhaul/marathon-2026-11-09` using a concise, professional English commit message (or a logical sequence of atomic commits).

Push the branch to `origin`:
```bash
git push -u origin overhaul/marathon-2026-11-09
```
(Remember: DO NOT merge to `main` and DO NOT deploy.)

Conclude with a concise engineering report containing:
- **Key Findings & Diagnosis Verification**: What you confirmed in the local repo (including any differences noticed during inspection).
- **Modified Files**: Summary of changes per file (`scripts/build.py`, `scripts/test_build.py`, `content/glossary.json`, `templates/base.html`, `assets/css/style.css`, `assets/js/main.js`, `assets/covers/*`, `PIPELINE.md`, `.gitignore`, and regenerated `public/`). Confirm whether any file in `content/articles/` was touched (none should need to be touched).
- **Verification Results**: Exact output from `python3 scripts/build.py`, `python3 scripts/test_build.py`, and `LAB_PORT=8125 node scripts/test_ui.js`.
