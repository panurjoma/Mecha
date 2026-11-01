# Virtual kitchen (Blender background)

A clean, modern work area built procedurally in Blender, used as the **background**. The only things composited over it are the
owner's own actions: hands, food, board, dishes and tools. Nothing outside the work area is modelled.

`build_kitchen.py` creates everything from scratch (no downloaded assets) and saves `kitchen.blend`.
Run it from `plate-and-price/` with Blender 5.2 (headless):

```powershell
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $B -b -P kitchen/build_kitchen.py -- build                        # kitchen.blend only
& $B -b -P kitchen/build_kitchen.py -- stills                       # + one PNG per camera preset in kitchen/renders/
& $B -b -P kitchen/build_kitchen.py -- stills only=hob only=sink    # just some presets
& $B -b -P kitchen/build_kitchen.py -- sweep samples=40            # + 168-frame PNG sequence of the 7 s pass
# encode with the GoPro lens finish: mild barrel distortion, vignette, fine temporal grain
ffmpeg -framerate 24 -i kitchen/renders/sweep/f_%04d.png `
  -vf "lenscorrection=k1=-0.08:k2=0,vignette=angle=PI/5,noise=alls=4:allf=t,format=yuv420p" `
  -c:v libx264 -crf 18 kitchen/renders/kitchen_sweep.mp4
```

Add `draft` for a fast low-sample render (about 5 s per frame at 1280x720 on the RTX 3060 Laptop, CUDA; OptiX does not load on
this laptop). Rendered videos stay out of git (see `.gitignore`); the stills and the `.blend` are tracked.

## Zones (metres; X right, Y away from the cook, Z up; back wall at y = 0)

| Zone | Where | What is there |
|---|---|---|
| Cutting | x -2.0 to -0.8 | oak butcher-block worktop, one wide drawer and two doors, utensil rail (ladle, spatula, whisk, tongs, slotted spoon) and a magnetic knife strip on the wall |
| Hob | x -0.8 to +0.4 | flush black induction hob (4 zones, touch slider), three drawers, slim black hood with light |
| Sink | x +0.4 to +2.0 | brushed-steel basin, gooseneck tap, soap pump, ribbed drainer |
| Opposite wall | y = -2.6 | floating oak shelf with six spice jars, salt and pepper mills, olive oil and two ceramic pots; charcoal sideboard |

Materials: matte charcoal fronts, white quartz, light oak, brushed steel, white stack-bond wall tiles, oak-plank floor.

## Camera presets (GoPro point of view)

Wide lens (16 mm on a 36 mm sensor, about 96 degrees), head/chest height, looking down at one zone like the recordings.
`PRESETS` in the script holds `(camera position, target)` for each; each becomes a camera object `CAM_<name>` in the `.blend`.

| Preset | Matches |
|---|---|
| `cutting` | chopping on the board (leek, onion, tomato, sausage) |
| `hob` | pan and pot on the hob (sauce, frying, boiling) |
| `sink` | washing and draining at the sink |
| `drawers` | looking down at the drawers |
| `utensils`, `knives` | the hanging utensils and knives |
| `spices` | turning round to the spice shelf |
| `overview` | the whole work area from a step back |

## The 7-second pass

`CAM_sweep`, 168 frames at 24 fps, Bezier-eased: utensils and board -> cutting -> hob -> drawers -> sink -> turn to the spices.
Edit the `SWEEP` list (frame, camera position, target) to change the route or timing.

## What makes it read as real

- **Scale and bevels:** everything is modelled at real size (worktop 40 mm, 25 mm overhang, 4 mm door gaps) and every edge has a
  small bevel so it catches light.
- **Procedural materials, no downloaded textures:** oak butcher block (growth rings plus glued strips with hairline joints),
  white quartz with speckle and faint veining, glazed wall tile with recessed matte grout and per-tile tint, oak-plank floor with
  satin lacquer, brushed stainless (streaked roughness and bump), black induction glass with faint smudges, matt charcoal
  lacquer whose roughness wanders, flat matt paint.
- **Roughness is never uniform:** low-frequency noise varies it on every surface, plus tiny bump and smudges.
- **Everyday detail:** brushed-steel J-pulls, rounded undermount basin with strainer, gooseneck tap with aerator, soap pump, ribbed
  drainer, hood grease filter, wall sockets, skirting boards, spice jars with kraft labels, wooden mills, real knife profiles on the
  magnetic strip, ladle and slotted spoon with hollow bowls, whisk wires.
- **Light:** warm ceiling panels (about 2700 K), a cool dusk fill from off-camera windows, a hood spot on the hob, a dim bluish
  world so metal and glass have something to reflect. Lights are hidden from the camera.
- **Camera:** 16 mm GoPro field of view, light depth of field (f/5.6, focus follows the target along the sweep), AgX tone mapping
  with a medium-high-contrast look.
- **Encode:** barrel distortion, vignette and grain are added by ffmpeg (command above).

Rendering is Cycles with adaptive sampling and denoising; 100 samples is the default for the sweep (about 12 s per frame on the
RTX 3060 Laptop). Match the real footage's home light by changing the colours and energies in `build_lights`.
