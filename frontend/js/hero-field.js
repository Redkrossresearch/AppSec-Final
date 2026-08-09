/* Hero point field.
 *
 * A grid of points lying on a flat plane, pushed through a pinhole projection
 * so the plane recedes into a trapezoid: near rows are wide and bright, far
 * rows collapse toward the vanishing point. A travelling wave lifts the points
 * off the plane (height drives both size and brightness), and the pointer acts
 * as a repulsion well that bends the rows around a circular void.
 *
 * Canvas 2D on purpose — this is points with a hand-rolled projection, so a 3D
 * library would add a megabyte to first paint for a pipeline we never use.
 * All maths runs in device pixels; integer coordinates keep the dots crisp.
 */
(function () {
  var canvas = document.getElementById("heroField");
  if (!canvas) return;

  var ctx = canvas.getContext("2d");
  if (!ctx) return;

  /* ── Shape of the projection ──────────────────────────────────────────────
   * Units are arbitrary: the field is measured once and scaled to fit the
   * canvas, so these constants only control proportions.
   * NEAR_Z / (NEAR_Z + DEPTH) is the far/near width ratio — how sharply the
   * trapezoid tapers. CAM_Y is camera elevation, which sets vertical extent. */
  var FOCAL = 1;
  var NEAR_Z = 2.2;
  var DEPTH = 5.7; // far rows end up 0.28x the width of near rows
  var CAM_Y = 3.2; // makes the field ~1.15x taller than it is wide
  var X_HALF = 1.25;

  var AMP = 0.22; // wave height, in the same arbitrary units
  var WAVE_SUM = 1.35; // sum of the four wave amplitudes below

  var DOT = 0.013; // dot size per unit of screen scale
  var DOT_FILL = 0.78; // cap: fraction of the gap between neighbouring columns
  var REPEL = 0.3; // repulsion radius, as a fraction of field width
  var REPEL_PUSH = 0.55; // how far a centred point is thrown, in radii
  var SHADES = 22;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── Accent colour, read from the stylesheet so the field stays in sync ──
  function accentRGB() {
    var raw = getComputedStyle(document.documentElement)
      .getPropertyValue("--accent")
      .trim();
    var hex = raw.charAt(0) === "#" ? raw.slice(1) : "";
    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    if (hex.length !== 6) return [255, 143, 31];
    var n = parseInt(hex, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  var palette = [];
  function buildPalette() {
    var rgb = accentRGB();
    palette.length = 0;
    for (var i = 0; i < SHADES; i++) {
      var a = 0.08 + 0.9 * (i / (SHADES - 1));
      palette.push("rgba(" + rgb[0] + "," + rgb[1] + "," + rgb[2] + "," + a.toFixed(3) + ")");
    }
  }
  buildPalette();

  // ── Grid, rebuilt on resize ─────────────────────────────────────────────
  var w = 0, h = 0, dpr = 1;
  var cols = 0, rows = 0;
  var fit = 0, originX = 0, originY = 0, repelR = 0;

  var colX, colS1, colC1, colS2, colC2, colW4; // per-column constants
  var rowZ, rowS1, rowC1, rowS2, rowC2, rowW3; // per-row, refreshed each frame

  function layout() {
    var cssW = canvas.clientWidth;
    var cssH = canvas.clientHeight;
    if (!cssW || !cssH) return false;

    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = Math.round(cssW * dpr);
    h = Math.round(cssH * dpr);
    canvas.width = w;
    canvas.height = h;

    // Denser grids on wider canvases; ~4k points at desktop size.
    cols = Math.max(32, Math.min(76, Math.round(cssW / 6.5)));
    rows = Math.max(28, Math.min(60, Math.round(cols * 0.8)));

    colX = new Float32Array(cols);
    colS1 = new Float32Array(cols);
    colC1 = new Float32Array(cols);
    colS2 = new Float32Array(cols);
    colC2 = new Float32Array(cols);
    colW4 = new Float32Array(cols);
    for (var c = 0; c < cols; c++) {
      var x = (c / (cols - 1)) * 2 * X_HALF - X_HALF;
      colX[c] = x;
      colS1[c] = Math.sin(x * 0.8);
      colC1[c] = Math.cos(x * 0.8);
      colS2[c] = Math.sin(x * -1.6);
      colC2[c] = Math.cos(x * -1.6);
      colW4[c] = x * 3.9;
    }

    // Rows are spaced between two distributions. Even steps in z look correct
    // in world terms but leave huge gaps between the near rows on screen;
    // even steps in 1/z give evenly spaced screen rows but flatten the depth.
    // Leaning toward the latter keeps the near rows dense without losing the
    // compression at the horizon.
    var invNear = 1 / NEAR_Z;
    var invFar = 1 / (NEAR_Z + DEPTH);
    var SCREEN_BIAS = 0.6;

    rowZ = new Float32Array(rows);
    rowS1 = new Float32Array(rows);
    rowC1 = new Float32Array(rows);
    rowS2 = new Float32Array(rows);
    rowC2 = new Float32Array(rows);
    rowW3 = new Float32Array(rows);
    for (var r = 0; r < rows; r++) {
      var u = r / (rows - 1);
      var zLinear = NEAR_Z + u * DEPTH;
      var zScreen = 1 / (invNear + u * (invFar - invNear));
      rowZ[r] = zLinear + (zScreen - zLinear) * SCREEN_BIAS;
    }

    // Measure the flat field, then scale it to fit with room for wave crests.
    var sNear = FOCAL / NEAR_Z;
    var sFar = FOCAL / (NEAR_Z + DEPTH);
    var rawW = 2 * X_HALF * sNear;
    var rawH = CAM_Y * (sNear - sFar) + AMP * WAVE_SUM * sNear;

    fit = Math.min((w * 0.98) / rawW, (h * 0.94) / rawH);
    originX = w / 2;
    originY = (h - CAM_Y * (sNear - sFar) * fit) / 2 - CAM_Y * sFar * fit;
    repelR = rawW * fit * REPEL;
    return true;
  }

  // ── Pointer ─────────────────────────────────────────────────────────────
  var pointerX = 0, pointerY = 0; // smoothed, device pixels
  var targetX = 0, targetY = 0;
  var power = 0, targetPower = 0; // influence, faded in on first move

  function onPointerMove(e) {
    var rect = canvas.getBoundingClientRect();
    if (!rect.width) return;
    var scale = w / rect.width;
    targetX = (e.clientX - rect.left) * scale;
    targetY = (e.clientY - rect.top) * scale;
    if (targetPower === 0) {
      pointerX = targetX;
      pointerY = targetY;
    }
    targetPower = 1;
  }

  // ── Frame ───────────────────────────────────────────────────────────────
  function draw(t) {
    ctx.clearRect(0, 0, w, h);

    for (var r = 0; r < rows; r++) {
      var z = rowZ[r];
      rowS1[r] = Math.sin(z * 1.7 - t * 1.1);
      rowC1[r] = Math.cos(z * 1.7 - t * 1.1);
      rowS2[r] = Math.sin(z * 2.9 + t * 0.75);
      rowC2[r] = Math.cos(z * 2.9 + t * 0.75);
      rowW3[r] = 0.28 * Math.sin(z * 4.2 - t * 1.6);
    }

    var pushR = repelR * power;
    var minDot = 1;
    var shade = -1;

    for (var row = 0; row < rows; row++) {
      var depth = row / (rows - 1);
      var s = (FOCAL / rowZ[row]) * fit; // screen scale for this row
      var yFlat = originY + CAM_Y * s;
      var dotBase = s * DOT; // s already carries dpr via `fit`
      // Dots must never grow past the gap between columns, or a bright crest
      // fuses into a solid bar instead of reading as discrete points.
      var dotMax = ((2 * X_HALF * s) / (cols - 1)) * DOT_FILL;
      // Far rows sit near the horizon and fade out; height still dominates.
      var depthFade = 1 - depth * depth * 0.78;

      var s1r = rowS1[row], c1r = rowC1[row];
      var s2r = rowS2[row], c2r = rowC2[row];
      var w3 = rowW3[row];

      for (var col = 0; col < cols; col++) {
        // Four sines, split into per-row and per-column halves so the inner
        // loop is multiplies rather than ~4 trig calls per point.
        var hgt =
          0.55 * (colS1[col] * c1r + colC1[col] * s1r) +
          0.32 * (colS2[col] * c2r + colC2[col] * s2r) +
          w3 +
          0.2 * Math.sin(colW4[col] + t * 0.9);

        var px = originX + colX[col] * s;
        var py = yFlat - hgt * AMP * s;

        if (pushR > 0) {
          var dx = px - pointerX;
          var dy = py - pointerY;
          var d2 = dx * dx + dy * dy;
          if (d2 < pushR * pushR && d2 > 0.0001) {
            var d = Math.sqrt(d2);
            var f = 1 - d / pushR;
            // Quadratic falloff: points near the centre are thrown furthest,
            // so they pile into a compressed ring at the edge of the void.
            var amt = (pushR * REPEL_PUSH * f * f) / d;
            px += dx * amt;
            py += dy * amt;
          }
        }

        // Height drives both brightness and size, so wave crests read as
        // bright chunky ridges and troughs recede into the background.
        var lift = (hgt / WAVE_SUM + 1) * 0.5; // 0 … 1
        var bright = lift * lift * lift * depthFade * 1.9;
        if (bright > 1) bright = 1;

        var idx = (bright * (SHADES - 1) + 0.5) | 0;
        if (idx !== shade) {
          shade = idx;
          ctx.fillStyle = palette[idx];
        }

        var raw = dotBase * (0.6 + 1.4 * lift * lift);
        var size = (raw < dotMax ? raw : dotMax) | 0;
        if (size < minDot) size = minDot;
        ctx.fillRect(px | 0, py | 0, size, size);
      }
    }
  }

  // ── Loop ────────────────────────────────────────────────────────────────
  var raf = 0;
  var visible = true;
  var start = 0;

  function frame(now) {
    raf = 0;
    if (!start) start = now;

    power += (targetPower - power) * 0.06;
    pointerX += (targetX - pointerX) * 0.14;
    pointerY += (targetY - pointerY) * 0.14;

    draw((now - start) / 1000);
    if (visible) raf = requestAnimationFrame(frame);
  }

  function play() {
    if (!raf && visible && !reduceMotion) raf = requestAnimationFrame(frame);
  }

  function stop() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  }

  function reset() {
    if (!layout()) return;
    // The cached pointer position is in device pixels, so a resize invalidates
    // it. Fade the well out rather than leaving it stuck at a stale spot; the
    // next pointermove brings it straight back.
    targetPower = 0;
    if (reduceMotion) {
      power = targetPower = 0;
      draw(0);
    } else {
      // `start` is deliberately untouched — resetting it would snap the wave
      // back to t=0 on every resize.
      play();
    }
  }

  if (!reduceMotion) {
    window.addEventListener("pointermove", onPointerMove, { passive: true });

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
        if (visible) play();
        else stop();
      }).observe(canvas);
    }

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop();
      else play();
    });
  }

  if ("ResizeObserver" in window) {
    new ResizeObserver(reset).observe(canvas);
  } else {
    window.addEventListener("resize", reset);
  }

  reset();
})();
