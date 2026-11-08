(function () {
  var OFFLINE = "讲解服务没连上。请先启动本机 8787 端口上的讲解服务，然后刷新页面。";
  var FILE_ERR = "请上传 8MB 以内的 png、jpeg 或 webp。";
  var MAX_BYTES = 8 * 1024 * 1024;
  var TYPES = { "image/png": 1, "image/jpeg": 1, "image/jpg": 1, "image/webp": 1 };

  var nav = document.querySelector(".nav");
  var upload = document.getElementById("upload");
  var fileInput = document.getElementById("file");
  var pick = document.getElementById("pick");
  var uploadLabel = document.getElementById("upload-label");
  var reselect = document.getElementById("reselect");
  var uploadError = document.getElementById("upload-error");
  var generateBtn = document.getElementById("generate");
  var generateLabel = document.getElementById("generate-label");
  var navGenerate = document.getElementById("nav-generate");
  var followup = document.getElementById("followup");
  var followupText = document.getElementById("followup-text");
  var followupActions = document.getElementById("followup-actions");
  var confirmYes = document.getElementById("confirm-yes");
  var confirmNo = document.getElementById("confirm-no");
  var formula = document.getElementById("formula");
  var parameterNote = document.getElementById("parameter-note");
  var anim = document.getElementById("anim");
  var canvas = document.getElementById("stage");
  var readoutFormula = document.getElementById("readout-formula");
  var readoutPeriod = document.getElementById("readout-period");
  var caption = document.getElementById("caption");
  var sliders = document.getElementById("sliders");
  var beatList = document.getElementById("beat-list");
  var checkList = document.getElementById("check-list");
  var checkForm = document.getElementById("check-form");
  var checkBanner = document.getElementById("check-banner");
  var submitCheck = document.getElementById("submit-check");
  var playBtn = document.getElementById("play");
  var replayBtn = document.getElementById("replay");
  var lessonTitle = document.getElementById("lesson-title");
  var lead = document.getElementById("lead");
  var conceptSinusoid = document.getElementById("concept-sinusoid");
  var conceptQuadratic = document.getElementById("concept-quadratic");
  var conceptLogarithm = document.getElementById("concept-logarithm");
  var conceptExponential = document.getElementById("concept-exponential");
  var conceptTrig = document.getElementById("concept-trig");

  var COPY = {
    sinusoid: {
      title: "正弦型函数",
      lead: "改一个参数，先想图像会怎么变，再看单位圆和波形。"
    },
    quadratic: {
      title: "二次函数",
      lead: "改一个参数，先想抛物线会怎么变，再看开口、对称轴和顶点。"
    },
    logarithm: {
      title: "对数函数",
      lead: "改底数之前，先判断会变成递增还是递减，再看图像是不是还过 (1, 0)。"
    },
    exponential: {
      title: "指数函数",
      lead: "改底数之前，先判断会变成递增还是递减，再看图像是不是还过 (0, 1)。"
    },
    trig: {
      title: "三角函数",
      lead: "拖动角之前，先想这个角的正弦是正还是负，再看单位圆上的点。"
    }
  };

  var state = {
    file: null,
    lesson: null,
    concept: "sinusoid",
    serviceUp: false,
    generating: false,
    stage: null,
    playing: false
  };

  function builtinLesson() {
    return {
      id: null,
      title: "正弦型函数 y = A sin(ωx + φ)",
      formula: "y = A sin(ωx + φ)",
      parameterNote: null,
      causal: [
        "A 决定离开平衡位置的最大距离，不改变周期。",
        "ω 决定周期 T = 2π/|ω|。|ω| 变大，波变得更密。",
        "φ>0 时图像向左平移 φ/|ω|；φ<0 时向右平移；φ=0 时不平移。"
      ],
      beats: [
        { id: "b1", title: "从单位圆展开", narration: "单位圆上的点转到角 t，它的纵坐标就是 sin t。把这个高度沿横轴展开，得到正弦波。", focus: "circle" },
        { id: "b2", title: "振幅 A", narration: "A 把波峰和波谷拉高或压低，周期不变。", focus: "A" },
        { id: "b3", title: "角频率与周期", narration: "ω 改变角走得有多快。周期是 T = 2π/|ω|。", focus: "omega" },
        { id: "b4", title: "初相", narration: "φ 是起步时的角度。φ>0 向左平移，φ<0 向右平移，φ=0 不平移。", focus: "phi" }
      ],
      animation: {
        type: "sinusoid",
        domain: [-6.2832, 6.2832],
        range: [-3, 3],
        params: [
          { key: "A", label: "A", name: "振幅", min: 0.5, max: 2.5, step: 0.1, value: 1 },
          { key: "omega", label: "ω", name: "角频率", min: 0.5, max: 3, step: 0.1, value: 1 },
          { key: "phi", label: "φ", name: "初相", min: -3.14, max: 3.14, step: 0.01, value: 0 }
        ]
      },
      checks: [
        { id: "c1", prompt: "A 从 1 改为 2，其他不变。周期怎么变？", choices: ["变为原来的 2 倍", "不变", "变为原来的一半"] },
        { id: "c2", prompt: "ω 从 1 改为 2，周期是多少？", choices: ["2π", "π", "π/2"] },
        { id: "c3", prompt: "φ 从 0 改为正数，图像往哪边平移？", choices: ["向右", "向左", "不平移"] }
      ]
    };
  }

  function builtinQuadratic() {
    return {
      id: null,
      title: "二次函数 y = a(x − h)² + k",
      formula: "y = a(x − h)² + k",
      conceptFamily: "quadratic",
      parameterNote: null,
      beats: [
        { id: "b1", title: "从 y = x² 出发", narration: "顶点在原点，开口向上，对称轴是 y 轴。", focus: "vertex" },
        { id: "b2", title: "开口 a", narration: "a>0 开口向上，a<0 开口向下。|a| 越大，开口越窄。", focus: "a" },
        { id: "b3", title: "对称轴 h", narration: "h 增大，对称轴向右移动。", focus: "h" },
        { id: "b4", title: "顶点高低 k", narration: "k 增大，顶点向上移动。", focus: "k" }
      ],
      animation: {
        type: "quadratic",
        domain: [-6, 6],
        range: [-8, 8],
        params: [
          { key: "a", label: "a", name: "开口", min: -2, max: 2, step: 0.1, value: 1 },
          { key: "h", label: "h", name: "对称轴", min: -3, max: 3, step: 0.5, value: 0 },
          { key: "k", label: "k", name: "顶点高低", min: -3, max: 3, step: 0.5, value: 0 }
        ]
      },
      checks: []
    };
  }

  function builtinLogarithm() {
    return {
      id: null,
      title: "对数函数 y = logₐ(x)",
      formula: "y = logₐ(x)",
      conceptFamily: "logarithm",
      parameterNote: null,
      beats: [
        { id: "b1", title: "对数在说什么", narration: "定义域是 x>0。", focus: "domain" },
        { id: "b2", title: "底数与单调性", narration: "a>1 时递增，0<a<1 时递减。", focus: "mono" },
        { id: "b3", title: "定点", narration: "图像过定点 (1, 0)。", focus: "point" },
        { id: "b4", title: "换成倒数", narration: "底数换成倒数后，图像关于 x 轴对称。", focus: "reciprocal" }
      ],
      animation: {
        type: "logarithm",
        domain: [0.15, 8],
        range: [-4, 4],
        params: [
          { key: "base", label: "a", name: "底数", min: 0.25, max: 4, step: 0.05, value: 2 }
        ]
      },
      checks: []
    };
  }

  function builtinExponential() {
    return {
      id: null,
      title: "指数函数 y = aˣ",
      formula: "y = aˣ",
      conceptFamily: "exponential",
      parameterNote: null,
      beats: [
        { id: "b1", title: "指数在说什么", narration: "定义域是全体实数，值域是 y>0。", focus: "domain" },
        { id: "b2", title: "底数与单调性", narration: "a>1 时递增，0<a<1 时递减。", focus: "mono" },
        { id: "b3", title: "定点", narration: "图像过定点 (0, 1)。", focus: "point" },
        { id: "b4", title: "换成倒数", narration: "底数换成倒数后，图像关于 y 轴对称。", focus: "reciprocal" }
      ],
      animation: {
        type: "exponential",
        domain: [-2, 4],
        range: [-1, 4],
        params: [
          { key: "base", label: "a", name: "底数", min: 0.25, max: 4, step: 0.05, value: 2 }
        ]
      },
      checks: []
    };
  }

  function builtinTrig() {
    return {
      id: null,
      title: "三角函数 sin θ，cos θ，tan θ",
      formula: "sin θ，cos θ，tan θ",
      conceptFamily: "trig",
      parameterNote: null,
      beats: [
        { id: "b1", title: "单位圆上的角", narration: "终边和单位圆的交点是 (cos θ, sin θ)。", focus: "circle" },
        { id: "b2", title: "正弦", narration: "sin θ 是纵坐标。", focus: "sin" },
        { id: "b3", title: "余弦", narration: "cos θ 是横坐标。", focus: "cos" },
        { id: "b4", title: "正切", narration: "tan θ = sin θ / cos θ。", focus: "tan" }
      ],
      animation: {
        type: "trig",
        domain: [-1.4, 1.4],
        range: [-1.4, 1.4],
        params: [
          { key: "theta", label: "θ", name: "角", min: 0, max: 6.28, step: 0.01, value: 1.05 }
        ]
      },
      checks: []
    };
  }

  function showUploadError(text) {
    uploadError.hidden = false;
    uploadError.textContent = text;
  }

  function clearUploadError() {
    uploadError.hidden = true;
    uploadError.textContent = "";
  }

  function showBanner(text) {
    checkBanner.hidden = false;
    checkBanner.textContent = text;
  }

  function clearBanner() {
    checkBanner.hidden = true;
    checkBanner.textContent = "";
  }

  function setBusy(on) {
    state.generating = on;
    generateBtn.disabled = on;
    navGenerate.disabled = on;
    confirmYes.disabled = on;
    confirmNo.disabled = on;
    generateLabel.textContent = on ? "正在生成" : "生成讲解";
  }

  function hideFollowup() {
    followup.hidden = true;
    followupText.textContent = "";
    followupActions.hidden = false;
  }

  function showAsked(text) {
    followup.hidden = false;
    followupText.textContent = text;
    followupActions.hidden = false;
  }

  function showDeclined(text) {
    followup.hidden = false;
    followupText.textContent = text;
    followupActions.hidden = true;
  }

  function fileAllowed(file) {
    var name = (file.name || "").toLowerCase();
    var extOk = /\.(png|jpe?g|webp)$/.test(name);
    var type = (file.type || "").toLowerCase();
    var typeOk = !!TYPES[type] || ((type === "" || type === "application/octet-stream") && extOk);
    return typeOk && file.size <= MAX_BYTES;
  }

  function acceptFile(file) {
    if (!fileAllowed(file)) {
      showUploadError(FILE_ERR);
      return;
    }
    state.file = file;
    uploadLabel.textContent = file.name;
    reselect.hidden = false;
    if (state.serviceUp) clearUploadError();
    else showUploadError(OFFLINE);
  }

  function familyOf(lesson) {
    var type = lesson && lesson.animation && lesson.animation.type;
    var families = { quadratic: 1, logarithm: 1, exponential: 1, trig: 1 };
    if (type && families[type]) return type;
    if (lesson && families[lesson.conceptFamily]) return lesson.conceptFamily;
    return "sinusoid";
  }

  function snapA(prev, raw) {
    var value = Number(raw);
    if (prev >= 0.5 && value < 0.5) return -0.5;
    if (prev <= -0.5 && value > -0.5) return 0.5;
    if (value > 2) return 2;
    if (value < -2) return -2;
    if (!isFinite(value) || Math.abs(value) < 0.5) return prev >= 0 ? 0.5 : -0.5;
    return Math.round(value * 10) / 10;
  }

  function snapBase(prev, raw) {
    var value = Number(raw);
    if (prev >= 1.25 && value < 1.25) return 0.8;
    if (prev <= 0.8 && value > 0.8) return 1.25;
    if (!isFinite(value)) return prev >= 1 ? 2 : 0.5;
    if (value >= 1) return Math.min(4, Math.max(1.25, Math.round(value * 20) / 20));
    return Math.min(0.8, Math.max(0.25, Math.round(value * 20) / 20));
  }

  function paramMap(lesson) {
    var map = {};
    var list = lesson && lesson.animation && lesson.animation.params;
    if (!list) return map;
    list.forEach(function (item) {
      if (item && item.key && isFinite(Number(item.value))) map[item.key] = Number(item.value);
    });
    return map;
  }

  function readSliderParams() {
    var map = paramMap(state.lesson || builtinLesson());
    Object.keys(map).forEach(function (key) {
      var input = document.getElementById("param-" + key);
      if (input) map[key] = Number(input.value);
    });
    return map;
  }

  function writeNarration(params) {
    if (!window.LessonNarration) return;
    var texts = window.LessonNarration.narrations(familyOf(state.lesson), params);
    Object.keys(texts).forEach(function (id) {
      var node = beatList.querySelector('[data-beat="' + id + '"] .beat-copy');
      if (node) node.textContent = texts[id];
    });
    var beats = state.lesson && state.lesson.beats;
    if (!beats) return;
    beats.forEach(function (beat) {
      if (beat && texts[beat.id]) beat.narration = texts[beat.id];
    });
  }

  function writeReadout(params) {
    var family = familyOf(state.lesson);
    if (family === "quadratic") {
      var fmt = window.QuadraticStage.formatValue;
      readoutPeriod.textContent = "顶点 (" + fmt(params.h) + ", " + fmt(params.k) + ")";
      return;
    }
    if (family === "logarithm") {
      readoutPeriod.textContent = params.base > 1 ? "递增，过 (1, 0)" : "递减，过 (1, 0)";
      return;
    }
    if (family === "exponential") {
      readoutPeriod.textContent = params.base > 1 ? "递增，过 (0, 1)" : "递减，过 (0, 1)";
      return;
    }
    if (family === "trig") {
      var fmt = window.LessonNarration ? window.LessonNarration.formatNumber : String;
      readoutPeriod.textContent = "sin " + fmt(Math.sin(params.theta)) + "，cos " + fmt(Math.cos(params.theta));
      return;
    }
    var text = window.SinusoidStage.formatPeriod(params.omega);
    readoutPeriod.textContent = text ? "T = " + text : "";
  }

  function highlight(focus) {
    var nodes = beatList.querySelectorAll(".beat");
    for (var i = 0; i < nodes.length; i += 1) {
      nodes[i].classList.toggle("is-current", nodes[i].getAttribute("data-focus") === focus);
    }
  }

  function setPlaying(on) {
    state.playing = on;
    playBtn.classList.toggle("is-on", on);
    playBtn.setAttribute("aria-pressed", on ? "true" : "false");
  }

  function mountStage(lesson) {
    if (state.stage) state.stage.destroy();
    var family = familyOf(lesson);
    var stages = {
      quadratic: window.QuadraticStage,
      logarithm: window.LogarithmStage,
      exponential: window.ExponentialStage,
      trig: window.TrigStage,
      sinusoid: window.SinusoidStage
    };
    var labels = {
      quadratic: "二次函数抛物线",
      logarithm: "对数函数图像",
      exponential: "指数函数图像",
      trig: "单位圆上的正弦、余弦和正切",
      sinusoid: "单位圆与正弦波形"
    };
    canvas.setAttribute("aria-label", labels[family] || labels.sinusoid);
    state.stage = (stages[family] || window.SinusoidStage).mount(canvas, lesson, {
      onFocus: highlight,
      onCaption: function (text) { caption.textContent = text || ""; },
      onPlaying: setPlaying
    });
  }

  function renderBeats(beats) {
    beatList.textContent = "";
    beats.forEach(function (beat, index) {
      var row = document.createElement("article");
      row.className = "beat";
      row.setAttribute("data-focus", beat.focus || "");
      row.setAttribute("data-beat", beat.id || "");
      var no = document.createElement("span");
      no.className = "beat-no";
      no.textContent = String(index + 1);
      var body = document.createElement("div");
      var title = document.createElement("h3");
      title.textContent = beat.title || "";
      var narration = document.createElement("p");
      narration.className = "beat-copy";
      narration.textContent = beat.narration || "";
      body.appendChild(title);
      body.appendChild(narration);
      row.appendChild(no);
      row.appendChild(body);
      beatList.appendChild(row);
    });
  }

  function renderChecks(checks) {
    checkList.textContent = "";
    clearBanner();
    checks.forEach(function (check, index) {
      var block = document.createElement("article");
      block.className = "question";
      block.setAttribute("data-id", check.id || "");
      var prompt = document.createElement("p");
      prompt.className = "prompt";
      prompt.textContent = (index + 1) + ". " + (check.prompt || "");
      var choices = document.createElement("div");
      choices.className = "choices";
      (check.choices || []).forEach(function (choice, choiceIndex) {
        var label = document.createElement("label");
        label.className = "choice";
        var input = document.createElement("input");
        input.type = "radio";
        input.name = "q-" + (check.id || index);
        input.value = String(choiceIndex);
        var text = document.createElement("span");
        text.textContent = choice;
        label.appendChild(input);
        label.appendChild(text);
        choices.appendChild(label);
      });
      var verdict = document.createElement("p");
      verdict.className = "verdict";
      verdict.hidden = true;
      var explain = document.createElement("p");
      explain.className = "explain";
      explain.hidden = true;
      block.appendChild(prompt);
      block.appendChild(choices);
      block.appendChild(verdict);
      block.appendChild(explain);
      checkList.appendChild(block);
    });
  }

  function renderSliders(lesson) {
    sliders.textContent = "";
    var list = (lesson.animation && lesson.animation.params) || [];
    list.forEach(function (item) {
      var wrap = document.createElement("div");
      wrap.className = "slider";
      var top = document.createElement("div");
      top.className = "slider-top";
      var name = document.createElement("label");
      name.htmlFor = "param-" + item.key;
      name.appendChild(document.createTextNode((item.name || item.key) + " "));
      var symbol = document.createElement("span");
      symbol.className = "mono";
      symbol.textContent = item.label || item.key;
      name.appendChild(symbol);
      var value = document.createElement("span");
      value.className = "mono";
      value.id = "val-" + item.key;
      value.textContent = String(item.value);
      var input = document.createElement("input");
      input.type = "range";
      input.id = "param-" + item.key;
      input.min = item.min;
      input.max = item.max;
      input.step = item.step;
      input.value = item.value;
      input.setAttribute("aria-label", (item.name || "") + " " + (item.label || item.key));
      input.addEventListener("input", function () {
        if (item.key === "a") {
          var prevA = Number(value.textContent);
          input.value = String(snapA(prevA, input.value));
        }
        if (item.key === "base") {
          var prevBase = Number(value.textContent);
          input.value = String(snapBase(prevBase, input.value));
        }
        value.textContent = input.value;
        var next = readSliderParams();
        writeReadout(next);
        writeNarration(next);
        if (state.stage) state.stage.setParams(next);
      });
      top.appendChild(name);
      top.appendChild(value);
      wrap.appendChild(top);
      wrap.appendChild(input);
      sliders.appendChild(wrap);
    });
  }

  function markConcept(concept) {
    state.concept = concept;
    var copy = COPY[concept] || COPY.sinusoid;
    lessonTitle.textContent = copy.title;
    lead.textContent = copy.lead;
    document.title = "研习 · " + copy.title;
    conceptSinusoid.classList.toggle("is-on", concept === "sinusoid");
    conceptQuadratic.classList.toggle("is-on", concept === "quadratic");
    conceptLogarithm.classList.toggle("is-on", concept === "logarithm");
    conceptExponential.classList.toggle("is-on", concept === "exponential");
    conceptTrig.classList.toggle("is-on", concept === "trig");
    conceptSinusoid.setAttribute("aria-selected", concept === "sinusoid" ? "true" : "false");
    conceptQuadratic.setAttribute("aria-selected", concept === "quadratic" ? "true" : "false");
    conceptLogarithm.setAttribute("aria-selected", concept === "logarithm" ? "true" : "false");
    conceptExponential.setAttribute("aria-selected", concept === "exponential" ? "true" : "false");
    conceptTrig.setAttribute("aria-selected", concept === "trig" ? "true" : "false");
  }

  function applyLesson(lesson) {
    state.lesson = lesson;
    markConcept(familyOf(lesson));
    var text = lesson.formula || "y = A sin(ωx + φ)";
    formula.textContent = text;
    readoutFormula.textContent = text;
    if (lesson.parameterNote) {
      parameterNote.hidden = false;
      parameterNote.textContent = lesson.parameterNote;
    } else {
      parameterNote.hidden = true;
      parameterNote.textContent = "";
    }
    renderBeats(lesson.beats || []);
    renderChecks(lesson.checks || []);
    renderSliders(lesson);
    writeReadout(paramMap(lesson));
    hideFollowup();
    mountStage(lesson);
  }

  async function loadSample(busy) {
    if (busy) setBusy(true);
    try {
      var query = state.concept === "sinusoid" ? "" : "?concept=" + encodeURIComponent(state.concept);
      var res = await fetch("/api/sample" + query);
      if (!res.ok) throw new Error("status");
      var data = await res.json();
      if (!data || !data.animation) throw new Error("shape");
      state.serviceUp = true;
      if (uploadError.textContent !== FILE_ERR) clearUploadError();
      applyLesson(data);
    } catch (err) {
      state.serviceUp = false;
      showUploadError(OFFLINE);
      var offline = {
        quadratic: builtinQuadratic,
        logarithm: builtinLogarithm,
        exponential: builtinExponential,
        trig: builtinTrig
      };
      applyLesson((offline[state.concept] || builtinLesson)());
    } finally {
      if (busy) setBusy(false);
    }
  }

  async function postLesson(body) {
    setBusy(true);
    hideFollowup();
    try {
      var res = await fetch("/api/lessons", { method: "POST", body: body });
      var data = null;
      try { data = await res.json(); } catch (err) { data = null; }
      if (res.status === 400 || res.status === 422) {
        var message = data && data.error ? data.error : "没有生成。";
        if (res.status === 422) message += "先看默认讲解，或换一张印刷体截图再试。";
        showUploadError(message);
        return;
      }
      if (!res.ok || !data) {
        state.serviceUp = false;
        showUploadError(OFFLINE);
        return;
      }
      if (data.animation) {
        state.serviceUp = true;
        clearUploadError();
        applyLesson(data);
        return;
      }
      var recognition = data.recognition || {};
      if (recognition.readFailed) {
        showUploadError(recognition.reason || "读图没有成功。请再试一次。");
        return;
      }
      if (typeof recognition.asked === "string" && recognition.asked.trim()) {
        showAsked(recognition.asked.trim());
        return;
      }
      if (typeof recognition.declined === "string" && recognition.declined.trim()) {
        showDeclined(recognition.declined.trim());
        return;
      }
      showUploadError("没有生成。换一张印刷体截图再试。");
    } catch (err) {
      state.serviceUp = false;
      showUploadError(OFFLINE);
    } finally {
      setBusy(false);
    }
  }

  function generate() {
    if (state.generating) return;
    if (!state.file) {
      loadSample(true);
      return;
    }
    if (!fileAllowed(state.file)) {
      showUploadError(FILE_ERR);
      return;
    }
    var body = new FormData();
    body.append("concept", state.concept);
    body.append("image", state.file);
    postLesson(body);
  }

  function collectAnswers() {
    var questions = checkList.querySelectorAll(".question");
    var answers = [];
    for (var i = 0; i < questions.length; i += 1) {
      var picked = questions[i].querySelector('input[type="radio"]:checked');
      if (!picked) return null;
      answers.push(Number(picked.value));
    }
    return answers;
  }

  function clearVerdicts() {
    var nodes = checkList.querySelectorAll(".verdict, .explain");
    for (var i = 0; i < nodes.length; i += 1) {
      nodes[i].hidden = true;
      nodes[i].textContent = "";
    }
  }

  checkForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    var answers = collectAnswers();
    if (!answers) {
      showBanner("三道题都要选完再交");
      return;
    }
    if (!state.serviceUp || !state.lesson || !state.lesson.id) {
      showBanner(OFFLINE);
      return;
    }
    submitCheck.disabled = true;
    clearVerdicts();
    try {
      var res = await fetch("/api/lessons/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lessonId: state.lesson.id, answers: answers })
      });
      if (!res.ok) throw new Error("status");
      var data = await res.json();
      if (typeof data.correct === "number" && typeof data.total === "number") {
        showBanner("对了 " + data.correct + " / " + data.total);
      } else {
        clearBanner();
      }
      (data.items || []).forEach(function (item) {
        var question = checkList.querySelector('.question[data-id="' + CSS.escape(String(item.id)) + '"]');
        if (!question) return;
        var verdict = question.querySelector(".verdict");
        var explain = question.querySelector(".explain");
        verdict.hidden = false;
        explain.hidden = false;
        verdict.textContent = item.ok ? "对" : "错";
        verdict.classList.toggle("is-ok", !!item.ok);
        verdict.classList.toggle("is-bad", !item.ok);
        explain.textContent = item.explain || "";
      });
    } catch (err) {
      state.serviceUp = false;
      showBanner(OFFLINE);
      showUploadError(OFFLINE);
    } finally {
      submitCheck.disabled = false;
    }
  });

  pick.addEventListener("click", function () { fileInput.click(); });
  fileInput.addEventListener("change", function () {
    var file = fileInput.files && fileInput.files[0];
    if (file) acceptFile(file);
    fileInput.value = "";
  });

  var dragDepth = 0;
  upload.addEventListener("dragenter", function (event) {
    event.preventDefault();
    dragDepth += 1;
    upload.classList.add("is-drag");
  });
  upload.addEventListener("dragover", function (event) { event.preventDefault(); });
  upload.addEventListener("dragleave", function () {
    dragDepth -= 1;
    if (dragDepth <= 0) {
      dragDepth = 0;
      upload.classList.remove("is-drag");
    }
  });
  upload.addEventListener("drop", function (event) {
    event.preventDefault();
    dragDepth = 0;
    upload.classList.remove("is-drag");
    var file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
    if (file) acceptFile(file);
  });
  window.addEventListener("dragover", function (event) {
    if (event.dataTransfer && Array.prototype.indexOf.call(event.dataTransfer.types, "Files") !== -1) event.preventDefault();
  });
  window.addEventListener("drop", function (event) {
    if (event.dataTransfer && Array.prototype.indexOf.call(event.dataTransfer.types, "Files") !== -1) event.preventDefault();
  });

  generateBtn.addEventListener("click", generate);
  navGenerate.addEventListener("click", function () {
    upload.scrollIntoView({ behavior: "smooth", block: "center" });
    if (state.file) generate();
  });
  confirmYes.addEventListener("click", function () {
    if (state.generating || !state.file) return;
    var body = new FormData();
    body.append("confirm", state.concept);
    body.append("concept", state.concept);
    body.append("image", state.file);
    postLesson(body);
  });
  confirmNo.addEventListener("click", function () {
    if (state.generating) return;
    var body = new FormData();
    body.append("confirm", "reject");
    body.append("concept", state.concept);
    postLesson(body);
  });

  document.querySelector(".brand").addEventListener("click", function (event) {
    event.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  window.addEventListener("scroll", function () {
    nav.classList.toggle("scrolled", window.scrollY > 4);
  }, { passive: true });

  playBtn.addEventListener("click", function () {
    if (!state.stage) return;
    if (state.playing) state.stage.pause();
    else state.stage.play();
  });
  replayBtn.addEventListener("click", function () { if (state.stage) state.stage.replay(); });
  canvas.addEventListener("pointerdown", function () { anim.focus(); });
  anim.addEventListener("keydown", function (event) {
    if (event.key !== " " && event.code !== "Space") return;
    if (event.target.closest && event.target.closest("button")) return;
    event.preventDefault();
    if (!state.stage) return;
    if (state.playing) state.stage.pause();
    else state.stage.play();
  });

  conceptSinusoid.addEventListener("click", function () {
    if (state.generating) return;
    state.concept = "sinusoid";
    hideFollowup();
    loadSample(true);
  });
  conceptQuadratic.addEventListener("click", function () {
    if (state.generating) return;
    state.concept = "quadratic";
    hideFollowup();
    loadSample(true);
  });
  conceptLogarithm.addEventListener("click", function () {
    if (state.generating) return;
    state.concept = "logarithm";
    hideFollowup();
    loadSample(true);
  });
  conceptExponential.addEventListener("click", function () {
    if (state.generating) return;
    state.concept = "exponential";
    hideFollowup();
    loadSample(true);
  });
  conceptTrig.addEventListener("click", function () {
    if (state.generating) return;
    state.concept = "trig";
    hideFollowup();
    loadSample(true);
  });

  loadSample(false);
})();
