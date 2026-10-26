"""Minimal ComfyUI HTTP client (standard library only) for the optional quality step.

ComfyUI must be running (default http://127.0.0.1:8188, override COMFY_URL). Export your workflow from ComfyUI with
"Save (API Format)" and keep it in config/comfy/. Not tested yet: no enhancement workflow exists in the repo.

    python comfy_client.py status
    python comfy_client.py run config/comfy/upscale.json --set 12.inputs.image=clip.png --out output/video-001/comfy
"""
import argparse
import json
import mimetypes
import os
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")


def _get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return r.read()


def status():
    return json.loads(_get("/system_stats"))


def upload(path):
    """Upload a file to ComfyUI's input folder; returns the stored name."""
    boundary = uuid.uuid4().hex
    p = Path(path)
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{p.name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + p.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE + "/upload/image", data=body,
                                 headers={"content-type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["name"]


def run_workflow(workflow, overrides=None, out_dir=".", timeout=1800):
    """workflow: API-format dict. overrides: {"node.inputs.key": value}. Returns saved file paths."""
    for dotted, value in (overrides or {}).items():
        node, *rest = dotted.split(".")
        target = workflow[node]
        for k in rest[:-1]:
            target = target[k]
        target[rest[-1]] = value
    req = urllib.request.Request(BASE + "/prompt", data=json.dumps({"prompt": workflow}).encode(),
                                 headers={"content-type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req, timeout=60).read())["prompt_id"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        hist = json.loads(_get(f"/history/{pid}"))
        if pid in hist:
            break
        time.sleep(2)
    else:
        raise TimeoutError(f"ComfyUI job {pid} not finished after {timeout}s")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for node_out in hist[pid]["outputs"].values():
        for item in node_out.get("images", []) + node_out.get("gifs", []) + node_out.get("videos", []):
            q = urllib.parse.urlencode({"filename": item["filename"], "subfolder": item.get("subfolder", ""),
                                        "type": item.get("type", "output")})
            dest = out_dir / item["filename"]
            dest.write_bytes(_get("/view?" + q))
            saved.append(str(dest))
    return saved


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    r = sub.add_parser("run")
    r.add_argument("workflow")
    r.add_argument("--set", action="append", default=[], help="node.inputs.key=value")
    r.add_argument("--out", default="output/comfy")
    a = ap.parse_args()
    if a.cmd == "status":
        s = status()
        print(s["system"]["comfyui_version"], s["devices"][0]["name"])
    else:
        ov = dict(x.split("=", 1) for x in a.set)
        print(run_workflow(json.loads(Path(a.workflow).read_text(encoding="utf-8")), ov, a.out))
