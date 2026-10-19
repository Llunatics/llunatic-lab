/* Uji interaksi main.js llunatic-lab via jsdom — butuh server lokal di $LAB_PORT. */
"use strict";
const assert = require("assert");
const { JSDOM } = require("jsdom");

const PORT = process.env.LAB_PORT || "8125";
const BASE = `http://127.0.0.1:${PORT}`;

(async () => {
  let n = 0;
  const ok = (c, name) => { n++; assert(c, "GAGAL UI: " + name); console.log("ok", n, "-", name); };

  const dom = await JSDOM.fromURL(BASE + "/", {
    runScripts: "dangerously", resources: "usable",
    // jsdom tidak punya IntersectionObserver (ada di browser asli) — stub minimal
    beforeParse(window) {
      window.IntersectionObserver = class {
        constructor(cb) { this.cb = cb; }
        observe(el) { this.cb([{ isIntersecting: true, target: el }], this); }
        unobserve() {} disconnect() {}
      };
    },
  });
  await new Promise(r => setTimeout(r, 1500));
  const { document } = dom.window;
  const win = dom.window;

  // 1. theme toggle: klik sungguhan
  ok(document.documentElement.getAttribute("data-theme") === "dark", "tema awal dark");
  document.querySelector(".theme-toggle").click();
  ok(document.documentElement.getAttribute("data-theme") === "light", "toggle -> light");
  ok(win.localStorage.getItem("llunatic-theme") === "light", "tema tersimpan");
  document.querySelector(".theme-toggle").click();

  // 2. search dengan judul jahat: stub fetch -> hasil harus teks, bukan elemen
  const evil = [{ title: '<img src=x onerror="window.__xss=1">', excerpt: "e", tags: ["t"], date: "1 Jan", url: "/artikel/x/" }];
  win.fetch = () => Promise.resolve({ json: () => Promise.resolve(evil) });
  document.querySelector(".search-toggle").click();
  await new Promise(r => setTimeout(r, 300));
  const input = document.querySelector(".search-box input");
  input.value = "img";
  input.dispatchEvent(new win.Event("input", { bubbles: true }));
  await new Promise(r => setTimeout(r, 200));
  const res = document.querySelector(".search-results");
  ok(res.querySelector("img") === null, "judul jahat tidak jadi <img>");
  ok(res.querySelector("a") !== null && res.textContent.includes('<img src=x'),
    "judul jahat tampil sebagai teks");
  ok(win.__xss !== 1, "tidak ada eksekusi onerror");
  ok(res.querySelector("a").getAttribute("href") === "/artikel/x/", "link hasil benar");
  // empty state
  input.value = "zzz-tidak-ada";
  input.dispatchEvent(new win.Event("input", { bubbles: true }));
  await new Promise(r => setTimeout(r, 200));
  ok(res.querySelector(".empty") !== null, "empty state muncul");
  win.document.dispatchEvent(new win.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  ok(!document.querySelector(".search-overlay").classList.contains("open"), "Escape menutup search");

  // 3. halaman artikel dulu (tooltip + copy + TOC semuanya di sini)
  const dom2 = await JSDOM.fromURL(BASE + "/artikel/nuclei-poc-to-template/", {
    runScripts: "dangerously", resources: "usable",
    beforeParse(window) {
      window.IntersectionObserver = class {
        constructor(cb) { this.cb = cb; }
        observe(el) { this.cb([{ isIntersecting: true, target: el }], this); }
        unobserve() {} disconnect() {}
      };
    },
  });
  await new Promise(r => setTimeout(r, 1500));
  const d2 = dom2.window.document;

  // tooltip glossary: hover -> pop tanpa HTML aktif
  const g = d2.querySelector(".gterm");
  if (g) {
    g.dispatchEvent(new dom2.window.Event("mouseenter", { bubbles: true }));
    await new Promise(r => setTimeout(r, 100));
    const pop = d2.querySelector(".gloss-pop");
    ok(pop.classList.contains("show"), "tooltip muncul");
    ok(pop.querySelector("script") === null && pop.querySelector("img") === null,
      "tooltip tidak menyuntik HTML");
    ok(pop.textContent.includes(g.getAttribute("data-term")), "tooltip memuat istilah");
    // definisi jahat (simulasi): tetap teks — pakai gterm asli, timpa data-def-nya
    g.setAttribute("data-def", "<img src=x onerror=alert(1)>");
    g.dispatchEvent(new dom2.window.Event("mouseenter", { bubbles: true }));
    await new Promise(r => setTimeout(r, 100));
    ok(pop.querySelector("img") === null, "definisi jahat tidak jadi elemen");
    ok(pop.textContent.includes("<img src=x"), "definisi jahat tampil sebagai teks");
  } else {
    console.log("(skip tooltip: tidak ada .gterm di artikel)");
  }

  // 4. tombol copy + TOC
  const pres = d2.querySelectorAll("pre");
  ok(pres.length > 0, "artikel punya code block");
  ok(d2.querySelector(".copy-btn") !== null, "tombol copy terpasang");
  const tocLinks = d2.querySelectorAll(".toc a");
  const ids = [...tocLinks].map(a => a.getAttribute("href").slice(1));
  ok(ids.length > 0 && new Set(ids).size === ids.length, "TOC link unik");
  ok(ids.every(id => d2.getElementById(id) !== null), "semua TOC link punya target");

  console.log("\n" + n + " asersi UI lolos.");
})().catch(e => { console.error(e); process.exit(1); });
