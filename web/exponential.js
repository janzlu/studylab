(function () {
  function formatValue(n) {
    if (!isFinite(n)) return "";
    var rounded = Math.round(Number(n) * 1000) / 1000;
    if (Object.is(rounded, -0)) rounded = 0;
    return String(rounded);
  }

  function readBase(lesson) {
    var list = lesson && lesson.animation && lesson.animation.params;
    if (!list) return 2;
    for (var i = 0; i < list.length; i += 1) {
      if (list[i] && list[i].key === "base" && isFinite(Number(list[i].value))) {
        return Number(list[i].value);
      }
    }
    return 2;
  }

  function cssColor(name, fallback) {
    try {
      var value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return value || fallback;
    } catch (err) {
      return fallback;
    }
  }

  function expY(base, x) {
    if (!(base > 0) || base === 1) return NaN;
    return Math.pow(base, x);
  }

  function mount(canvas, lesson, hooks) {
    hooks = hooks || {};
    var ctx = canvas.getContext("2d");
    var base = readBase(lesson);
    var t = 0;
    var settled = false;
    var playing = false;
    var raf = 0;
    var stamp = null;
    var lastFocus = "";
    var cssW = 0;
    var cssH = 0;
    var dpr = 1;
    var observer = null;

    function domainOf() {
      var domain = lesson && lesson.animation && lesson.animation.domain;
      if (domain && domain.length === 2) return [Number(domain[0]), Number(domain[1])];
      return [-2, 4];
    }

    function rangeOf() {
      var range = lesson && lesson.animation && lesson.animation.range;
      if (range && range.length === 2) return [Number(range[0]), Number(range[1])];
      return [-1, 4];
    }

    function emit(focus, text) {
      if (hooks.onFocus) hooks.onFocus(focus);
      if (hooks.onCaption && text != null) hooks.onCaption(text);
    }

    function focusAt(progress) {
      if (progress < 0.25) return "domain";
      if (progress < 0.5) return "mono";
      if (progress < 0.75) return "point";
      return "reciprocal";
    }

    function sliderCaption(prev) {
      var word = base > 1 ? "递增" : "递减";
      var crossed = (prev > 1) !== (base > 1);
      if (crossed) return "底数跨过 1，函数改为" + word + "。图像仍过 (0, 1)。";
      if (base > prev + 1e-9) return "底数变大。函数仍" + word + "，仍过 (0, 1)。";
      if (base < prev - 1e-9) return "底数变小。函数仍" + word + "，仍过 (0, 1)。";
      return "函数仍" + word + "，图像仍过 (0, 1)。";
    }

    function layout() {
      var domain = domainOf();
      var range = rangeOf();
      var plotLeft = 36;
      var plotRight = Math.max(plotLeft + 20, cssW - 24);
      var plotTop = 16;
      var plotBottom = Math.max(plotTop + 20, cssH - 28);
      var xMin = domain[0];
      var xMax = domain[1];
      var yMin = range[0];
      var yMax = range[1];
      return {
        domain: domain,
        xToPx: function (x) { return plotLeft + (x - xMin) * ((plotRight - plotLeft) / (xMax - xMin || 1)); },
        yToPx: function (y) { return plotTop + (yMax - y) * ((plotBottom - plotTop) / (yMax - yMin || 1)); },
        plotLeft: plotLeft,
        plotRight: plotRight,
        plotTop: plotTop,
        plotBottom: plotBottom
      };
    }

    function strokeExp(box, which, from, to, color, width, dash) {
      if (to - from < 1e-4) return;
      var steps = Math.max(24, Math.ceil((to - from) / ((box.domain[1] - box.domain[0]) || 1) * 240));
      ctx.beginPath();
      var started = false;
      ctx.setLineDash(dash || []);
      for (var i = 0; i <= steps; i += 1) {
        var x = from + (to - from) * (i / steps);
        var y = expY(which, x);
        if (!isFinite(y)) continue;
        var px = box.xToPx(x);
        var py = box.yToPx(y);
        if (!started) {
          ctx.moveTo(px, py);
          started = true;
        } else ctx.lineTo(px, py);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.stroke();
      ctx.setLineDash([]);
    }

    function draw() {
      var colors = {
        ink: cssColor("--ink", "#0e1018"),
        line: cssColor("--line", "#d4c8af"),
        accent: cssColor("--accent", "#1c3b5a"),
        bronze: cssColor("--bronze", "#8b6f47"),
        bg: cssColor("--bg", "#f3ede2")
      };
      var box = layout();
      var head = box.domain[0] + t * (box.domain[1] - box.domain[0]);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, cssW, cssH);
      ctx.save();
      ctx.beginPath();
      ctx.rect(box.plotLeft, box.plotTop, box.plotRight - box.plotLeft, box.plotBottom - box.plotTop);
      ctx.clip();
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.beginPath();
      var x;
      for (x = Math.ceil(box.domain[0]); x <= box.domain[1]; x += 1) {
        var px = box.xToPx(x);
        ctx.moveTo(px, box.plotTop);
        ctx.lineTo(px, box.plotBottom);
      }
      var y;
      for (y = 0; y <= 4; y += 1) {
        var py = box.yToPx(y);
        ctx.moveTo(box.plotLeft, py);
        ctx.lineTo(box.plotRight, py);
      }
      ctx.stroke();
      var y0 = box.yToPx(0);
      var x0 = box.xToPx(0);
      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      ctx.moveTo(box.plotLeft, y0);
      ctx.lineTo(box.plotRight, y0);
      ctx.moveTo(x0, box.plotBottom);
      ctx.lineTo(x0, box.plotTop);
      ctx.stroke();
      strokeExp(box, 1 / base, box.domain[0], box.domain[1], colors.bronze, 1.4, [5, 4]);
      if (settled) strokeExp(box, base, box.domain[0], box.domain[1], colors.ink, 2.2);
      else {
        strokeExp(box, base, box.domain[0], head, colors.ink, 2.2);
        strokeExp(box, base, head, box.domain[1], "rgba(14, 16, 24, 0.28)", 1.5);
      }
      ctx.restore();
      ctx.beginPath();
      ctx.arc(box.xToPx(0), box.yToPx(1), 4.5, 0, Math.PI * 2);
      ctx.fillStyle = colors.bg;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = colors.accent;
      ctx.stroke();
      ctx.font = '12px "JetBrains Mono", ui-monospace, Menlo, monospace';
      ctx.fillStyle = colors.accent;
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillText("(0, 1)", box.xToPx(0) + 8, box.yToPx(1) - 8);
      ctx.fillStyle = colors.bronze;
      ctx.textAlign = "right";
      ctx.textBaseline = "top";
      ctx.fillText("倒数底 " + formatValue(1 / base), box.plotRight - 4, box.plotTop + 4);
      ctx.fillStyle = colors.ink;
      ctx.textAlign = "left";
      ctx.fillText("y", x0 + 8, box.plotTop + 14);
      ctx.textBaseline = "top";
      ctx.textAlign = "right";
      ctx.fillText("x", box.plotRight - 4, y0 + 6);
    }

    function tickFocus() {
      var focus = focusAt(t);
      if (focus === lastFocus) return;
      lastFocus = focus;
      var beats = (lesson && lesson.beats) || [];
      var text = "";
      for (var i = 0; i < beats.length; i += 1) {
        if (beats[i].focus === focus) text = beats[i].narration || "";
      }
      emit(focus, text);
    }

    function resize() {
      var rect = canvas.getBoundingClientRect();
      cssW = Math.max(1, rect.width);
      cssH = Math.max(1, rect.height);
      dpr = Math.max(1, window.devicePixelRatio || 1);
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
      if (stamp == null) stamp = now;
      var u = Math.min(1, (now - stamp) / 8000);
      t = u;
      if (u >= 1) {
        t = 1;
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
      if (settled || t >= 1 - 1e-3) {
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
      var prev = base;
      base = isFinite(Number(next.base)) ? Number(next.base) : prev;
      var was = playing;
      stopClock();
      settled = true;
      t = 1;
      draw();
      if (was && hooks.onPlaying) hooks.onPlaying(false);
      if (Math.abs(prev - base) > 1e-9) emit("mono", sliderCaption(prev));
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
    return { setParams: setParams, play: play, pause: pause, replay: replay, destroy: destroy };
  }

  var root = typeof window !== "undefined" ? window : globalThis;
  root.ExponentialStage = { mount: mount, formatValue: formatValue };
})();
