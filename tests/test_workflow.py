import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import wave
import zipfile
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from mecha.cli import main
from mecha.models import MechaError, validate
from mecha.render import render, subtitles, probe
from mecha.store import Store
from mecha.review import review_packet

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "orbit-proof.json"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "workspace")
        self.doc = json.loads(EXAMPLE.read_text())
        self.store.save(self.doc, "Initial assistant draft")

    def tearDown(self):
        self.temp.cleanup()

    def audio(self, seconds=3):
        path = self.root / "voice.wav"
        with wave.open(str(path), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(8000)
            stream.writeframes(b"\0\0" * round(8000 * seconds))
        return path

    def test_corrections_are_immutable_and_require_current_revision(self):
        self.store.feedback("orbit-proof", "Make the intro shorter", 1)
        changed = copy.deepcopy(self.doc)
        changed["scenes"][0]["narration"] = "Versión corregida."
        self.store.save(changed, "Apply creator feedback", 1)
        with self.assertRaisesRegex(MechaError, "Revision conflict"):
            self.store.save(self.doc, "Stale assistant update", 1)
        with self.assertRaisesRegex(MechaError, "expected-revision"):
            self.store.save(self.doc, "Unsafe update")
        history = self.store.history("orbit-proof")
        self.assertEqual(len(history["revisions"]), 2)
        self.assertEqual(history["revisions"][0]["document"], self.doc)
        self.assertEqual(history["events"][0]["payload"]["text"], "Make the intro shorter")

    def test_approval_does_not_survive_a_script_revision(self):
        self.store.approve("orbit-proof", "script", "Creator approved script", 1)
        changed = copy.deepcopy(self.doc)
        changed["storytelling"] += " Revised."
        self.store.save(changed, "Change story", 1)
        self.assertEqual(self.store.approvals("orbit-proof", 2), [])
        with self.assertRaisesRegex(MechaError, "Revision changed"):
            self.store.approve("orbit-proof", "storyboard", "Stale approval", 1)
        with self.assertRaisesRegex(MechaError, "approvals"):
            render(self.store, "orbit-proof", "manim", True)

    def test_export_restore_preserves_all_revisions_and_feedback(self):
        self.store.feedback("orbit-proof", "Clarify the red arrow", 1)
        bundle = self.root / "project.zip"
        self.store.export_bundle("orbit-proof", bundle)
        restored = Store(self.root / "restored")
        restored.restore_bundle(bundle)
        self.assertEqual(restored.history("orbit-proof"), self.store.history("orbit-proof"))
        with self.assertRaisesRegex(MechaError, "already exists"):
            restored.restore_bundle(bundle)

    def test_tampered_bundle_and_traversal_do_not_create_episode(self):
        bundle = self.root / "project.zip"
        self.store.export_bundle("orbit-proof", bundle)
        with zipfile.ZipFile(bundle) as z:
            payload = json.loads(z.read("project.json"))
        payload["revisions"][0]["document"]["topic"] = "Tampered"
        bad = self.root / "bad.zip"
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("project.json", json.dumps(payload))
        restored = Store(self.root / "restored")
        with self.assertRaisesRegex(MechaError, "hash"):
            restored.restore_bundle(bad)
        with self.assertRaisesRegex(MechaError, "Unknown episode"):
            restored.current("orbit-proof")
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("project.json", json.dumps(payload))
            z.writestr("../../evil", "not extracted")
        with self.assertRaises(MechaError):
            restored.restore_bundle(bad)
        self.assertFalse((self.root / "evil").exists())

    def test_contract_rejects_unknown_fields_bad_sources_and_invalid_durations(self):
        for mutate in (
            lambda d: d.update(python="exec('unsafe')"),
            lambda d: d["scenes"][0].update(duration_seconds=float("nan")),
            lambda d: d["scenes"][0]["visual"].update(kind="python"),
            lambda d: d["sources"][0].update(url="file:///etc/passwd"),
            lambda d: d["scenes"][0]["claims"][0].update(source_ids=["missing"]),
            lambda d: d.update(id="../../escape"),
        ):
            doc = copy.deepcopy(self.doc)
            mutate(doc)
            with self.assertRaises(MechaError):
                validate(doc)

    def test_cli_errors_are_machine_readable(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["--workspace", str(self.store.root), "show", "missing"])
        self.assertEqual(code, 2)
        self.assertIn("Unknown episode", json.loads(stderr.getvalue())["error"])

    def test_scene_caption_timing(self):
        srt = subtitles(self.doc)
        self.assertIn("00:00:15,000 --> 00:00:45,000", srt)
        self.assertIn("00:00:45,000 --> 00:01:00,000", srt)

    def test_review_packet_contains_current_script_sources_and_feedback(self):
        self.store.feedback("orbit-proof", "Use a simpler analogy", 1)
        path = self.root / "review-r1.md"
        review_packet(self.store, "orbit-proof", path)
        packet = path.read_text()
        self.assertIn(self.doc["storytelling"], packet)
        self.assertIn(self.doc["scenes"][1]["narration"], packet)
        self.assertIn("Use a simpler analogy", packet)
        self.assertIn("Current approvals: none", packet)
        with self.assertRaisesRegex(MechaError, "exists"):
            review_packet(self.store, "orbit-proof", path)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_audio_bundle_and_changed_audio_checksum(self):
        voice = self.audio()
        info = self.store.attach_audio("orbit-proof", voice)
        bundle = self.root / "audio.zip"
        self.store.export_bundle("orbit-proof", bundle, include_audio=True)
        restored = Store(self.root / "restored")
        restored.restore_bundle(bundle)
        self.assertEqual(restored.get_audio("orbit-proof")["hash"], info["hash"])
        Path(restored.get_audio("orbit-proof")["path"]).write_bytes(b"corrupt")
        with self.assertRaisesRegex(MechaError, "corrupt"):
            restored.get_audio("orbit-proof")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_render_real_media_cache_invalidation_and_audio_duration(self):
        # Very short clip, including filter-metacharacters as literal text.
        doc = copy.deepcopy(self.doc)
        doc["scenes"] = doc["scenes"][:1]
        doc["scenes"][0]["duration_seconds"] = 1
        doc["scenes"][0]["title"] = "Señal: 100% %{n} ' [a,b]"
        self.store.save(doc, "Short render test", 1)
        result = render(self.store, "orbit-proof")
        path = Path(result["directory"]) / "preview.mp4"
        self.assertTrue(path.is_file())
        self.assertTrue(any(s["codec_type"] == "video" for s in probe(path)["streams"]))
        self.assertTrue(result["silent"])
        self.assertTrue(render(self.store, "orbit-proof")["cached"])
        # Corrupt a final cache: it must be regenerated, not silently reused.
        path.write_bytes(b"bad")
        self.assertFalse(render(self.store, "orbit-proof")["cached"])
        self.store.attach_audio("orbit-proof", self.audio(1))
        voiced = render(self.store, "orbit-proof")
        self.assertNotEqual(voiced["key"], result["key"])
        self.assertFalse(voiced["silent"])
        info = probe(Path(voiced["directory"]) / "preview.mp4")
        self.assertTrue(any(s["codec_type"] == "audio" for s in info["streams"]))
        self.store.attach_audio("orbit-proof", self.audio(2))
        with self.assertRaisesRegex(MechaError, "revise scene durations"):
            render(self.store, "orbit-proof")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_final_needs_voice_and_never_accepts_cards(self):
        with self.assertRaisesRegex(MechaError, "storyboard preview"):
            render(self.store, "orbit-proof", "cards", True)
        for stage in ("script", "storyboard"):
            self.store.approve("orbit-proof", stage, "Test fixture approval, not a real creator approval", 1)
        with self.assertRaisesRegex(MechaError, "recorded narration"):
            render(self.store, "orbit-proof", "manim", True)


if __name__ == "__main__":
    unittest.main()
