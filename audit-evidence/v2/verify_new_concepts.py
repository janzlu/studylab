
import sys, math, itertools
sys.path.insert(0, "server")
import sinusoid, quadratic, logarithm

# Quadratic slider-reachable values: a in [-2,-.5] U [.5,2] step .1; h,k in [-3,3] step .5
a_vals = [round(-2 + 0.1*i, 1) for i in range(41)]
a_vals = [v for v in a_vals if abs(v) >= 0.5]
h_vals = [round(-3 + 0.5*i, 1) for i in range(13)]
k_vals = h_vals
bad = []
count = 0
for a in a_vals:
    for h in h_vals:
        for k in k_vals:
            count += 1
            lesson = quadratic.build_lesson(a, h, k, "q", None)
            ok, reason = quadratic.inspect_lesson(lesson)
            if not ok:
                bad.append((a, h, k, reason))
                if len(bad) > 5: break
        if len(bad) > 5: break
    if len(bad) > 5: break
print("quadratic combos:", count, "failures:", len(bad), bad[:3])

# Logarithm slider values .25..4 step .05, excluding (0.8, 1.25)
base_vals = [round(0.25 + 0.05*i, 2) for i in range(76)]
base_vals = [v for v in base_vals if v <= 0.8 or v >= 1.25]
bad = []
count = 0
for base in base_vals:
    count += 1
    lesson = logarithm.build_lesson(base, "g", None)
    ok, reason = logarithm.inspect_lesson(lesson)
    if not ok:
        bad.append((base, reason))
print("logarithm bases:", count, "failures:", len(bad), bad[:5])
print("log base values:", base_vals[:3], "...", base_vals[-3:])

# General form conversion checks
for a,b,c in [(1,-2,1), (1,2,3), (2,-4,1), (-1,2,1), (0.5,-1,-2), (0,1,1)]:
    amp,h,k,note = quadratic.reading_params(a,None,None,b,c)
    print("general", (a,b,c), "->", (amp,h,k), "|", note)
    lesson = quadratic.build_lesson(amp,h,k,"q",note)
    print("  self-check:", quadratic.inspect_lesson(lesson))

# Sinusoid spot checks after resolve change
for raw in [(2,None,None), (None,2,None), (None,None,1.57), (9,0,9)]:
    amp,omega,phi,note = sinusoid.resolve_params(*raw)
    print("sinusoid", raw, "->", (amp,omega,phi), "|", note)
