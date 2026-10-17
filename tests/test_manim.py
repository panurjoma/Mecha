"""Opt-in native renderer integration, run by the animation CI job."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from mecha.render import render
from mecha.store import Store


@unittest.skipUnless(os.environ.get("MECHA_TEST_MANIM") == "1" and importlib.util.find_spec("manim"), "Set MECHA_TEST_MANIM=1 with Manim installed")
class ManimIntegration(unittest.TestCase):
    def test_orbit_and_card_render_into_one_clip(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            doc = json.loads((Path(__file__).resolve().parents[1] / "examples/orbit-proof.json").read_text())
            for scene in doc["scenes"]:
                scene["duration_seconds"] = 1
            store.save(doc, "Renderer integration fixture")
            result = render(store, doc["id"], "manim")
            self.assertAlmostEqual(result["duration_seconds"], 3, delta=0.2)
            self.assertEqual(result["renderer"], "manim")
