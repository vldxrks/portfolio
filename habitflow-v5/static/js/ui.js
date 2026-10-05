// Visual-only enhancements: scroll reveal, cursor glow on cards, demo heatmap.
(function () {
  var io = "IntersectionObserver" in window && new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach(function (el, i) {
    el.style.transitionDelay = (i % 4) * 70 + "ms";
    io ? io.observe(el) : el.classList.add("in");
  });
  document.addEventListener("pointermove", function (e) {
    var c = e.target.closest && e.target.closest(".card");
    if (!c) return;
    var r = c.getBoundingClientRect();
    c.style.setProperty("--mx", e.clientX - r.left + "px");
    c.style.setProperty("--my", e.clientY - r.top + "px");
  });
  document.querySelectorAll(".heat[data-demo]").forEach(function (h) {
    var s = 7;
    for (var i = 0; i < 84; i++) {
      s = (s * 9301 + 49297) % 233280;
      var l = Math.floor((s / 233280) * 5), cell = document.createElement("i");
      cell.dataset.l = i > 70 ? Math.min(4, l + 1) : l;
      h.appendChild(cell);
    }
  });
})();
