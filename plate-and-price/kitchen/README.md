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
ffmpeg -framerate 24 -i kitchen/renders/sweep/f_%04d.png -c:v libx264 -pix_fmt yuv420p kitchen/renders/kitchen_sweep.mp4
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

Rendering is Cycles with denoising. The working area is lit by ceiling panels and the hood light so that the real footage's warm
home light can be matched later by changing the `build_lights` colours and energies.
