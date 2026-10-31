"""Plate & Price virtual kitchen: a clean, modern work area built procedurally in Blender.

Run headless from plate-and-price/:
    blender -b -P kitchen/build_kitchen.py -- build            # kitchen.blend only
    blender -b -P kitchen/build_kitchen.py -- stills           # + one PNG per camera preset
    blender -b -P kitchen/build_kitchen.py -- sweep            # + PNG sequence of the 7 s pass (encode with ffmpeg)
    add `draft` to any command for a fast low-sample render.

Layout (metres, X right, Y away from the cook, Z up; back wall at y=0, camera looks toward +Y):
    cutting zone  x -2.0..-0.8   oak block counter, drawer + doors, knife strip and utensil rail on the wall
    hob zone      x -0.8..+0.4   flush black induction hob, three drawers, slim hood
    sink zone     x +0.4..+2.0   brushed-steel sink, gooseneck tap, ribbed drainer
    opposite wall y=-2.6         floating shelf with spices, salt and pepper, oil; low sideboard
The cook's hands, food and tools are composited over this background; nothing here is animated except the camera.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(HERE, "renders")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["build"]
DRAFT = "draft" in ARGS

# --------------------------------------------------------------------------- materials
_mats = {}


def mat(name, color, rough=0.5, metal=0.0, **extra):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in extra.items():
        k = "IOR" if k == "ior" else k.replace("_", " ").title()
        if k in b.inputs:
            b.inputs[k].default_value = (*v, 1) if isinstance(v, tuple) and len(v) == 3 else v
    _mats[name] = m
    return m


def principled(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def tiled(name, color_a, color_b, mortar, width, height, mortar_size, offset, rough, scale_xy, bump=0.4):
    """Brick-texture surface in UV space; scale_xy is the size in metres of the UV square."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = principled(m)
    b.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale_xy[0], scale_xy[1], 1)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = offset
    br.inputs["Color1"].default_value = (*color_a, 1)
    br.inputs["Color2"].default_value = (*color_b, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = mortar_size
    br.inputs["Mortar Smooth"].default_value = 0.1
    br.inputs["Brick Width"].default_value = width
    br.inputs["Row Height"].default_value = height
    bu = nt.nodes.new("ShaderNodeBump")
    bu.inputs["Strength"].default_value = bump
    bu.inputs["Distance"].default_value = 0.002
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(br.outputs["Fac"], bu.inputs["Height"])
    nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


# --------------------------------------------------------------------------- primitives
def _finish(o, name, m, bevel):
    o.name = name
    if m:
        o.data.materials.append(m)
    if bevel:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
    return o


def box(name, x0, x1, y0, y1, z0, z1, m, bevel=0.003):
    bpy.ops.mesh.primitive_cube_add()
    o = bpy.context.object
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    o.scale = (abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, m, bevel)


def cyl(name, x, y, z0, z1, r, m, verts=48, bevel=0.0015, axis="Z"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=abs(z1 - z0))
    o = bpy.context.object
    o.location = (x, y, (z0 + z1) / 2)
    if axis == "X":
        o.rotation_euler = (0, math.radians(90), 0)
        o.location = (x, y, z0)
    bpy.ops.object.transform_apply(rotation=True)
    return _finish(o, name, m, bevel)


def sphere(name, x, y, z, r, m, sz=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r)
    o = bpy.context.object
    o.location = (x, y, z)
    o.scale = (1, 1, sz)
    bpy.ops.object.shade_smooth()
    return _finish(o, name, m, 0)


def tube(name, pts, radius, m):
    """Round pipe through the given points (used for the tap)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 6
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for p, c in zip(sp.bezier_points, pts):
        p.co = c
        p.handle_left_type = p.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    cu.materials.append(m)
    return o


def smooth_cyl(name, x, y, z0, z1, r, m, verts=48):
    o = cyl(name, x, y, z0, z1, r, m, verts, bevel=0)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    return o


# --------------------------------------------------------------------------- scene
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build_room():
    wall = mat("wall_white", (0.72, 0.72, 0.70), 0.9)
    tile = tiled("tile_white", (0.93, 0.93, 0.92), (0.90, 0.90, 0.89), (0.62, 0.62, 0.6),
                 0.30, 0.10, 0.004, 0.0, 0.18, (4.6, 2.3))
    floor = tiled("floor_oak", (0.30, 0.22, 0.14), (0.27, 0.19, 0.12), (0.10, 0.07, 0.04),
                  1.0, 0.16, 0.003, 0.5, 0.45, (5.2, 3.0), bump=0.2)
    # floor
    bpy.ops.mesh.primitive_plane_add(size=1)
    f = bpy.context.object
    f.name = "floor"
    f.scale = (5.2, 3.0, 1)
    f.location = (0, -1.3, 0)
    bpy.ops.object.transform_apply(scale=True)
    f.data.materials.append(floor)
    # back wall (tiled), faces -Y
    bpy.ops.mesh.primitive_plane_add(size=1)
    w = bpy.context.object
    w.name = "wall_back"
    w.rotation_euler = (math.radians(90), 0, 0)
    w.scale = (4.6, 2.3, 1)
    w.location = (0, 0, 1.15)
    bpy.ops.object.transform_apply(rotation=True, scale=True)
    w.data.materials.append(tile)
    # remaining walls and ceiling (plain)
    box("wall_front", -2.6, 2.6, -2.62, -2.6, 0, 2.4, wall, 0)
    box("wall_left", -2.3, -2.28, -2.62, 0, 0, 2.4, wall, 0)
    box("wall_right", 2.28, 2.3, -2.62, 0, 0, 2.4, wall, 0)
    box("ceiling", -2.3, 2.3, -2.62, 0, 2.4, 2.42, wall, 0)


def build_counter_run():
    charcoal = mat("front_charcoal", (0.035, 0.04, 0.045), 0.5)
    carcass = mat("carcass_dark", (0.03, 0.03, 0.032), 0.8)
    quartz = mat("quartz_white", (0.88, 0.88, 0.86), 0.22)
    oak = mat("oak_block", (0.40, 0.26, 0.14), 0.4)
    steel = mat("steel", (0.62, 0.63, 0.65), 0.28, 1.0)
    dark = mat("gap_dark", (0.005, 0.005, 0.005), 0.9)

    D, TOP0, TOP1 = 0.60, 0.86, 0.90
    # plinth + carcass
    box("plinth", -2.0, 2.0, -D + 0.06, 0, 0, 0.10, dark, 0)
    box("carcass", -2.0, 2.0, -D + 0.02, 0, 0.10, TOP0, carcass, 0)

    # worktops: oak butcher block (cutting zone) and white quartz (hob + sink), sink hole by boolean
    box("top_oak", -2.0, -0.8, -D, 0, TOP0, TOP1, oak, 0.004)
    box("top_hob", -0.8, 0.4, -D, 0, TOP0, TOP1, quartz, 0.004)
    sink_top = box("top_sink", 0.4, 2.0, -D, 0, TOP0, TOP1, quartz, 0.004)
    cutter = box("cutter", 0.58, 1.14, -0.52, -0.08, 0.5, 1.0, dark, 0)
    bm = sink_top.modifiers.new("hole", "BOOLEAN")
    bm.operation = "DIFFERENCE"
    bm.object = cutter
    bm.solver = "EXACT"
    bpy.context.view_layer.objects.active = sink_top
    bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(cutter, do_unlink=True)

    # drawer / door fronts: 4 mm gaps, charcoal, with a dark J-pull gap on top of each drawer
    def front(name, x0, x1, z0, z1, drawer):
        box(name, x0 + 0.002, x1 - 0.002, -D - 0.018, -D + 0.002, z0 + 0.002, z1 - 0.002, charcoal, 0.003)
        if drawer:
            box(name + "_pull", x0 + 0.02, x1 - 0.02, -D - 0.02, -D - 0.012, z1 - 0.032, z1 - 0.012, dark, 0)

    # cutting zone: one wide drawer + two doors
    front("cut_drawer", -2.0, -0.8, 0.66, 0.86, True)
    front("cut_door_l", -2.0, -1.4, 0.10, 0.66, False)
    front("cut_door_r", -1.4, -0.8, 0.10, 0.66, False)
    # hob zone: three drawers
    front("hob_drawer_1", -0.8, 0.4, 0.62, 0.86, True)
    front("hob_drawer_2", -0.8, 0.4, 0.36, 0.62, True)
    front("hob_drawer_3", -0.8, 0.4, 0.10, 0.36, True)
    # sink zone: two doors
    front("sink_door_l", 0.4, 1.2, 0.10, 0.86, False)
    front("sink_door_r", 1.2, 2.0, 0.10, 0.86, False)

    # ---- induction hob, flush with the worktop
    glass = mat("hob_glass", (0.006, 0.006, 0.008), 0.06)
    ring = mat("hob_ring", (0.35, 0.35, 0.36), 0.3)
    led = mat("hob_led", (1, 1, 1), 0.3, emission_color=(1, 0.95, 0.85), emission_strength=6.0)
    hx, hy = -0.2, -0.30
    box("hob_glass", hx - 0.29, hx + 0.29, hy - 0.26, hy + 0.26, TOP1, TOP1 + 0.006, glass, 0.002)
    for i, (dx, dy, r) in enumerate([(-0.14, 0.09, 0.105), (0.14, 0.09, 0.085), (-0.14, -0.12, 0.085), (0.14, -0.12, 0.105)]):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.0013, major_segments=64, minor_segments=8)
        t = bpy.context.object
        t.name = f"hob_ring_{i}"
        t.location = (hx + dx, hy + dy, TOP1 + 0.0065)
        t.scale = (1, 1, 0.5)
        t.data.materials.append(ring)
    box("hob_slider", hx - 0.13, hx + 0.13, hy - 0.235, hy - 0.231, TOP1 + 0.0062, TOP1 + 0.0066, mat("hob_slider", (0.5, 0.5, 0.5), 0.3), 0)
    for i in range(5):
        cyl(f"hob_dot_{i}", hx - 0.20 + 0.10 * i, hy - 0.215, TOP1 + 0.0062, TOP1 + 0.0067, 0.004, led, 16, 0)

    # ---- slim hood with light, and a dark chimney to the ceiling
    hood_m = mat("hood_black", (0.025, 0.025, 0.028), 0.35, 0.6)
    box("hood_body", hx - 0.30, hx + 0.30, -0.50, 0.0, 1.62, 1.70, hood_m, 0.004)
    box("hood_chimney", hx - 0.15, hx + 0.15, -0.22, 0.0, 1.70, 2.4, hood_m, 0.004)
    box("hood_light", hx - 0.22, hx + 0.22, -0.40, -0.30, 1.618, 1.622,
        mat("hood_led", (1, 1, 1), 0.3, emission_color=(1, 0.88, 0.7), emission_strength=25), 0)

    # ---- sink: steel basin under the hole, gooseneck tap, ribbed drainer
    bx0, bx1, by0, by1 = 0.60, 1.12, -0.50, -0.10
    box("basin_floor", bx0, bx1, by0, by1, 0.66, 0.668, steel, 0)
    box("basin_back", bx0, bx1, by1 - 0.008, by1, 0.66, TOP1 - 0.04, steel, 0)
    box("basin_front", bx0, bx1, by0, by0 + 0.008, 0.66, TOP1 - 0.04, steel, 0)
    box("basin_left", bx0, bx0 + 0.008, by0, by1, 0.66, TOP1 - 0.04, steel, 0)
    box("basin_right", bx1 - 0.008, bx1, by0, by1, 0.66, TOP1 - 0.04, steel, 0)
    cyl("drain", (bx0 + bx1) / 2, (by0 + by1) / 2, 0.668, 0.672, 0.035, dark, 32, 0)
    cx = 1.14 + 0.0
    box("drainer", 1.22, 1.92, -0.54, -0.06, TOP1, TOP1 + 0.003, steel, 0.001)
    for i in range(9):
        box(f"groove_{i}", 1.26 + i * 0.075, 1.285 + i * 0.075, -0.50, -0.10, TOP1 + 0.003, TOP1 + 0.0035, dark, 0)
    # tap: base, gooseneck, lever
    tx, ty = 0.86, -0.06
    cyl("tap_base", tx, ty, TOP1, TOP1 + 0.05, 0.022, steel, 32, 0.002)
    tap = tube("tap_neck", [(tx, ty, TOP1 + 0.05), (tx, ty, TOP1 + 0.28), (tx, ty - 0.07, TOP1 + 0.40),
                            (tx, ty - 0.17, TOP1 + 0.38), (tx, ty - 0.23, TOP1 + 0.30)], 0.014, steel)
    cyl("tap_tip", tx, ty - 0.23, TOP1 + 0.27, TOP1 + 0.31, 0.016, steel, 24, 0.001)
    box("tap_lever", tx + 0.022, tx + 0.085, ty - 0.008, ty + 0.008, TOP1 + 0.07, TOP1 + 0.085, steel, 0.002)
    # a clean soap pump, to read as a sink area
    cyl("soap", 1.05, -0.04, TOP1, TOP1 + 0.14, 0.03, mat("soap_black", (0.02, 0.02, 0.02), 0.25), 32, 0.002)


def build_wall_items():
    steel = mat("steel", (0.62, 0.63, 0.65), 0.28, 1.0)
    oak = mat("oak_block", (0.40, 0.26, 0.14), 0.4)
    black = mat("handle_black", (0.02, 0.02, 0.02), 0.45)
    wood_h = mat("handle_wood", (0.35, 0.2, 0.1), 0.5)
    # utensil rail with S-hooks and utensils (cutting zone, high on the wall)
    ry, rz = -0.05, 1.78
    rail = cyl("rail", 0, ry, 0, 0.75, 0.009, steel, 24, 0, axis="X")  # 0.75 m long along X
    rail.location = (-1.575, ry, rz)
    for i, x in enumerate([-1.88, -1.74, -1.60, -1.46, -1.32]):
        hook = tube(f"hook_{i}", [(x, ry, rz - 0.01), (x, ry - 0.02, rz - 0.035), (x, ry, rz - 0.06)], 0.0025, steel)
    # ladle
    cyl("ladle_h", -1.88, ry - 0.02, rz - 0.40, rz - 0.04, 0.005, steel, 12, 0)
    sphere("ladle_bowl", -1.88, ry - 0.02, rz - 0.43, 0.045, steel, 0.5)
    # spatula
    cyl("spat_h", -1.74, ry - 0.02, rz - 0.33, rz - 0.04, 0.007, wood_h, 12, 0)
    box("spat_head", -1.775, -1.705, ry - 0.03, ry - 0.015, rz - 0.47, rz - 0.33, black, 0.002)
    # whisk
    cyl("whisk_h", -1.60, ry - 0.02, rz - 0.20, rz - 0.04, 0.008, steel, 12, 0)
    sphere("whisk_head", -1.60, ry - 0.02, rz - 0.29, 0.04, steel, 1.7).display_type = "WIRE"
    # tongs (two flat bars)
    box("tongs_a", -1.472, -1.462, ry - 0.03, ry - 0.012, rz - 0.40, rz - 0.04, steel, 0.001)
    box("tongs_b", -1.452, -1.442, ry - 0.03, ry - 0.012, rz - 0.40, rz - 0.04, steel, 0.001)
    # slotted spoon
    cyl("spoon_h", -1.32, ry - 0.02, rz - 0.36, rz - 0.04, 0.005, black, 12, 0)
    sphere("spoon_bowl", -1.32, ry - 0.02, rz - 0.39, 0.04, steel, 0.4)

    # magnetic knife strip with four knives (left of the hood)
    box("knife_strip", -1.12, -0.58, -0.035, -0.002, 1.60, 1.66, oak, 0.003)
    for i, (x, blade, grip) in enumerate([(-1.06, 0.20, 0.12), (-0.94, 0.17, 0.11), (-0.82, 0.14, 0.10), (-0.70, 0.11, 0.10)]):
        top = 1.65
        box(f"knife_blade_{i}", x - 0.018, x + 0.018, -0.045, -0.040, top - blade, top, steel, 0.001)
        box(f"knife_handle_{i}", x - 0.011, x + 0.011, -0.052, -0.036, top - blade - grip, top - blade, black, 0.003)


def build_opposite_wall():
    oak = mat("oak_block", (0.40, 0.26, 0.14), 0.4)
    charcoal = mat("front_charcoal", (0.035, 0.04, 0.045), 0.5)
    quartz = mat("quartz_white", (0.88, 0.88, 0.86), 0.22)
    dark = mat("gap_dark", (0.005, 0.005, 0.005), 0.9)
    wy = -2.60
    # low sideboard
    box("side_body", -1.2, 1.2, wy, wy + 0.45, 0.06, 0.86, charcoal, 0.003)
    box("side_plinth", -1.2, 1.2, wy, wy + 0.40, 0, 0.06, dark, 0)
    box("side_top", -1.2, 1.2, wy, wy + 0.47, 0.86, 0.90, oak, 0.004)
    for i in range(3):
        x0 = -1.2 + i * 0.8
        box(f"side_door_{i}", x0 + 0.003, x0 + 0.797, wy + 0.45, wy + 0.466, 0.07, 0.855, charcoal, 0.003)
    # floating oak shelf
    box("shelf", -1.0, 1.0, wy, wy + 0.24, 1.30, 1.335, oak, 0.003)
    sz = 1.335
    glass = mat("jar_glass", (0.9, 0.95, 0.95), 0.03, 0.0, transmission_weight=1.0, ior=1.45)
    lid = mat("jar_lid", (0.05, 0.05, 0.05), 0.4, 0.6)
    spices = [("paprika", (0.65, 0.12, 0.03)), ("cumin", (0.42, 0.26, 0.10)), ("oregano", (0.16, 0.28, 0.08)),
              ("chilli", (0.50, 0.04, 0.02)), ("turmeric", (0.80, 0.50, 0.04)), ("pepper_corn", (0.05, 0.05, 0.05))]
    for i, (n, col) in enumerate(spices):
        x = -0.90 + i * 0.115
        y = wy + 0.12
        cyl(f"jar_{n}", x, y, sz, sz + 0.11, 0.036, glass, 32, 0)
        cyl(f"jar_{n}_fill", x, y, sz + 0.002, sz + 0.075, 0.033, mat("sp_" + n, col, 0.95), 32, 0)
        cyl(f"jar_{n}_lid", x, y, sz + 0.11, sz + 0.125, 0.037, lid, 32, 0.001)
    # salt and pepper mills (wood + steel top), bigger, in front
    for n, x, col in [("salt", 0.00, (0.9, 0.9, 0.88)), ("pepper", 0.12, (0.06, 0.05, 0.05))]:
        y = wy + 0.10
        smooth_cyl(f"mill_{n}", x, y, sz, sz + 0.17, 0.027, mat("mill_" + n, col, 0.4), 32)
        smooth_cyl(f"mill_{n}_cap", x, y, sz + 0.17, sz + 0.19, 0.029, mat("steel", (0.62, 0.63, 0.65), 0.28, 1.0), 32)
    # olive oil bottle (green glass) and a small white ceramic pot
    bottle = mat("bottle_green", (0.08, 0.30, 0.12), 0.05, 0.0, transmission_weight=0.7, ior=1.45)
    smooth_cyl("oil_bottle", 0.40, wy + 0.12, sz, sz + 0.20, 0.033, bottle, 32)
    smooth_cyl("oil_neck", 0.40, wy + 0.12, sz + 0.20, sz + 0.27, 0.012, bottle, 24)
    cyl("oil_cap", 0.40, wy + 0.12, sz + 0.27, sz + 0.285, 0.014, mat("steel", (0.62, 0.63, 0.65), 0.28, 1.0), 24, 0)
    smooth_cyl("pot_white", 0.56, wy + 0.12, sz, sz + 0.09, 0.045, mat("ceramic_white", (0.92, 0.92, 0.9), 0.25), 32)
    smooth_cyl("pot_white_2", 0.70, wy + 0.12, sz, sz + 0.07, 0.04, mat("ceramic_white", (0.92, 0.92, 0.9), 0.25), 32)
    # a small plant-free decor: a wooden board leaning on the sideboard
    box("lean_board", -0.9, -0.4, wy + 0.05, wy + 0.075, 0.90, 1.12, oak, 0.004)


def build_lights():
    def area(name, loc, size, energy, color, rot=(0, 0, 0), shape="RECTANGLE"):
        d = bpy.data.lights.new(name, "AREA")
        d.shape = shape
        d.size = size[0]
        if shape == "RECTANGLE":
            d.size_y = size[1]
        d.energy = energy
        d.color = color
        o = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = rot
        return o

    warm = (1.0, 0.93, 0.82)
    neutral = (1.0, 0.98, 0.95)
    # ceiling panels (pointing down)
    area("ceil_cutting", (-1.2, -0.75, 2.38), (1.2, 0.5), 55, neutral)
    area("ceil_sink", (1.1, -0.75, 2.38), (1.2, 0.5), 55, neutral)
    area("ceil_mid", (0.0, -1.6, 2.38), (2.0, 0.6), 45, warm)
    # hood spot on the hob
    d = bpy.data.lights.new("hood_spot", "SPOT")
    d.energy = 20
    d.spot_size = math.radians(80)
    d.spot_blend = 0.6
    d.color = (1.0, 0.88, 0.72)
    o = bpy.data.objects.new("hood_spot", d)
    bpy.context.collection.objects.link(o)
    o.location = (-0.2, -0.35, 1.60)
    # shelf wash
    area("shelf_fill", (0.0, -1.9, 2.0), (1.8, 0.4), 18, warm, rot=(math.radians(150), 0, 0))
    # world: dim neutral
    w = bpy.data.worlds.new("world")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.5, 0.5, 0.52, 1)
    bg.inputs["Strength"].default_value = 0.04
    bpy.context.scene.world = w


# --------------------------------------------------------------------------- cameras
# GoPro-like point of view: wide lens, chest/head height, looking at one work zone.
# (position, target) in metres; lens 16 mm on a 36 mm sensor = about 96 degrees horizontal.
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


def aim(loc, target, prev_z=None):
    f = Vector(target) - Vector(loc)
    f.normalize()
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
    cd.dof.use_dof = False
    o = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = aim(loc, target)
    return o


# Seven-second pass (24 fps = 168 frames): knives/utensils -> cutting -> hob -> drawers -> sink -> turn to spices.
FPS = 24
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
        cam.keyframe_insert("location", frame=fr)
        cam.keyframe_insert("rotation_euler", frame=fr)
    return cam


# --------------------------------------------------------------------------- render
def setup_render(width=1280, height=720):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.samples = next((int(a.split("=")[1]) for a in ARGS if a.startswith("samples=")), 24 if DRAFT else 64)
    cy.use_denoising = True
    cy.max_bounces = 6
    cy.glossy_bounces = 4
    cy.transmission_bounces = 6
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"  # OptiX fails to load on this laptop, CUDA works
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type != "CPU"
        cy.device = "GPU"
    except Exception as e:  # falls back to CPU
        print("GPU unavailable, using CPU:", e)
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, 168
    sc.render.image_settings.file_format = "PNG"
    for vt in ("Khronos PBR Neutral", "AgX", "Standard"):
        try:
            sc.view_settings.view_transform = vt
            break
        except TypeError:
            continue
    sc.view_settings.exposure = -0.9


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
        sc.render.filepath = os.path.join(OUT, "sweep", "f_")
        os.makedirs(os.path.join(OUT, "sweep"), exist_ok=True)
        bpy.ops.render.render(animation=True)
        print("rendered sweep")


main()
