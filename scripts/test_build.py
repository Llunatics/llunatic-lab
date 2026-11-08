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
x = build.inline_md('[[SQL injection|injeksi SQL]] menyerang', G, "id")
ok('class="gterm"' in x and 'data-term="SQL injection"' in x and '>injeksi SQL</span>' in x and 'data-def="SQL jahat via input"' in x, "glossary pipe alias")
g_poc = {"proof of concept": {"en": "working exploit PoC", "id": "PoC exploit jalan"}}
x = build.inline_md('Lihat [[proof-of-concept]] ini', g_poc, "en")
ok('class="gterm"' in x and 'data-term="proof of concept"' in x and '>proof-of-concept</span>' in x, "glossary hyphen-to-space normalization")
x = build.inline_md('[[Unknown|Label]]', G, "en")
ok("Label" in x and "|" not in x and "Unknown" not in x, "unmatched pipe term returns label")
x = build.inline_md('**tebal** dan *miring* dan `kode`', G, "en")
ok("<strong>tebal</strong>" in x and "<em>miring</em>" in x and "<code>kode</code>" in x,
   "bold/italic/code")
x = build.inline_md('**4. Patch *and* hunt.**', G, "en")
ok("<strong>4. Patch <em>and</em> hunt.</strong>" in x, "nested italic dalam bold")
x = build.inline_md('**tebal satu** dan **tebal dua**', G, "en")
ok("<strong>tebal satu</strong>" in x and "<strong>tebal dua</strong>" in x, "multiple bold pada satu baris")
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
all_mds = list(p.glob("*.md"))
en_count = len([f for f in all_mds if not f.name.endswith(".id.md")])
id_count = len([f for f in all_mds if f.name.endswith(".id.md")])
sj = json.loads((pub / "search.json").read_text(encoding="utf-8"))
ok(len(sj) == en_count and all("url" in a and a["url"].startswith("/artikel/") for a in sj),
   f"search.json {en_count} artikel EN, url valid")
sm = (pub / "sitemap.xml").read_text(encoding="utf-8")
# deep-5 (2026-10-20): lastmod halaman indeks = tanggal artikel terbaru
# (deterministik), bukan hari build.
newest = max(build.parse_md(md)["date"] for md in p.glob("*.md"))
ok(f"<lastmod>{newest}</lastmod>" in sm, "sitemap lastmod = artikel terbaru")
ok("https://lab.llunaticsys.web.id/artikel/" in sm, "sitemap URL absolut")
rss = (pub / "id" / "rss.xml").read_text(encoding="utf-8")
rss_expected = min(20, id_count)
ok(rss.count("<item>") == rss_expected and "<language>id</language>" in rss, f"RSS ID {rss_expected} item")
# og:image absolut di semua halaman artikel
bad_og = [f for f in (pub / "artikel").rglob("index.html")
          if 'og:image" content="/assets' in f.read_text(encoding="utf-8")]
ok(not bad_og, "og:image absolut")
# tidak ada id duplikat per halaman artikel (EN dan ID)
article_htmls = list((pub / "artikel").rglob("index.html")) + list((pub / "id" / "artikel").rglob("index.html"))
for f in article_htmls:
    ids = re.findall(r'id="([^"]+)"', f.read_text(encoding="utf-8"))
    assert len(ids) == len(set(ids)), "id duplikat di " + str(f)
ok(True, f"tidak ada id duplikat di {len(article_htmls)} halaman artikel")
# hreflang ada di halaman artikel EN yang punya pasangan ID
art = (pub / "artikel" / "nuclei-poc-to-template" / "index.html").read_text(encoding="utf-8")
ok('hreflang="id"' in art and 'hreflang="en"' in art, "hreflang EN<->ID")
# semua cover yang dirujuk ada filenya dan non-empty, tidak ada .json bocor
covers = set()
for md in p.glob("*.md"):
    c = build.parse_md(md)["cover"]
    if c: covers.add(c.lstrip("/"))
missing = [c for c in covers if not (pub / c).exists() or (pub / c).stat().st_size == 0]
ok(not missing, "semua cover ada dan valid: " + str(missing[:3]))
json_leaks = list((pub / "assets" / "covers").glob("*.json"))
ok(len(json_leaks) == 0, f"tidak ada file .json bocor di public/assets/covers: {json_leaks}")

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


# --- deep-9 (2026-10-20): regression dari mutation testing ---
# LB03: definisi glossary mengikuti bahasa halaman, fallback EN
g3 = {"X": {"en": "EN def", "id": "ID def"}}
x = build.inline_md('[[X]]', g3, "id")
ok('data-def="ID def"' in x, "glossary def pakai bahasa halaman (id)")
x = build.inline_md('[[X]]', g3, "id")
ok('data-def="EN def"' not in x, "glossary def id tidak jatuh ke EN bila ada id")
# LB04: slugify fallback untuk heading tanpa alfanumerik
ok(build.slugify("!!!") == "bagian", "slugify fallback 'bagian'")
# LB10: nomor h2 dua digit (01, 02, ...)
h, _ = build.md_to_html("## Satu\n\n## Dua", G, "en")
ok('class="hnum">01<' in h and 'class="hnum">02<' in h, "nomor h2 zero-padded 01/02")
# LB12: baris pemisah tabel tanpa '-' BUKAN tabel
h, _ = build.md_to_html("|a|b|\n|:|:|\n|1|2|", G, "en")
ok("<table>" not in h, "separator tabel tanpa dash tidak jadi tabel")
# LB13: '-x' tanpa spasi bukan list item
h, _ = build.md_to_html("-nempel", G, "en")
ok("<li>" not in h and "<p>" in h, "marker list butuh spasi")
# LB15: tag_url path
ok(build.tag_url("x", "en") == "/tag/x/", "tag_url EN")
ok(build.tag_url("x", "id") == "/id/tag/x/", "tag_url ID")
# LB17: beranda hanya 6 tulisan terbaru
home = (pub / "index.html").read_text(encoding="utf-8")
ok(home.count('class="index-row rv"') == 6, "beranda 6 index-row terbaru")
# LB18: lastmod artikel di sitemap = tanggal artikel itu sendiri
_dates = {build.parse_md(md)["slug"]: build.parse_md(md)["date"] for md in p.glob("*.md") if not md.name.endswith(".id.md")}
_old_slug = min(_dates, key=lambda s: _dates[s])
_m = re.search(r"<loc>https://lab\.llunaticsys\.web\.id/artikel/" + re.escape(_old_slug) + r"/</loc><lastmod>([^<]+)</lastmod>", sm)
ok(_m and _m.group(1) == _dates[_old_slug], "sitemap lastmod artikel = tanggalnya: " + _old_slug)
# LB19: blockquote multi-baris digabung <br>
h, _ = build.md_to_html("> q1\n> q2", G, "en")
ok("q1<br>q2" in h, "blockquote baris digabung <br>")
# LB20: istilah tak dikenal tetap tampil sebagai teks
x = build.inline_md('[[TidakAda]] halo', G, "en")
ok("TidakAda" in x and "halo" in x, "istilah tak dikenal tetap teks")

# marathon-2026-11-09: template placeholder collision safety
safe_body = "<code>{{title}} {{description}} {{extra_head}} {{s:nav_archive}}</code>"
rendered_page = build.page("Sample Title", "Sample Desc", safe_body, "en")
ok("<code>{{title}} {{description}} {{extra_head}} {{s:nav_archive}}</code>" in rendered_page,
   "template placeholder di content tidak ter-replace")

# marathon-2026-11-09: TOC clean text without markdown / glossary syntax
_, test_toc = build.md_to_html("## Testing `code` and [[SQL injection]]", G, "en")
ok(test_toc[0][2] == "Testing code and SQL injection",
   "TOC membersihkan markdown syntax dari heading: " + str(test_toc[0][2]))

# marathon-2026-11-09: semua 98 entri glossary punya definisi en dan id
gl = json.loads((ROOT / "content" / "glossary.json").read_text(encoding="utf-8"))
all_translated = all(isinstance(v, dict) and "en" in v and "id" in v and v["en"] and v["id"] for v in gl.values())
ok(all_translated and len(gl) == 98, f"semua {len(gl)} entri glossary memiliki definisi en dan id")

print(f"\n{n} asersi lolos.")
