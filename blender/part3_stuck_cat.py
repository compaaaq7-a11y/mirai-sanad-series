"""الجزء الثالث «القطة العالقة»: العصفوران ينبّهان الطفلين، وسند وميراي ينزلان القطة عن الشجرة.

    python blender/part3_stuck_cat.py --out build/part3/frames
    python blender/part3_stuck_cat.py --still 3,8,14 --res 360x640 --samples 8
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from garden_common import *  # noqa: E402,F401,F403
from garden_common import (scene, CHICK, MOM, NEST_P, BARK, LEAF, TREE, YARN, F, K, Vector, arm_swing,  # noqa: E402
                           arms, bird, blink, bow, camera_shots, cat, chirp_hop, empty, flap, frange, heading, hop,
                           kid, lights, look, mat, near, part, rod, render, turn, walk, degrees)

# ============================================================ غصن عالٍ تعلق عليه القطة، والصندوق
CB_A = (TREE.x - 0.05, TREE.y - 0.05, 1.55)
CB_B = (-1.25, 1.75, 1.72)
rod("branch_cat", CB_A, CB_B, 0.065, BARK, kind="taper")


def on_branch(a, b, x, r=0.065):
    u = (x - a[0]) / (b[0] - a[0])
    return (x, a[1] + u * (b[1] - a[1]), a[2] + u * (b[2] - a[2]) + r)


LOW_A = (TREE.x + 0.1, TREE.y - 0.1, 0.62)
LOW_B = (NEST_P.x + 0.35, NEST_P.y - 0.12, NEST_P.z - 0.06)
CAT_SPOT = on_branch(CB_A, CB_B, -0.85, 0.06)
CAT_HEAD = heading(CB_A, CB_B)  # تتّجه نحو طرف الغصن

WOOD = mat("box_wood", "#B07A45", 0.75, vary=("#8C5A2E", 14), bump=(0.3, 30))
BOX_H = 0.34
BOX0 = (-2.3, 0.35)
box = empty("box", (BOX0[0], BOX0[1], 0))
part("cube", "box_body", (0, 0, BOX_H / 2), (0.46, 0.46, BOX_H), WOOD, box)
for z in (0.08, BOX_H - 0.08):
    part("cube", f"box_band{z}", (0, 0, z), (0.47, 0.47, 0.035), mat("box_band", "#7A4A24", 0.7), box)

# ============================================================ الشخصيات
S_PLAY, M_PLAY = (1.05, -0.65), (-0.25, -0.75)
S_NEAR, M_NEAR = (-0.35, 0.75), (-1.35, 0.85)
BOX_END = (CAT_SPOT[0], CAT_SPOT[1] - 0.44)
M_WAVE = (-1.55, 1.2)
CAT_DOWN = (-0.55, 0.85, 0.0)     # حيث تُنزَل القطة
_d = Vector((BOX_END[0] - BOX0[0], BOX_END[1] - BOX0[1], 0)).normalized()
S_PUSH = (BOX0[0] - 0.45 * _d.x, BOX0[1] - 0.45 * _d.y)          # خلف الصندوق قبل دفعه
S_PUSH_END = (BOX_END[0] - 0.45 * _d.x, BOX_END[1] - 0.45 * _d.y)

sanad = kid("sanad", S_PLAY, -90)
mirai = kid("mirai", M_PLAY, 90, girl=True)
kitty = cat(CAT_SPOT, CAT_HEAD)
kitty["root"].location = CAT_SPOT
chick = bird("chick", (NEST_P.x, NEST_P.y, NEST_P.z), 0, CHICK, 1.3)
mom = bird("mom", on_branch(LOW_A, LOW_B, 1.62, 0.04), -90, MOM, 1.35, mom=True)

yarn_roll = empty("yarn_roll", (M_PLAY[0] + 0.3, M_PLAY[1], 0.1))
yarn = part("sphere", "yarn", (0, 0, 0), 0.1, YARN, yarn_roll)


def fly(b, keys):
    ang = degrees(b["root"].rotation_euler.z)
    for i, (t, p) in enumerate(keys):
        K(b["root"], t, loc=p)
        if i + 1 < len(keys):
            ang = near(ang, heading(p, keys[i + 1][1]))
            K(b["root"], t + 0.05, rz=ang)
    return ang


def meow(t):
    """مواء: الرأس يرتفع والجسم ينكمش قليلاً."""
    K(kitty["head"], t, rx=8)
    K(kitty["head"], t + 0.18, rx=-14)
    K(kitty["head"], t + 0.5, rx=8)


# ============================================================ المشهد 1 (0–5): زقزقة عالية والعصفوران يرفرفان حول الشجرة
for k in (sanad, mirai):
    K(k["root"], 0, rz=degrees(k["root"].rotation_euler.z), loc=(k["root"].location.x, k["root"].location.y, 0))
    arms(k, 0)
    bow(k, 0, 0)
    look(k, 0)
for t in (0.2, 0.7):
    hop(sanad, t, 0.1)
    hop(mirai, t + 0.2, 0.1)
# الطفلان يتقاذفان الكرة بدحرجتها
K(yarn_roll, 0, loc=(M_PLAY[0] + 0.3, M_PLAY[1], 0.1))
K(yarn_roll, 1.3, loc=(S_PLAY[0] - 0.3, S_PLAY[1], 0.1))
K(yarn, 0, ry=0)
K(yarn, 1.3, ry=700)
# العصفوران يدوران حول الشجرة ويزقزقان بإلحاح
LOW_PERCH = on_branch(LOW_A, LOW_B, 1.62, 0.04)
CIRCLE_M = [(0.0, LOW_PERCH), (0.6, (1.6, 1.0, 1.6)), (1.4, (0.2, 0.9, 2.0)), (2.2, (-1.0, 1.4, 1.9)),
            (3.0, (-0.9, 2.2, 1.95)), (3.8, (0.3, 1.4, 1.7)), (4.6, (-0.2, 1.75, 2.2))]
CIRCLE_C = [(0.2, (NEST_P.x, NEST_P.y, NEST_P.z)), (0.8, (1.3, 1.2, 1.4)), (1.6, (0.0, 1.1, 1.8)),
            (2.4, (-1.2, 1.6, 1.7)), (3.2, (-0.6, 2.4, 1.8)), (4.0, (0.5, 1.6, 1.5)), (4.8, (-0.45, 1.6, 2.3))]
fly(mom, CIRCLE_M)
fly(chick, CIRCLE_C)
flap(mom, 0.0, 4.6, amp=70, period=0.14)
flap(chick, 0.2, 4.8, amp=80, period=0.12)
# يحوّمان قرب القطة حتى المشهد الثالث
for t in frange(4.6, 10.0, 0.6):
    K(mom["root"], t, loc=(-0.2 + 0.08 * ((t * 10) % 2), 1.75, 2.2 + 0.05 * ((t * 10) % 3)))
    K(chick["root"], t + 0.1, loc=(-0.45, 1.6 + 0.06 * ((t * 10) % 2), 2.3))
flap(mom, 4.6, 10.0, amp=60, period=0.15)
flap(chick, 4.8, 10.0, amp=70, period=0.13)
look(sanad, 1.8, rz=0)
look(sanad, 2.2, rz=-40, rx=-20)
look(mirai, 1.9, rz=0)
look(mirai, 2.3, rz=40, rx=-20)
blink(mirai, 3.2)

# ============================================================ المشهد 2 (5–10): القطة عالقة وخائفة
K(kitty["root"], 0, loc=CAT_SPOT, rz=CAT_HEAD)
K(kitty["head"], 0, rx=0, rz=0)
K(kitty["head"], 5.2, rx=0, rz=0)
K(kitty["head"], 5.8, rx=25, rz=55)     # تنظر إلى الأسفل بخوف
K(kitty["body"], 5.0, loc=(0, 0, 0), rx=0)
K(kitty["body"], 5.6, loc=(0, 0, -0.06), rx=-3)  # تنكمش
for t in (6.2, 7.6, 9.0):
    meow(t)
sg = 1
for t in frange(0.0, 16.0, 0.6):
    K(kitty["tail"], t, rz=12 * sg, rx=-25)   # ذيل متدلٍّ يتحرك قليلاً
    sg = -sg
# الطفلان يركضان نحو الشجرة
ang_s = turn(sanad, 4.8, 5.1, heading(S_PLAY, S_NEAR))
ang_m = turn(mirai, 4.9, 5.2, heading(M_PLAY, M_NEAR))
look(sanad, 5.1, rz=0, rx=0)
look(mirai, 5.2, rz=0, rx=0)
walk(sanad, 5.1, 7.4, S_NEAR, step=0.34)
arm_swing(sanad, 5.1, 7.4, step=0.34)
walk(mirai, 5.2, 7.6, M_NEAR, step=0.34)
arm_swing(mirai, 5.2, 7.6, step=0.34)
ang_s = turn(sanad, 7.4, 7.7, heading(S_NEAR, CAT_SPOT))
ang_m = turn(mirai, 7.6, 7.9, heading(M_NEAR, CAT_SPOT))
look(sanad, 7.8, rx=-28)
look(mirai, 7.9, rx=-28)
arms(mirai, 8.2, (0, 0), (0, 0))
arms(mirai, 8.6, (-150, 0), (-150, 0))  # يداها على فمها/رأسها قلقاً
arms(mirai, 9.6, (-150, 0), (-150, 0))
arms(mirai, 10.0, (0, 0), (0, 0))

# ============================================================ المشهد 3 (10–16): سند يدفع الصندوق ويقف عليه، وميراي تهزّ الكرة
ang_s = turn(sanad, 9.8, 10.1, heading(S_NEAR, S_PUSH))
look(sanad, 10.0, rx=0)
walk(sanad, 10.1, 11.2, S_PUSH, step=0.34)
arm_swing(sanad, 10.1, 11.2, step=0.34)
push_dir = heading(BOX0, BOX_END)
ang_s = turn(sanad, 11.2, 11.4, near(ang_s, push_dir))
bow(sanad, 11.4, 25)
arms(sanad, 11.4, (-80, 0), (-80, 0))
K(box, 0, loc=(BOX0[0], BOX0[1], 0))
K(box, 11.5, loc=(BOX0[0], BOX0[1], 0))
K(box, 13.4, loc=(BOX_END[0], BOX_END[1], 0))
walk(sanad, 11.5, 13.4, S_PUSH_END, step=0.4)
bow(sanad, 13.4, 25)
bow(sanad, 13.7, 0)
arms(sanad, 13.6, (0, 0), (0, 0))
# يصعد فوق الصندوق ويواجه القطة
ang_s = turn(sanad, 13.7, 14.0, near(ang_s, 180))
K(sanad["root"], 14.0, loc=(S_PUSH_END[0], S_PUSH_END[1], 0))
K(sanad["root"], 14.35, loc=(BOX_END[0], BOX_END[1] - 0.05, BOX_H + 0.12))
K(sanad["root"], 14.6, loc=(BOX_END[0], BOX_END[1], BOX_H))
look(sanad, 14.6, rx=-25)
arms(sanad, 14.7, (0, 0), (0, 0))
arms(sanad, 15.4, (-145, 6), (-145, -6))
# ميراي تأخذ الكرة وتهزّها للقطة
ang_m = turn(mirai, 10.0, 10.3, heading(M_NEAR, M_WAVE))
walk(mirai, 10.3, 11.6, M_WAVE, step=0.34)
arm_swing(mirai, 10.3, 11.6, step=0.34)
ang_m = turn(mirai, 11.6, 11.9, heading(M_WAVE, CAT_SPOT))
look(mirai, 11.9, rx=-25)
YARN_HAND_T0, YARN_HAND_T1 = 12.2, 19.0
for i, t in enumerate(frange(12.2, 18.8, 0.3)):
    arms(mirai, t, (-150 + (14 if i % 2 else -14), 8), (0, 0))
arms(mirai, 19.0, (0, 0), (0, 0))

# ============================================================ المشهد 4 (16–23): القطة تقفز إلى ذراعي سند
K(kitty["head"], 15.6, rx=25, rz=55)
K(kitty["head"], 16.3, rx=20, rz=95)    # تنظر إلى الكرة
K(kitty["body"], 16.9, loc=(0, 0, -0.06), rx=-3)
K(kitty["body"], 17.4, loc=(0, -0.02, -0.1), rx=8)  # تستعدّ للقفز
K(kitty["root"], 17.3, rz=CAT_HEAD)
K(kitty["root"], 17.6, rz=near(CAT_HEAD, 180))
K(kitty["body"], 17.7, loc=(0, 0, 0), rx=0)
K(kitty["head"], 17.6, rx=0, rz=0)
for lp in kitty["legs"]:
    K(lp, 17.5, rx=0)
    K(lp, 17.8, rx=30)
    K(lp, 18.4, rx=0)

# القطة تتبع يدي سند بعد القفز (نقرأ موضع اليدين إطاراً بإطار)
K(kitty["root"], 17.6, loc=CAT_SPOT)
scene.frame_set(F(18.3))
catch = (sanad["handpt1"].matrix_world.translation + sanad["handpt-1"].matrix_world.translation) / 2
mid = (Vector(CAT_SPOT) + catch) / 2 + Vector((0, 0, 0.18))
K(kitty["root"], 17.95, loc=tuple(mid))
# بعد الإمساك: سند يضمّها وينزل عن الصندوق ثم يضعها على الأرض
arms(sanad, 18.3, (-145, 6), (-145, -6))
arms(sanad, 18.9, (-85, 18), (-85, -18))
look(sanad, 18.9, rx=10)
K(sanad["root"], 19.6, loc=(BOX_END[0], BOX_END[1], BOX_H))
K(sanad["root"], 19.85, loc=(BOX_END[0], BOX_END[1] - 0.25, BOX_H + 0.1))
K(sanad["root"], 20.2, loc=(BOX_END[0], BOX_END[1] - 0.45, 0))
ang_s = turn(sanad, 20.3, 20.7, near(ang_s, heading((BOX_END[0], BOX_END[1] - 0.45), CAT_DOWN)))
K(sanad["root"], 20.7, loc=(BOX_END[0], BOX_END[1] - 0.45, 0))
walk(sanad, 20.7, 21.4, (CAT_DOWN[0] - 0.05, CAT_DOWN[1] + 0.35), step=0.34)
bow(sanad, 21.5, 0)
bow(sanad, 22.0, 45)
arms(sanad, 21.5, (-85, 18), (-85, -18))
arms(sanad, 22.0, (-70, 18), (-70, -18))
bow(sanad, 22.5, 45)
bow(sanad, 22.9, 0)
arms(sanad, 22.9, (0, 0), (0, 0))
carry = list(range(F(18.3), F(22.2) + 1))
pos = []
for f in carry:
    scene.frame_set(f)
    h = (sanad["handpt1"].matrix_world.translation + sanad["handpt-1"].matrix_world.translation) / 2
    pos.append(h + Vector((0, 0, -0.16)))
for f, p in zip(carry, pos):
    kitty["root"].location = p
    kitty["root"].keyframe_insert("location", frame=f)
K(kitty["root"], 18.5, rz=near(CAT_HEAD, 180) + 90)
K(kitty["root"], 22.6, loc=CAT_DOWN)
K(kitty["root"], 22.6, rz=near(degrees(kitty["root"].rotation_euler.z), heading(CAT_DOWN, (M_WAVE[0] + 0.4, M_WAVE[1] - 0.6))))
for lp in kitty["legs"]:
    K(lp, 22.2, rx=20)
    K(lp, 22.6, rx=0)

# ============================================================ المشهد 5 (23–30): لعب بالكرة والجميع أصدقاء
# الكرة في يد ميراي حتى تدحرجها نحو القطة
K(yarn_roll, 11.8, loc=(S_PLAY[0] - 0.3, S_PLAY[1], 0.1))
scene.frame_set(F(12.0))
for f in range(F(12.0), F(19.0) + 1, 2):
    scene.frame_set(f)
    yarn_roll.location = mirai["handpt1"].matrix_world.translation + Vector((0, 0, 0.06))
    yarn_roll.keyframe_insert("location", frame=f)
ang_m = turn(mirai, 19.2, 19.6, heading(M_WAVE, CAT_DOWN))
look(mirai, 19.6, rx=0)
walk(mirai, 19.6, 21.6, (CAT_DOWN[0] - 0.75, CAT_DOWN[1] - 0.15), step=0.34)
arm_swing(mirai, 19.6, 21.6, step=0.34)
K(yarn_roll, 19.2, loc=tuple(yarn_roll.location))
K(yarn_roll, 19.6, loc=(M_WAVE[0] + 0.25, M_WAVE[1] - 0.25, 0.1))
K(yarn_roll, 21.6, loc=(CAT_DOWN[0] - 0.55, CAT_DOWN[1] - 0.12, 0.1))
K(yarn, 19.6, ry=0)
K(yarn, 21.6, ry=600)
bow(mirai, 22.8, 0)
bow(mirai, 23.2, 35)
arms(mirai, 22.8, (0, 0), (0, 0))
arms(mirai, 23.2, (-60, 0), (0, 0))
bow(mirai, 23.7, 0)
arms(mirai, 23.7, (0, 0), (0, 0))
# الكرة تتدحرج إلى القطة، والقطة تلعب بها
K(yarn_roll, 23.2, loc=(CAT_DOWN[0] - 0.55, CAT_DOWN[1] - 0.12, 0.1))
K(yarn_roll, 24.0, loc=(CAT_DOWN[0] - 0.12, CAT_DOWN[1] - 0.3, 0.1))
K(yarn, 24.0, ry=900)
sg = 1
for t in frange(24.3, 30.0, 0.8):
    K(yarn_roll, t, loc=(CAT_DOWN[0] - 0.12 + 0.12 * sg, CAT_DOWN[1] - 0.3 - 0.06 * sg, 0.1))
    K(yarn, t, ry=900 + 140 * sg)
    lp = kitty["legs"][0 if sg > 0 else 1]
    K(lp, t - 0.3, rx=0)
    K(lp, t - 0.15, rx=-70)
    K(lp, t, rx=0)
    K(kitty["head"], t, rz=14 * sg, rx=10)
    sg = -sg
for t in frange(22.6, 30.0, 0.45):
    K(kitty["tail"], t, rz=25 * sg, rx=0)
    sg = -sg
# العصفوران يحطّان على الغصن المنخفض يراقبان بسلام
LOW_PERCH2 = on_branch(LOW_A, LOW_B, 1.15, 0.04)
fly(mom, [(10.0, (-0.2, 1.75, 2.2)), (11.5, (0.6, 1.4, 1.5)), (12.6, LOW_PERCH)])
fly(chick, [(10.1, (-0.45, 1.6, 2.3)), (11.7, (0.4, 1.5, 1.3)), (12.8, LOW_PERCH2)])
flap(mom, 10.0, 12.6, amp=70, period=0.14)
flap(chick, 10.1, 12.8, amp=80, period=0.12)
K(mom["root"], 12.9, rz=near(degrees(mom["root"].rotation_euler.z), heading(LOW_PERCH, CAT_DOWN)))
K(chick["root"], 13.0, rz=near(degrees(chick["root"].rotation_euler.z), heading(LOW_PERCH2, CAT_DOWN)))
for t in (18.6, 19.0, 25.5, 26.0, 28.6):
    chirp_hop(chick, t, 0.03)
for t in (18.8, 26.3):
    chirp_hop(mom, t, 0.02)
# الطفلان سعيدان: يصفّقان ويلوّحان
ang_s = turn(sanad, 23.4, 23.8, near(ang_s, heading((CAT_DOWN[0] - 0.05, CAT_DOWN[1] + 0.35), (CAT_DOWN[0] - 0.4, CAT_DOWN[1] - 0.2))))
for i, t in enumerate(frange(24.2, 26.2, 0.26)):
    c = 12 if i % 2 == 0 else 34
    K(sanad["arms"][0], t, rx=-75, ry=0, rz=-c)
    K(sanad["arms"][1], t, rx=-75, ry=0, rz=c)
K(sanad["arms"][0], 26.5, rx=0, ry=0, rz=0)
K(sanad["arms"][1], 26.5, rx=0, ry=0, rz=0)
K(sanad["arms"][0], 23.9, rx=0, ry=0, rz=0)
K(sanad["arms"][1], 23.9, rx=0, ry=0, rz=0)
hop(sanad, 26.6, 0.08)
hop(mirai, 26.7, 0.08)
ang_s = turn(sanad, 27.2, 27.6, near(ang_s, 0))
ang_m = turn(mirai, 27.2, 27.6, near(ang_m, 0))
look(sanad, 27.6, rx=0, rz=0)
look(mirai, 27.6, rx=0, rz=0)
for tt, a in ((27.8, -150), (28.2, -120), (28.6, -150), (29.0, -120), (29.4, -150)):
    arms(sanad, tt, (0, 0), (-20, a + 10))
    arms(mirai, tt, (-20, -a - 10), (0, 0))
blink(sanad, 24.8)
blink(mirai, 28.0)

# ============================================================ الكاميرا
CS = CAT_SPOT
SHOTS = [
    (0.0, 2.6, (0.4, -4.8, 1.3), (0.35, -4.3, 1.3), (0.3, 0.3, 0.9), (0.2, 0.8, 1.2), 28, 28),
    (2.6, 5.0, (0.6, -1.6, 1.0), (0.3, -1.2, 1.1), (-0.3, 1.5, 1.8), (-0.8, 1.6, 1.95), 28, 30),
    (5.0, 7.4, (-1.3, 0.95, 1.85), (-1.25, 1.05, 1.85), (CS[0] - 0.1, CS[1] - 0.05, CS[2] + 0.3), (CS[0] - 0.1, CS[1] - 0.05, CS[2] + 0.32), 36, 40),
    (7.4, 10.0, (-0.8, -1.9, 1.0), (-0.85, -1.6, 1.05), (-0.85, 1.0, 1.1), (-0.85, 1.2, 1.25), 28, 28),
    (10.0, 13.6, (-0.9, -2.4, 1.2), (-1.1, -2.0, 1.2), (-1.6, 0.4, 0.5), (-1.1, 0.9, 0.6), 26, 26),
    (13.6, 16.0, (-2.05, 2.45, 1.0), (-2.0, 2.4, 1.0), (-0.85, 1.55, 1.35), (-0.85, 1.6, 1.5), 26, 26),
    (16.0, 19.2, (-2.0, 2.4, 1.0), (-1.95, 2.35, 1.02), (-0.85, 1.65, 1.55), (-0.85, 1.55, 1.4), 26, 28),
    (19.2, 23.0, (0.6, -1.0, 1.0), (0.4, -0.8, 0.9), (-0.7, 1.0, 0.8), (-0.6, 0.85, 0.5), 30, 32),
    (23.0, 26.8, (-0.5, -1.2, 0.7), (-0.6, -1.0, 0.65), (-0.75, 0.6, 0.35), (-0.75, 0.6, 0.4), 30, 30),
    (26.8, 30.05, (-0.6, -1.0, 0.7), (-0.2, -5.6, 1.8), (-0.75, 0.6, 0.45), (-0.2, 1.2, 1.0), 30, 26),
]
cam, target, _ = camera_shots(SHOTS)
# لقطة وجه القطة الخائفة: الكاميرا أمام رأسها مباشرة
for t in (5.0, 7.37):
    scene.frame_set(F(t))
    hm = kitty["head"].matrix_world
    face = hm.to_3x3() @ Vector((0, -1, 0))
    face.z = 0
    face.normalize()
    hp_ = hm.translation + Vector((0, 0, 0.02))
    cam.location = hp_ + face * 0.95 + Vector((0, 0, -0.12 if t < 6 else -0.1))
    cam.keyframe_insert("location", frame=F(t) if t < 6 else F(7.4) - 1)
    target.location = hp_
    target.keyframe_insert("location", frame=F(t) if t < 6 else F(7.4) - 1)
lights()
render("build/part3/frames")
