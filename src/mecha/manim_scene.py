"""Fixed data-driven templates, never load generated/user-provided Python."""

import json
import os
import textwrap

from manim import Arrow, BLUE, Circle, Dot, DOWN, GREEN, LEFT, MoveAlongPath, ORIGIN, RED, RIGHT, Scene, Text, UP, WHITE, YELLOW, always_redraw, linear


class EpisodeScene(Scene):
    def construct(self):
        with open(os.environ["MECHA_SCENE_SPEC"], encoding="utf-8") as stream:
            spec = json.load(stream)
        self.camera.background_color = "#101C2D"
        title = Text(spec["title"], font="DejaVu Sans", font_size=32, color=WHITE)
        title.scale_to_fit_width(min(title.width, 12)).to_edge(UP)
        self.add(title)
        caption = Text("\n".join(textwrap.wrap(spec["visual"]["caption"], 70)), font="DejaVu Sans", font_size=20, color=WHITE)
        if spec["visual"]["kind"] == "orbit":
            earth = Circle(radius=1.1, color=BLUE, fill_opacity=0.8)
            orbit = Circle(radius=2.25, color=GREEN)
            satellite = Dot(orbit.point_from_proportion(0), color=YELLOW, radius=0.12)
            gravity = always_redraw(lambda: Arrow(satellite.get_center(), satellite.get_center() * 0.63, buff=0, color=RED))
            # Tangent direction follows the counterclockwise path; lengths are illustrative.
            velocity = always_redraw(lambda: Arrow(satellite.get_center(), satellite.get_center() + 0.4 * (-satellite.get_y() * RIGHT + satellite.get_x() * UP), buff=0, color=YELLOW))
            labels = Text("Gravedad: rojo · Velocidad: amarillo\nIlustración idealizada, no a escala", font="DejaVu Sans", font_size=15).to_edge(DOWN)
            caption.next_to(labels, UP)
            self.add(earth, orbit, satellite, gravity, velocity, labels, caption)
            turns = spec["visual"].get("turns", 1)
            # Circle path supports fractional turns without altering narrated time.
            from manim import ParametricFunction
            import numpy as np
            path = ParametricFunction(lambda t: np.array([2.25 * np.cos(t), 2.25 * np.sin(t), 0]), t_range=[0, 2 * np.pi * turns])
            self.play(MoveAlongPath(satellite, path), run_time=spec["duration_seconds"], rate_func=linear)
        else:
            caption.move_to(ORIGIN)
            self.add(caption)
            self.wait(spec["duration_seconds"])
