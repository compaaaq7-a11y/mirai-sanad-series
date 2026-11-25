"""الجزء الثاني «أول رحلة للعصفور»: الفرخ يكبر ويطير أول مرة إلى جانب أمّه.

    python blender/ep07_first_flight.py --out build/ep07/frames            # كل الإطارات
    python blender/ep07_first_flight.py --still 3,9,16 --res 360x640 --samples 8
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from garden_common import *  # noqa: E402,F401,F403
from garden_common import (scene, CHICK, MOM, NEST_P, BARK, LEAF, TREE, F, K, Vector, arm_swing, arms,  # noqa: E402
                           bird, blink, bow, camera_shots, chirp_hop, flap, frange, heading, hop, kid,
                           lights, look, near, part, rod, render, turn, walk, degrees)

# ============================================================ غصن أعلى قريب من العش
HIGH_A = (TREE.x + 0.12, TREE.y, 1.0)
HIGH_B = (2.15, 2.32, 1.07)
rod("branch_high", HIGH_A, HIGH_B, 0.055, BARK, kind="taper")
part("ico", "branch_high_leaf", (HIGH_B[0] + 0.08, HIGH_B[1], HIGH_B[2] + 0.06), (0.2, 0.15, 0.14), LEAF)


def on_high(x):
    """نقطة الوقوف فوق الغصن الأعلى عند الإحداثي x."""
    u = (x - HIGH_A[0]) / (HIGH_B[0] - HIGH_A[0])
    y = HIGH_A[1] + u * (HIGH_B[1] - HIGH_A[1])
    z = HIGH_A[2] + u * (HIGH_B[2] - HIGH_A[2]) + 0.04
    return (x, y, z)


# ============================================================ الشخصيات
IN_NEST = (NEST_P.x, NEST_P.y, NEST_P.z)
CHICK_PERCH = on_high(1.58)
MOM_PERCH = on_high(1.92)
FENCE_MOM = (2.6, 6.0, 0.93)
FENCE_CHICK = (2.28, 6.0, 0.93)
S_START, S_STOP = (1.9, -1.6), (0.99, 0.92)
M_START, M_STOP = (-0.6, -1.7), (0.33, 0.9)

sanad = kid("sanad", S_START, heading(S_START, S_STOP))
mirai = kid("mirai", M_START, heading(M_START, M_STOP), girl=True)
chick = bird("chick", (IN_NEST[0], IN_NEST[1], IN_NEST[2] - 0.13), 0, CHICK, 1.3)  # كبر قليلاً
mom = bird("mom", MOM_PERCH, -90, MOM, 1.35, mom=True)


def fly(b, keys):
    """keys: [(t, (x,y,z))] مسار طيران، ويتّجه الطائر نحو النقطة التالية."""
    ang = degrees(b["root"].rotation_euler.z)
    for i, (t, p) in enumerate(keys):
        K(b["root"], t, loc=p)
        if i + 1 < len(keys):
            ang = near(ang, heading(p, keys[i + 1][1]))
            K(b["root"], t + 0.05, rz=ang)
    return ang


# ============================================================ المشهد 1 (0–6): العودة إلى الشجرة والفرخ يطلّ
for k in (sanad, mirai):
    K(k["root"], 0, rz=degrees(k["root"].rotation_euler.z))
    arms(k, 0)
    bow(k, 0, 0)
    look(k, 0)
walk(sanad, 0.0, 3.6, S_STOP)
arm_swing(sanad, 0.0, 3.6)
walk(mirai, 0.2, 3.8, M_STOP)
arm_swing(mirai, 0.2, 3.8)
ang_s = turn(sanad, 3.6, 4.0, heading(S_STOP, NEST_P))
ang_m = turn(mirai, 3.8, 4.2, heading(M_STOP, NEST_P))
# زقزقة مألوفة: يرفعان رأسيهما
look(sanad, 3.9, rx=0)
look(sanad, 4.4, rx=-22)
look(mirai, 4.0, rx=0)
look(mirai, 4.5, rx=-22)
blink(mirai, 5.4)
# الفرخ يطلّ من العش
K(chick["root"], 0, rz=0)
K(chick["root"], 3.6, loc=(IN_NEST[0], IN_NEST[1], IN_NEST[2] - 0.13))
K(chick["root"], 4.6, loc=IN_NEST)
for t in (4.7, 5.3):
    chirp_hop(chick, t)
K(chick["head"], 5.6, rz=0)
K(chick["head"], 6.0, rz=-30)  # يلتفت نحو أمّه

# ============================================================ المشهد 2 (6–13): الأم تنادي، رفرفة متردّدة وقفزة إلى غصن
K(mom["root"], 0, loc=MOM_PERCH, rz=-90)
for t in (6.3, 7.1):
    chirp_hop(mom, t, 0.02)
flap(mom, 6.4, 6.9, amp=35, period=0.18)
K(chick["head"], 7.4, rz=-30)
K(chick["head"], 7.8, rz=0)
flap(chick, 7.9, 8.6, amp=35, period=0.22)  # رفرفة متردّدة
K(chick["body"], 8.6, rx=0)
K(chick["body"], 9.0, rx=-12)  # ينظر إلى الأسفل بتردّد
K(chick["body"], 9.4, rx=0)
# القفزة إلى الغصن القريب
K(chick["root"], 9.4, loc=IN_NEST, rz=0)
ang_c = near(0, heading(IN_NEST, CHICK_PERCH))
K(chick["root"], 9.6, rz=ang_c)
mid = ((IN_NEST[0] + CHICK_PERCH[0]) / 2, (IN_NEST[1] + CHICK_PERCH[1]) / 2, CHICK_PERCH[2] + 0.18)
K(chick["root"], 9.9, loc=mid)
K(chick["root"], 10.3, loc=CHICK_PERCH)
flap(chick, 9.5, 10.4, amp=70, period=0.14)
# يتأرجح ثم يثبت
for i, t in enumerate(frange(10.3, 11.3, 0.2)):
    K(chick["body"], t, ry=(14 if i % 2 == 0 else -14) * (1 - i * 0.18))
K(chick["body"], 11.3, ry=0)
ang_c = near(ang_c, -90)
K(chick["root"], 11.0, rz=near(ang_c, heading(CHICK_PERCH, MOM_PERCH)))
# سند يبتسم وميراي تصفّق بهدوء
look(sanad, 10.5, rx=-22)
look(sanad, 11.0, rx=-15, rz=-15)
arms(mirai, 10.6, (0, 0), (0, 0))
for i, t in enumerate(frange(10.9, 12.5, 0.24)):
    open_ = i % 2 == 0
    c = 12 if open_ else 34  # دوران حول المحور الرأسي يقرّب الكفّين
    K(mirai["arms"][0], t, rx=-75, ry=0, rz=-c)
    K(mirai["arms"][1], t, rx=-75, ry=0, rz=c)
K(mirai["arms"][0], 10.6, rz=0)
K(mirai["arms"][1], 10.6, rz=0)
K(mirai["arms"][0], 12.7, rx=0, ry=0, rz=0)
K(mirai["arms"][1], 12.7, rx=0, ry=0, rz=0)
hop(sanad, 11.4, 0.05, 0.3)
blink(sanad, 12.2)

# ============================================================ المشهد 3 (13–23): المحاولة الثانية والطيران
# الأم تطير إلى السياج وتنادي من هناك
K(mom["root"], 12.4, loc=MOM_PERCH)
fly(mom, [(12.4, MOM_PERCH), (13.2, (2.3, 4.0, 1.7)), (14.0, FENCE_MOM)])
flap(mom, 12.4, 14.0, amp=70, period=0.14)
K(mom["root"], 14.3, rz=heading(FENCE_MOM, FENCE_CHICK))
for t in (14.4, 15.0):
    chirp_hop(mom, t, 0.02)
# الفرخ يمدّ جناحيه ثم ينطلق: هبوط بسيط ثم ارتفاع فوق الأزهار
for wg, sg in zip(chick["wings"], (1, -1)):
    K(wg, 14.3, ry=0)
    K(wg, 14.8, ry=75 * sg)
    K(wg, 15.3, ry=75 * sg)
K(chick["root"], 14.9, rz=near(ang_c, heading(CHICK_PERCH, FENCE_CHICK)))
FLIGHT = [
    (15.3, CHICK_PERCH),
    (15.9, (1.75, 2.9, 0.72)),   # يهبط قليلاً في الهواء
    (17.2, (2.0, 3.7, 1.25)),    # يرفرف ويرتفع فوق الأزهار
    (19.0, (2.3, 4.8, 1.45)),
    (20.6, (2.29, 5.75, 1.15)),
    (21.1, FENCE_CHICK),         # يحطّ بجانب أمّه
]
K(chick["root"], 15.3, loc=CHICK_PERCH)
ang_c = fly(chick, FLIGHT)
flap(chick, 15.3, 15.9, amp=45, period=0.22)   # بداية متعثّرة
flap(chick, 15.9, 21.1, amp=80, period=0.12)   # رفرفة قوية
K(chick["root"], 21.4, rz=near(ang_c, heading(FENCE_CHICK, FENCE_MOM)))
for t in (21.5, 22.0, 22.5):
    chirp_hop(chick, t, 0.03)
K(mom["head"], 21.6, rx=0)
K(mom["head"], 22.0, rx=18)
K(mom["head"], 22.4, rx=0)
# الطفلان يتابعان الطيران
ang_s = turn(sanad, 14.8, 15.4, heading(S_STOP, (2.2, 4.5)))
ang_m = turn(mirai, 14.9, 15.5, heading(M_STOP, (2.2, 4.5)))
look(sanad, 15.4, rx=-15)
look(mirai, 15.5, rx=-15)
look(sanad, 18.5, rx=-5)
look(mirai, 18.5, rx=-5)
arms(sanad, 21.0, (0, 0), (0, 0))
arms(sanad, 21.4, (-150, 10), (-150, -10))  # فرح
arms(sanad, 22.2, (0, 0), (0, 0))
hop(mirai, 21.2, 0.08)

# ============================================================ المشهد 4 (23–30): ضحك وتصفيق، والعصفوران يطيران معاً
ang_s = turn(sanad, 22.6, 23.0, near(ang_s, -90))
ang_m = turn(mirai, 22.7, 23.1, near(ang_m, 90))
look(sanad, 23.0, rz=0, rx=0)
look(mirai, 23.0, rz=0, rx=0)
arms(sanad, 23.3, (0, 0), (0, 0))
arms(mirai, 23.3, (0, 0), (0, 0))
arms(sanad, 23.8, (-118, 6), (0, 0))
arms(mirai, 23.8, (0, 0), (-118, -6))
arms(sanad, 24.6, (-118, 6), (0, 0))
arms(mirai, 24.6, (0, 0), (-118, -6))
arms(sanad, 25.0, (0, 0), (0, 0))
arms(mirai, 25.0, (0, 0), (0, 0))
for t in (23.7, 25.2, 25.7):
    hop(sanad, t, 0.08)
    hop(mirai, t + 0.08, 0.08)
look(sanad, 25.2, rx=-8, rz=10)
look(mirai, 25.2, rx=-8, rz=-10)
blink(sanad, 26.0)
# العصفوران يطيران فوق الحديقة
SKY_MOM = [(26.0, FENCE_MOM), (27.0, (1.6, 4.6, 1.9)), (28.4, (-0.4, 3.3, 2.5)), (30.1, (-2.8, 2.4, 3.1))]
SKY_CHICK = [(26.2, FENCE_CHICK), (27.2, (1.3, 4.8, 1.75)), (28.6, (-0.7, 3.6, 2.35)), (30.1, (-3.0, 2.7, 2.9))]
K(mom["root"], 25.9, loc=FENCE_MOM)
K(chick["root"], 26.1, loc=FENCE_CHICK)
fly(mom, SKY_MOM)
fly(chick, SKY_CHICK)
flap(mom, 26.0, 30.1, amp=70, period=0.15)
flap(chick, 26.2, 30.1, amp=80, period=0.12)
# الطفلان يلوّحان للعصفورين
ang_s = turn(sanad, 26.6, 27.0, near(ang_s, 180))
ang_m = turn(mirai, 26.6, 27.0, near(ang_m, 180))
look(sanad, 27.0, rx=-25)
look(mirai, 27.0, rx=-25)
for tt, a in ((27.3, -150), (27.7, -120), (28.1, -150), (28.5, -120), (28.9, -150)):
    arms(sanad, tt, (0, 0), (-20, a + 10))
    arms(mirai, tt, (-20, -a - 10), (0, 0))

# ============================================================ الكاميرا
C = CHICK_PERCH
SHOTS = [
    (0.0, 4.0, (0.5, -4.6, 1.25), (0.6, -3.6, 1.15), (0.6, 0.6, 0.8), (0.7, 0.9, 0.85), 28, 28),
    (4.0, 6.6, (1.75, 0.7, 0.75), (1.7, 0.85, 0.8), (NEST_P.x, NEST_P.y, 0.9), (NEST_P.x, NEST_P.y, 0.92), 42, 46),
    (6.6, 9.3, (2.35, 0.55, 1.05), (2.3, 0.65, 1.05), (1.65, 2.0, 0.98), (1.6, 2.0, 0.98), 32, 34),
    (9.3, 11.2, (2.3, 0.65, 1.05), (2.25, 0.8, 1.1), (1.5, 2.05, 1.0), (1.55, 2.2, 1.08), 34, 36),
    (11.2, 13.0, (0.66, 1.8, 0.42), (0.66, 1.75, 0.45), (0.66, 0.9, 1.05), (0.66, 0.9, 1.08), 22, 22),
    (13.0, 15.3, (2.4, 1.2, 1.15), (2.35, 1.35, 1.15), (1.75, 2.3, 1.1), (C[0], C[1], C[2] + 0.08), 32, 38),
    (15.3, 17.2, (2.6, 1.6, 1.0), (3.4, 3.0, 1.15), (C[0], C[1], C[2]), (2.0, 3.7, 1.25), 34, 34),
    (17.2, 21.2, (3.4, 3.0, 1.15), (3.3, 5.1, 1.2), (2.0, 3.7, 1.25), (FENCE_CHICK[0], 5.95, 1.0), 34, 34),
    (21.2, 23.0, (2.45, 5.0, 1.05), (2.44, 5.1, 1.02), (2.44, 6.0, 0.98), (2.44, 6.0, 0.98), 40, 42),
    (23.0, 26.3, (0.66, -1.3, 1.05), (0.66, -1.1, 1.05), (0.66, 0.91, 0.95), (0.66, 0.91, 0.98), 32, 32),
    (26.3, 30.05, (0.66, -1.1, 1.05), (0.4, -6.0, 1.7), (0.66, 0.91, 0.98), (-0.3, 2.6, 1.9), 32, 26),
]
cam, target, _ = camera_shots(SHOTS)
# أثناء الطيران تتبع الكاميرا الفرخ نفسه
for t in frange(15.5, 21.0, 0.25):
    scene.frame_set(F(t))
    target.location = chick["root"].matrix_world.translation + Vector((0, 0, 0.08))
    target.keyframe_insert("location", frame=F(t))
sun_d, bg = lights()
# «الحديقة المضيئة»: يزداد الضوء الدافئ قليلاً في النهاية
sun_d.keyframe_insert("energy", frame=F(25.5))
sun_d.energy = 4.0
sun_d.keyframe_insert("energy", frame=F(29.5))

render("build/ep07/frames")
