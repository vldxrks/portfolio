// Scroll-driven motion for the Apple-style theme (visual only).
(function () {
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var io = "IntersectionObserver" in window && new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll(".reveal").forEach(function (el) { io ? io.observe(el) : el.classList.add("in"); });

  setTimeout(function () { document.querySelectorAll('.ap-hero .reveal').forEach(function (el) { el.classList.add('in'); }); }, 900);

  // Demo heatmaps
  document.querySelectorAll(".heat[data-demo]").forEach(function (h) {
    var s = 11;
    for (var i = 0; i < 91; i++) {
      s = (s * 9301 + 49297) % 233280;
      var l = Math.floor((s / 233280) * 5), c = document.createElement("i");
      c.dataset.l = i > 75 ? Math.min(4, l + 1) : l;
      h.appendChild(c);
    }
  });

  // Statement: words fill in as you scroll
  var st = document.querySelector(".ap-statement");
  var words = [];
  if (st) {
    st.innerHTML = st.textContent.trim().split(/\s+/).map(function (w) { return "<span>" + w + "</span>"; }).join(" ");
    words = st.querySelectorAll("span");
  }
  var dev = document.querySelector(".ap-device");
  var big = document.querySelector("[data-count]");
  var counted = false;

  function frame() {
    var vh = innerHeight;
    if (dev && !reduce) {
      var r = dev.getBoundingClientRect();
      var p = Math.min(1, Math.max(0, 1 - r.top / (vh * 0.85)));
      dev.style.setProperty("--rx", (14 * (1 - p)).toFixed(2) + "deg");
      dev.style.setProperty("--sc", (0.9 + 0.1 * p).toFixed(3));
    }
    if (st && words.length) {
      var b = st.getBoundingClientRect();
      var q = Math.min(1, Math.max(0, (vh * 0.85 - b.top) / (vh * 0.6 + b.height * 0.5)));
      var n = Math.round(q * words.length);
      words.forEach(function (w, i) { w.classList.toggle("on", i < n); });
    }
    if (big && !counted && big.getBoundingClientRect().top < vh * 0.8) {
      counted = true;
      var target = +big.dataset.count, t0 = performance.now();
      (function step(t) {
        var k = Math.min(1, (t - t0) / 1600), e = 1 - Math.pow(1 - k, 4);
        big.textContent = Math.round(target * e);
        if (k < 1) requestAnimationFrame(step);
      })(t0);
    }
  }
  var ticking = false;
  addEventListener("scroll", function () {
    if (!ticking) { ticking = true; requestAnimationFrame(function () { frame(); ticking = false; }); }
  }, { passive: true });
  addEventListener("resize", frame);
  frame();
})();
