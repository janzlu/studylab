(function () {
  var TAU = Math.PI * 2;

  function gcd(a, b) {
    a = Math.abs(a);
    b = Math.abs(b);
    while (b) {
      var t = a % b;
      a = b;
      b = t;
    }
    return a || 1;
  }

  function formatPi(n, d) {
    var g = gcd(n, d);
    n = Math.abs(n / g);
    d = Math.abs(d / g);
    if (n === 0) return "0";
    var num = n === 1 ? "π" : n + "π";
    return d === 1 ? num : num + "/" + d;
  }

  function formatPeriod(omega) {
    var abs = Math.abs(Number(omega));
    if (!abs || !isFinite(abs)) return "";
    var ratio = 2 / abs;
    var d;
    for (d = 1; d <= 40; d += 1) {
      var n = Math.round(ratio * d);
      if (Math.abs(n / d - ratio) <= 1e-3) return formatPi(n, d);
    }
    return ((TAU) / abs).toFixed(3);
  }

  function formatValue(n) {
    if (!isFinite(n)) return "";
    return String(Math.round(n * 1000) / 1000);
  }

  function readParams(lesson) {
    var found = { A: 1, omega: 1, phi: 0 };
    var list = lesson && lesson.animation && lesson.animation.params;
    if (!list) return found;
    for (var i = 0; i < list.length; i += 1) {
      var item = list[i];
      if (!item || found[item.key] === undefined) continue;
      var value = Number(item.value);
      if (isFinite(value)) found[item.key] = value;
    }
    return found;
  }

  function cssColor(name, fallback) {
    try {
      var value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return value || fallback;
    } catch (err) {
      return fallback;
    }
  }

  function mount(canvas, lesson, hooks) {
    hooks = hooks || {};
    var ctx = canvas.getContext("2d");
    var params = readParams(lesson);
    var t = 0;
    var settled = false;
    var playing = false;
    var raf = 0;
    var stamp = null;
    var origin = 0;
    var lastFocus = "";
    var cssW = 0;
    var cssH = 0;
    var dpr = 1;
    var observer = null;

    function domainOf() {
      var domain = lesson && lesson.animation && lesson.animation.domain;
      if (domain && domain.length === 2) return [Number(domain[0]), Number(domain[1])];
      return [-TAU, TAU];
    }

    function rangeOf() {
      var range = lesson && lesson.animation && lesson.animation.range;
      if (range && range.length === 2) return [Number(range[0]), Number(range[1])];
      return [-3, 3];
    }

    function emit(focus, text) {
      lastFocus = focus;
      if (hooks.onFocus) hooks.onFocus(focus);
      if (hooks.onCaption && text != null) hooks.onCaption(text);
    }

    function focusAt(time) {
      var p = time / TAU;
      if (p < 0.25) return "circle";
      if (p < 0.5) return "A";
      if (p < 0.75) return "omega";
      return "phi";
    }

    function captionFor(focus) {
      var beats = (lesson && lesson.beats) || [];
      var causal = (lesson && lesson.causal) || [];
      var index = { A: 0, omega: 1, phi: 2 }[focus];
      if (index !== undefined && causal[index]) return causal[index];
      for (var i = 0; i < beats.length; i += 1) {
        if (beats[i].focus === focus) return beats[i].narration || "";
      }
      return "";
    }

    function tickFocus() {
      var focus = focusAt(t);
      if (focus === lastFocus) return;
      emit(focus, captionFor(focus));
    }

    function sliderCaption(key, prev) {
      var period = formatPeriod(params.omega);
      if (key === "A") return "波峰变为当前的 " + formatValue(params.A) + "，周期仍是 " + period + "。";
      if (key === "omega") {
        var next = Math.abs(params.omega);
        var old = Math.abs(prev.omega);
        if (next > old + 1e-9) return "周期变为 " + period + "，图像变密。";
        if (next < old - 1e-9) return "周期变为 " + period + "，图像变疏。";
        return "周期变为 " + period + "。";
      }
      var shift = formatValue(Math.abs(params.phi) / Math.max(1e-9, Math.abs(params.omega)));
      if (params.phi > 1e-8) return "图像向左平移 " + shift + "。";
      if (params.phi < -1e-8) return "图像向右平移 " + shift + "。";
      return "图像不平移。";
    }

    function layout() {
      var domain = domainOf();
      var range = rangeOf();
      var padTop = 20;
      var padBottom = Math.max(42, Math.min(54, cssH * 0.13));
      var plotTop = padTop;
      var plotBottom = Math.max(plotTop + 20, cssH - padBottom);
      var plotH = plotBottom - plotTop;
      var yMin = range[0];
      var yMax = range[1];
      var scaleY = plotH / (yMax - yMin || 1);
      var split = Math.round(cssW * 0.5);
      var waveLeft = split + 12;
      var waveRight = Math.max(waveLeft + 20, cssW - 28);
      var xMin = domain[0];
      var xMax = domain[1];
      var scaleX = (waveRight - waveLeft) / (xMax - xMin || 1);
      return {
        domain: domain,
        range: range,
        plotTop: plotTop,
        plotBottom: plotBottom,
        split: split,
        waveLeft: waveLeft,
        waveRight: waveRight,
        scaleX: scaleX,
        scaleY: scaleY,
        xToPx: function (x) { return waveLeft + (x - xMin) * scaleX; },
        yToPx: function (y) { return plotTop + (yMax - y) * scaleY; }
      };
    }

    function periodSpan(box) {
      var omega = params.omega;
      var abs = Math.abs(omega);
      if (!abs) return null;
      var width = TAU / abs;
      var d0 = box.domain[0];
      var d1 = box.domain[1];
      var start = -params.phi / omega;
      if (!isFinite(start)) start = d0;
      if (!(start >= d0 - 1e-4 && start + width <= d1 + 1e-4)) {
        var k = Math.ceil((d0 - start) / width);
        if (isFinite(k)) start += k * width;
        if (start + width > d1 + 1e-3) start = d1 - width;
      }
      if (start < d0 - 1e-3) return null;
      var end = Math.min(d1, start + width);
      if (end - start < width * 0.5) return null;
      return [start, end];
    }

    function strokeWave(box, from, to, color, width) {
      if (to - from < 1e-4) return;
      var steps = Math.max(32, Math.ceil(((to - from) / (box.domain[1] - box.domain[0] || 1)) * 420));
      ctx.beginPath();
      for (var i = 0; i <= steps; i += 1) {
        var x = from + (to - from) * (i / steps);
        var y = params.A * Math.sin(params.omega * x + params.phi);
        var px = box.xToPx(x);
        var py = box.yToPx(y);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.stroke();
    }

    function peakX(box) {
      var omega = params.omega;
      if (!omega) return null;
      var best = null;
      var bestScore = Infinity;
      for (var k = -8; k <= 8; k += 1) {
        var x = (Math.PI / 2 + TAU * k - params.phi) / omega;
        if (x < box.domain[0] + 0.08 || x > box.domain[1] - 0.08) continue;
        var score = x >= 0 ? x : 100 + Math.abs(x);
        if (score < bestScore) {
          bestScore = score;
          best = x;
        }
      }
      return best;
    }

    function draw() {
      if (!ctx || cssW < 2 || cssH < 2) return;
      var colors = {
        ink: cssColor("--ink", "#0e1018"),
        line: cssColor("--line", "#d4c8af"),
        accent: cssColor("--accent", "#1c3b5a"),
        bronze: cssColor("--bronze", "#8b6f47"),
        bg: cssColor("--bg", "#f3ede2")
      };
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, cssW, cssH);
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      if (!lesson || !lesson.animation || lesson.animation.type !== "sinusoid") return;

      var box = layout();
      var y0 = box.yToPx(0);
      var axisX = box.xToPx(0);
      var head = Math.min(Math.max(t, box.domain[0]), box.domain[1]);

      ctx.save();
      ctx.beginPath();
      ctx.rect(box.waveLeft, box.plotTop, box.waveRight - box.waveLeft, box.plotBottom - box.plotTop);
      ctx.clip();

      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.beginPath();
      var x = Math.ceil(box.domain[0] / (Math.PI / 2)) * (Math.PI / 2);
      for (; x <= box.domain[1] + 1e-6; x += Math.PI / 2) {
        if (Math.abs(x) < 1e-3) continue;
        var px = box.xToPx(x);
        ctx.moveTo(px, box.plotTop);
        ctx.lineTo(px, box.plotBottom);
      }
      var y;
      for (y = Math.ceil(box.range[0]); y <= box.range[1]; y += 1) {
        if (y === 0) continue;
        var py = box.yToPx(y);
        ctx.moveTo(box.waveLeft, py);
        ctx.lineTo(box.waveRight, py);
      }
      ctx.stroke();

      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      ctx.moveTo(box.waveLeft, y0);
      ctx.lineTo(box.waveRight - 2, y0);
      ctx.moveTo(axisX, box.plotBottom);
      ctx.lineTo(axisX, box.plotTop + 2);
      ctx.stroke();
      arrow(box.waveRight - 10, y0, box.waveRight - 1, y0);
      arrow(axisX, box.plotTop + 10, axisX, box.plotTop + 1);

      if (settled) strokeWave(box, box.domain[0], box.domain[1], colors.ink, 2.2);
      else {
        strokeWave(box, box.domain[0], head, colors.ink, 2.2);
        strokeWave(box, head, box.domain[1], "rgba(14, 16, 24, 0.28)", 1.5);
      }

      var crest = peakX(box);
      var crestPx = 0;
      var crestPy = 0;
      if (crest !== null) {
        crestPx = box.xToPx(crest);
        crestPy = box.yToPx(params.A);
        ctx.strokeStyle = colors.bronze;
        ctx.lineWidth = 1.25;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(crestPx, y0);
        ctx.lineTo(crestPx, crestPy);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      ctx.restore();
      if (crest !== null) {
        var crestText = "A=" + formatValue(params.A);
        var crestAlign = crestPx + 52 > box.waveRight ? "right" : "left";
        var crestLabelX = crestAlign === "right" ? crestPx - 8 : crestPx + 8;
        label(colors, crestText, crestLabelX, Math.max(box.plotTop + 10, crestPy - 12), crestAlign);
      }

      ctx.font = 'italic 16px "Songti SC", STSong, serif';
      ctx.fillStyle = colors.ink;
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillText("y", Math.min(box.waveRight - 18, axisX + 8), box.plotTop + 16);
      ctx.textBaseline = "top";
      ctx.fillText("x", box.waveRight - 12, y0 + 6);

      var span = periodSpan(box);
      if (span) {
        var p0 = Math.max(box.waveLeft, Math.min(box.xToPx(span[0]), box.waveRight));
        var p1 = Math.max(box.waveLeft, Math.min(box.xToPx(span[1]), box.waveRight));
        if (p1 - p0 > 12) {
          var by = box.plotBottom + 16;
          ctx.strokeStyle = colors.bronze;
          ctx.lineWidth = 1.25;
          ctx.beginPath();
          ctx.moveTo(p0, by - 5);
          ctx.lineTo(p0, by + 5);
          ctx.moveTo(p0, by);
          ctx.lineTo(p1, by);
          ctx.moveTo(p1, by - 5);
          ctx.lineTo(p1, by + 5);
          ctx.stroke();
          label(colors, formatPeriod(params.omega), (p0 + p1) / 2, by - 12, "center");
        }
      }

      var theta = params.omega * t + params.phi;
      var R = Math.abs(params.A) * box.scaleY;
      var cx = box.split * 0.5;
      var cy = y0;
      var cpx = cx + R * Math.cos(theta);
      var cpy = cy - R * Math.sin(theta);
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, box.split, cssH);
      ctx.clip();
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.moveTo(cx - R - 10, cy);
      ctx.lineTo(cx + R + 10, cy);
      ctx.moveTo(cx, cy + R + 10);
      ctx.lineTo(cx, cy - R - 10);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.arc(cx, cy, Math.max(R, 0.5), 0, TAU);
      ctx.stroke();

      var shown = theta % TAU;
      if (shown < 0) shown += TAU;
      if (shown > 0.08 && R > 8) {
        var arcR = Math.max(12, Math.min(R * 0.34, 28));
        ctx.strokeStyle = colors.bronze;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        var stepsArc = Math.max(8, Math.ceil(shown / TAU * 48));
        for (var s = 0; s <= stepsArc; s += 1) {
          var a = shown * (s / stepsArc);
          var ax = cx + arcR * Math.cos(a);
          var ay = cy - arcR * Math.sin(a);
          if (s === 0) ctx.moveTo(ax, ay);
          else ctx.lineTo(ax, ay);
        }
        ctx.stroke();
      }

      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cpx, cpy);
      ctx.stroke();
      ctx.restore();

      var wpx = box.xToPx(t);
      var wpy = box.yToPx(params.A * Math.sin(theta));
      ctx.strokeStyle = colors.bronze;
      ctx.lineWidth = 1.25;
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      ctx.moveTo(cpx, cpy);
      ctx.lineTo(wpx, wpy);
      ctx.stroke();
      ctx.setLineDash([]);

      dot(colors, cpx, cpy);
      dot(colors, wpx, wpy);

      function arrow(x0, y0, x1, y1) {
        var ang = Math.atan2(y1 - y0, x1 - x0);
        var size = 6;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x1 - size * Math.cos(ang - 0.45), y1 - size * Math.sin(ang - 0.45));
        ctx.moveTo(x1, y1);
        ctx.lineTo(x1 - size * Math.cos(ang + 0.45), y1 - size * Math.sin(ang + 0.45));
        ctx.stroke();
      }

      function label(palette, text, x, y, align) {
        ctx.font = '12px "JetBrains Mono", ui-monospace, Menlo, monospace';
        ctx.textAlign = align || "left";
        ctx.textBaseline = "middle";
        var w = ctx.measureText(text).width;
        var left = x;
        if (align === "center") left = x - w / 2;
        if (align === "right") left = x - w;
        ctx.fillStyle = palette.bg;
        ctx.fillRect(left - 3, y - 8, w + 6, 16);
        ctx.fillStyle = palette.ink;
        ctx.fillText(text, x, y);
      }

      function dot(palette, x, y) {
        ctx.beginPath();
        ctx.arc(x, y, 4.5, 0, TAU);
        ctx.fillStyle = palette.bg;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = palette.accent;
        ctx.stroke();
      }
    }

    function resize() {
      var rect = canvas.getBoundingClientRect();
      cssW = Math.max(1, rect.width);
      cssH = Math.max(1, rect.height);
      dpr = Math.max(1, (typeof window !== "undefined" && window.devicePixelRatio) || 1);
      var bw = Math.round(cssW * dpr);
      var bh = Math.round(cssH * dpr);
      if (canvas.width !== bw || canvas.height !== bh) {
        canvas.width = bw;
        canvas.height = bh;
      }
      draw();
    }

    function stopClock() {
      playing = false;
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
    }

    function frame(now) {
      if (!playing) return;
      if (stamp == null) {
        stamp = now;
        origin = t;
      }
      var span = Math.max(1e-6, TAU - origin);
      var dur = 8000 * (span / TAU);
      var u = Math.min(1, (now - stamp) / dur);
      t = origin + span * u;
      if (u >= 1) {
        t = TAU;
        settled = true;
        stopClock();
        draw();
        tickFocus();
        if (hooks.onPlaying) hooks.onPlaying(false);
        return;
      }
      tickFocus();
      draw();
      raf = requestAnimationFrame(frame);
    }

    function play() {
      if (playing) return;
      if (settled || t >= TAU - 1e-3) {
        settled = false;
        t = 0;
        lastFocus = "";
      }
      playing = true;
      stamp = null;
      if (hooks.onPlaying) hooks.onPlaying(true);
      tickFocus();
      raf = requestAnimationFrame(frame);
    }

    function pause() {
      var was = playing;
      stopClock();
      draw();
      if (was && hooks.onPlaying) hooks.onPlaying(false);
    }

    function replay() {
      stopClock();
      settled = false;
      t = 0;
      lastFocus = "";
      play();
    }

    function setParams(next) {
      var prev = { A: params.A, omega: params.omega, phi: params.phi };
      params = {
        A: isFinite(Number(next.A)) ? Number(next.A) : prev.A,
        omega: isFinite(Number(next.omega)) ? Number(next.omega) : prev.omega,
        phi: isFinite(Number(next.phi)) ? Number(next.phi) : prev.phi
      };
      var changed = [];
      if (Math.abs(prev.A - params.A) > 1e-9) changed.push("A");
      if (Math.abs(prev.omega - params.omega) > 1e-9) changed.push("omega");
      if (Math.abs(prev.phi - params.phi) > 1e-9) changed.push("phi");
      var was = playing;
      stopClock();
      settled = true;
      t = TAU;
      draw();
      if (was && hooks.onPlaying) hooks.onPlaying(false);
      if (changed.length === 1) emit(changed[0], sliderCaption(changed[0], prev));
    }

    function destroy() {
      stopClock();
      if (observer) observer.disconnect();
      observer = null;
    }

    if (typeof ResizeObserver !== "undefined") {
      observer = new ResizeObserver(resize);
      observer.observe(canvas);
    }
    resize();
    play();

    return {
      setParams: setParams,
      play: play,
      pause: pause,
      replay: replay,
      destroy: destroy
    };
  }

  var root = typeof window !== "undefined" ? window : globalThis;
  root.SinusoidStage = {
    mount: mount,
    formatPeriod: formatPeriod
  };
})();
