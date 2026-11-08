(function () {
  function cssColor(name, fallback) {
    try {
      var value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return value || fallback;
    } catch (err) {
      return fallback;
    }
  }

  function readTheta(lesson) {
    var list = lesson && lesson.animation && lesson.animation.params;
    if (!list) return 1.05;
    for (var i = 0; i < list.length; i += 1) {
      if (list[i] && list[i].key === "theta" && isFinite(Number(list[i].value))) {
        return Number(list[i].value);
      }
    }
    return 1.05;
  }

  function mount(canvas, lesson, hooks) {
    hooks = hooks || {};
    var ctx = canvas.getContext("2d");
    var theta = readTheta(lesson);
    var shown = 0;
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

    function emit(focus, text) {
      if (hooks.onFocus) hooks.onFocus(focus);
      if (hooks.onCaption && text != null) hooks.onCaption(text);
    }

    function focusAt(progress) {
      if (progress < 0.25) return "circle";
      if (progress < 0.5) return "sin";
      if (progress < 0.75) return "cos";
      return "tan";
    }

    function formatShort(n) {
      if (!isFinite(n)) return "";
      var rounded = Math.round(n * 1000) / 1000;
      return String(rounded);
    }

    function sliderCaption() {
      var sine = formatShort(Math.sin(theta));
      var cosine = formatShort(Math.cos(theta));
      return "θ 变为 " + formatShort(theta) + "。sin = " + sine + "，cos = " + cosine + "。";
    }

    function layout() {
      var plotLeft = 28;
      var plotRight = Math.max(plotLeft + 20, cssW - 16);
      var plotTop = 16;
      var plotBottom = Math.max(plotTop + 20, cssH - 20);
      var radius = Math.min(plotRight - plotLeft, plotBottom - plotTop) * 0.36;
      return {
        originX: (plotLeft + plotRight) / 2,
        originY: (plotTop + plotBottom) / 2,
        radius: radius,
        plotLeft: plotLeft,
        plotRight: plotRight,
        plotTop: plotTop,
        plotBottom: plotBottom
      };
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
      var angle = settled ? theta : shown;
      var cosine = Math.cos(angle);
      var sine = Math.sin(angle);
      var ox = box.originX;
      var oy = box.originY;
      var radius = box.radius;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, cssW, cssH);
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(box.plotLeft, oy);
      ctx.lineTo(box.plotRight, oy);
      ctx.moveTo(ox, box.plotBottom);
      ctx.lineTo(ox, box.plotTop);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(ox, oy, radius, 0, Math.PI * 2);
      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = 1.25;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(ox + cosine * radius, oy);
      ctx.strokeStyle = colors.bronze;
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(ox + cosine * radius, oy);
      ctx.lineTo(ox + cosine * radius, oy - sine * radius);
      ctx.strokeStyle = colors.accent;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(ox + cosine * radius, oy - sine * radius);
      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(ox, oy, Math.max(16, radius * 0.22), 0, -angle, angle < 0);
      ctx.strokeStyle = colors.bronze;
      ctx.lineWidth = 1.25;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(ox + cosine * radius, oy - sine * radius, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = colors.bg;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = colors.accent;
      ctx.stroke();
      ctx.font = '12px "JetBrains Mono", ui-monospace, Menlo, monospace';
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillStyle = colors.accent;
      ctx.fillText("sin", ox + cosine * radius + 8, oy - sine * radius - 4);
      ctx.fillStyle = colors.bronze;
      ctx.textBaseline = "top";
      ctx.fillText("cos", ox + cosine * radius * 0.45, oy + 6);
      ctx.fillStyle = colors.ink;
      ctx.fillText("x", box.plotRight - 12, oy + 6);
      ctx.textBaseline = "top";
      ctx.fillText("y", ox + 6, box.plotTop + 2);
    }

    function tickFocus() {
      var progress = settled ? 1 : shown / (Math.PI * 2);
      var focus = focusAt(Math.min(1, Math.max(0, progress)));
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
        origin = shown;
      }
      var end = Math.PI * 2;
      var span = Math.max(1e-6, end - origin);
      var u = Math.min(1, (now - stamp) / (8000 * (span / end)));
      shown = origin + span * u;
      if (u >= 1) {
        settled = true;
        shown = theta;
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
      if (settled) {
        settled = false;
        shown = 0;
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
      shown = 0;
      lastFocus = "";
      play();
    }

    function setParams(next) {
      var prev = theta;
      theta = isFinite(Number(next.theta)) ? Number(next.theta) : prev;
      var was = playing;
      stopClock();
      settled = true;
      shown = theta;
      draw();
      if (was && hooks.onPlaying) hooks.onPlaying(false);
      if (Math.abs(prev - theta) > 1e-9) emit("sin", sliderCaption());
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
  root.TrigStage = { mount: mount };
})();
