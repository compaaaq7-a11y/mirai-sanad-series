"""الجزء الرابع «جرس البقرة»: بقرة أضاعت جرسها، والقطة تلعب به، وسند وميراي يعيدانه.

    python blender/part4_cow_bell.py --check
    python blender/part4_cow_bell.py --still 3,9,16 --res 360x640 --samples 8
    python blender/part4_cow_bell.py --out build/part4/frames
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from garden_common import *  # noqa: E402,F401,F403
from garden_common import (EVENTS, scene, F, K, Vector, arm_swing, arms, bell_shape, blink, bow,  # noqa: E402
                           camera_shots, cat, cow, cow_walk, empty, frange, heading, hop, kid, lights, look,
                           near, render, turn, walk, degrees)

# ============================================================ الأماكن
COW_IN = (4.8, 2.2)
COW_STOP = (1.4, 1.2)      # تقف وجانبها للكاميرا ورأسها نحو اليسار
COW_OUT = (4.6, 3.8)
S_PLAY, M_PLAY = (0.0, -0.45), (-1.0, -0.35)
S_COW = (0.8, 0.5)         # خلف رأس البقرة بجانب كتفها، بعيداً عن رأسها وجسمها
M_COW = (-0.45, 1.5)       # أمام رأسها على مسافة آمنة
BELL_GROUND = Vector((-1.75, 1.15, 0.07))
CAT0 = (-2.15, 1.35)
M_BELL = (-1.35, 0.85)     # حيث تلتقط ميراي الجرس
M_GIVE = (0.05, 0.36)      # تقف قرب سند لتعطيه الجرس (بعيداً عن أنف البقرة ورأس سند)

sanad = kid("sanad", S_PLAY, -90)
mirai = kid("mirai", M_PLAY, 90, girl=True)
moo = cow(COW_IN, heading(COW_IN, COW_STOP))
kitty = cat(CAT0, heading(CAT0, BELL_GROUND))
from garden_common import SOLIDS  # noqa: E402
SOLIDS.append(("القطة", kitty["body"], (0, 0.02, 0.22), 0.17))

# الجرس الضائع على الأرض، وجرس الطوق (يظهر عند تعليقه)
ground_bell = bell_shape("bell_ground", None, tuple(BELL_GROUND), 1.0)
ground_bell.rotation_euler = (0, 1.4, 0.3)  # ملقى على جنبه بين الأزهار
collar_bell = bell_shape("bell_collar", moo["body"], (0.2, -0.6, 0.6), 1.0)   # على جانب الطوق المواجه لسند


def show(obj, t, visible):
    """إظهار/إخفاء جسم وكل أجزائه عند الثانية t."""
    for o in [obj] + list(obj.children_recursive):
        o.hide_render = not visible
        o.keyframe_insert("hide_render", frame=F(t))


show(collar_bell, 0, False)
show(collar_bell, 19.8, True)
show(ground_bell, 0, True)
show(ground_bell, 19.8, False)


def moo_head(t, happy=False):
    """خوار: الرأس يرتفع ويفتح قليلاً."""
    K(moo["head"], t, rx=0)
    K(moo["head"], t + 0.3, rx=-18 if happy else -10)
    K(moo["head"], t + 1.0, rx=0)


# ============================================================ المشهد 1 (0–5): بقرة حزينة تدخل الحديقة
for k in (sanad, mirai):
    K(k["root"], 0, rz=degrees(k["root"].rotation_euler.z), loc=(k["root"].location.x, k["root"].location.y, 0))
    arms(k, 0)
    bow(k, 0, 0)
    look(k, 0)
K(moo["root"], 0, rz=degrees(moo["root"].rotation_euler.z))
cow_walk(moo, 0.2, 4.3, COW_STOP)
turn(moo, 4.3, 4.9, -90)   # تقف وجانبها للكاميرا، رأسها نحو -X
moo_head(7.0)   # خوار حزين في الفاصل بين جملتي التعليق
K(moo["head"], 5.4, rz=0)
K(moo["head"], 6.0, rz=25)     # تتلفّت حولها
K(moo["head"], 6.8, rz=-20)
K(moo["head"], 7.6, rz=0)
sg = 1
for t in frange(0.0, 30.0, 0.7):
    K(moo["tail"], t, ry=14 * sg)
    sg = -sg
# الطفلان يلعبان ثم يلتفتان إلى البقرة
for t in (0.2, 0.7):
    hop(sanad, t, 0.08)
    hop(mirai, t + 0.2, 0.08)
look(sanad, 1.5, rz=0)
look(sanad, 2.0, rz=-45)
look(mirai, 1.6, rz=0)
look(mirai, 2.1, rz=-40)
blink(mirai, 3.3)

# ============================================================ المشهد 2 (5–11): يقتربان ويفهمان أنها أضاعت جرسها
ang_s = turn(sanad, 4.6, 4.9, heading(S_PLAY, S_COW))
ang_m = turn(mirai, 4.7, 5.0, heading(M_PLAY, M_COW))
look(sanad, 4.9, rz=0)
look(mirai, 5.0, rz=0)
walk(sanad, 4.9, 7.0, S_COW)
arm_swing(sanad, 4.9, 7.0)
walk(mirai, 5.0, 7.3, M_COW)
arm_swing(mirai, 5.0, 7.3)
ang_s = turn(sanad, 7.0, 7.3, heading(S_COW, (S_COW[0], COW_STOP[1])))
ang_m = turn(mirai, 7.3, 7.6, heading(M_COW, (COW_STOP[0], COW_STOP[1])))
# البقرة تنظر إلى طوقها الفارغ ثم إلى العشب (بعيداً عن الطفلين)
K(moo["head"], 8.0, rx=0, rz=0)
K(moo["head"], 8.6, rx=28, rz=-10)
K(moo["head"], 9.6, rx=28, rz=-10)
K(moo["head"], 10.2, rx=12, rz=-30)
look(sanad, 8.6, rx=15)
look(mirai, 8.8, rx=10)
look(sanad, 9.8, rz=-35)          # ينظر سند إلى ميراي
look(mirai, 9.9, rz=35)
blink(sanad, 10.3)

# ============================================================ المشهد 3 (11–18): رنين بين الأزهار، القطة تلعب بالجرس
K(kitty["root"], 0, loc=(CAT0[0], CAT0[1], 0), rz=heading(CAT0, BELL_GROUND))
K(kitty["body"], 0, loc=(0, 0, -0.05), rx=-4)
bell_hits = []
sg = 1
bx = BELL_GROUND.copy()
K(ground_bell, 0, loc=tuple(bx))
for i, t in enumerate(frange(11.0, 14.2, 0.7)):
    lp = kitty["legs"][0 if sg > 0 else 1]
    K(lp, t - 0.25, rx=0)
    K(lp, t - 0.1, rx=-70)
    K(lp, t, rx=0)
    nb = bx + Vector((0.12 * sg, -0.05, 0))
    K(ground_bell, t, loc=tuple(bx), rz=0.3 + i * 0.6)
    K(ground_bell, t + 0.35, loc=tuple(nb), rz=0.3 + (i + 1) * 0.6)
    bx = nb
    bell_hits.append(round(t + 0.05, 2))
    K(kitty["head"], t, rz=10 * sg)
    sg = -sg
EVENTS["bell"] = list(bell_hits)
sg = 1
for t in frange(10.5, 30.0, 0.45):
    K(kitty["tail"], t, rz=22 * sg, rx=0)
    sg = -sg
# الطفلان يلتفتان نحو الرنين، وميراي تذهب لتلتقط الجرس
look(sanad, 11.2, rz=0)
look(sanad, 11.6, rz=60, rx=5)
look(mirai, 11.3, rz=0)
look(mirai, 11.7, rz=55, rx=5)
ang_m = turn(mirai, 12.0, 12.3, heading(M_COW, M_BELL))
look(mirai, 12.3, rz=0)
walk(mirai, 12.3, 14.2, M_BELL)
arm_swing(mirai, 12.3, 14.2)
scene.frame_set(F(14.2))
bell_final = Vector(ground_bell.location)
ang_m = turn(mirai, 14.2, 14.45, heading(M_BELL, bell_final))
K(kitty["root"], 14.2, loc=(CAT0[0], CAT0[1], 0))
K(kitty["root"], 14.9, loc=(CAT0[0] - 0.25, CAT0[1] + 0.25, 0))   # تبتعد قليلاً وتجلس
bow(mirai, 14.5, 0)
bow(mirai, 15.0, 50)
arms(mirai, 14.5, (0, 0), (0, 0))
arms(mirai, 15.0, (-55, 18), (0, 0))
bow(mirai, 15.3, 50)
bow(mirai, 15.8, 0)
arms(mirai, 15.8, (-75, 10), (0, 0))
ang_m = turn(mirai, 15.8, 16.1, heading(M_BELL, M_GIVE))
walk(mirai, 16.1, 17.9, M_GIVE)
ang_m = turn(mirai, 17.9, 18.15, heading(M_GIVE, S_COW))
arms(mirai, 17.9, (-75, 10), (0, 0))
arms(mirai, 18.3, (-85, -5), (0, 0))    # تمدّ الجرس إلى سند
arms(mirai, 18.9, (0, 0), (0, 0))

# ============================================================ المشهد 4 (18–24): سند يعلّق الجرس، والبقرة تفرح
ang_s = turn(sanad, 17.5, 17.8, heading(S_COW, M_GIVE))
arms(sanad, 17.8, (0, 0), (0, 0))
arms(sanad, 18.2, (-70, -8), (-70, 8))
scene.frame_set(F(19.0))
BELL_ON = collar_bell.matrix_world.translation.copy()
ang_s = turn(sanad, 18.65, 18.95, near(ang_s, heading(S_COW, BELL_ON)))
arms(sanad, 18.95, (-40, -8), (-40, 8))
arms(sanad, 19.35, (-52, -10), (-52, 10))
arms(sanad, 19.75, (-52, -10), (-52, 10))
arms(sanad, 20.2, (0, 0), (0, 0))
S_BACK = (1.0, 0.05)  # يتراجع خطوتين بعد تعليق الجرس ليبتعد عن البقرة حين تستدير
ang_s = turn(sanad, 20.25, 20.45, near(ang_s, heading(S_COW, S_BACK)))
walk(sanad, 20.45, 21.2, S_BACK, step=0.3)
ang_s = turn(sanad, 21.2, 21.5, near(ang_s, heading(S_BACK, (COW_STOP[0] - 0.7, COW_STOP[1]))))
# مسار الجرس بلا قفزات: الأرض -> يد ميراي -> (انتقال ناعم) -> يدا سند -> (انتقال ناعم) -> الطوق
def hand_of(k, both):
    a = k["handpt1"].matrix_world.translation
    if not both:
        return a.copy()
    return (a + k["handpt-1"].matrix_world.translation) / 2


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


for f in range(F(14.95), F(19.8) + 1):
    scene.frame_set(f)
    t = (f - 1) / 24
    pm = hand_of(mirai, False) + Vector((0, 0, -0.05))
    ps = hand_of(sanad, True) + Vector((0, 0, -0.05))
    if t < 15.2:
        p = bell_final.lerp(pm, smooth((t - 14.95) / 0.25))
    elif t < 18.25:
        p = pm
    elif t < 18.6:
        p = pm.lerp(ps, smooth((t - 18.25) / 0.35))
    elif t < 19.45:
        p = ps
    else:
        p = ps.lerp(BELL_ON, smooth((t - 19.45) / 0.35))
    ground_bell.location = p
    ground_bell.keyframe_insert("location", frame=f)
    ground_bell.rotation_euler = (0, 0, 0)
    ground_bell.keyframe_insert("rotation_euler", frame=f)
# ميراي تتراجع خطوة ثم تصفّق فرحاً (دون لمس البقرة)
M_AFTER = (-0.45, 0.25)
ang_m = turn(mirai, 18.7, 18.9, near(ang_m, heading(M_GIVE, M_AFTER)))
walk(mirai, 18.9, 19.4, M_AFTER, step=0.3)
ang_m = turn(mirai, 19.4, 19.7, near(ang_m, heading(M_AFTER, (COW_STOP[0] - 0.8, COW_STOP[1]))))
arms(mirai, 19.0, (0, 0), (0, 0))
for i, t in enumerate(frange(19.9, 21.5, 0.26)):
    c = 12 if i % 2 == 0 else 34
    K(mirai["arms"][0], t, rx=-75, ry=0, rz=-c)
    K(mirai["arms"][1], t, rx=-75, ry=0, rz=c)
    EVENTS.setdefault("claps", []).append(round(t, 2)) if i % 2 == 1 else None
K(mirai["arms"][0], 21.8, rx=0, ry=0, rz=0)
K(mirai["arms"][1], 21.8, rx=0, ry=0, rz=0)
mirai["root"].location = (M_AFTER[0], M_AFTER[1], 0)
hop(mirai, 21.9, 0.07)
# البقرة تهزّ رأسها فيرنّ الجرس، ثم تخور فرحاً
K(moo["head"], 19.9, rx=0, rz=0)
for i, t in enumerate(frange(20.6, 21.8, 0.3)):
    K(moo["head"], t, rz=-12 if i % 2 == 0 else 8)
    EVENTS["bell"].append(round(t, 2))
K(moo["head"], 21.9, rz=0)
moo_head(22.65, happy=True)
look(sanad, 20.4, rx=0, rz=0)
look(mirai, 20.4, rx=-5)

# ============================================================ المشهد 5 (24–30): البقرة تلتفت إلى سند شاكرة، ثم تعود وجرسها يرنّ
K(moo["head"], 23.8, rz=0, rx=0)
K(moo["head"], 24.4, rz=20, rx=6)       # تلتفت نحو سند شاكرةً (دون أن تلمسه)
K(moo["head"], 24.7, rz=23, rx=2)
K(moo["head"], 25.0, rz=20, rx=6)
K(moo["head"], 25.5, rz=0, rx=0)
look(sanad, 24.3, rz=0)
look(sanad, 24.8, rz=-15, rx=-14)       # يضحك
look(sanad, 25.6, rz=0, rx=0)
sanad["root"].location = (S_BACK[0], S_BACK[1], 0)   # frame_set أعلاه غيّر الموضع الحالي
hop(sanad, 25.4, 0.08)
mirai["root"].location = (M_AFTER[0], M_AFTER[1], 0)
hop(mirai, 25.5, 0.08)
blink(sanad, 24.75)
ang_c = turn(moo, 25.8, 26.6, heading(COW_STOP, COW_OUT))
EVENTS["cow_bell_from"] = 26.6
cow_walk(moo, 26.6, 30.2, COW_OUT)
ang_s = turn(sanad, 26.0, 26.4, near(ang_s, heading(S_BACK, COW_OUT)))
ang_m = turn(mirai, 26.1, 26.5, near(ang_m, heading(M_AFTER, COW_OUT)))
arms(sanad, 26.5, (0, 0), (0, 0))   # تثبيت الذراعين حتى يبدأ التلويح
arms(mirai, 26.5, (0, 0), (0, 0))
for tt, a in ((27.0, -150), (27.4, -120), (27.8, -150), (28.2, -120), (28.6, -150)):
    arms(sanad, tt, (0, 0), (-20, -a - 10))   # تلويح للخارج
    arms(mirai, tt, (-20, a + 10), (0, 0))
arms(sanad, 29.0, (0, 0), (0, 0))
arms(mirai, 29.0, (0, 0), (0, 0))
# القطة تتبع البقرة قليلاً ثم تجلس
ang_k = degrees(kitty["root"].rotation_euler.z)
K(kitty["root"], 26.6, loc=(CAT0[0] - 0.25, CAT0[1] + 0.25, 0), rz=ang_k)
K(kitty["root"], 27.0, rz=near(ang_k, heading((CAT0[0] - 0.25, CAT0[1] + 0.25), (1.2, 1.4))))
K(kitty["root"], 28.8, loc=(-0.6, 1.3, 0))
sg = 1
for t in frange(27.0, 28.8, 0.2):
    for i, lp in enumerate(kitty["legs"]):
        K(lp, t, rx=(20 if i in (0, 3) else -20) * sg)
    sg = -sg
for lp in kitty["legs"]:
    K(lp, 28.8, rx=0)
K(kitty["body"], 28.8, loc=(0, 0, 0), rx=0)
K(kitty["body"], 29.2, loc=(0, 0.04, -0.06), rx=10)   # تجلس

# ============================================================ الكاميرا
SHOTS = [
    (0.0, 2.6, (0.6, -5.2, 1.4), (0.7, -4.6, 1.3), (1.0, 0.8, 0.8), (1.2, 1.0, 0.9), 28, 28),
    (2.6, 5.0, (1.3, -1.0, 1.0), (1.25, -0.9, 1.0), (1.9, 1.4, 1.1), (0.9, 1.2, 1.1), 30, 30),
    (5.0, 8.0, (-1.6, -2.2, 1.25), (-1.4, -1.9, 1.25), (0.3, 0.3, 0.9), (0.5, 0.6, 0.95), 28, 28),
    (8.0, 11.0, (-1.3, 0.1, 1.25), (-1.27, 0.12, 1.25), (0.6, 1.0, 1.05), (0.6, 1.0, 1.05), 28, 28),
    (11.0, 14.2, (-1.2, 0.0, 0.45), (-1.25, 0.1, 0.42), (-1.85, 1.2, 0.15), (-1.8, 1.15, 0.12), 34, 38),
    (14.2, 17.0, (-0.4, -1.7, 0.95), (-0.3, -1.6, 0.95), (-1.3, 0.9, 0.5), (-0.4, 0.7, 0.75), 30, 30),
    (17.0, 18.9, (0.5, -1.45, 1.1), (0.5, -1.4, 1.1), (0.45, 0.45, 1.0), (0.5, 0.45, 1.0), 30, 30),
    (18.9, 20.4, (-0.2, 0.6, 0.9), (-0.15, 0.62, 0.9), (0.7, 0.8, 0.85), (0.72, 0.85, 0.85), 30, 32),
    (20.4, 24.0, (0.4, -2.0, 1.3), (0.4, -1.85, 1.28), (0.5, 0.55, 0.95), (0.5, 0.55, 0.95), 26, 26),
    (24.0, 26.6, (-1.14, 1.24, 1.2), (-1.1, 1.22, 1.2), (0.73, 0.62, 1.1), (0.73, 0.62, 1.1), 28, 28),
    (26.6, 30.05, (1.0, -3.0, 1.3), (0.6, -5.8, 1.9), (0.6, 0.9, 1.0), (2.0, 2.2, 0.9), 28, 26),
]
camera_shots(SHOTS)
lights()
render("build/part4/frames")
