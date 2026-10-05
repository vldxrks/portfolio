// Living backgrounds. Each page picks a scene via <body data-scene="...">:
// aurora | waves | grid | stars | bokeh. Pure canvas, no dependencies.
(function () {
  var cv = document.getElementById("bg");
  if (!cv) return;
  var ctx = cv.getContext("2d");
  var scene = document.body.dataset.scene || "aurora";
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var W, H, dpr, raf, mouse = { x: .5, y: .4, tx: .5, ty: .4 };
  var PAL = ["#ff9f0a", "#ff375f", "#bf5af2", "#0a84ff", "#30d158"];
  var blobs = [], dots = [], orbs = [], sparks = [];
  var rnd = Math.random;

  function dark() { return document.documentElement.getAttribute("data-bs-theme") === "dark"; }

  function resize() {
    dpr = Math.min(devicePixelRatio || 1, 1.75);
    W = innerWidth; H = innerHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    cv.style.width = W + "px"; cv.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var small = W < 700;
    dots = Array.from({ length: small ? 26 : 64 }, function () {
      return { x: rnd() * W, y: rnd() * H, vx: (rnd() - .5) * .3, vy: (rnd() - .5) * .3, r: rnd() * 1.6 + .6 };
    });
    orbs = Array.from({ length: small ? 10 : 20 }, function (_, i) {
      return { x: rnd() * W, y: rnd() * H, r: 30 + rnd() * 110, vy: .12 + rnd() * .35, ph: rnd() * 6.28, c: PAL[i % 5] };
    });
    sparks = Array.from({ length: small ? 40 : 110 }, function () {
      return { x: rnd() * W, y: rnd() * H, s: rnd() * 2.2 + .6, ph: rnd() * 6.28, sp: .6 + rnd() * 1.6, vy: .06 + rnd() * .22, c: PAL[(rnd() * 5) | 0] };
    });
  }
  blobs = PAL.map(function (c, i) {
    return { c: c, a: i * 1.3, sx: .00022 + i * .00006, r: .34 + (i % 3) * .07, ox: .12 + i * .19, oy: .22 + (i % 2) * .42 };
  });

  function fieldGlow(t, k) {
    var isDark = dark(), sy = (scrollY || 0) * .12, a = isDark ? 0x66 : 0x5c;
    a = Math.round(a * k).toString(16).padStart(2, "0");
    ctx.globalCompositeOperation = isDark ? "lighter" : "source-over";
    blobs.forEach(function (b, i) {
      var x = (b.ox + Math.sin(t * b.sx + b.a) * .24 + (mouse.x - .5) * (.1 + i * .035)) * W;
      var y = (b.oy + Math.cos(t * b.sx * 1.25 + b.a) * .22 + (mouse.y - .5) * (.1 + i * .035)) * H - sy;
      var r = b.r * Math.max(W, H), g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, b.c + a); g.addColorStop(1, b.c + "00");
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    });
    ctx.globalCompositeOperation = "source-over";
  }

  function constellation() {
    var ink = dark() ? "255,255,255" : "40,40,60", mx = mouse.x * W, my = mouse.y * H;
    for (var i = 0; i < dots.length; i++) {
      var p = dots[i]; p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1;
      var dm = Math.hypot(p.x - mx, p.y - my);
      if (dm < 150) { p.x += (p.x - mx) / dm * .8; p.y += (p.y - my) / dm * .8; }
      ctx.fillStyle = "rgba(" + ink + "," + (dark() ? .6 : .4) + ")";
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill();
      for (var j = i + 1; j < dots.length; j++) {
        var q = dots[j], d = Math.hypot(p.x - q.x, p.y - q.y);
        if (d < 120) {
          ctx.strokeStyle = "rgba(" + ink + "," + (1 - d / 120) * (dark() ? .22 : .16) + ")";
          ctx.lineWidth = .7; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
        }
      }
    }
  }

  function waves(t) {
    var isDark = dark();
    for (var k = 0; k < 5; k++) {
      var base = H * (.58 + k * .075) - (scrollY || 0) * (.04 + k * .01);
      var amp = 26 + k * 12 + (1 - mouse.y) * 34, f = .0042 - k * .0003, sp = t * (.0004 + k * .00012);
      var g = ctx.createLinearGradient(0, 0, W, 0);
      PAL.forEach(function (c, i) { g.addColorStop(i / 4, c + (isDark ? "44" : "38")); });
      ctx.beginPath(); ctx.moveTo(0, H);
      for (var x = 0; x <= W; x += 10) {
        ctx.lineTo(x, base + Math.sin(x * f + sp + k * 1.7) * amp + Math.sin(x * f * 2.3 - sp * 1.4) * amp * .35 + (mouse.x - .5) * 30);
      }
      ctx.lineTo(W, H); ctx.closePath(); ctx.fillStyle = g; ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255," + (isDark ? .08 : .45) + ")"; ctx.lineWidth = 1.2; ctx.stroke();
    }
  }

  function grid(t) {
    var isDark = dark(), hy = H * .5, vx = W * (.5 + (mouse.x - .5) * .18);
    var gl = ctx.createRadialGradient(vx, hy, 0, vx, hy, W * .55);
    gl.addColorStop(0, isDark ? "rgba(191,90,242,.38)" : "rgba(191,90,242,.22)"); gl.addColorStop(1, "rgba(191,90,242,0)");
    ctx.fillStyle = gl; ctx.fillRect(0, hy - H * .35, W, H * .7);
    var col = isDark ? "180,140,255" : "109,94,252";
    ctx.lineWidth = 1;
    for (var i = -24; i <= 24; i++) {
      var xb = vx + i * W * .075;
      var lg = ctx.createLinearGradient(0, hy, 0, H);
      lg.addColorStop(0, "rgba(" + col + ",0)"); lg.addColorStop(1, "rgba(" + col + "," + (isDark ? .45 : .32) + ")");
      ctx.strokeStyle = lg; ctx.beginPath(); ctx.moveTo(vx + i * 6, hy); ctx.lineTo(xb, H); ctx.stroke();
    }
    var off = (t * .00028) % 1;
    for (var n = 0; n < 16; n++) {
      var z = (n + off) / 16, y = hy + (H - hy) * Math.pow(z, 2.3);
      ctx.strokeStyle = "rgba(" + col + "," + (.05 + z * (isDark ? .5 : .35)) + ")";
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
    var sky = ctx.createLinearGradient(0, 0, 0, hy);
    sky.addColorStop(0, "rgba(10,132,255,0)"); sky.addColorStop(1, isDark ? "rgba(255,55,95,.18)" : "rgba(255,55,95,.1)");
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, hy);
  }

  function stars(t) {
    var isDark = dark();
    ctx.globalCompositeOperation = isDark ? "lighter" : "source-over";
    sparks.forEach(function (s) {
      s.y -= s.vy; if (s.y < -10) { s.y = H + 10; s.x = rnd() * W; }
      var tw = .5 + .5 * Math.sin(t * .001 * s.sp + s.ph), r = s.s * (1.4 + tw * 2.2);
      var g = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, r * 4);
      g.addColorStop(0, s.c + (isDark ? "cc" : "99")); g.addColorStop(1, s.c + "00");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(s.x, s.y, r * 4, 0, 6.283); ctx.fill();
      ctx.strokeStyle = isDark ? "rgba(255,255,255," + (.4 + tw * .5) + ")" : s.c;
      ctx.lineWidth = .9; ctx.beginPath();
      ctx.moveTo(s.x - r * 2, s.y); ctx.lineTo(s.x + r * 2, s.y); ctx.moveTo(s.x, s.y - r * 2); ctx.lineTo(s.x, s.y + r * 2); ctx.stroke();
    });
    ctx.globalCompositeOperation = "source-over";
  }

  function bokeh(t) {
    var isDark = dark();
    orbs.forEach(function (o) {
      o.y -= o.vy; if (o.y < -o.r) { o.y = H + o.r; o.x = rnd() * W; }
      var x = o.x + Math.sin(t * .0004 + o.ph) * 40 + (mouse.x - .5) * o.r * .5, y = o.y + (mouse.y - .5) * o.r * .3;
      var g = ctx.createRadialGradient(x - o.r * .3, y - o.r * .3, o.r * .1, x, y, o.r);
      g.addColorStop(0, o.c + (isDark ? "55" : "44")); g.addColorStop(1, o.c + "0a");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, o.r, 0, 6.283); ctx.fill();
      ctx.strokeStyle = o.c + (isDark ? "55" : "40"); ctx.lineWidth = 1.2; ctx.stroke();
    });
  }

  function draw(t) {
    mouse.x += (mouse.tx - mouse.x) * .045; mouse.y += (mouse.ty - mouse.y) * .045;
    ctx.clearRect(0, 0, W, H);
    if (scene === "grid") { fieldGlow(t, .8); grid(t); }
    else if (scene === "waves") { fieldGlow(t, .9); waves(t); }
    else if (scene === "stars") { fieldGlow(t, 1); stars(t); }
    else if (scene === "bokeh") { fieldGlow(t, 1.1); bokeh(t); }
    else { fieldGlow(t, 1); constellation(); }
    if (!reduce && !document.hidden) raf = requestAnimationFrame(draw);
  }

  addEventListener("pointermove", function (e) { mouse.tx = e.clientX / innerWidth; mouse.ty = e.clientY / innerHeight; }, { passive: true });
  addEventListener("resize", resize);
  document.addEventListener("visibilitychange", function () { if (!document.hidden && !reduce) { cancelAnimationFrame(raf); raf = requestAnimationFrame(draw); } });
  resize(); raf = requestAnimationFrame(draw);
  window.__bgReady = true;
})();
