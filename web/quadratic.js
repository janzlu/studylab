(function () {
  function formatValue(n) {
    if (!isFinite(n)) return "";
    var rounded = Math.round(Number(n) * 1000) / 1000;
    if (Object.is(rounded, -0)) rounded = 0;
    return String(rounded);
  }

  function readParams(lesson) {
    var found = { a: 1, h: 0, k: 0 };
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
      return [-6, 6];
    }

    function rangeOf() {
      var range = lesson && lesson.animation && lesson.animation.range;
      if (range && range.length === 2) return [Number(range[0]), Number(range[1])];
      return [-8, 8];
    }

    function yAt(x) {
      var dx = x - params.h;
      return params.a * dx * dx + params.k;
    }

    function emit(focus, text) {
      if (hooks.onFocus) hooks.onFocus(focus);
      if (hooks.onCaption && text != null) hooks.onCaption(text);
    }

    function focusAt(progress) {
      if (progress < 0.25) return "vertex";
      if (progress < 0.5) return "a";
      if (progress < 0.75) return "h";
      return "k";
    }

    function sliderCaption(key, prev) {
      if (key === "a") {
        var dir = params.a > 0 ? "向上" : "向下";
        var next = Math.abs(params.a);
        var old = Math.abs(prev.a);
        if (next > old + 1e-9) return "开口变为" + dir + "，并且变窄。";
        if (next < old - 1e-9) return "开口变为" + dir + "，并且变宽。";
        return "开口变为" + dir + "。";
      }
      if (key === "h") {
        var hx = formatValue(params.h);
        if (params.h > prev.h + 1e-9) return "对称轴向右移动，现在是 x = " + hx + "。";
        if (params.h < prev.h - 1e-9) return "对称轴向左移动，现在是 x = " + hx + "。";
        return "对称轴仍是 x = " + hx + "。";
      }
      var ky = formatValue(params.k);
      if (params.k > prev.k + 1e-9) return "顶点向上移动，现在是 y = " + ky + "。";
      if (params.k < prev.k - 1e-9) return "顶点向下移动，现在是 y = " + ky + "。";
      return "顶点高度仍是 y = " + ky + "。";
    }

    function layout() {
      var domain = domainOf();
      var range = rangeOf();
      var pad = 28;
      var plotLeft = pad + 8;
      var plotRight = Math.max(plotLeft + 20, cssW - pad);
      var plotTop = 16;
      var plotBottom = Math.max(plotTop + 20, cssH - 36);
      var xMin = domain[0];
      var xMax = domain[1];
      var yMin = range[0];
      var yMax = range[1];
      return {
        domain: domain,
        range: range,
        plotLeft: plotLeft,
        plotRight: plotRight,
        plotTop: plotTop,
        plotBottom: plotBottom,
        scaleX: (plotRight - plotLeft) / (xMax - xMin || 1),
        scaleY: (plotBottom - plotTop) / (yMax - yMin || 1),
        xToPx: function (x) { return plotLeft + (x - xMin) * ((plotRight - plotLeft) / (xMax - xMin || 1)); },
        yToPx: function (y) { return plotTop + (yMax - y) * ((plotBottom - plotTop) / (yMax - yMin || 1)); }
      };
    }

    function strokeCurve(box, from, to, color, width) {
      if (to - from < 1e-4) return;
      var span = box.domain[1] - box.domain[0] || 1;
      var steps = Math.max(24, Math.ceil((to - from) / span * 360));
      ctx.beginPath();
      var started = false;
      for (var i = 0; i <= steps; i += 1) {
        var x = from + (to - from) * (i / steps);
        var y = yAt(x);
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
      var x = Math.ceil(box.domain[0]);
      for (; x <= box.domain[1]; x += 1) {
        var px = box.xToPx(x);
        ctx.moveTo(px, box.plotTop);
        ctx.lineTo(px, box.plotBottom);
      }
      var y;
      for (y = Math.ceil(box.range[0]); y <= box.range[1]; y += 2) {
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

      var axis = box.xToPx(params.h);
      ctx.strokeStyle = colors.bronze;
      ctx.lineWidth = 1.25;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(axis, box.plotTop);
      ctx.lineTo(axis, box.plotBottom);
      ctx.stroke();
      ctx.setLineDash([]);

      if (settled) strokeCurve(box, box.domain[0], box.domain[1], colors.ink, 2.2);
      else {
        strokeCurve(box, box.domain[0], head, colors.ink, 2.2);
        strokeCurve(box, head, box.domain[1], "rgba(14, 16, 24, 0.28)", 1.5);
      }

      var vertexY = box.yToPx(params.k);
      ctx.restore();

      ctx.font = '12px "JetBrains Mono", ui-monospace, Menlo, monospace';
      ctx.fillStyle = colors.ink;
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillText("y", Math.min(box.plotRight - 14, x0 + 8), box.plotTop + 14);
      ctx.textBaseline = "top";
      ctx.textAlign = "right";
      ctx.fillText("x", box.plotRight - 4, y0 + 6);

      ctx.textAlign = "center";
      ctx.fillStyle = colors.bronze;
      ctx.fillText("x = " + formatValue(params.h), axis, box.plotBottom + 8);

      ctx.beginPath();
      ctx.arc(axis, vertexY, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = colors.bg;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = colors.accent;
      ctx.stroke();
      ctx.fillStyle = colors.accent;
      ctx.textAlign = axis > cssW * 0.7 ? "right" : "left";
      var labelX = axis > cssW * 0.7 ? axis - 8 : axis + 8;
      ctx.textBaseline = "bottom";
      ctx.fillText("顶点 (" + formatValue(params.h) + ", " + formatValue(params.k) + ")", labelX, vertexY - 8);
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
      if (stamp == null) {
        stamp = now;
        origin = t;
      }
      var span = Math.max(1e-6, 1 - origin);
      var u = Math.min(1, (now - stamp) / (8000 * span));
      t = origin + span * u;
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
      var prev = { a: params.a, h: params.h, k: params.k };
      params = {
        a: isFinite(Number(next.a)) ? Number(next.a) : prev.a,
        h: isFinite(Number(next.h)) ? Number(next.h) : prev.h,
        k: isFinite(Number(next.k)) ? Number(next.k) : prev.k
      };
      var changed = [];
      if (Math.abs(prev.a - params.a) > 1e-9) changed.push("a");
      if (Math.abs(prev.h - params.h) > 1e-9) changed.push("h");
      if (Math.abs(prev.k - params.k) > 1e-9) changed.push("k");
      var was = playing;
      stopClock();
      settled = true;
      t = 1;
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

    return { setParams: setParams, play: play, pause: pause, replay: replay, destroy: destroy };
  }

  var root = typeof window !== "undefined" ? window : globalThis;
  root.QuadraticStage = { mount: mount, formatValue: formatValue };
})();
