/* LLUNATIC-LAB interactions */
(function () {
  "use strict";
  var root = document.documentElement;

  /* ---------- theme ---------- */
  function setTheme(t) {
    root.setAttribute("data-theme", t);
    try { localStorage.setItem("llunatic-theme", t); } catch (e) {}
    var dark = t !== "light";
    document.querySelectorAll(".theme-toggle").forEach(function (b) {
      b.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
      b.innerHTML = dark ? ICON_SUN : ICON_MOON;
    });
  }
  var ICON_SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var ICON_MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
  var saved = null;
  try { saved = localStorage.getItem("llunatic-theme"); } catch (e) {}
  setTheme(saved || "dark");
  document.querySelectorAll(".theme-toggle").forEach(function (b) {
    b.addEventListener("click", function () {
      setTheme(root.getAttribute("data-theme") === "light" ? "dark" : "light");
    });
  });

  /* ---------- reveal on scroll ---------- */
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
    });
  }, { threshold: 0.08 });
  document.querySelectorAll(".rv").forEach(function (el) { io.observe(el); });

  /* ---------- reading progress ---------- */
  var prog = document.querySelector(".progress");
  if (prog) {
    var onScroll = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      prog.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------- TOC scrollspy ---------- */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  if (tocLinks.length) {
    var heads = tocLinks.map(function (a) { return document.querySelector(a.getAttribute("href")); })
      .filter(Boolean);
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          tocLinks.forEach(function (a) {
            a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id);
          });
        }
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    heads.forEach(function (h) { spy.observe(h); });
  }

  /* ---------- code copy buttons ---------- */
  document.querySelectorAll("pre").forEach(function (pre) {
    var code = pre.querySelector("code");
    if (!code) return;
    var lang = (code.className.match(/language-(\w+)/) || [null, "code"])[1];
    var head = document.createElement("div");
    head.className = "code-head";
    head.innerHTML = '<span class="dots"><i></i><i></i><i></i></span><span>' + lang + '</span>';
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.textContent = "copy";
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(code.innerText).then(function () {
        btn.textContent = "copied ✓";
        setTimeout(function () { btn.textContent = "copy"; }, 1600);
      });
    });
    head.appendChild(btn);
    pre.insertBefore(head, pre.firstChild);
  });

  /* ---------- glossary tooltips ---------- */
  var pop = document.createElement("div");
  pop.className = "gloss-pop";
  document.body.appendChild(pop);
  var hideTimer = null;

  function showPop(term, def, anchor) {
    pop.innerHTML = "<b>" + term + "</b>" + def;
    pop.classList.add("show");
    var r = anchor.getBoundingClientRect();
    var pw = Math.min(300, window.innerWidth - 32);
    var x = Math.max(16, Math.min(window.innerWidth - pw - 16, r.left + r.width / 2 - pw / 2));
    var y = r.bottom + 10;
    if (y + 140 > window.innerHeight) y = r.top - 150;
    pop.style.left = x + "px";
    pop.style.top = Math.max(12, y) + "px";
    pop.style.maxWidth = pw + "px";
  }
  function hidePop() { pop.classList.remove("show"); }

  document.querySelectorAll(".gterm").forEach(function (el) {
    var term = el.getAttribute("data-term");
    var def = el.getAttribute("data-def");
    el.addEventListener("mouseenter", function () {
      clearTimeout(hideTimer);
      showPop(term, def, el);
    });
    el.addEventListener("mouseleave", function () {
      hideTimer = setTimeout(hidePop, 180);
    });
    el.addEventListener("click", function (e) {
      e.preventDefault();
      if (pop.classList.contains("show")) hidePop();
      else showPop(term, def, el);
    });
  });
  pop.addEventListener("mouseenter", function () { clearTimeout(hideTimer); });
  pop.addEventListener("mouseleave", function () { hidePop(); });

  /* ---------- search ---------- */
  var overlay = document.querySelector(".search-overlay");
  var input = document.querySelector(".search-box input");
  var results = document.querySelector(".search-results");
  var index = null;

  function openSearch() {
    overlay.classList.add("open");
    input.value = "";
    results.innerHTML = "";
    setTimeout(function () { input.focus(); }, 60);
    if (!index) {
      var searchUrl = document.documentElement.lang === "id" ? "/id/search.json" : "/search.json";
      fetch(searchUrl).then(function (r) { return r.json(); })
        .then(function (j) { index = j; });
    }
  }
  function closeSearch() { overlay.classList.remove("open"); }

  document.querySelectorAll(".search-toggle").forEach(function (b) {
    b.addEventListener("click", openSearch);
  });
  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) closeSearch();
  });
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openSearch(); }
    if (e.key === "Escape") closeSearch();
  });
  var SEARCH_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>';
  document.querySelectorAll(".search-toggle").forEach(function (b) { b.innerHTML = SEARCH_ICON; });

  if (input) {
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      if (!index || q.length < 2) { results.innerHTML = ""; return; }
      var hits = index.filter(function (a) {
        return (a.title + " " + a.excerpt + " " + a.tags.join(" ")).toLowerCase().indexOf(q) !== -1;
      }).slice(0, 8);
      results.innerHTML = hits.length
        ? hits.map(function (a) {
            return '<a href="' + a.url + '"><div class="t">' + a.title + '</div>' +
              '<div class="m">' + a.date + " · " + a.tags.join(" · ") + "</div></a>";
          }).join("")
        : '<div class="empty">' + results.getAttribute("data-empty") + "</div>";
    });
  }

  /* ---------- ticker: duplicate track for seamless loop ---------- */
  document.querySelectorAll(".ticker-track").forEach(function (t) {
    t.innerHTML += t.innerHTML;
  });

  /* ---------- footer year ---------- */
  document.querySelectorAll(".js-year").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
