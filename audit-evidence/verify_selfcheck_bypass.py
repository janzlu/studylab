
import sys
sys.path.insert(0, "server")
import sinusoid

def mutate(omega, old, new):
    lesson = sinusoid.build_lesson(1, omega, 0, "x", None)
    for beat in lesson["beats"]:
        if beat["id"] in ("b2", "b3"):
            beat["narration"] = beat["narration"].replace(old, new)
    ok, reason = sinusoid.inspect_lesson(lesson)
    print(f"omega={omega}: replace {old!r}->{new!r} in b2/b3 => inspect={ok} {reason!r}")
    print("  b3:", lesson["beats"][2]["narration"])

mutate(1, "T = 2π", "T = 2π/3")
mutate(2, "T = π", "T = π/2")
mutate(3, "T = 2π/3", "T = 2π/3/7")

# Also demonstrate a wrong direction that still passes?
lesson = sinusoid.build_lesson(1, 1, 1, "x", None)
lesson["beats"][3]["narration"] = lesson["beats"][3]["narration"].replace("向左", "向右")
print("phase flipped:", sinusoid.inspect_lesson(lesson))
