
import sys, itertools, math
sys.path.insert(0, "server")
import sinusoid

A_vals = [0.5 + 0.1*i for i in range(21)]
W_vals = [0.5 + 0.1*i for i in range(26)]
P_vals = [-3.14 + 0.01*i for i in range(629)]

bad = []
count = 0
for a in A_vals:
    for w in W_vals:
        for p in P_vals:
            count += 1
            lesson = sinusoid.build_lesson(a, w, p, "x", None)
            ok, reason = sinusoid.inspect_lesson(lesson)
            if not ok:
                bad.append((a, w, p, reason))
                if len(bad) > 5: break
        if len(bad) > 5: break
    if len(bad) > 5: break
print("combos checked:", count, "self-check failures:", len(bad), bad[:3])

# Period formatting consistency and correctness
for w in [0.5, 0.6, 0.7, 1.0, 1.1, 1.3, 1.7, 2.0, 2.5, 2.9, 3.0]:
    text = sinusoid.format_period(w)
    parsed = sinusoid.parse_period_text(text)
    ok = abs(parsed - 2*math.pi/abs(w)) < 1e-6
    print(f"omega={w}: text={text!r} parsed={parsed:.9f} true={2*math.pi/w:.9f} ok={ok}")

# Recognition clamping cases
for args in [(9, 1, 0), (1, 0, 0), (1, 1, 9), (-2, 4, -4), (None, None, None)]:
    lesson = sinusoid.lesson_for_reading(*args, "x")
    print("raw", args, "->", [p["value"] for p in lesson["animation"]["params"]], "note:", lesson["parameterNote"])
    print("   self-check:", sinusoid.self_check(lesson))
