#!/usr/bin/env python3
"""Uji regresi llunatic-lab build.py — stdlib only: python3 scripts/test_build.py"""
import re, sys, json, html as htmlmod
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build

G = {"SQL injection": {"en": "malicious SQL via input", "id": "SQL jahat via input"}}
n = 0
def ok(cond, name):
    global n
    n += 1
    assert cond, "GAGAL: " + name
    print("ok", n, "-", name)

# --- parse_md ---
p = ROOT / "content" / "articles"
en = build.parse_md(p / "2026-10-19-nuclei-poc-to-template.md")
ok(en["lang"] == "en" and en["slug"] == "nuclei-poc-to-template", "parse EN frontmatter+slug")
ok(isinstance(en["tags"], list) and len(en["tags"]) >= 2, "tags terparse: " + str(en["tags"]))
ide = build.parse_md(p / "2026-10-19-nuclei-poc-to-template.id.md")
ok(ide["lang"] == "id" and ide["slug"] == "nuclei-poc-to-template", "varian .id pairing slug sama")
ok(build.tgl("id", "2026-10-19") == "19 Oktober 2026", "tgl id")
ok(build.tgl("en", "2026-10-19") == "19 October 2026", "tgl en")

# --- inline_md: XSS ---
x = build.inline_md('<script>alert(1)</script>', G, "en")
ok("<script>" not in x and "&lt;script&gt;" in x, "tag script di-escape")
x = build.inline_md('[klik](javascript:alert(1))', G, "en")
ok('href="javascript:' not in x, "javascript: URL tidak lolos mentah: " + x[:80])
x = build.inline_md('![a" onerror="alert(1)](x.png)', G, "en")
m = re.search(r'alt="([^"]*)"', x)
ok(m and htmlmod.unescape(m.group(1)) == 'a" onerror="alert(1)' and "<img" in x,
   "quote di alt tetap data, bukan markup: " + x[:90])
x = build.inline_md('[[SQL injection]] menyerang', G, "en")
ok('class="gterm"' in x and 'data-def="malicious SQL via input"' in x, "glossary tooltip")
x = build.inline_md('**tebal** dan *miring* dan `kode`', G, "en")
ok("<strong>tebal</strong>" in x and "<em>miring</em>" in x and "<code>kode</code>" in x,
   "bold/italic/code")
# definisi glossary ber-HTML tidak bisa jadi markup aktif (disimpan escaped di data-def)
g2 = {"X": {"en": "<img src=x onerror=alert(1)>"}}
x = build.inline_md('[[X]]', g2, "en")
ok("<img" not in x and "&lt;img" in x, "definisi glossary di-escape di data-def")

# --- md_to_html: blok ---
h, toc = build.md_to_html("```python\nprint('<x>')\n```", G, "en")
ok('<code class="language-python">' in h and "&lt;x&gt;" in h, "code block di-escape")
h, toc = build.md_to_html("## Judul\n\n## Judul\n\n### Sub", G, "en")
ids = re.findall(r'id="([^"]+)"', h)
ok(len(ids) == len(set(ids)) == 3, "heading id unik: " + str(ids))
ok(len(toc) == 3 and toc[0][1] != toc[1][1], "TOC id unik")
h, _ = build.md_to_html("|a|b|\n|---|---|\n|1|2|", G, "en")
ok("<table>" in h and "<th>a</th>" in h and "<td>2</td>" in h, "tabel GFM")
h, _ = build.md_to_html("- a\n- b\n\n1. x\n2. y\n\n> q1\n> q2\n\n---", G, "en")
ok("<ul>" in h and "<ol>" in h and "<blockquote>" in h and "<hr>" in h, "list/quote/hr")
ok(build.slugify("Nmap: Scan Cepat!") == "nmap-scan-cepat", "slugify")

# --- build penuh + artefak ---
build.main()
pub = ROOT / "public"
ok((pub / "index.html").exists() and (pub / "id" / "index.html").exists(), "home EN+ID")
ok((pub / "search.json").exists() and (pub / "id" / "search.json").exists(), "search.json")
sj = json.loads((pub / "search.json").read_text(encoding="utf-8"))
ok(len(sj) == 9 and all("url" in a and a["url"].startswith("/artikel/") for a in sj),
   "search.json 9 artikel EN, url valid")
sm = (pub / "sitemap.xml").read_text(encoding="utf-8")
# deep-5 (2026-10-20): lastmod halaman indeks = tanggal artikel terbaru
# (deterministik), bukan hari build.
newest = max(build.parse_md(md)["date"] for md in p.glob("*.md"))
ok(f"<lastmod>{newest}</lastmod>" in sm, "sitemap lastmod = artikel terbaru")
ok("https://lab.llunaticsys.web.id/artikel/" in sm, "sitemap URL absolut")
rss = (pub / "id" / "rss.xml").read_text(encoding="utf-8")
ok(rss.count("<item>") == 9 and "<language>id</language>" in rss, "RSS ID 9 item")
# og:image absolut di semua halaman artikel
bad_og = [f for f in (pub / "artikel").rglob("index.html")
          if 'og:image" content="/assets' in f.read_text(encoding="utf-8")]
ok(not bad_og, "og:image absolut")
# tidak ada id duplikat per halaman artikel
for f in (pub / "artikel").rglob("index.html"):
    ids = re.findall(r'id="([^"]+)"', f.read_text(encoding="utf-8"))
    assert len(ids) == len(set(ids)), "id duplikat di " + str(f)
ok(True, "tidak ada id duplikat di 18 halaman artikel")
# hreflang ada di halaman artikel EN yang punya pasangan ID
art = (pub / "artikel" / "nuclei-poc-to-template" / "index.html").read_text(encoding="utf-8")
ok('hreflang="id"' in art and 'hreflang="en"' in art, "hreflang EN<->ID")
# semua cover yang dirujuk ada filenya
missing = [a["cover"] for a in sj if a.get("cover")]
# (cover diambil dari search.json EN saja; cek file fisik via parse)
covers = set()
for md in p.glob("*.md"):
    c = build.parse_md(md)["cover"]
    if c: covers.add(c.lstrip("/"))
missing = [c for c in covers if not (pub / c).exists()]
ok(not missing, "semua cover ada: " + str(missing[:3]))

# --- deep-5 (2026-10-20): slug & tag sanitization ---
# slug/tag mengalir ke path filesystem (pre/"artikel"/slug) dan atribut href
# yang tidak di-escape -> hostile frontmatter tidak boleh lolos.
import tempfile
def _parse_tmp(fm_lines):
    d = Path(tempfile.mkdtemp())
    f = d / "2026-10-20-x.md"
    f.write_text("---\n" + "\n".join(fm_lines) + "\n---\n\nHai.\n", encoding="utf-8")
    return build.parse_md(f)

a = _parse_tmp(['title: T', 'slug: \'><script>alert(1)</script>', 'tags: [ok-tag]'])
ok(a["slug"] == "script-alert-1---script", "slug hostile di-sanitize: " + a["slug"])
ok(re.fullmatch(r"[a-z0-9-]+", a["slug"]) is not None, "slug hanya [a-z0-9-]")
a = _parse_tmp(['title: T', 'slug: ../../etc/pwned', 'tags: [ok]'])
ok(".." not in a["slug"] and "/" not in a["slug"], "slug traversal diblok: " + a["slug"])
a = _parse_tmp(['title: T', 'tags: ["><svg onload=alert(1)>, Blue Team, a/b]'])
ok(a["tags"] == ["svg-onload-alert-1", "blue-team", "a-b"], "tag hostile di-sanitize: " + str(a["tags"]))
ok(all(re.fullmatch(r"[a-z0-9-]+", t) for t in a["tags"]), "semua tag [a-z0-9-]")
a = _parse_tmp(['title: T'])
ok(a["slug"] == "x", "slug default dari filename tetap")
u = build.art_url(a["slug"], "en")
ok(u == "/artikel/x/" and '"' not in u and "<" not in u, "art_url aman: " + u)

print(f"\n{n} asersi lolos.")
