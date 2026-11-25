"""حلقة «سند وميراي والفرخ الصغير» ثلاثية الأبعاد في Blender.

يبني المشهد كاملاً بالكود (حديقة، شجرة، عش، سند، ميراي، قطة، فرخ وأمه)
ويحرّكه حسب جدول المشاهد (30 ثانية)، ثم يرسم الإطارات بمحرك Cycles.

الاستخدام:
    python blender/ep06_baby_bird.py --out build/ep06/frames     # مع: pip install bpy==4.2.*
    blender -b -P blender/ep06_baby_bird.py -- --out build/ep06/frames
    blender -b -P blender/ep06_baby_bird.py -- --still 3,8,14 --res 360x640 --samples 8
    blender -b -P blender/ep06_baby_bird.py -- --frames 1 180      # جزء من الحلقة

الخيارات:
    --out DIR          مجلد الإطارات (الافتراضي build/ep06/frames)
    --res WxH          الدقة (الافتراضي 720x1280، عمودي 9:16)
    --samples N        عيّنات Cycles لكل بكسل (الافتراضي 32)
    --frames A B       رسم الإطارات من A إلى B فقط
    --still T1,T2,...  رسم صور ثابتة عند هذه الثواني فقط (للمعاينة)
    --save FILE.blend  حفظ ملف Blender لفتحه وتعديله يدوياً
"""

import argparse
import math
import random
import sys
from math import atan2, cos, degrees, radians, sin
from pathlib import Path

import bpy
from mathutils import Vector

FPS = 24
DURATION = 30.0
S = 1.15  # مقياس الطفلين


def F(t: float) -> int:
    return int(round(t * FPS)) + 1


# ============================================================ أدوات عامة
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = F(DURATION) - 1
random.seed(7)


def lin(h: str):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


_mats: dict = {}


def mat(name, hexc, rough=0.55, emit=0.0, vary=None, bump=None, sheen=0.0):
    """مادة بسيطة. vary=(لون ثانٍ، مقياس) لتدرّج لوني، bump=(قوة، مقياس) لملمس."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hexc), 1)
    b.inputs["Roughness"].default_value = rough
    if sheen and "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = sheen
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(hexc), 1)
        b.inputs["Emission Strength"].default_value = emit
    if vary:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = vary[1]
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.7
        ramp.color_ramp.elements[0].color = (*lin(hexc), 1)
        ramp.color_ramp.elements[1].color = (*lin(vary[0]), 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    if bump:
        tex2 = nt.nodes.new("ShaderNodeTexNoise")
        tex2.inputs["Scale"].default_value = bump[1]
        tex2.inputs["Detail"].default_value = 6
        bn = nt.nodes.new("ShaderNodeBump")
        bn.inputs["Strength"].default_value = bump[0]
        nt.links.new(tex2.outputs["Fac"], bn.inputs["Height"])
        nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    _mats[name] = m
    return m


_meshes: dict = {}


def base_mesh(kind):
    if kind in _meshes:
        return _meshes[kind]
    ops = bpy.ops.mesh
    if kind == "sphere":
        ops.primitive_uv_sphere_add(radius=1, segments=32, ring_count=16)
    elif kind == "ball":  # كرة خفيفة للأشياء الكثيرة الصغيرة
        ops.primitive_uv_sphere_add(radius=1, segments=14, ring_count=8)
    elif kind == "ico":
        ops.primitive_ico_sphere_add(radius=1, subdivisions=3)
    elif kind == "cyl":
        ops.primitive_cylinder_add(radius=1, depth=1, vertices=20)
    elif kind == "cone":
        ops.primitive_cone_add(radius1=1, radius2=0, depth=1, vertices=20)
    elif kind == "taper":
        ops.primitive_cone_add(radius1=1, radius2=0.6, depth=1, vertices=20)
    elif kind == "dress":
        ops.primitive_cone_add(radius1=1, radius2=0.38, depth=1, vertices=32)
    elif kind == "cube":
        ops.primitive_cube_add(size=1)
    o = bpy.context.object
    me = o.data
    me.name = kind
    if kind != "cube":
        for p in me.polygons:
            p.use_smooth = True
        if hasattr(me, "use_auto_smooth"):
            me.use_auto_smooth = True
            me.auto_smooth_angle = radians(50)
    bpy.data.objects.remove(o)
    _meshes[kind] = me
    return me


def link(o):
    scene.collection.objects.link(o)
    return o


def part(kind, name, loc=(0, 0, 0), scale=1.0, m=None, parent=None, rot=(0, 0, 0)):
    me = base_mesh(kind) if isinstance(kind, str) else kind
    o = link(bpy.data.objects.new(name, me))
    if len(o.material_slots) == 0:
        me.materials.append(None)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = m
    o.parent = parent
    o.location = loc
    o.scale = scale if isinstance(scale, (tuple, list)) else (scale,) * 3
    o.rotation_euler = [radians(a) for a in rot]
    return o


def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    o = link(bpy.data.objects.new(name, None))
    o.empty_display_size = 0.1
    o.parent = parent
    o.location = loc
    o.rotation_euler = [radians(a) for a in rot]
    return o


def rod(name, p0, p1, r, m, parent=None, kind="cyl"):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    o = part(kind, name, (p0 + p1) / 2, (r, r, d.length), m, parent)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


def K(o, t, loc=None, rx=None, ry=None, rz=None, s=None):
    """مفتاح حركة عند الثانية t (الزوايا بالدرجات)."""
    f = F(t)
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=f)
    for i, v in enumerate((rx, ry, rz)):
        if v is not None:
            o.rotation_euler[i] = radians(v)
            o.keyframe_insert("rotation_euler", index=i, frame=f)
    if s is not None:
        o.scale = s if isinstance(s, (tuple, list)) else (s,) * 3
        o.keyframe_insert("scale", frame=f)


def heading(p_from, p_to):
    """زاوية الدوران حول Z ليواجه الجسم (المصمَّم نحو -Y) النقطة p_to."""
    return degrees(atan2(p_to[0] - p_from[0], -(p_to[1] - p_from[1])))


def near(prev, ang):
    """اختر الزاوية المكافئة الأقرب للسابقة كي لا يدور الجسم دورة كاملة."""
    while ang - prev > 180:
        ang -= 360
    while ang - prev < -180:
        ang += 360
    return ang


def frange(a, b, step):
    t = a
    while t < b - 1e-6:
        yield t
        t += step


# ============================================================ المواد
SKIN = mat("skin", "#F1AE82", 0.5, sheen=0.3)
WHITE = mat("eye_white", "#FFFFFF", 0.25)
IRIS = mat("iris", "#5A3418", 0.2)
PUPIL = mat("pupil", "#120A05", 0.15)
SHINE = mat("shine", "#FFFFFF", 0.1, emit=3.0)
MOUTH = mat("mouth", "#B5413F", 0.4)
BROW_S = mat("brow_s", "#5A3218", 0.6)
HAIR_S = mat("hair_sanad", "#7A4524", 0.55, vary=("#5E3419", 6), sheen=0.4)
HAIR_M = mat("hair_mirai", "#3A2216", 0.45, sheen=0.4)
HAIR_M_CURL = mat("hair_mirai_curl", "#3A2216", 0.5, vary=("#24140C", 7), sheen=0.5)

SHIRT = mat("shirt_blue", "#3D8BE0", 0.7, sheen=0.5)
SHORTS = mat("shorts", "#2B3C66", 0.7, sheen=0.4)
DRESS = mat("dress_yellow", "#FFC93C", 0.7, sheen=0.5)
RIBBON = mat("ribbon", "#FF7A59", 0.5)
SHOE_S = mat("shoe_sanad", "#E8553D", 0.45)
SHOE_M = mat("shoe_mirai", "#FFFFFF", 0.45)
CAT = mat("cat_orange", "#F08A2C", 0.6, vary=("#FFB466", 9), sheen=0.6)
CAT_W = mat("cat_white", "#FFF4E6", 0.6, sheen=0.6)
CAT_EYE = mat("cat_eye", "#7BC043", 0.2)
NOSE = mat("pink", "#F28AA0", 0.4)
CHICK = mat("chick_yellow", "#FFD84A", 0.6, sheen=0.8)
MOM = mat("mom_blue", "#4F86D9", 0.5, sheen=0.5)
MOM_B = mat("mom_belly", "#FFA45C", 0.55, sheen=0.5)
BEAK = mat("beak", "#FF9A1F", 0.4)
YARN = mat("yarn", "#E8456B", 0.8, bump=(0.6, 40), sheen=0.6)
BARK = mat("bark", "#7A4B2A", 0.85, vary=("#5C3820", 12), bump=(0.4, 18))
LEAF = mat("leaves", "#4FAE45", 0.65, vary=("#7ACB4C", 3), bump=(0.5, 14))
NEST = mat("nest", "#A4733C", 0.9, vary=("#7A5228", 30), bump=(1.0, 60))
GRASS = mat("grass", "#58B848", 0.8, vary=("#7FCC52", 0.6))
LAWN_HAIR = mat("grass_blades", "#62C04E", 0.6, vary=("#8AD65A", 2))
FENCE = mat("fence", "#FFF8EE", 0.6)
CLOUD = mat("cloud", "#FFFFFF", 0.9, emit=0.15)
HILL = mat("hill", "#7CC45A", 0.9, vary=("#9AD36B", 0.2))
PETALS = [mat(f"petal{i}", c, 0.5) for i, c in enumerate(["#FF6FA3", "#FFFFFF", "#B98CFF", "#FF8A3D", "#FF5A5A"])]
FLOWER_C = mat("flower_center", "#FFD23F", 0.5)

# ============================================================ الحديقة
bpy.ops.mesh.primitive_plane_add(size=1)
lawn = bpy.context.object
lawn.name = "lawn"
lawn.scale = (18, 18, 1)
lawn.location = (0, 2, 0)
bpy.ops.object.transform_apply(scale=True)
lawn.data.materials.append(GRASS)
lawn.data.materials.append(LAWN_HAIR)
lawn.modifiers.new("grass", "PARTICLE_SYSTEM")
ps = lawn.particle_systems[0].settings
ps.type = "HAIR"
ps.count = 30000
ps.hair_length = 0.05
ps.use_advanced_hair = True
ps.length_random = 0.6 if hasattr(ps, "length_random") else 0
ps.child_type = "INTERPOLATED"
ps.child_percent = 2
ps.rendered_child_count = 4
ps.material_slot = "grass_blades"
ps.root_radius = 1.0
ps.tip_radius = 0.0
ps.radius_scale = 0.007
ps.use_rotations = True
ps.rotation_factor_random = 0.3
ps.child_length_threshold = 0.0
ps.kink = "NO"

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.002))
far = bpy.context.object
far.name = "ground_far"
far.data.materials.append(GRASS)

# الشجرة والغصن المنخفض والعش
TREE = Vector((0.2, 2.3, 0))
part("taper", "trunk", (TREE.x, TREE.y, 1.4), (0.3, 0.3, 2.8), BARK)
rod("root1", (TREE.x, TREE.y, 0.15), (TREE.x + 0.45, TREE.y - 0.15, 0.0), 0.12, BARK, kind="taper")
rod("root2", (TREE.x, TREE.y, 0.15), (TREE.x - 0.45, TREE.y - 0.1, 0.0), 0.12, BARK, kind="taper")
NEST_P = Vector((1.35, 1.75, 0.80))
rod("branch_low", (TREE.x + 0.1, TREE.y - 0.1, 0.62), (NEST_P.x + 0.35, NEST_P.y - 0.12, NEST_P.z - 0.06), 0.065, BARK, kind="taper")
rod("twig", (NEST_P.x - 0.2, NEST_P.y, NEST_P.z - 0.08), (NEST_P.x - 0.05, NEST_P.y + 0.25, NEST_P.z + 0.25), 0.025, BARK)
part("ico", "twig_leaf", (NEST_P.x - 0.05, NEST_P.y + 0.27, NEST_P.z + 0.28), (0.18, 0.12, 0.12), LEAF)
rod("branch_up1", (TREE.x, TREE.y, 2.2), (TREE.x + 1.1, TREE.y + 0.2, 3.0), 0.09, BARK, kind="taper")
rod("branch_up2", (TREE.x, TREE.y, 2.4), (TREE.x - 1.0, TREE.y + 0.1, 3.1), 0.09, BARK, kind="taper")
for i, (dx, dy, dz, r) in enumerate([(0, 0, 3.6, 1.25), (1.0, 0.2, 3.2, 0.95), (-1.0, 0.1, 3.3, 1.0),
                                     (0.5, -0.5, 3.0, 0.8), (-0.5, -0.4, 3.1, 0.8), (0.2, 0.4, 4.3, 0.9),
                                     (-0.6, 0.5, 4.0, 0.85), (0.8, 0.6, 3.9, 0.8)]):
    part("ico", f"leaves{i}", (TREE.x + dx, TREE.y + dy, dz), (r, r * 0.95, r * 0.85), LEAF)

bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.065, major_segments=32, minor_segments=12,
                                 location=NEST_P)
nest = bpy.context.object
nest.name = "nest"
nest.data.materials.append(NEST)
for p in nest.data.polygons:
    p.use_smooth = True
part("sphere", "nest_bottom", (NEST_P.x, NEST_P.y, NEST_P.z - 0.035), (0.17, 0.17, 0.06), NEST)

# سياج أبيض وشجيرات وتلال وغيوم
for i in range(45):
    x = -7 + i * 0.32
    part("cube", f"picket{i}", (x, 6.0, 0.4), (0.12, 0.04, 0.8), FENCE)
    part("cone", f"picket_tip{i}", (x, 6.0, 0.86), (0.085, 0.085, 0.12), FENCE, rot=(0, 0, 45))
for z in (0.25, 0.6):
    part("cube", f"rail{z}", (0, 6.05, z), (14.5, 0.03, 0.08), FENCE)
for i in range(14):
    x = -7 + i * 1.05 + random.uniform(-0.2, 0.2)
    for j in range(3):
        r = random.uniform(0.35, 0.55)
        part("ico", f"bush{i}_{j}", (x + random.uniform(-0.3, 0.3), 6.6 + random.uniform(-0.2, 0.2), r * 0.8),
             (r, r, r * 0.9), LEAF)
for i, (x, y, r) in enumerate([(-14, 40, 14), (6, 45, 16), (24, 38, 12), (-30, 35, 10)]):
    part("sphere", f"hill{i}", (x, y, -r * 0.55), (r * 1.6, r, r), HILL)
for i, (x, z) in enumerate([(-6, 9), (3, 10.5), (9, 8.5), (-1, 12)]):
    for j in range(5):
        r = random.uniform(0.9, 1.6)
        part("ball", f"cloud{i}_{j}", (x + j * 1.1 - 2.2, 30, z + random.uniform(-0.4, 0.5)), (r, r * 0.7, r * 0.8), CLOUD)
for i, (x, y) in enumerate([(-5.5, 5.2), (5.2, 5.0)]):
    part("taper", f"bgtrunk{i}", (x, y, 1.0), (0.22, 0.22, 2.0), BARK)
    for j in range(4):
        r = random.uniform(0.8, 1.1)
        part("ico", f"bgleaf{i}_{j}", (x + random.uniform(-0.6, 0.6), y + random.uniform(-0.3, 0.3), 2.3 + random.uniform(0, 1)),
             (r, r, r * 0.9), LEAF)

# زهور (بعيداً عن منطقة الحركة)
n = 0
while n < 150:
    x, y = random.uniform(-6.5, 6.5), random.uniform(-3.5, 5.6)
    if -3.4 < x < 2.4 and -1.4 < y < 2.9 and random.random() < 0.9:
        continue
    pm = random.choice(PETALS)
    h = random.uniform(0.08, 0.16)
    rod(f"stem{n}", (x, y, 0), (x, y, h), 0.008, LEAF)
    part("ball", f"fc{n}", (x, y, h), (0.025, 0.025, 0.018), FLOWER_C)
    for k in range(5):
        a = k * 2 * math.pi / 5
        part("ball", f"fp{n}_{k}", (x + 0.04 * cos(a), y + 0.04 * sin(a), h - 0.004), (0.032, 0.032, 0.01), pm,
             rot=(0, 0, degrees(a)))
    n += 1


# ============================================================ الطفلان
def kid(name, pos, head_deg, girl=False):
    root = empty(name, (pos[0], pos[1], 0), rot=(0, 0, head_deg))
    root.scale = (S, S, S)
    k = {"root": root, "girl": girl}
    shoe = SHOE_M if girl else SHOE_S
    legs = []
    for sx in (1, -1):
        lp = empty(f"{name}_leg{sx}", (0.085 * sx, 0, 0.44), root)
        part("cyl", f"{name}_legm{sx}", (0, 0, -0.2), (0.055, 0.055, 0.38), SKIN, lp)
        part("sphere", f"{name}_shoe{sx}", (0, -0.035, -0.4), (0.07, 0.115, 0.055), shoe, lp)
        legs.append(lp)
    k["legs"] = legs
    hips = empty(f"{name}_hips", (0, 0, 0.44), root)
    k["hips"] = hips
    top = SHIRT if not girl else DRESS
    if girl:
        part("dress", f"{name}_dress", (0, 0, 0.02), (0.27, 0.24, 0.42), DRESS, hips)
        part("sphere", f"{name}_bodice", (0, 0, 0.2), (0.165, 0.14, 0.13), DRESS, hips)
        part("cyl", f"{name}_hem", (0, 0, -0.18), (0.272, 0.242, 0.03), mat("hem", "#FFFFFF", 0.6), hips)
    else:
        part("cyl", f"{name}_shorts", (0, 0, 0.02), (0.17, 0.14, 0.16), SHORTS, hips)
        part("sphere", f"{name}_torso", (0, 0, 0.17), (0.19, 0.155, 0.2), SHIRT, hips)
        part("cyl", f"{name}_collar", (0, -0.01, 0.33), (0.08, 0.07, 0.03), mat("collar", "#FFFFFF", 0.6), hips)
    part("cyl", f"{name}_neck", (0, 0, 0.34), (0.05, 0.05, 0.08), SKIN, hips)

    arms = []
    for sx in (1, -1):
        sh = empty(f"{name}_sh{sx}", (0.2 * sx, 0, 0.27), hips)
        part("sphere", f"{name}_sleeve{sx}", (0.005 * sx, 0, -0.03), (0.075, 0.075, 0.085), top, sh)
        part("cyl", f"{name}_arm{sx}", (0, 0, -0.17), (0.042, 0.042, 0.28), SKIN, sh)
        part("sphere", f"{name}_hand{sx}", (0, 0, -0.33), (0.055, 0.05, 0.06), SKIN, sh)
        hand_pt = empty(f"{name}_handpt{sx}", (0, 0, -0.34), sh)
        arms.append(sh)
        k[f"handpt{sx}"] = hand_pt
    k["arms"] = arms

    hp = empty(f"{name}_headpivot", (0, 0, 0.36), hips)
    k["head"] = hp
    hc = Vector((0, 0, 0.23))
    part("sphere", f"{name}_head", hc, (0.24, 0.23, 0.235), SKIN, hp)
    for sx in (1, -1):
        part("sphere", f"{name}_ear{sx}", hc + Vector((0.235 * sx, 0.01, -0.01)), (0.035, 0.05, 0.06), SKIN, hp)
    part("sphere", f"{name}_nose", hc + Vector((0, -0.235, -0.04)), (0.028, 0.02, 0.022), SKIN, hp)
    eyes = empty(f"{name}_eyes", hc + Vector((0, -0.207, 0.0)), hp)
    k["eyes"] = eyes
    for sx in (1, -1):  # عينان صغيرتان داكنتان ملتصقتان بالوجه
        e = Vector((0.085 * sx, 0, 0))
        part("sphere", f"{name}_iris{sx}", e + Vector((0, -0.006, -0.004)), (0.03, 0.01, 0.038), IRIS, eyes)
        part("sphere", f"{name}_pupil{sx}", e + Vector((0, -0.011, -0.006)), (0.018, 0.006, 0.024), PUPIL, eyes)
        part("sphere", f"{name}_shine{sx}", e + Vector((0.009, -0.014, 0.012)), (0.008, 0.003, 0.008), SHINE, eyes)
        part("sphere", f"{name}_brow{sx}", hc + Vector((0.085 * sx, -0.2, 0.085)), (0.035, 0.01, 0.008),
             BROW_S if not girl else HAIR_M, hp, rot=(0, -8 * sx, 0))
    # ابتسامة: نصف حلقة
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.008, major_segments=24, minor_segments=8)
    sm = bpy.context.object
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(sm.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > -0.012], context="VERTS")
    bm.to_mesh(sm.data)
    bm.free()
    for p in sm.data.polygons:
        p.use_smooth = True
    sm.data.materials.append(MOUTH)
    sm.name = f"{name}_smile"
    sm.parent = hp
    sm.location = hc + Vector((0, -0.205, -0.1))
    sm.rotation_euler = (radians(90 - 8), 0, 0)
    sm.scale = (1, 1, 0.5)

    if not girl:  # شعر بني مجعّد
        golden = math.pi * (3 - math.sqrt(5))
        for i in range(140):
            zz = 1 - (i / 139) * 2
            rr = math.sqrt(1 - zz * zz)
            a = golden * i
            d = Vector((cos(a) * rr, sin(a) * rr, zz))
            if d.z < -0.05 or (d.y < -0.35 and d.z < 0.55) or (abs(d.x) > 0.8 and d.z < 0.25):
                continue
            rad = random.uniform(0.06, 0.075)
            part("ball", f"{name}_curl{i}", hc + d * 0.225 + Vector((0, 0.01, 0.015)), rad, HAIR_S, hp)
    else:  # شعر داكن وضفيرتان
        # غطاء شعر واحد متصل: يغطي الجبهة وأعلى الرأس وخلفه ويترك الوجه مكشوفاً
        import bmesh
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=128, ring_count=64)
        cap = bpy.context.object
        bm = bmesh.new()
        bm.from_mesh(cap.data)
        def sstep(e0, e1, x):
            t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
            return t * t * (3 - 2 * t)

        # بدل قصّ الشكل: نُدخل منطقة الوجه داخل الرأس بتدرّج ناعم فيظهر خط شعر منحنٍ وأملس
        for v in bm.verts:
            d = v.co.copy()
            hairline = 0.42 + 0.25 * min(1.0, abs(d.x) / 0.6) ** 2
            face = sstep(-0.35, -0.5, d.y) * sstep(hairline + 0.03, hairline - 0.03, d.z) * sstep(0.78, 0.68, abs(d.x))
            under = sstep(-0.4, -0.5, d.z) * sstep(0.4, 0.3, d.y)
            v.co = d * (1 - 0.3 * max(face, under))
        bm.to_mesh(cap.data)
        bm.free()
        for p in cap.data.polygons:
            p.use_smooth = True
        cap.data.materials.append(HAIR_M)
        cap.name = f"{name}_haircap"
        cap.parent = hp
        cap.location = hc + Vector((0, 0.008, 0.012))
        cap.scale = (0.256, 0.244, 0.246)
        # تجعيدات داكنة فوق الغطاء، بنفس خط الشعر، ليبدو الشعر مجعّداً ومتصلاً
        golden = math.pi * (3 - math.sqrt(5))
        for i in range(260):
            zz = 1 - (i / 259) * 2
            rr = math.sqrt(max(0.0, 1 - zz * zz))
            a = golden * i
            d = Vector((cos(a) * rr, sin(a) * rr, zz))
            hairline = 0.42 + 0.25 * min(1.0, abs(d.x) / 0.6) ** 2
            face = sstep(-0.35, -0.5, d.y) * sstep(hairline + 0.03, hairline - 0.03, d.z) * sstep(0.78, 0.68, abs(d.x))
            under = sstep(-0.4, -0.5, d.z) * sstep(0.4, 0.3, d.y)
            if max(face, under) > 0.05 or d.z < -0.35:
                continue
            p = Vector((d.x * 0.256, d.y * 0.244, d.z * 0.246)) + hc + Vector((0, 0.008, 0.012))
            part("ball", f"{name}_curl{i}", p, random.uniform(0.042, 0.055), HAIR_M_CURL, hp)
        for sx in (1, -1):
            bp = empty(f"{name}_braid{sx}", hc + Vector((0.2 * sx, 0.06, -0.06)), hp)
            for j in range(6):
                rr = 0.055 - j * 0.003
                part("sphere", f"{name}_braid{sx}_{j}", (0.03 * sx + 0.012 * j * sx, 0.01 * j, -0.065 * j), rr, HAIR_M, bp)
            part("sphere", f"{name}_tie{sx}", (0.03 * sx + 0.012 * 5 * sx, 0.05, -0.36), (0.045, 0.045, 0.025), RIBBON, bp)
            part("sphere", f"{name}_tuft{sx}", (0.03 * sx + 0.012 * 6 * sx, 0.06, -0.41), (0.04, 0.04, 0.05), HAIR_M, bp)
            part("sphere", f"{name}_bow{sx}", hc + Vector((0.17 * sx, 0.02, 0.17)), (0.05, 0.03, 0.035), RIBBON, hp,
                 rot=(0, 30 * sx, 0))
    return k


# ============================================================ القطة والطيور
def cat(pos, head_deg):
    root = empty("cat", (pos[0], pos[1], 0), rot=(0, 0, head_deg))
    c = {"root": root}
    body = empty("cat_body", (0, 0, 0), root)
    c["body"] = body
    part("sphere", "cat_torso", (0, 0.02, 0.22), (0.14, 0.27, 0.13), CAT, body)
    part("sphere", "cat_chest", (0, -0.17, 0.2), (0.1, 0.08, 0.1), CAT_W, body)
    hp = empty("cat_headpivot", (0, -0.24, 0.3), body)
    c["head"] = hp
    part("sphere", "cat_head", (0, -0.06, 0.04), (0.14, 0.125, 0.12), CAT, hp)
    for sx in (1, -1):
        part("cone", f"cat_ear{sx}", (0.075 * sx, -0.05, 0.15), (0.05, 0.03, 0.1), CAT, hp, rot=(0, 18 * sx, 0))
        part("cone", f"cat_earin{sx}", (0.075 * sx, -0.068, 0.145), (0.03, 0.01, 0.07), NOSE, hp, rot=(0, 18 * sx, 0))
        part("sphere", f"cat_eye{sx}", (0.052 * sx, -0.17, 0.06), (0.033, 0.016, 0.037), CAT_EYE, hp)
        part("sphere", f"cat_pupil{sx}", (0.052 * sx, -0.183, 0.06), (0.012, 0.006, 0.03), PUPIL, hp)
        part("sphere", f"cat_shine{sx}", (0.058 * sx, -0.188, 0.075), (0.007, 0.003, 0.007), SHINE, hp)
        part("sphere", f"cat_muzzle{sx}", (0.026 * sx, -0.172, -0.005), (0.035, 0.03, 0.03), CAT_W, hp)
    part("sphere", "cat_nose", (0, -0.198, 0.018), (0.015, 0.01, 0.01), NOSE, hp)
    legs = []
    for i, (lx, ly) in enumerate([(0.08, -0.17), (-0.08, -0.17), (0.08, 0.17), (-0.08, 0.17)]):
        lp = empty(f"cat_leg{i}", (lx, ly, 0.17), root)
        part("cyl", f"cat_legm{i}", (0, 0, -0.08), (0.036, 0.036, 0.16), CAT, lp)
        part("sphere", f"cat_paw{i}", (0, -0.012, -0.155), (0.042, 0.05, 0.03), CAT_W, lp)
        legs.append(lp)
    c["legs"] = legs
    tail = empty("cat_tail", (0, 0.27, 0.25), body)
    c["tail"] = tail
    p = Vector((0, 0, 0))
    for j in range(8):
        a = radians(20 + j * 11)
        p = p + Vector((0, 0.055 * cos(a), 0.055 * sin(a)))
        part("ball", f"cat_tail{j}", p.copy(), 0.036 - j * 0.001, CAT if j < 7 else CAT_W, tail)
    return c


def bird(name, pos, head_deg, body_m, size=1.0, mom=False):
    root = empty(name, pos, rot=(0, 0, head_deg))
    root.scale = (size,) * 3
    b = {"root": root}
    bd = empty(f"{name}_body", (0, 0, 0), root)
    b["body"] = bd
    part("sphere", f"{name}_torso", (0, 0, 0.09), (0.09, 0.1, 0.085), body_m, bd)
    if mom:
        part("sphere", f"{name}_belly", (0, -0.04, 0.08), (0.075, 0.07, 0.07), MOM_B, bd)
        part("cone", f"{name}_tail", (0, 0.13, 0.11), (0.05, 0.02, 0.1), body_m, bd, rot=(-70, 0, 0))
    hp = empty(f"{name}_headpivot", (0, -0.05, 0.15), bd)
    b["head"] = hp
    part("sphere", f"{name}_head", (0, -0.01, 0.03), 0.068, body_m, hp)
    part("cone", f"{name}_beak", (0, -0.085, 0.02), (0.022, 0.018, 0.045), BEAK, hp, rot=(90, 0, 0))
    for sx in (1, -1):
        part("sphere", f"{name}_eye{sx}", (0.034 * sx, -0.055, 0.045), (0.017, 0.012, 0.02), PUPIL, hp)
        part("sphere", f"{name}_shine{sx}", (0.038 * sx, -0.066, 0.052), 0.005, SHINE, hp)
    if not mom:
        for j in range(3):
            part("sphere", f"{name}_tuft{j}", (0.012 * (j - 1), 0.0, 0.1), (0.012, 0.012, 0.03), body_m, hp,
                 rot=(0, 20 * (j - 1), 0))
    wings = []
    for sx in (1, -1):
        wp = empty(f"{name}_wing{sx}", (0.08 * sx, 0.0, 0.12), bd)
        part("sphere", f"{name}_wingm{sx}", (0.02 * sx, 0.02, -0.03), (0.025, 0.07 if mom else 0.055, 0.05), body_m, wp,
             rot=(-15, 0, 0))
        wings.append(wp)
    b["wings"] = wings
    for sx in (1, -1):
        rod(f"{name}_leg{sx}", (0.03 * sx, 0, 0.03), (0.03 * sx, -0.01, 0.0), 0.008, BEAK, bd)
    return b


# ============================================================ الشخصيات في أماكنها
CHICK_P = Vector((0.75, 1.3, 0.0))
SANAD0 = (1.55, -0.55)
MIRAI0 = (-0.55, -0.55)
YARN0 = Vector((-0.95, -0.6, 0.1))
YARN1 = Vector((-2.6, -0.35, 0.1))
CAT0 = (-3.2, 2.5)
CAT_STALK = (-0.05, 1.55)
CAT_PLAY = (-2.25, -0.08)
HI_S = (1.06, 0.55)
HI_M = (0.40, 0.55)

sanad = kid("sanad", SANAD0, -90)
mirai = kid("mirai", MIRAI0, 90, girl=True)
kitty = cat(CAT0, heading(CAT0, CAT_STALK))
chick = bird("chick", (CHICK_P.x, CHICK_P.y, 0), 0, CHICK, 1.0)
mom = bird("mom", (5.0, 5.5, 3.6), 0, MOM, 1.35, mom=True)

yarn_roll = empty("yarn_roll", YARN0)
yarn = part("sphere", "yarn", (0, 0, 0), 0.1, YARN, yarn_roll)
for j in range(5):  # لفّات الخيط
    bpy.ops.mesh.primitive_torus_add(major_radius=0.098, minor_radius=0.006, major_segments=40, minor_segments=6)
    w = bpy.context.object
    w.name = f"yarn_wrap{j}"
    w.data.materials.append(YARN)
    w.parent = yarn
    w.scale = (10, 10, 10)
    w.rotation_euler = (radians(random.uniform(0, 180)), radians(random.uniform(0, 180)), 0)
yarn.scale = (0.1, 0.1, 0.1)
rod("yarn_thread", (YARN0.x + 0.08, YARN0.y, 0.01), (YARN0.x + 0.3, YARN0.y + 0.1, 0.005), 0.006, YARN)
bpy.data.objects["yarn_thread"].parent = None


# ============================================================ أدوات الحركة
def walk(k, t0, t1, p1, step=0.42, legs_key=True):
    root = k["root"]
    p0 = tuple(root.location)[:2]
    K(root, t0, loc=(p0[0], p0[1], 0))
    K(root, t1, loc=(p1[0], p1[1], 0))
    if legs_key:
        sgn = 1
        for t in frange(t0, t1, step / 2):
            K(k["legs"][0], t, rx=24 * sgn)
            K(k["legs"][1], t, rx=-24 * sgn)
            K(k["hips"], t + step / 4, loc=(0, 0, 0.455))
            K(k["hips"], t, loc=(0, 0, 0.44))
            sgn = -sgn
        K(k["legs"][0], t1, rx=0)
        K(k["legs"][1], t1, rx=0)
        K(k["hips"], t1, loc=(0, 0, 0.44))


def arm_swing(k, t0, t1, step=0.42):
    sgn = 1
    for t in frange(t0, t1, step / 2):
        K(k["arms"][0], t, rx=-18 * sgn, ry=0)
        K(k["arms"][1], t, rx=18 * sgn, ry=0)
        sgn = -sgn
    K(k["arms"][0], t1, rx=0, ry=0)
    K(k["arms"][1], t1, rx=0, ry=0)


def turn(k, t0, t1, ang):
    root = k["root"]
    cur = degrees(root.rotation_euler.z)
    ang = near(cur, ang)
    K(root, t0, rz=cur)
    K(root, t1, rz=ang)
    return ang


def hop(k, t, h=0.12, dur=0.36):
    root = k["root"]
    x, y = root.location.x, root.location.y
    K(root, t, loc=(x, y, 0))
    K(root, t + dur / 2, loc=(x, y, h))
    K(root, t + dur, loc=(x, y, 0))


def blink(k, t):
    K(k["eyes"], t - 0.05, s=1)
    K(k["eyes"], t, s=(1, 1, 0.1))
    K(k["eyes"], t + 0.08, s=1)


def look(k, t, rz=0, rx=0, ry=0):
    K(k["head"], t, rx=rx, ry=ry, rz=rz)


def arms(k, t, a=(0, 0), b=(0, 0)):
    """a/b = (rx, ry) للذراع اليمنى(+x) واليسرى(-x). rx سالب = الذراع للأمام."""
    K(k["arms"][0], t, rx=a[0], ry=a[1])
    K(k["arms"][1], t, rx=b[0], ry=b[1])


def bow(k, t, deg):
    K(k["hips"], t, rx=deg)


def flap(b, t0, t1, amp=55, period=0.16):
    sgn = 1
    for t in frange(t0, t1, period / 2):
        K(b["wings"][0], t, ry=amp * sgn)
        K(b["wings"][1], t, ry=-amp * sgn)
        sgn = -sgn
    K(b["wings"][0], t1, ry=0)
    K(b["wings"][1], t1, ry=0)


def chirp_hop(b, t, h=0.03):
    bd = b["body"]
    K(bd, t, loc=(0, 0, 0))
    K(bd, t + 0.08, loc=(0, 0, h))
    K(bd, t + 0.16, loc=(0, 0, 0))
    K(b["head"], t, rx=0)
    K(b["head"], t + 0.08, rx=-25)
    K(b["head"], t + 0.2, rx=0)


# ============================================================ المشهد 1 (0–6): زقزقة واكتشاف الفرخ
for k in (sanad, mirai):
    K(k["root"], 0, rz=degrees(k["root"].rotation_euler.z))
    arms(k, 0)
    bow(k, 0, 0)
    look(k, 0)
# لعب: قفزات وتلويح
for t in (0.2, 0.75, 1.3):
    hop(sanad, t, 0.1)
    hop(mirai, t + 0.25, 0.1)
arms(sanad, 0.2, (-20, -60), (-20, 60))
arms(sanad, 1.6, (0, 0), (0, 0))
arms(mirai, 0.4, (-30, -50), (-30, 50))
arms(mirai, 1.7, (0, 0), (0, 0))
# زقزقة: الفرخ يرفرف والطفلان يلتفتان
for t in (0.6, 1.4, 2.2, 3.4, 4.6):
    chirp_hop(chick, t)
flap(chick, 2.2, 2.7, amp=40)
flap(chick, 4.6, 5.1, amp=40)
look(sanad, 2.1, rz=0)
look(sanad, 2.5, rz=-35, rx=-10)
look(mirai, 2.2, rz=0)
look(mirai, 2.6, rz=40, rx=-10)
ang_s = turn(sanad, 3.0, 3.6, heading(SANAD0, CHICK_P))
ang_m = turn(mirai, 3.1, 3.7, heading(MIRAI0, CHICK_P))
look(sanad, 3.6, rz=0, rx=-5)
look(mirai, 3.7, rz=0, rx=-5)
blink(sanad, 1.9)
blink(mirai, 4.4)
# الفرخ يلتفت يميناً ويساراً
K(chick["head"], 0, rz=0)
for t, a in ((3.0, 25), (3.8, -25), (4.4, 0), (5.4, 20)):
    K(chick["head"], t, rz=a)

# ============================================================ المشهد 2 (6–12): القطة تتسلل، سند يشير
K(kitty["root"], 0, loc=(CAT0[0], CAT0[1], 0))
K(kitty["root"], 6.0, loc=(CAT0[0], CAT0[1], 0))
K(kitty["body"], 6.0, loc=(0, 0, 0), rx=0)
K(kitty["body"], 7.0, loc=(0, 0, -0.06), rx=-4)  # انخفاض
K(kitty["root"], 10.6, loc=(CAT_STALK[0], CAT_STALK[1], 0))
sg = 1
for t in frange(6.4, 10.6, 0.3):
    for i, lp in enumerate(kitty["legs"]):
        K(lp, t, rx=(18 if i in (0, 3) else -18) * sg)
    sg = -sg
for lp in kitty["legs"]:
    K(lp, 10.6, rx=0)
K(kitty["head"], 6.0, rx=0, rz=0)
K(kitty["head"], 7.0, rx=8, rz=0)
# ذيل يتحرك يميناً ويساراً، ثم هزّة استعداد
sg = 1
for t in frange(6.0, 12.6, 0.5):
    K(kitty["tail"], t, rz=28 * sg, rx=0)
    sg = -sg
for t in frange(10.9, 12.4, 0.2):
    K(kitty["body"], t, loc=(0.02 * sg, 0, -0.08), rx=-6)
    sg = -sg
K(kitty["body"], 12.4, loc=(0, 0, -0.08), rx=-6)
# الفرخ يتجمّد خائفاً قليلاً
K(chick["head"], 8.5, rz=40)
K(chick["body"], 8.5, loc=(0, 0, 0))
# سند يلاحظ ويشير بسرعة
look(sanad, 8.4, rz=0, rx=-5)
look(sanad, 8.8, rz=-25, rx=-5)
K(sanad["eyes"], 8.8, s=1)
K(sanad["eyes"], 9.0, s=1.25)
K(sanad["eyes"], 10.5, s=1.25)
K(sanad["eyes"], 10.8, s=1)
ang_s = turn(sanad, 9.0, 9.3, heading(SANAD0, (0.35, 1.45)))
arms(sanad, 9.0, (0, 0), (0, 0))
arms(sanad, 9.3, (-100, 0), (0, 0))
arms(sanad, 11.2, (-100, 0), (0, 0))
arms(sanad, 11.6, (0, 0), (0, 0))
look(sanad, 9.3, rz=0, rx=-5)
hop(sanad, 9.35, 0.06, 0.25)
# ميراي تلتفت إليه
look(mirai, 9.5, rz=0)
look(mirai, 9.9, rz=-55)
look(mirai, 11.2, rz=-55)
look(mirai, 11.6, rz=0)
blink(mirai, 10.3)

# ============================================================ المشهد 3 (12–19): ميراي تدحرج الكرة، القطة تجري، سند يرفع الفرخ
ang_m = turn(mirai, 11.6, 12.1, heading(MIRAI0, YARN1))
bow(mirai, 12.1, 0)
bow(mirai, 12.5, 38)
arms(mirai, 12.1, (0, 0), (0, 0))
arms(mirai, 12.5, (40, 0), (0, 0))
arms(mirai, 13.0, (-75, 0), (0, 0))
bow(mirai, 13.4, 38)
bow(mirai, 13.9, 0)
arms(mirai, 13.9, (0, 0), (0, 0))
# دحرجة الكرة بعيداً عن الشجرة
d = (YARN1 - YARN0)
axis_ang = degrees(atan2(d.y, d.x)) + 90  # محور الدوران عمودي على الاتجاه
K(yarn_roll, 0, loc=tuple(YARN0), rz=axis_ang - 90)
K(yarn_roll, 12.9, loc=tuple(YARN0), rz=axis_ang - 90)
K(yarn_roll, 15.2, loc=tuple(YARN1), rz=axis_ang - 90)
yarn_roll.rotation_euler.z = radians(axis_ang - 90)
K(yarn, 12.9, ry=0)
K(yarn, 15.2, ry=degrees(d.length / 0.1))
for c in yarn_roll.animation_data.action.fcurves:
    for kp in c.keyframe_points:
        kp.interpolation = "BEZIER"
        kp.easing = "EASE_OUT"
# القطة تلتفت وتجري خلف الكرة
K(kitty["head"], 12.6, rz=0)
K(kitty["head"], 13.1, rz=-50)
K(kitty["root"], 13.0, loc=(CAT_STALK[0], CAT_STALK[1], 0), rz=heading(CAT0, CAT_STALK))
cat_ang = near(heading(CAT0, CAT_STALK), heading(CAT_STALK, CAT_PLAY))
K(kitty["root"], 13.5, rz=cat_ang)
K(kitty["head"], 13.5, rz=0, rx=0)
K(kitty["body"], 13.0, loc=(0, 0, -0.08), rx=-6)
K(kitty["body"], 13.4, loc=(0, 0, 0), rx=0)
K(kitty["root"], 13.5, loc=(CAT_STALK[0], CAT_STALK[1], 0))
K(kitty["root"], 16.0, loc=(CAT_PLAY[0], CAT_PLAY[1], 0))
sg = 1
for t in frange(13.5, 16.0, 0.16):
    for i, lp in enumerate(kitty["legs"]):
        K(lp, t, rx=(35 if i < 2 else -35) * sg)
    K(kitty["body"], t, loc=(0, 0, 0.04 if sg > 0 else 0), rx=4 * sg)
    sg = -sg
for lp in kitty["legs"]:
    K(lp, 16.0, rx=0)
K(kitty["body"], 16.0, loc=(0, 0, 0), rx=0)
# سند يمشي إلى الفرخ ويرفعه بكلتا يديه
PICK = (CHICK_P.x, CHICK_P.y - 0.33)
ang_s = turn(sanad, 12.6, 13.0, heading(SANAD0, PICK))
K(sanad["root"], 12.6, loc=(SANAD0[0], SANAD0[1], 0))
walk(sanad, 13.0, 15.6, PICK)
arm_swing(sanad, 13.0, 15.6)
ang_s = turn(sanad, 15.6, 15.9, near(ang_s, 180))
bow(sanad, 15.8, 0)
bow(sanad, 16.5, 58)
arms(sanad, 15.8, (0, 0), (0, 0))
arms(sanad, 16.5, (-58, 20), (-58, -20))
bow(sanad, 16.9, 58)
arms(sanad, 16.9, (-58, 20), (-58, -20))
bow(sanad, 17.8, 8)
arms(sanad, 17.8, (-80, 18), (-80, -18))
look(sanad, 15.8, rz=0, rx=0)
look(sanad, 16.5, rx=-15)
look(sanad, 17.8, rx=20)
look(mirai, 14.5, rz=0)
ang_m = turn(mirai, 14.5, 15.0, heading(MIRAI0, PICK))

# ============================================================ المشهد 4 (19–25): العودة إلى العش وأمّ الفرخ
NEST_STAND = (NEST_P.x, NEST_P.y - 0.43)
ang_s = turn(sanad, 18.6, 18.9, heading(PICK, NEST_STAND))
walk(sanad, 18.9, 20.6, NEST_STAND, legs_key=True)
ang_s = turn(sanad, 20.6, 20.9, near(ang_s, 180))
arms(sanad, 18.9, (-80, 18), (-80, -18))
arms(sanad, 20.7, (-80, 18), (-80, -18))
bow(sanad, 20.7, 8)
arms(sanad, 21.4, (-95, 16), (-95, -16))
bow(sanad, 21.4, 0)
arms(sanad, 21.8, (-95, 16), (-95, -16))
arms(sanad, 22.4, (-20, 0), (-20, 0))
arms(sanad, 22.8, (0, 0), (0, 0))
look(sanad, 21.4, rx=5)
look(sanad, 23.2, rx=10)
BACK = (NEST_STAND[0] - 0.33, NEST_STAND[1] - 0.3)
walk(sanad, 22.5, 23.1, BACK, step=0.3)

# الفرخ يتبع يدي سند أثناء الحمل (نقرأ موضع اليدين إطاراً بإطار)
K(chick["root"], 16.6, loc=(CHICK_P.x, CHICK_P.y, 0), rz=0)
carry_frames = list(range(F(16.7), F(21.75) + 1))
positions = []
for f in carry_frames:
    scene.frame_set(f)
    h1 = sanad["handpt1"].matrix_world.translation
    h2 = sanad["handpt-1"].matrix_world.translation
    positions.append((h1 + h2) / 2 + Vector((0, 0, -0.03)))
pick_root = Vector((CHICK_P.x, CHICK_P.y, 0))
for i, (f, p) in enumerate(zip(carry_frames, positions)):
    w = min(1.0, i / 8)  # انتقال ناعم من الأرض إلى اليدين
    q = pick_root.lerp(p, w)
    chick["root"].location = q
    chick["root"].keyframe_insert("location", frame=f)
chick_rz = near(0, ang_s - 180 + 180)
K(chick["root"], 17.0, rz=0)
K(chick["root"], 18.0, rz=near(0, ang_s + 180))
IN_NEST = Vector((NEST_P.x, NEST_P.y, NEST_P.z + 0.0))
K(chick["root"], 22.2, loc=tuple(IN_NEST))
K(chick["root"], 22.0, rz=near(0, ang_s + 180))
K(chick["root"], 22.6, rz=near(0, 90))
# الأم تطير وتهبط بجانب العش
MOM_LAND = (NEST_P.x + 0.3, NEST_P.y + 0.02, NEST_P.z + 0.03)
K(mom["root"], 0, loc=(5.0, 5.5, 3.6))
K(mom["root"], 21.6, loc=(5.0, 5.5, 3.6), rz=heading((5.0, 5.5), MOM_LAND))
K(mom["root"], 22.6, loc=(2.8, 3.3, 1.9))
K(mom["root"], 23.4, loc=MOM_LAND)
K(mom["root"], 23.1, rz=heading((5.0, 5.5), MOM_LAND))
K(mom["root"], 23.6, rz=-90)
flap(mom, 21.6, 23.5, amp=70, period=0.14)
flap(mom, 23.5, 23.9, amp=30, period=0.2)
K(mom["head"], 23.6, rx=0)
K(mom["head"], 24.1, rx=20)
K(mom["head"], 24.5, rx=0)
# الفرخ يزقزق ويفتح جناحيه
for t in (23.6, 24.0, 24.4, 24.8):
    chirp_hop(chick, t, 0.035)
flap(chick, 23.7, 25.0, amp=75, period=0.2)
for wg, sg in zip(chick["wings"], (1, -1)):
    K(wg, 25.0, ry=60 * sg)
    K(wg, 25.6, ry=0)
look(sanad, 23.6, rx=-10, rz=0)
look(sanad, 24.6, rz=-30)

# ميراي تأتي لتقف قرب سند
ang_m = turn(mirai, 19.3, 19.6, heading(MIRAI0, HI_M))
walk(mirai, 19.6, 23.2, HI_M)
arm_swing(mirai, 19.6, 23.2)
ang_m = turn(mirai, 23.2, 23.6, heading(HI_M, NEST_P))
look(mirai, 23.6, rx=-12)
look(mirai, 24.9, rx=0)
blink(mirai, 21.0)
blink(sanad, 19.4)

# ============================================================ المشهد 5 (25–30): تصفيق الكفّين وتراجع الكاميرا
ang_s = turn(sanad, 24.7, 25.0, heading(BACK, HI_S))
walk(sanad, 25.0, 25.9, HI_S)
ang_s = turn(sanad, 25.9, 26.2, near(ang_s, -90))
ang_m = turn(mirai, 25.0, 25.5, near(ang_m, 90))
look(sanad, 25.0, rz=0, rx=0)
look(mirai, 25.0, rz=0, rx=0)
arms(sanad, 26.0, (0, 0), (0, 0))
arms(mirai, 26.0, (0, 0), (0, 0))
arms(sanad, 26.6, (-118, 6), (0, 0))
arms(mirai, 26.6, (0, 0), (-118, -6))
arms(sanad, 27.6, (-118, 6), (0, 0))
arms(mirai, 27.6, (0, 0), (-118, -6))
arms(sanad, 28.1, (0, 0), (0, 0))
arms(mirai, 28.1, (0, 0), (0, 0))
hop(sanad, 26.45, 0.1)
hop(mirai, 26.45, 0.1)
hop(sanad, 28.3, 0.08)
hop(mirai, 28.45, 0.08)
blink(sanad, 27.9)
blink(mirai, 29.0)
ang_s = turn(sanad, 28.0, 28.4, near(ang_s, 0))
ang_m = turn(mirai, 28.0, 28.4, near(ang_m, 0))
arms(sanad, 28.5, (0, 0), (0, 0))
arms(sanad, 28.9, (0, 0), (-20, -110))
arms(mirai, 28.9, (-20, 110), (0, 0))
for tt in (29.2, 29.6):
    arms(sanad, tt, (0, 0), (-20, -130 if tt == 29.2 else -95))
    arms(mirai, tt, (-20, 130 if tt == 29.2 else 95), (0, 0))
# القطة تلعب بالكرة في الخلفية
yb = YARN1
sg = 1
for i, t in enumerate(frange(16.4, 30.0, 0.9)):
    off = Vector((0.18 * sg, 0.05 * sg, 0))
    K(yarn_roll, t, loc=tuple(yb + off))
    K(yarn, t, ry=degrees(d.length / 0.1) + 120 * sg)
    lp = kitty["legs"][0 if sg > 0 else 1]
    K(lp, t - 0.3, rx=0)
    K(lp, t - 0.15, rx=-70)
    K(lp, t, rx=0)
    K(kitty["head"], t, rz=12 * sg)
    sg = -sg
sg = 1
for t in frange(16.0, 30.0, 0.45):
    K(kitty["tail"], t, rz=22 * sg)
    sg = -sg

# ============================================================ الكاميرا
cam_data = bpy.data.cameras.new("cam")
cam = link(bpy.data.objects.new("cam", cam_data))
scene.camera = cam
target = empty("cam_target")
con = cam.constraints.new("TRACK_TO")
con.target = target
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"
cam_data.sensor_fit = "AUTO"
cam_data.dof.use_dof = True
cam_data.dof.focus_object = target
cam_data.dof.aperture_fstop = 3.5
cam_data.clip_start = 0.05

N = lambda v: tuple(v)
SHOTS = [
    # (t0, t1, cam0, cam1, tgt0, tgt1, lens0, lens1)
    (0.0, 3.0, (0.5, -5.3, 1.4), (0.5, -4.5, 1.25), (0.5, 0.2, 0.75), (0.5, 0.4, 0.7), 28, 28),
    (3.0, 6.0, (0.5, -4.5, 1.25), (0.85, 0.45, 0.3), (0.5, 0.4, 0.7), (CHICK_P.x, CHICK_P.y, 0.12), 28, 40),
    (6.0, 9.0, (-4.3, 1.6, 0.45), (-2.6, 1.0, 0.42), (-3.0, 2.4, 0.22), (-0.3, 1.6, 0.18), 28, 28),
    (9.0, 12.0, (2.3, 1.0, 1.0), (2.2, 0.8, 0.98), (1.35, -0.45, 0.85), (1.35, -0.45, 0.85), 32, 34),
    (12.0, 16.0, (-1.0, -5.0, 1.5), (-1.4, -4.6, 1.3), (-1.0, 0.3, 0.45), (-1.8, 0.1, 0.35), 28, 28),
    (16.0, 19.0, (2.9, 1.15, 0.6), (2.8, 1.1, 0.65), (0.75, 1.15, 0.5), (0.8, 1.1, 0.6), 30, 30),
    (19.0, 22.6, (3.1, -0.9, 1.4), (2.75, -0.2, 1.3), (1.15, 1.4, 0.8), (NEST_P.x, NEST_P.y, 0.85), 30, 34),
    (22.6, 25.0, (1.95, 0.75, 1.2), (1.9, 0.85, 1.15), (NEST_P.x + 0.12, NEST_P.y, 0.86), (NEST_P.x + 0.12, NEST_P.y, 0.86), 38, 42),
    (25.0, 27.8, (0.73, -2.0, 1.05), (0.73, -1.75, 1.05), (0.73, 0.55, 0.9), (0.73, 0.55, 0.95), 32, 32),
    (27.8, 30.05, (0.73, -1.75, 1.05), (-0.2, -7.6, 2.7), (0.73, 0.55, 0.95), (-0.4, 1.0, 0.8), 32, 28),
]
for t0, t1, c0, c1, g0, g1, l0, l1 in SHOTS:
    f0, f1 = F(t0), F(t1) - 1
    for f, c, g, l in ((f0, c0, g0, l0), (f1, c1, g1, l1)):
        cam.location = c
        cam.keyframe_insert("location", frame=f)
        target.location = g
        target.keyframe_insert("location", frame=f)
        cam_data.lens = l
        cam_data.keyframe_insert("lens", frame=f)

# ============================================================ الإضاءة والعالم
sun_d = bpy.data.lights.new("sun", "SUN")
sun_d.energy = 3.2
sun_d.color = (1.0, 0.92, 0.78)
sun_d.angle = radians(8)
sun = link(bpy.data.objects.new("sun", sun_d))
sun.rotation_euler = (radians(48), 0, radians(-35))
fill_d = bpy.data.lights.new("fill", "SUN")
fill_d.energy = 0.6
fill_d.color = (0.75, 0.85, 1.0)
fill_d.angle = radians(30)
fill = link(bpy.data.objects.new("fill", fill_d))
fill.rotation_euler = (radians(60), 0, radians(150))
fill_d.cycles.cast_shadow = False if hasattr(fill_d, "cycles") else True

world = bpy.data.worlds.new("sky")
scene.world = world
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes["Background"]
sky = wn.nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA"
sky.sun_disc = False
sky.sun_elevation = radians(42)
sky.sun_rotation = radians(145)
sky.air_density = 1.0
sky.dust_density = 0.6
wn.links.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.22

# ============================================================ إعدادات الرسم
if "--" in sys.argv:
    argv = sys.argv[sys.argv.index("--") + 1:]
elif sys.argv and sys.argv[0].endswith(".py"):  # تشغيل كوحدة bpy من pip
    argv = sys.argv[1:]
else:
    argv = []
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="build/ep06/frames")
ap.add_argument("--res", default="720x1280")
ap.add_argument("--samples", type=int, default=32)
ap.add_argument("--frames", nargs=2, type=int)
ap.add_argument("--still")
ap.add_argument("--save")
args = ap.parse_args(argv)

w, h = (int(v) for v in args.res.lower().split("x"))
r = scene.render
r.engine = "CYCLES"
r.resolution_x, r.resolution_y = w, h
r.resolution_percentage = 100
r.use_persistent_data = True
r.film_transparent = False
cy = scene.cycles
cy.device = "CPU"
cy.samples = args.samples
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.03
cy.use_denoising = True
try:
    cy.denoiser = "OPENIMAGEDENOISE"
except TypeError:
    pass
cy.max_bounces = 4
cy.diffuse_bounces = 2
cy.glossy_bounces = 1
cy.transmission_bounces = 1
cy.transparent_max_bounces = 2
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.blur_glossy = 1.0
for vt, look_name in (("AgX", "AgX - Punchy"), ("Filmic", "Medium High Contrast")):
    try:
        scene.view_settings.view_transform = vt
        scene.view_settings.look = look_name
        break
    except TypeError:
        continue
scene.view_settings.exposure = 0.2
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGB"

if args.save:
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.save).resolve()))

out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
if args.still:
    for t in [float(x) for x in args.still.split(",")]:
        scene.frame_set(F(t))
        r.filepath = str(out / f"still_{t:05.1f}.png")
        bpy.ops.render.render(write_still=True)
else:
    if args.frames:
        scene.frame_start, scene.frame_end = args.frames
    r.filepath = str(out / "f_")
    r.use_file_extension = True
    bpy.ops.render.render(animation=True)
