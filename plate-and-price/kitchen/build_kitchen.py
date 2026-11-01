"""Plate & Price virtual kitchen: a clean, modern, photoreal work area built procedurally in Blender.

Run headless from plate-and-price/:
    blender -b -P kitchen/build_kitchen.py -- build                # kitchen.blend only
    blender -b -P kitchen/build_kitchen.py -- stills               # + one PNG per camera preset
    blender -b -P kitchen/build_kitchen.py -- stills only=hob      # just some presets
    blender -b -P kitchen/build_kitchen.py -- sweep                # + PNG sequence of the 7 s pass
    add `draft` for a fast low-sample render, `samples=N` to choose.

Layout (metres, X right, Y away from the cook, Z up; back wall at y=0, the camera looks toward +Y):
    cutting zone  x -2.0..-0.8   oak butcher-block worktop, drawer + doors, utensil rail and knife strip on the wall
    hob zone      x -0.8..+0.4   flush black induction hob, three drawers, slim hood
    sink zone     x +0.4..+2.0   brushed-steel undermount sink, gooseneck tap, ribbed drainer
    opposite wall y=-2.6         floating shelf with spices, salt and pepper, oil; low sideboard
Only the camera moves. The cook's hands, food and tools are composited over this background.

Realism checklist implemented here: real-world scale, bevels on every edge, procedural wood grain, quartz speckle, glazed
tile with grout, brushed steel, roughness variation and faint smudges on every surface, warm key light with a cool fill,
soft area lights, light depth of field. Lens barrel, vignette and grain are added at encode time (see README).
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(HERE, "renders")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["build"]
DRAFT = "draft" in ARGS


# =========================================================================== node helpers
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m


def bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def N(nt, kind, **props):
    n = nt.nodes.new(kind)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def link(nt, a, b):
    nt.links.new(a, b)


def ramp(nt, fac, stops):
    """Colour ramp with [(position, (r,g,b)), ...]."""
    r = N(nt, "ShaderNodeValToRGB")
    cr = r.color_ramp
    while len(cr.elements) > len(stops):
        cr.elements.remove(cr.elements[-1])
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, stops):
        el.position = p
        el.color = (*c, 1)
    link(nt, fac, r.inputs["Fac"])
    return r


def mix_rgb(nt, a, b, fac, blend="MULTIPLY"):
    m = N(nt, "ShaderNodeMix", data_type="RGBA", blend_type=blend)
    m.inputs[0].default_value = fac if not hasattr(fac, "node") else 1.0
    if hasattr(fac, "node"):
        link(nt, fac, m.inputs[0])
    for idx, v in ((6, a), (7, b)):
        if hasattr(v, "node"):
            link(nt, v, m.inputs[idx])
        else:
            m.inputs[idx].default_value = (*v, 1)
    return m.outputs[2]


def noise(nt, vec, scale, detail=4.0, rough=0.5, distortion=0.0):
    n = N(nt, "ShaderNodeTexNoise", noise_dimensions="3D")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    n.inputs["Distortion"].default_value = distortion
    link(nt, vec, n.inputs["Vector"])
    return n


def mapped(nt, scale=(1, 1, 1), rot=(0, 0, 0)):
    tc = N(nt, "ShaderNodeTexCoord")
    mp = N(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    mp.inputs["Rotation"].default_value = rot
    link(nt, tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def bump(nt, height, strength, distance=0.002):
    b = N(nt, "ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    link(nt, height, b.inputs["Height"])
    return b.outputs["Normal"]


def math_node(nt, op, a, b=None):
    m = N(nt, "ShaderNodeMath", operation=op)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if hasattr(v, "node"):
            link(nt, v, m.inputs[i])
        else:
            m.inputs[i].default_value = v
    return m.outputs[0]


def rough_var(nt, b, base, spread, scale=3.0):
    """Roughness that wanders around `base` (never perfectly uniform) via low-frequency noise."""
    n = noise(nt, mapped(nt), scale, 3.0, 0.6)
    r = math_node(nt, "MULTIPLY", n.outputs["Fac"], spread)
    r = math_node(nt, "ADD", r, base - spread / 2)
    link(nt, r, b.inputs["Roughness"])


# =========================================================================== materials
_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def simple(name, color, rough, metal=0.0, **extra):
    def make():
        m = new_mat(name)
        b = bsdf(m)
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        for k, v in extra.items():
            k = "IOR" if k == "ior" else k.replace("_", " ").title()
            if k in b.inputs:
                b.inputs[k].default_value = (*v, 1) if isinstance(v, tuple) and len(v) == 3 else v
        return m
    return cached(name, make)


def wood(name, light, dark, grain=(0.35, 3.0, 3.0), rough=0.42, ring=10.0, scale_noise=40.0, coat=0.0, strips=0.0):
    """Oak-like wood: wavy growth rings stretched along X plus fine pores, colour + roughness + bump driven by the grain."""
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        vec = mapped(nt, grain)
        w = N(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", wave_profile="SAW")
        w.inputs["Scale"].default_value = ring
        w.inputs["Distortion"].default_value = 5.0
        w.inputs["Detail"].default_value = 3.0
        w.inputs["Detail Scale"].default_value = 2.0
        w.inputs["Detail Roughness"].default_value = 0.6
        link(nt, vec, w.inputs["Vector"])
        pores = noise(nt, mapped(nt, (1, 40, 40)), scale_noise, 2.0, 0.5)
        tone = mix_rgb(nt, w.outputs["Fac"], pores.outputs["Fac"], 0.18, "MIX")
        col = ramp(nt, tone, [(0.05, dark), (0.85, light)])
        patch = noise(nt, mapped(nt, (0.6, 1.5, 1.5)), 2.0, 2.0, 0.5)  # slow colour drift between boards
        tint = ramp(nt, patch.outputs["Fac"], [(0.2, (0.9, 0.9, 0.9)), (0.8, (1.05, 1.0, 0.97))])
        colour = mix_rgb(nt, col.outputs["Color"], tint.outputs["Color"], 1.0, "MULTIPLY")
        height = tone
        if strips:  # butcher block: glued strips along X, each with its own tone, hairline joints
            br = N(nt, "ShaderNodeTexBrick", offset=0.37, offset_frequency=2, squash=1.0)
            br.inputs["Color1"].default_value = (1.10, 1.04, 0.96, 1)
            br.inputs["Color2"].default_value = (0.70, 0.64, 0.56, 1)
            br.inputs["Mortar"].default_value = (0.35, 0.30, 0.25, 1)
            br.inputs["Scale"].default_value = 1.0
            br.inputs["Mortar Size"].default_value = 0.0012
            br.inputs["Mortar Smooth"].default_value = 0.2
            br.inputs["Brick Width"].default_value = 1.6
            br.inputs["Row Height"].default_value = strips
            link(nt, mapped(nt), br.inputs["Vector"])
            colour = mix_rgb(nt, colour, br.outputs["Color"], 1.0, "MULTIPLY")
            height = math_node(nt, "ADD", tone, math_node(nt, "MULTIPLY", br.outputs["Fac"], 1.5))
        link(nt, colour, b.inputs["Base Color"])
        link(nt, bump(nt, height, 0.6, 0.0015), b.inputs["Normal"])
        rough_var(nt, b, rough, 0.18, 6.0)
        if "Coat Weight" in b.inputs and coat:
            b.inputs["Coat Weight"].default_value = coat
            b.inputs["Coat Roughness"].default_value = 0.25
        return m
    return cached(name, make)


def quartz(name="quartz_white"):
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        speck = noise(nt, mapped(nt), 900.0, 0.0, 0.5)
        sp = ramp(nt, speck.outputs["Fac"], [(0.55, (0.80, 0.79, 0.76)), (0.75, (0.52, 0.50, 0.47))])
        vein = N(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
        vein.inputs["Scale"].default_value = 1.5
        vein.inputs["Distortion"].default_value = 14.0
        vein.inputs["Detail"].default_value = 4.0
        link(nt, mapped(nt), vein.inputs["Vector"])
        vr = ramp(nt, vein.outputs["Fac"], [(0.45, (1.0, 1.0, 1.0)), (0.55, (0.93, 0.93, 0.92))])
        link(nt, mix_rgb(nt, sp.outputs["Color"], vr.outputs["Color"], 1.0, "MULTIPLY"), b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.2
        rough_var(nt, b, 0.2, 0.14, 8.0)
        b.inputs["Specular IOR Level"].default_value = 0.6
        return m
    return cached(name, make)


def lacquer(name="front_charcoal", color=(0.022, 0.025, 0.031)):
    """Matte lacquered fronts: roughness wanders and faint finger smudges lift the specular here and there."""
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        b.inputs["Base Color"].default_value = (*color, 1)
        smudge = noise(nt, mapped(nt, (1, 1, 1)), 6.0, 4.0, 0.6, 0.4)
        r = ramp(nt, smudge.outputs["Fac"], [(0.35, (0.80, 0.80, 0.80)), (0.65, (0.62, 0.62, 0.62))])
        link(nt, r.outputs["Color"], b.inputs["Roughness"])
        link(nt, bump(nt, smudge.outputs["Fac"], 0.02, 0.0005), b.inputs["Normal"])
        b.inputs["Specular IOR Level"].default_value = 0.3
        return m
    return cached(name, make)


def steel(name="steel", base=0.7, rough=0.3):
    """Brushed stainless: streaks along X drive roughness and bump."""
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        b.inputs["Base Color"].default_value = (base, base, base * 1.02, 1)
        b.inputs["Metallic"].default_value = 1.0
        streak = noise(nt, mapped(nt, (1, 90, 90)), 120.0, 6.0, 0.6)
        link(nt, math_node(nt, "ADD", math_node(nt, "MULTIPLY", streak.outputs["Fac"], 0.22), rough - 0.1),
             b.inputs["Roughness"])
        link(nt, bump(nt, streak.outputs["Fac"], 0.08, 0.0006), b.inputs["Normal"])
        return m
    return cached(name, make)


def black_glass(name="hob_glass"):
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        b.inputs["Base Color"].default_value = (0.004, 0.004, 0.006, 1)
        smudge = noise(nt, mapped(nt), 20.0, 4.0, 0.6, 1.0)
        r = ramp(nt, smudge.outputs["Fac"], [(0.4, (0.04, 0.04, 0.04)), (0.7, (0.10, 0.10, 0.10))])
        link(nt, r.outputs["Color"], b.inputs["Roughness"])
        b.inputs["Specular IOR Level"].default_value = 0.8
        return m
    return cached(name, make)


def glaze_tile(name="tile_white", scale_w=0.30, scale_h=0.10, offset=0.0):
    """Glazed ceramic wall tile with recessed grout, per-tile tint, slight unevenness. Wall lies in the XZ plane."""
    def make():
        m = new_mat(name)
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        b = bsdf(m)
        tc = N(nt, "ShaderNodeTexCoord")
        sep = N(nt, "ShaderNodeSeparateXYZ")
        com = N(nt, "ShaderNodeCombineXYZ")
        link(nt, tc.outputs["Object"], sep.inputs["Vector"])
        link(nt, sep.outputs["X"], com.inputs["X"])
        link(nt, sep.outputs["Z"], com.inputs["Y"])
        br = N(nt, "ShaderNodeTexBrick", offset=offset, offset_frequency=2, squash=1.0)
        br.inputs["Color1"].default_value = (0.92, 0.91, 0.88, 1)
        br.inputs["Color2"].default_value = (0.86, 0.86, 0.84, 1)
        br.inputs["Mortar"].default_value = (0.55, 0.54, 0.52, 1)
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.0035
        br.inputs["Mortar Smooth"].default_value = 0.15
        br.inputs["Bias"].default_value = 0.0
        br.inputs["Brick Width"].default_value = scale_w
        br.inputs["Row Height"].default_value = scale_h
        link(nt, com.outputs["Vector"], br.inputs["Vector"])
        wavy = noise(nt, tc.outputs["Object"], 25.0, 3.0, 0.5)
        h = math_node(nt, "ADD", math_node(nt, "MULTIPLY", wavy.outputs["Fac"], 0.35), br.outputs["Fac"])
        link(nt, br.outputs["Color"], b.inputs["Base Color"])
        link(nt, bump(nt, h, 0.55, 0.0025), b.inputs["Normal"])
        b.inputs["Roughness"].default_value = 0.12
        # grout is matte, tile glossy: second shader mixed by the brick mask (Fac = 1 on tile, 0 in mortar)
        grout = N(nt, "ShaderNodeBsdfDiffuse")
        grout.inputs["Color"].default_value = (0.50, 0.49, 0.47, 1)
        grout.inputs["Roughness"].default_value = 0.95
        mixs = N(nt, "ShaderNodeMixShader")
        mask = ramp(nt, br.outputs["Fac"], [(0.4, (0, 0, 0)), (0.6, (1, 1, 1))])
        link(nt, mask.outputs["Color"], mixs.inputs[0])
        link(nt, grout.outputs["BSDF"], mixs.inputs[1])
        link(nt, b.outputs["BSDF"], mixs.inputs[2])
        link(nt, mixs.outputs["Shader"], out.inputs["Surface"])
        return m
    return cached(name, make)


def plank_floor(name="floor_oak"):
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        tc = N(nt, "ShaderNodeTexCoord")
        br = N(nt, "ShaderNodeTexBrick", offset=0.5, offset_frequency=2, squash=1.0)
        br.inputs["Color1"].default_value = (0.36, 0.22, 0.11, 1)
        br.inputs["Color2"].default_value = (0.27, 0.16, 0.08, 1)
        br.inputs["Mortar"].default_value = (0.05, 0.035, 0.02, 1)
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.0025
        br.inputs["Mortar Smooth"].default_value = 0.1
        br.inputs["Brick Width"].default_value = 1.2
        br.inputs["Row Height"].default_value = 0.18
        link(nt, tc.outputs["Object"], br.inputs["Vector"])
        w = N(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", wave_profile="SAW")
        w.inputs["Scale"].default_value = 14.0
        w.inputs["Distortion"].default_value = 6.0
        w.inputs["Detail"].default_value = 3.0
        link(nt, mapped(nt, (0.25, 6, 6)), w.inputs["Vector"])
        g = ramp(nt, w.outputs["Fac"], [(0.0, (0.82, 0.82, 0.82)), (1.0, (1.08, 1.04, 1.0))])
        link(nt, mix_rgb(nt, br.outputs["Color"], g.outputs["Color"], 1.0, "MULTIPLY"), b.inputs["Base Color"])
        link(nt, bump(nt, math_node(nt, "ADD", w.outputs["Fac"], br.outputs["Fac"]), 0.5, 0.002), b.inputs["Normal"])
        rough_var(nt, b, 0.38, 0.2, 4.0)
        b.inputs["Coat Weight"].default_value = 0.35  # satin lacquer
        b.inputs["Coat Roughness"].default_value = 0.2
        return m
    return cached(name, make)


def wall_paint(name="wall_paint", color=(0.80, 0.79, 0.75)):
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = 0.95
        b.inputs["Specular IOR Level"].default_value = 0.05  # flat matt paint: no grazing-angle sheen
        n = noise(nt, mapped(nt), 220.0, 2.0, 0.5)
        link(nt, bump(nt, n.outputs["Fac"], 0.08, 0.0008), b.inputs["Normal"])
        return m
    return cached(name, make)


def glass_mat(name, tint=(0.92, 0.96, 0.95), rough=0.02):
    def make():
        m = new_mat(name)
        b = bsdf(m)
        b.inputs["Base Color"].default_value = (*tint, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["IOR"].default_value = 1.45
        return m
    return cached(name, make)


def powder(name, color):
    def make():
        m = new_mat(name)
        nt = m.node_tree
        b = bsdf(m)
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = 0.95
        n = noise(nt, mapped(nt), 300.0, 2.0, 0.5)
        link(nt, bump(nt, n.outputs["Fac"], 0.6, 0.002), b.inputs["Normal"])
        return m
    return cached(name, make)


# =========================================================================== geometry helpers
def _finish(o, name, m, bevel, segments=3):
    o.name = name
    if m:
        o.data.materials.append(m)
    if bevel:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = segments
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(35)
    return o


def box(name, x0, x1, y0, y1, z0, z1, m, bevel=0.0025, segments=3):
    bpy.ops.mesh.primitive_cube_add()
    o = bpy.context.object
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    o.scale = (abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, m, min(bevel, abs(x1 - x0) / 2.2, abs(y1 - y0) / 2.2, abs(z1 - z0) / 2.2), segments)


def cyl(name, x, y, z0, z1, r, m, verts=48, bevel=0.0015, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=abs(z1 - z0))
    o = bpy.context.object
    o.location = (x, y, (z0 + z1) / 2)
    if smooth:
        bpy.ops.object.shade_smooth()
    return _finish(o, name, m, min(bevel, r * 0.5), 2)


def cyl_x(name, x0, x1, y, z, r, m, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=abs(x1 - x0))
    o = bpy.context.object
    o.rotation_euler = (0, math.radians(90), 0)
    o.location = ((x0 + x1) / 2, y, z)
    bpy.ops.object.transform_apply(rotation=True)
    bpy.ops.object.shade_smooth()
    return _finish(o, name, m, 0, 1)


def sphere(name, x, y, z, r, m, sx=1.0, sy=1.0, sz=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=r)
    o = bpy.context.object
    o.location = (x, y, z)
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    return _finish(o, name, m, 0)


def shell_bowl(name, x, y, z, r, depth, m, facing=-1):
    """Open hemispherical bowl (ladle, spoon) with a thin wall; opening faces the room (-Y)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=18, radius=1.0)
    for v in [v for v in bm.verts if v.co.y * facing < -0.02]:
        v.co.y = v.co.y  # keep; deletion below
    geom = [v for v in bm.verts if v.co.y * facing > 0.0]
    bmesh.ops.delete(bm, geom=geom, context="VERTS")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.scale = (r, depth, r * 1.15)
    o.location = (x, y, z)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(scale=True)
    sm = o.modifiers.new("solid", "SOLIDIFY")
    sm.thickness = 0.0015
    for p in me.polygons:
        p.use_smooth = True
    o.data.materials.append(m)
    return o


def blade(name, x, y, z_bottom, length, width, thick, m):
    """Chef-knife blade lying flat on the wall (x,z plane): straight spine, curved belly, pointed tip."""
    bm = bmesh.new()
    pts = [(-width / 2, 0), (width / 2, 0), (width / 2, length * 0.35), (width * 0.30, length * 0.80),
           (-width / 2 + 0.002, length), (-width / 2, length * 0.97)]
    vs = [bm.verts.new((px, 0, pz)) for px, pz in pts]
    bm.faces.new(vs)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = (x, y, z_bottom)
    sm = o.modifiers.new("solid", "SOLIDIFY")
    sm.thickness = thick
    bv = o.modifiers.new("bevel", "BEVEL")
    bv.width = thick * 0.35
    bv.segments = 1
    o.data.materials.append(m)
    return o


def tube(name, pts, radius, m, resolution=10):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    cu.resolution_u = resolution
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for p, c in zip(sp.bezier_points, pts):
        p.co = c
        p.handle_left_type = p.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    cu.materials.append(m)
    return o


# =========================================================================== scene
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build_room():
    # floor
    bpy.ops.mesh.primitive_plane_add(size=1)
    f = bpy.context.object
    f.name = "floor"
    f.scale = (4.6, 2.62, 1)
    f.location = (0, -1.31, 0)
    bpy.ops.object.transform_apply(scale=True)
    f.data.materials.append(plank_floor())
    # tiled back wall (faces -Y)
    bpy.ops.mesh.primitive_plane_add(size=1)
    w = bpy.context.object
    w.name = "wall_back"
    w.rotation_euler = (math.radians(90), 0, 0)
    w.scale = (4.6, 2.4, 1)
    w.location = (0, 0, 1.2)
    bpy.ops.object.transform_apply(rotation=True, scale=True)
    w.data.materials.append(glaze_tile())
    paint = wall_paint()
    box("wall_front", -2.3, 2.3, -2.64, -2.60, 0, 2.4, paint, 0)
    box("wall_left", -2.32, -2.28, -2.64, 0, 0, 2.4, paint, 0)
    box("wall_right", 2.28, 2.32, -2.64, 0, 0, 2.4, paint, 0)
    box("ceiling", -2.3, 2.3, -2.64, 0, 2.4, 2.44, wall_paint("ceiling_paint", (0.86, 0.85, 0.82)), 0)
    # skirting boards on the three painted walls
    sk = simple("skirting", (0.80, 0.79, 0.76), 0.5)
    box("skirt_front", -2.28, 2.28, -2.60, -2.585, 0, 0.09, sk, 0.002)
    box("skirt_left", -2.28, -2.265, -2.60, -0.62, 0, 0.09, sk, 0.002)
    box("skirt_right", 2.265, 2.28, -2.60, -0.62, 0, 0.09, sk, 0.002)


def front(name, x0, x1, z0, z1, drawer, cy=-0.60):
    ch = lacquer()
    box(name, x0 + 0.002, x1 - 0.002, cy - 0.019, cy + 0.001, z0 + 0.002, z1 - 0.002, ch, 0.003)
    if drawer:
        # brushed-steel J-pull on the top edge of the front
        box(name + "_pull", x0 + 0.015, x1 - 0.015, cy - 0.040, cy - 0.008, z1 - 0.030, z1 - 0.006, steel("steel_pull", 0.55, 0.38), 0.0025)
        box(name + "_pull_shadow", x0 + 0.015, x1 - 0.015, cy - 0.020, cy - 0.019, z1 - 0.036, z1 - 0.030, simple("gap_dark", (0.004, 0.004, 0.004), 0.9), 0)


def build_counter_run():
    carcass = simple("carcass_dark", (0.02, 0.02, 0.022), 0.8)
    dark = simple("gap_dark", (0.004, 0.004, 0.004), 0.9)
    q = quartz()
    oak = wood("oak_block", (0.58, 0.34, 0.14), (0.30, 0.15, 0.05), rough=0.38, coat=0.25, strips=0.032)
    st = steel()
    D, T0, T1 = 0.60, 0.86, 0.90
    box("plinth", -2.0, 2.0, -D + 0.07, 0, 0, 0.10, dark, 0)
    box("carcass", -2.0, 2.0, -D + 0.01, 0, 0.10, T0, carcass, 0)

    # worktops: 40 mm, 25 mm overhang; oak block and quartz; sink hole cut with a boolean
    box("top_oak", -2.0, -0.8, -D - 0.025, 0, T0, T1, oak, 0.004)
    box("top_hob", -0.8, 0.4, -D - 0.025, 0, T0, T1, q, 0.004)
    sink_top = box("top_sink", 0.4, 2.0, -D - 0.025, 0, T0, T1, q, 0.004)
    cutter = box("cutter", 0.58, 1.14, -0.52, -0.08, 0.5, 1.0, dark, 0)
    for md in list(cutter.modifiers):
        cutter.modifiers.remove(md)
    for md in list(sink_top.modifiers):
        bpy.context.view_layer.objects.active = sink_top
        bpy.ops.object.modifier_apply(modifier=md.name)
    bm = sink_top.modifiers.new("hole", "BOOLEAN")
    bm.operation = "DIFFERENCE"
    bm.object = cutter
    bm.solver = "EXACT"
    bpy.context.view_layer.objects.active = sink_top
    bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(cutter, do_unlink=True)
    bv = sink_top.modifiers.new("bevel", "BEVEL")
    bv.width = 0.003
    bv.segments = 3
    bv.limit_method = "ANGLE"

    # fronts: cutting zone drawer + two doors, hob zone three drawers, sink zone two doors
    front("cut_drawer", -2.0, -0.8, 0.66, 0.86, True)
    front("cut_door_l", -2.0, -1.4, 0.10, 0.66, False)
    front("cut_door_r", -1.4, -0.8, 0.10, 0.66, False)
    front("hob_drawer_1", -0.8, 0.4, 0.62, 0.86, True)
    front("hob_drawer_2", -0.8, 0.4, 0.36, 0.62, True)
    front("hob_drawer_3", -0.8, 0.4, 0.10, 0.36, True)
    front("sink_door_l", 0.4, 1.2, 0.10, 0.86, False)
    front("sink_door_r", 1.2, 2.0, 0.10, 0.86, False)
    # short vertical pulls on the sink doors (inner edges)
    for nm, x in (("sink_pull_l", 1.185), ("sink_pull_r", 1.215)):
        box(nm, x - 0.006, x + 0.006, -D - 0.034, -D - 0.012, 0.62, 0.84, steel("steel_pull", 0.55, 0.38), 0.002)

    # ---- induction hob
    glass = black_glass()
    ring = simple("hob_ring", (0.30, 0.30, 0.32), 0.35)
    led = simple("hob_led", (1, 1, 1), 0.3, emission_color=(1.0, 0.96, 0.9), emission_strength=3.0)
    hx, hy = -0.2, -0.30
    box("hob_trim", hx - 0.296, hx + 0.296, hy - 0.266, hy + 0.266, T1, T1 + 0.0012, steel("steel_trim", 0.45, 0.4), 0.0006, 1)
    box("hob_glass", hx - 0.292, hx + 0.292, hy - 0.262, hy + 0.262, T1 + 0.0012, T1 + 0.0062, glass, 0.0015, 2)
    for i, (dx, dy, r) in enumerate([(-0.14, 0.09, 0.105), (0.14, 0.09, 0.085), (-0.14, -0.12, 0.085), (0.14, -0.12, 0.105)]):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.0010, major_segments=96, minor_segments=6)
        t = bpy.context.object
        t.name = f"hob_ring_{i}"
        t.location = (hx + dx, hy + dy, T1 + 0.0066)
        t.scale = (1, 1, 0.4)
        t.data.materials.append(ring)
    box("hob_slider", hx - 0.13, hx + 0.13, hy - 0.236, hy - 0.232, T1 + 0.0064, T1 + 0.0068, ring, 0)
    for i in range(5):
        cyl(f"hob_dot_{i}", hx - 0.20 + 0.10 * i, hy - 0.216, T1 + 0.0064, T1 + 0.0069, 0.0035, led, 16, 0, False)

    # ---- hood: black telescopic chimney with a steel grease filter and warm LEDs
    hood_m = simple("hood_black", (0.02, 0.02, 0.023), 0.4, 0.5)
    box("hood_body", hx - 0.30, hx + 0.30, -0.50, 0.0, 1.62, 1.70, hood_m, 0.004)
    box("hood_chimney", hx - 0.15, hx + 0.15, -0.22, 0.0, 1.70, 2.44, hood_m, 0.004)
    box("hood_filter", hx - 0.26, hx + 0.26, -0.46, -0.04, 1.617, 1.622, steel("steel_filter", 0.5, 0.45), 0.001, 1)
    for i in range(13):
        box(f"hood_slot_{i}", hx - 0.255 + i * 0.0425, hx - 0.249 + i * 0.0425, -0.45, -0.05, 1.6165, 1.6172, dark, 0, 1)
    box("hood_led", hx - 0.22, hx + 0.22, -0.495, -0.475, 1.618, 1.621,
        simple("hood_led_m", (1, 1, 1), 0.3, emission_color=(1.0, 0.82, 0.60), emission_strength=18), 0, 1)

    # ---- sink: undermount steel basin with rounded corners, strainer, gooseneck tap, ribbed drainer
    bx0, bx1, by0, by1 = 0.60, 1.12, -0.50, -0.10
    bpy.ops.mesh.primitive_cube_add()
    bs = bpy.context.object
    bs.name = "basin"
    bs.location = ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.77)
    bs.scale = ((bx1 - bx0) / 2, (by1 - by0) / 2, 0.19 / 2)
    bpy.ops.object.transform_apply(scale=True)
    me = bs.data
    bmx = bmesh.new()
    bmx.from_mesh(me)
    top = [f for f in bmx.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bmx, geom=top, context="FACES")
    bmx.to_mesh(me)
    bmx.free()
    bv = bs.modifiers.new("bevel", "BEVEL")
    bv.width = 0.03
    bv.segments = 6
    bv.limit_method = "ANGLE"
    so = bs.modifiers.new("solid", "SOLIDIFY")
    so.thickness = 0.004
    so.offset = -1
    bs.data.materials.append(st)
    bpy.ops.object.shade_smooth()
    cx, cy_ = (bx0 + bx1) / 2, (by0 + by1) / 2
    cyl("strainer", cx, cy_, 0.676, 0.680, 0.045, st, 40, 0.001)
    for i in range(10):
        a = i * math.tau / 10
        cyl(f"strainer_hole_{i}", cx + 0.028 * math.cos(a), cy_ + 0.028 * math.sin(a), 0.6795, 0.6805, 0.0045, dark, 12, 0, False)
    cyl("strainer_hole_c", cx, cy_, 0.6795, 0.6805, 0.007, dark, 12, 0, False)
    # drainer: raised ribs sloping toward the basin
    box("drainer_plate", 1.22, 1.92, -0.54, -0.06, T1, T1 + 0.002, st, 0.001, 1)
    for i in range(16):
        box(f"rib_{i}", 1.245 + i * 0.0415, 1.259 + i * 0.0415, -0.51, -0.09, T1 + 0.002, T1 + 0.0042, st, 0.0008, 2)
    # tap
    tx, ty = 0.86, -0.06
    cyl("tap_base", tx, ty, T1, T1 + 0.012, 0.030, st, 48, 0.003)
    cyl("tap_body", tx, ty, T1 + 0.012, T1 + 0.22, 0.0155, st, 48, 0.002)
    tube("tap_neck", [(tx, ty, T1 + 0.22), (tx, ty, T1 + 0.30), (tx, ty - 0.05, T1 + 0.375), (tx, ty - 0.14, T1 + 0.385),
                      (tx, ty - 0.215, T1 + 0.33), (tx, ty - 0.225, T1 + 0.27)], 0.0135, st, 16)
    cyl("tap_tip", tx, ty - 0.225, T1 + 0.245, T1 + 0.275, 0.0165, st, 40, 0.002)
    cyl("tap_aerator", tx, ty - 0.225, T1 + 0.2435, T1 + 0.2455, 0.012, simple("aerator", (0.05, 0.05, 0.05), 0.5, 0.2), 24, 0, False)
    box("tap_lever", tx + 0.016, tx + 0.095, ty - 0.010, ty + 0.010, T1 + 0.085, T1 + 0.104, st, 0.004)
    # soap pump
    blk = simple("soap_black", (0.015, 0.015, 0.016), 0.28)
    cyl("soap", 1.05, -0.05, T1, T1 + 0.145, 0.032, blk, 48, 0.004)
    cyl("soap_neck", 1.05, -0.05, T1 + 0.145, T1 + 0.17, 0.0075, st, 24, 0.001)
    box("soap_nozzle", 1.045, 1.092, -0.057, -0.043, T1 + 0.17, T1 + 0.18, st, 0.003)


def build_wall_items():
    st = steel()
    black = simple("handle_black", (0.015, 0.015, 0.016), 0.4)
    wood_h = wood("handle_wood", (0.55, 0.38, 0.20), (0.36, 0.22, 0.11), rough=0.45)
    oak = wood("oak_block", (0.58, 0.34, 0.14), (0.30, 0.15, 0.05), rough=0.38, coat=0.25, strips=0.032)
    ry, rz = -0.05, 1.78
    # rail with end brackets
    cyl_x("rail", -1.95, -1.2, ry, rz, 0.008, st)
    for x in (-1.945, -1.205):
        box(f"rail_bracket_{x}", x - 0.008, x + 0.008, ry - 0.008, 0.0, rz - 0.012, rz + 0.012, st, 0.003)
    for i, x in enumerate([-1.88, -1.74, -1.60, -1.46, -1.32]):
        tube(f"hook_{i}", [(x, ry, rz + 0.0), (x, ry - 0.016, rz - 0.012), (x, ry - 0.016, rz - 0.04), (x, ry - 0.016, rz - 0.052)], 0.0022, st, 8)
    # ladle
    cyl("ladle_h", -1.88, ry - 0.016, rz - 0.40, rz - 0.052, 0.0045, st, 16, 0)
    shell_bowl("ladle_bowl", -1.88, ry - 0.016, rz - 0.405, 0.044, 0.04, st)
    # spatula: wooden handle + black silicone head
    cyl("spat_h", -1.74, ry - 0.016, rz - 0.30, rz - 0.052, 0.0075, wood_h, 20, 0.002)
    box("spat_neck", -1.7445, -1.7355, ry - 0.021, ry - 0.011, rz - 0.36, rz - 0.30, black, 0.002)
    box("spat_head", -1.778, -1.702, ry - 0.0215, ry - 0.0105, rz - 0.49, rz - 0.355, black, 0.004)
    # whisk: handle + wire loops
    cyl("whisk_h", -1.60, ry - 0.016, rz - 0.18, rz - 0.052, 0.008, st, 20, 0.001)
    for i in range(7):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.034, minor_radius=0.0009, major_segments=36, minor_segments=5)
        t = bpy.context.object
        t.name = f"whisk_wire_{i}"
        t.scale = (1, 1, 2.2)
        t.rotation_euler = (math.radians(90), math.radians(i * 180 / 7), 0)
        t.location = (-1.60, ry - 0.016, rz - 0.265)
        t.data.materials.append(st)
        bpy.context.view_layer.objects.active = t
        bpy.ops.object.shade_smooth()
    # tongs: two arms joined at the top
    box("tongs_a", -1.4725, -1.4635, ry - 0.026, ry - 0.011, rz - 0.38, rz - 0.052, st, 0.001, 2)
    box("tongs_b", -1.4515, -1.4425, ry - 0.026, ry - 0.011, rz - 0.38, rz - 0.052, st, 0.001, 2)
    box("tongs_tip_a", -1.4725, -1.4635, ry - 0.026, ry - 0.011, rz - 0.41, rz - 0.38, black, 0.001, 1)
    box("tongs_tip_b", -1.4515, -1.4425, ry - 0.026, ry - 0.011, rz - 0.41, rz - 0.38, black, 0.001, 1)
    # slotted spoon
    cyl("spoon_h", -1.32, ry - 0.016, rz - 0.34, rz - 0.052, 0.0055, black, 16, 0.001)
    shell_bowl("spoon_bowl", -1.32, ry - 0.016, rz - 0.345, 0.036, 0.016, st)

    # magnetic knife strip with four knives
    box("knife_strip", -1.12, -0.58, -0.033, -0.002, 1.60, 1.665, oak, 0.003)
    for i, (x, bl, bw, grip) in enumerate([(-1.06, 0.21, 0.046, 0.125), (-0.94, 0.18, 0.040, 0.115),
                                           (-0.82, 0.15, 0.034, 0.105), (-0.70, 0.12, 0.030, 0.10)]):
        top = 1.655
        blade(f"knife_blade_{i}", x, -0.036, top - bl, bl, bw, 0.0022, st)
        box(f"knife_handle_{i}", x - 0.0115, x + 0.0115, -0.053, -0.033, top - bl - grip, top - bl + 0.004, black, 0.004)
        for k in range(2):
            cyl(f"rivet_{i}_{k}", x, -0.0535, top - bl - grip * (0.3 + 0.4 * k), top - bl - grip * (0.3 + 0.4 * k) + 0.0015, 0.0025, st, 12, 0, False)

    # wall sockets (white double sockets) — everyday detail that sells scale
    plate = simple("socket_plate", (0.86, 0.86, 0.84), 0.35)
    hole = simple("socket_hole", (0.01, 0.01, 0.01), 0.6)
    for sx in (-0.98, 1.72):
        box(f"socket_{sx}", sx - 0.040, sx + 0.040, -0.011, -0.001, 1.04, 1.12, plate, 0.004)
        for sxx in (-0.020, 0.020):
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.0185, depth=0.004)
            c = bpy.context.object
            c.rotation_euler = (math.radians(90), 0, 0)
            c.location = (sx + sxx, -0.012, 1.08)
            c.name = f"socket_cup_{sx}_{sxx}"
            c.data.materials.append(plate)
            for hx_ in (-0.0115, 0.0115):
                bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.0028, depth=0.002)
                h = bpy.context.object
                h.rotation_euler = (math.radians(90), 0, 0)
                h.location = (sx + sxx + hx_, -0.0135, 1.08)
                h.name = f"socket_hole_{sx}_{sxx}_{hx_}"
                h.data.materials.append(hole)


def build_opposite_wall():
    oak = wood("oak_block", (0.58, 0.34, 0.14), (0.30, 0.15, 0.05), rough=0.38, coat=0.25, strips=0.032)
    ch = lacquer()
    dark = simple("gap_dark", (0.004, 0.004, 0.004), 0.9)
    st = steel()
    wy = -2.60
    box("side_body", -1.2, 1.2, wy, wy + 0.45, 0.06, 0.86, ch, 0.003)
    box("side_plinth", -1.2, 1.2, wy, wy + 0.40, 0, 0.06, dark, 0)
    box("side_top", -1.2, 1.2, wy, wy + 0.47, 0.86, 0.90, oak, 0.004)
    for i in range(3):
        x0 = -1.2 + i * 0.8
        box(f"side_door_{i}", x0 + 0.003, x0 + 0.797, wy + 0.45, wy + 0.468, 0.07, 0.855, ch, 0.003)
        box(f"side_pull_{i}", x0 + 0.37, x0 + 0.43, wy + 0.468, wy + 0.49, 0.80, 0.82, st, 0.002)
    box("shelf", -1.0, 1.0, wy, wy + 0.24, 1.30, 1.335, oak, 0.003)
    sz = 1.335
    glass = glass_mat("jar_glass")
    lid = steel("jar_lid", 0.15, 0.4)
    kraft = simple("label_kraft", (0.62, 0.50, 0.34), 0.85)
    spices = [("paprika", (0.62, 0.10, 0.03)), ("cumin", (0.42, 0.26, 0.10)), ("oregano", (0.17, 0.27, 0.08)),
              ("chilli", (0.48, 0.04, 0.02)), ("turmeric", (0.78, 0.48, 0.04)), ("pepper_corn", (0.05, 0.05, 0.05))]
    for i, (n, col) in enumerate(spices):
        x = -0.90 + i * 0.115
        y = wy + 0.12
        cyl(f"jar_{n}", x, y, sz, sz + 0.105, 0.036, glass, 48, 0.002)
        cyl(f"jar_{n}_fill", x, y, sz + 0.003, sz + 0.07 - 0.005 * (i % 3), 0.0335, powder("sp_" + n, col), 40, 0, True)
        cyl(f"jar_{n}_label", x, y, sz + 0.03, sz + 0.07, 0.0368, kraft, 48, 0)
        cyl(f"jar_{n}_lid", x, y, sz + 0.105, sz + 0.123, 0.0375, lid, 48, 0.002)
    for n, x, col in [("salt", 0.00, (0.88, 0.87, 0.84)), ("pepper", 0.12, (0.05, 0.04, 0.04))]:
        y = wy + 0.10
        cyl(f"mill_{n}", x, y, sz, sz + 0.17, 0.027, wood("mill_" + n, (0.55, 0.36, 0.18) if n == "salt" else (0.30, 0.18, 0.09),
                                                          (0.40, 0.24, 0.12) if n == "salt" else (0.14, 0.08, 0.04), rough=0.45), 48, 0.004)
        cyl(f"mill_{n}_cap", x, y, sz + 0.17, sz + 0.19, 0.029, st, 48, 0.003)
        cyl(f"mill_{n}_knob", x, y, sz + 0.19, sz + 0.205, 0.014, st, 32, 0.003)
    bottle = glass_mat("bottle_green", (0.10, 0.34, 0.14), 0.03)
    cyl("oil_bottle", 0.40, wy + 0.12, sz, sz + 0.20, 0.033, bottle, 48, 0.004)
    cyl("oil_neck", 0.40, wy + 0.12, sz + 0.20, sz + 0.27, 0.012, bottle, 32, 0.002)
    cyl("oil_cap", 0.40, wy + 0.12, sz + 0.27, sz + 0.285, 0.0145, st, 32, 0.002)
    cyl("oil_inner", 0.40, wy + 0.12, sz + 0.004, sz + 0.14, 0.030, simple("oil", (0.55, 0.50, 0.08), 0.1, transmission_weight=0.9, ior=1.47), 40, 0)
    cer = simple("ceramic_white", (0.90, 0.90, 0.87), 0.22, coat_weight=0.3)
    cyl("pot_white", 0.56, wy + 0.12, sz, sz + 0.09, 0.045, cer, 48, 0.006)
    cyl("pot_white_2", 0.70, wy + 0.12, sz, sz + 0.07, 0.04, cer, 48, 0.006)
    box("lean_board", -0.9, -0.4, wy + 0.05, wy + 0.075, 0.90, 1.12, oak, 0.004)


def build_lights():
    def area(name, loc, size, energy, color, rot=(0, 0, 0)):
        d = bpy.data.lights.new(name, "AREA")
        d.shape = "RECTANGLE"
        d.size, d.size_y = size
        d.energy = energy
        d.color = color
        o = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = rot
        o.visible_camera = False  # emitters must not show up as plates in the picture
        return o

    warm = (1.0, 0.80, 0.60)      # about 2700 K ceiling light
    soft = (1.0, 0.88, 0.74)
    cool = (0.70, 0.82, 1.0)       # dusk spill from off-camera windows
    area("ceil_cutting", (-1.2, -0.80, 2.40), (1.4, 0.7), 70, warm)
    area("ceil_sink", (1.1, -0.80, 2.40), (1.4, 0.7), 70, warm)
    area("ceil_mid", (0.0, -1.70, 2.40), (2.2, 0.8), 55, soft)
    area("left_window_fill", (-2.2, -1.0, 1.5), (1.4, 1.2), 55, cool, rot=(0, math.radians(90), 0))
    area("shelf_fill", (0.0, -1.5, 2.0), (1.8, 0.5), 22, soft, rot=(math.radians(155), 0, 0))
    d = bpy.data.lights.new("hood_spot", "SPOT")
    d.energy = 22
    d.spot_size = math.radians(85)
    d.spot_blend = 0.7
    d.shadow_soft_size = 0.08
    d.color = (1.0, 0.84, 0.64)
    o = bpy.data.objects.new("hood_spot", d)
    bpy.context.collection.objects.link(o)
    o.location = (-0.2, -0.35, 1.60)
    o.visible_camera = False
    w = bpy.data.worlds.new("world")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.55, 0.60, 0.70, 1)
    bg.inputs["Strength"].default_value = 0.22
    bpy.context.scene.world = w


# =========================================================================== cameras
# GoPro-like point of view: wide lens, chest/head height, looking at one work zone.
PRESETS = {
    "cutting":  ((-1.40, -1.00, 1.45), (-1.40, -0.28, 0.88)),
    "hob":      ((-0.20, -1.00, 1.45), (-0.20, -0.30, 0.88)),
    "sink":     (( 0.90, -1.00, 1.45), ( 0.90, -0.30, 0.88)),
    "drawers":  ((-0.20, -1.00, 1.10), (-0.20, -0.60, 0.45)),
    "utensils": ((-1.40, -0.95, 1.45), (-1.40,  0.00, 1.55)),
    "knives":   ((-0.85, -0.95, 1.45), (-0.85,  0.00, 1.50)),
    "spices":   (( 0.00, -1.20, 1.55), ( 0.00, -2.60, 1.40)),
    "overview": (( 0.00, -2.40, 1.75), ( 0.00,  0.00, 0.95)),
}
LENS = 16.0
FPS = 24


def aim(loc, target, prev_z=None):
    f = (Vector(target) - Vector(loc)).normalized()
    yaw = math.atan2(-f.x, f.y)
    if prev_z is not None:
        while yaw - prev_z > math.pi:
            yaw -= 2 * math.pi
        while yaw - prev_z < -math.pi:
            yaw += 2 * math.pi
    return (math.radians(90) + math.asin(f.z), 0.0, yaw)


def make_camera(name, loc, target, lens=LENS):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cd.clip_end = 30
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 5.6  # light depth of field, as in a real wide lens at close range
    cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    o = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = aim(loc, target)
    return o


# Seven-second pass (24 fps = 168 frames): utensils -> cutting -> hob -> drawers -> sink -> turn to the spices.
SWEEP = [
    (1,   (-1.50, -1.00, 1.45), (-1.40, -0.10, 1.30)),
    (30,  (-1.40, -1.00, 1.45), (-1.40, -0.28, 0.88)),
    (46,  (-1.25, -1.00, 1.45), (-1.25, -0.28, 0.88)),
    (68,  (-0.20, -1.00, 1.45), (-0.20, -0.30, 0.88)),
    (86,  (-0.20, -1.00, 1.45), (-0.20, -0.30, 0.88)),
    (98,  (-0.20, -1.00, 1.10), (-0.20, -0.60, 0.45)),
    (118, (0.90, -1.00, 1.45), (0.90, -0.30, 0.88)),
    (136, (1.00, -1.00, 1.45), (1.00, -0.30, 0.88)),
    (156, (0.30, -1.20, 1.55), (-0.30, -2.60, 1.40)),
    (168, (0.30, -1.20, 1.55), (-0.30, -2.60, 1.40)),
]


def build_sweep_camera():
    cam = make_camera("CAM_sweep", SWEEP[0][1], SWEEP[0][2])
    prev = None
    for fr, loc, tgt in SWEEP:
        e = aim(loc, tgt, prev)
        prev = e[2]
        cam.location = loc
        cam.rotation_euler = e
        cam.data.dof.focus_distance = (Vector(tgt) - Vector(loc)).length
        cam.keyframe_insert("location", frame=fr)
        cam.keyframe_insert("rotation_euler", frame=fr)
        cam.data.dof.keyframe_insert("focus_distance", frame=fr)
    return cam


# =========================================================================== render
def setup_render(width=1280, height=720):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.samples = next((int(a.split("=")[1]) for a in ARGS if a.startswith("samples=")), 32 if DRAFT else 128)
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    cy.max_bounces = 8
    cy.diffuse_bounces = 4
    cy.glossy_bounces = 4
    cy.transmission_bounces = 8
    cy.sample_clamp_indirect = 8.0  # tames fireflies from the glass and steel
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"  # OptiX fails to load on this laptop, CUDA works
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type != "CPU"
        cy.device = "GPU"
    except Exception as e:
        print("GPU unavailable, using CPU:", e)
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, 168
    sc.render.image_settings.file_format = "PNG"
    for vt in ("AgX", "Khronos PBR Neutral", "Standard"):
        try:
            sc.view_settings.view_transform = vt
            break
        except TypeError:
            continue
    for look in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
    sc.view_settings.exposure = next((float(a.split("=")[1]) for a in ARGS if a.startswith("exposure=")), -0.7)


def main():
    clear()
    build_room()
    build_counter_run()
    build_wall_items()
    build_opposite_wall()
    build_lights()
    for n, (loc, tgt) in PRESETS.items():
        make_camera("CAM_" + n, loc, tgt)
    sweep = build_sweep_camera()
    setup_render()
    sc = bpy.context.scene
    sc.camera = bpy.data.objects["CAM_cutting"]
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "kitchen.blend"))
    print("saved kitchen.blend")
    if "stills" in ARGS:
        only = [a.split("=", 1)[1] for a in ARGS if a.startswith("only=")]
        for n in PRESETS:
            if only and n not in only:
                continue
            sc.camera = bpy.data.objects["CAM_" + n]
            sc.render.filepath = os.path.join(OUT, f"{n}.png")
            bpy.ops.render.render(write_still=True)
            print("rendered", n)
    if "sweep" in ARGS:
        sc.camera = sweep
        os.makedirs(os.path.join(OUT, "sweep"), exist_ok=True)
        sc.render.filepath = os.path.join(OUT, "sweep", "f_")
        bpy.ops.render.render(animation=True)
        print("rendered sweep")


main()
