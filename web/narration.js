(function (root, factory) {
  var api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.LessonNarration = api;
})(typeof window !== "undefined" ? window : null, function () {
  function gcd(a, b) {
    while (b) {
      var t = a % b;
      a = b;
      b = t;
    }
    return a;
  }

  function asIntegerRatio(value) {
    var sign = value < 0 ? -1n : 1n;
    var buffer = new ArrayBuffer(8);
    var view = new DataView(buffer);
    view.setFloat64(0, Math.abs(value));
    var hi = BigInt(view.getUint32(0));
    var lo = BigInt(view.getUint32(4));
    var bits = (hi << 32n) | lo;
    var biased = Number((bits >> 52n) & 0x7ffn);
    var mant = bits & ((1n << 52n) - 1n);
    var exp;
    if (biased === 0) {
      exp = -1022 - 52;
    } else {
      mant |= 1n << 52n;
      exp = biased - 1023 - 52;
    }
    var numerator = mant;
    var denominator = 1n;
    if (exp > 0) numerator <<= BigInt(exp);
    else if (exp < 0) denominator <<= BigInt(-exp);
    var divisor = gcd(numerator, denominator);
    return [sign * (numerator / divisor), denominator / divisor];
  }

  function limitDenominator(numerator, denominator, maxDenominator) {
    var cap = BigInt(maxDenominator);
    var sign = numerator < 0n ? -1n : 1n;
    var originalN = numerator < 0n ? -numerator : numerator;
    var originalD = denominator;
    if (originalD <= cap) return [sign * originalN, originalD];
    var p0 = 0n;
    var q0 = 1n;
    var p1 = 1n;
    var q1 = 0n;
    var n = originalN;
    var d = originalD;
    while (d !== 0n) {
      var a = n / d;
      var q2 = q0 + a * q1;
      if (q2 > cap) break;
      var nextP = p0 + a * p1;
      var nextQ = q2;
      p0 = p1;
      q0 = q1;
      p1 = nextP;
      q1 = nextQ;
      var remainder = n - a * d;
      n = d;
      d = remainder;
    }
    var k = (cap - q0) / q1;
    var bound1N = p0 + k * p1;
    var bound1D = q0 + k * q1;
    var left = absBig(p1 * originalD - originalN * q1) * bound1D;
    var right = absBig(bound1N * originalD - originalN * bound1D) * q1;
    if (left <= right) return [sign * p1, q1];
    return [sign * bound1N, bound1D];
  }

  function absBig(value) {
    return value < 0n ? -value : value;
  }

  function formatNumber(value) {
    var number = Number(value);
    if (!isFinite(number)) return "";
    var negative = number < 0;
    var scaled = Math.abs(number).toFixed(8);
    var parts = scaled.split(".");
    var whole = parts[0];
    var frac = (parts[1] || "").padEnd(8, "0");
    var keep = frac.slice(0, 6);
    var rest = frac.slice(6);
    var bump = rest[0] > "5" || (rest[0] === "5" && (/[1-9]/.test(rest.slice(1)) || Number(keep[keep.length - 1]) % 2 === 1));
    var body = whole + keep;
    if (bump) body = incrementDigits(body);
    body = body.replace(/^0+(?=\d)/, "");
    var split = body.length - 6;
    var head = split > 0 ? body.slice(0, split) : "0";
    var tail = (split > 0 ? body.slice(split) : body.padStart(6, "0")).replace(/0+$/, "");
    var text = tail ? head + "." + tail : head;
    if (text === "0") return "0";
    return (negative ? "-" : "") + text;
  }

  function incrementDigits(digits) {
    var chars = digits.split("");
    var carry = 1;
    for (var i = chars.length - 1; i >= 0 && carry; i -= 1) {
      var sum = Number(chars[i]) + carry;
      chars[i] = String(sum % 10);
      carry = sum >= 10 ? 1 : 0;
    }
    if (carry) chars.unshift("1");
    return chars.join("");
  }

  function piText(numerator, denominator) {
    if (denominator === 1) return numerator === 1 ? "π" : numerator + "π";
    if (numerator === 1) return "π/" + denominator;
    return numerator + "π/" + denominator;
  }

  function formatPeriod(omega) {
    var magnitude = Math.abs(Number(omega));
    if (!(magnitude > 0) || !isFinite(magnitude)) return "";
    var ratio = 2 / magnitude;
    var exact = asIntegerRatio(ratio);
    var limited = limitDenominator(exact[0], exact[1], 100);
    var numerator = Number(limited[0]);
    var denominator = Number(limited[1]);
    var approx = numerator / denominator;
    var truePeriod = (Math.PI * 2) / magnitude;
    if (Math.abs(approx - ratio) < 1e-6 && Math.abs(approx * Math.PI - truePeriod) < 1e-6) {
      return piText(Math.abs(numerator), denominator);
    }
    return truePeriod.toFixed(6);
  }

  function sinusoid(params) {
    var amplitude = Number(params.A);
    var omega = Number(params.omega);
    var phi = Number(params.phi);
    var period = formatPeriod(omega);
    var phase;
    if (phi > 1e-9) {
      phase = "φ 是起步时的角度。当前 φ = " + formatNumber(phi) + "。图像向左平移 " + formatNumber(phi / Math.abs(omega)) + "。";
    } else if (phi < -1e-9) {
      phase = "φ 是起步时的角度。当前 φ = " + formatNumber(phi) + "。图像向右平移 " + formatNumber(Math.abs(phi) / Math.abs(omega)) + "。";
    } else {
      phase = "φ 是起步时的角度。当前 φ = 0。图像不平移。";
    }
    return {
      b1: "单位圆上的点转到角 t，它的纵坐标就是 sin t。把这个高度沿横轴展开，得到正弦波。当前 A = " + formatNumber(amplitude) + "，ω = " + formatNumber(omega) + "，φ = " + formatNumber(phi) + "。",
      b2: "A 把波峰和波谷拉高或压低，周期不变。当前 A = " + formatNumber(amplitude) + "。T = " + period + "。",
      b3: "ω 改变角走得有多快。当前 ω = " + formatNumber(omega) + "。T = " + period + "。",
      b4: phase
    };
  }

  function axisSentence(horizontal) {
    var text = formatNumber(horizontal);
    if (horizontal > 1e-9) return "对称轴在 y 轴右侧，x = " + text + "。";
    if (horizontal < -1e-9) return "对称轴在 y 轴左侧，x = " + text + "。";
    return "对称轴就是 y 轴，x = 0。";
  }

  function vertexSentence(vertical) {
    var text = formatNumber(vertical);
    if (vertical > 1e-9) return "顶点向上离开 x 轴，y = " + text + "。";
    if (vertical < -1e-9) return "顶点向下离开 x 轴，y = " + text + "。";
    return "顶点在 x 轴上，y = 0。";
  }

  function quadratic(params) {
    var amplitude = Number(params.a);
    var horizontal = Number(params.h);
    var vertical = Number(params.k);
    var word = amplitude < 0 ? "向下" : "向上";
    return {
      b1: "先看 y = x²：顶点在原点，开口向上，对称轴是 y 轴。放上 a、h、k 之后，顶点是 (" + formatNumber(horizontal) + ", " + formatNumber(vertical) + ")。",
      b2: "a 决定开口方向和开口大小。当前 a = " + formatNumber(amplitude) + "。开口" + word + "。|a| = " + formatNumber(Math.abs(amplitude)) + "，|a| 越大，开口越窄。",
      b3: "h 决定对称轴。当前 h = " + formatNumber(horizontal) + "。" + axisSentence(horizontal),
      b4: "k 决定顶点的高低。当前 k = " + formatNumber(vertical) + "。" + vertexSentence(vertical)
    };
  }

  function logarithm(params) {
    var base = Number(params.base);
    var text = formatNumber(base);
    var reciprocal = formatNumber(1 / base);
    var mono = base > 1
      ? "当前 a = " + text + "。a>1，函数递增。"
      : "当前 a = " + text + "。0<a<1，函数递减。";
    return {
      b1: "aʸ = x 时，y 就是 logₐ(x)。定义域是 x>0。图像只出现在 y 轴右侧，y 轴是渐近线。",
      b2: mono,
      b3: "不论底数取允许的值，图像都过定点 (1, 0)。因为任何允许的 a 都满足 a⁰ = 1。",
      b4: "把底数 " + text + " 换成倒数 " + reciprocal + "。函数值变号，图像关于 x 轴对称。"
    };
  }

  function exponential(params) {
    var base = Number(params.base);
    var text = formatNumber(base);
    var reciprocal = formatNumber(1 / base);
    var mono = base > 1
      ? "当前 a = " + text + "。a>1，函数递增。"
      : "当前 a = " + text + "。0<a<1，函数递减。";
    return {
      b1: "指数函数是 y = aˣ。定义域是全体实数，值域是 y>0。x 轴是水平渐近线，图像在 x 轴上方。",
      b2: mono,
      b3: "不论底数取允许的值，图像都过定点 (0, 1)。因为任何允许的 a 都满足 a⁰ = 1。",
      b4: "把底数 " + text + " 换成倒数 " + reciprocal + "。图像关于 y 轴对称。"
    };
  }

  function trig(params) {
    var theta = Number(params.theta);
    var text = formatNumber(theta);
    var sine = formatNumber(Math.sin(theta));
    var cosine = formatNumber(Math.cos(theta));
    var tangent = Math.abs(Math.cos(theta)) <= 1e-6
      ? "cos θ = 0，tan θ 没有定义。"
      : "当前 tan θ = " + formatNumber(Math.tan(theta)) + "。";
    return {
      b1: "角 θ 的始边在 x 轴正方向，终边逆时针转到 θ。当前 θ = " + text + "。终边和单位圆的交点是 (cos θ, sin θ)。",
      b2: "sin θ 是这个点的纵坐标。当前 sin θ = " + sine + "。",
      b3: "cos θ 是这个点的横坐标。当前 cos θ = " + cosine + "。并且 sin²θ + cos²θ = 1。",
      b4: "tan θ = sin θ / cos θ。当前 cos θ = " + cosine + "。" + tangent
    };
  }

  function narrations(family, params) {
    if (family === "quadratic") return quadratic(params);
    if (family === "logarithm") return logarithm(params);
    if (family === "exponential") return exponential(params);
    if (family === "trig") return trig(params);
    return sinusoid(params);
  }

  return { narrations: narrations, formatNumber: formatNumber, formatPeriod: formatPeriod };
});
