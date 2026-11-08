
import sys
sys.path.insert(0, "server")
import sinusoid, quadratic, logarithm

def show(name, lesson, mutate, inspect):
    before = mutate(lesson, dry=True)
    ok, reason = inspect(lesson)
    print(name, "=>", ok, repr(reason), "|", before)

# sinusoid: wrong A, wrong omega text
l = sinusoid.build_lesson(1, 1, 0, "x", None)
l["beats"][1]["narration"] = l["beats"][1]["narration"].replace("当前 A = 1", "当前 A = 99")
print("sinusoid wrong A:", sinusoid.inspect_lesson(l))
l2 = sinusoid.build_lesson(1, 1, 0, "x", None)
l2["beats"][2]["narration"] = l2["beats"][2]["narration"].replace("当前 ω = 1", "当前 ω = 99")
print("sinusoid wrong omega:", sinusoid.inspect_lesson(l2))
l3 = sinusoid.build_lesson(1, 1, 0, "x", None)
l3["beats"][1]["narration"] = l3["beats"][1]["narration"].replace("T = 2π", "T = 2π/3")
print("sinusoid wrong period:", sinusoid.inspect_lesson(l3))

# quadratic: wrong vertex, a, h, k
q = quadratic.build_lesson(1, 0, 0, "q", None)
q["beats"][0]["narration"] = q["beats"][0]["narration"].replace("(0, 0)", "(9, 9)")
print("quadratic wrong vertex:", quadratic.inspect_lesson(q))
q2 = quadratic.build_lesson(1, 0, 0, "q", None)
q2["beats"][1]["narration"] = q2["beats"][1]["narration"].replace("当前 a = 1", "当前 a = 99")
print("quadratic wrong a:", quadratic.inspect_lesson(q2))
q3 = quadratic.build_lesson(1, 0, 0, "q", None)
q3["beats"][2]["narration"] = q3["beats"][2]["narration"].replace("x = 0", "x = 99")
print("quadratic wrong h:", quadratic.inspect_lesson(q3))
q4 = quadratic.build_lesson(1, 0, 0, "q", None)
q4["beats"][3]["narration"] = q4["beats"][3]["narration"].replace("y = 0", "y = 99")
print("quadratic wrong k:", quadratic.inspect_lesson(q4))

# logarithm: wrong base, wrong reciprocal
g = logarithm.build_lesson(2, "g", None)
g["beats"][1]["narration"] = g["beats"][1]["narration"].replace("当前 a = 2", "当前 a = 99")
print("log wrong base:", logarithm.inspect_lesson(g))
g2 = logarithm.build_lesson(2, "g", None)
g2["beats"][3]["narration"] = g2["beats"][3]["narration"].replace("0.5", "9")
print("log wrong reciprocal:", logarithm.inspect_lesson(g2))
g3 = logarithm.build_lesson(2, "g", None)
g3["beats"][0]["narration"] = g3["beats"][0]["narration"].replace("x>0", "x>99")
print("log wrong domain:", logarithm.inspect_lesson(g3))
