#!/usr/bin/env python3
"""Render one approved sticker reference through the local H3 API, once."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlparse

import requests


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def with_supports(spec):
    """Use a declared seat/support before falling back to standing on the floor."""
    entities = copy.deepcopy(spec["entities"])
    contacts = copy.deepcopy(spec.get("contacts", []))
    supports = spec.get("supports", {})
    performers = [e for e in entities if e["kind"] in {"character", "creature", "robot"}]
    ids = {e["id"] for e in performers}
    if set(supports) - ids:
        raise ValueError("Support references an undeclared performer")
    ground = {"id": "studio_floor", "kind": "set_piece", "label": "plain studio floor",
              "count": 1, "parts": {}, "contact_points": [], "roles": [], "inserted": False}
    endpoints = {e["id"] + ":" + point for e in entities for point in e["contact_points"]}
    for performer in performers:
        performer["contact_points"].append("body_support")
        support = supports.get(performer["id"])
        if support:
            if set(support) != {"target", "relation"}:
                raise ValueError("Support accepts only target and relation")
            if support["target"] not in endpoints or not support["relation"].strip():
                raise ValueError("Support target/relation is invalid")
            contacts.append({"source": performer["id"] + ":body_support", **support})
        else:
            ground["contact_points"].append(performer["id"] + "_support")
            contacts.append({"source": performer["id"] + ":body_support",
                             "relation": "balances through feet on",
                             "target": "studio_floor:" + performer["id"] + "_support"})
    if ground["contact_points"]:
        entities.append(ground)
    return entities, contacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--api", default="http://127.0.0.1:8190")
    parser.add_argument("--font", type=Path, required=True)
    args = parser.parse_args()
    if urlparse(args.api).hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("only a local H3 API is allowed")
    spec = json.loads(args.spec.read_text())
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", spec.get("id", "")):
        parser.error("id must be a lowercase, hyphenated filename slug")
    if spec.get("reference_approved") is not True:
        parser.error("inspect the reference and set reference_approved before rendering")
    root = args.spec.resolve().parent
    reference = (root / spec["reference"]).resolve()
    if not reference.is_file() or not args.font.is_file():
        parser.error("reference and font must exist")
    fingerprint = hashlib.sha256(args.spec.read_bytes() + reference.read_bytes()).hexdigest()
    destination = root / spec["id"]
    destination.mkdir(exist_ok=True)
    lock = destination / "worker.lock"
    import fcntl
    with (root / ".render.lock").open("a") as series_handle, lock.open("a") as handle:
        fcntl.flock(series_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(args, spec, reference, destination, fingerprint)


def run(args, spec, reference, out, fingerprint):
    receipt_path = out / "receipt.json"
    intent_path = out / "submission-intent.json"
    session = requests.Session()
    session.trust_env = False
    base = args.api.rstrip("/")
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["fingerprint"] != fingerprint:
            raise SystemExit("Input changed after submission; preserve this version and create a new one.")
        job_id = receipt["id"]
    else:
        if intent_path.exists():
            raise SystemExit("Unresolved submission intent: inspect the server job list before any resubmission.")
        memory = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        kib = lambda key: int(memory[key].split()[0])
        if kib("MemAvailable") < 24 * 1024**2:
            raise SystemExit("Less than 24 GiB available RAM; no submission.")
        if kib("SwapTotal") and (kib("SwapTotal") - kib("SwapFree")) / kib("SwapTotal") > .75:
            raise SystemExit("Swap exceeds 75%; no submission.")
        with reference.open("rb") as source:
            upload = session.post(base + "/api/uploads?kind=image", files={"file": source}, timeout=120)
        upload.raise_for_status()
        uploaded = upload.json()
        save(out / "upload.json", uploaded)
        token = uploaded["token"]
        entities, contacts = with_supports(spec)
        motions = []
        for entity in entities:
            if entity["kind"] not in {"character", "creature", "robot"}:
                continue
            for kind, description in [
                ("body_balance", "Natural posture and limb movement supporting the described sticker action."),
                ("blink_or_head_reaction", "Small motivated eye and head reactions matching the emotion."),
                ("secondary_response", "Clothing or articulated body details respond gently to the action.")]:
                motions.append({"entity": entity["id"], "kind": kind, "description": description})
        request = {"mode": "i2v", "profile": "quality_int8_offload", "width": 512,
                   "height": 512, "duration": 5, "seed": spec["seed"],
                   "first_frame": token, "last_frame": token, "audio_intent": "ambient", "dialogue": [],
                   "prompt": spec["action"] + " Exact reference identity and clothing, tactile cute 3D figurines. "
                   "Locked camera, plain white background. Clear expressive character action, not camera wobble. "
                   "All heads and hands remain visible. Settle back into the starting pose for a gentle loop. "
                   "No text or subtitles. Quiet movement sounds only, no speech.",
                   "physical_contract": {"entities": entities, "contacts": contacts,
                                         "motions": motions}}
        save(out / "request.json", request)
        # An ambiguous POST must never be silently repeated after a restart.
        save(intent_path, {"fingerprint": fingerprint, "created": time.time()})
        response = session.post(base + "/api/renders", json=request, timeout=120)
        if response.status_code in {400, 422}:
            save(out / "rejected.json", {"status": response.status_code, "body": response.text})
        response.raise_for_status()
        receipt = response.json()
        receipt["fingerprint"] = fingerprint
        save(receipt_path, receipt)
        job_id = receipt["id"]
    print(json.dumps({"id": spec["id"], "job_id": job_id}), flush=True)
    deadline = time.monotonic() + 3600
    previous = None
    while time.monotonic() < deadline:
        response = session.get(base + "/api/jobs/" + job_id, timeout=30)
        response.raise_for_status()
        status = response.json()
        save(out / "status.json", status)
        state = status.get("status")
        if state != previous:
            print(json.dumps({"state": state, "progress": status.get("progress")}), flush=True)
            previous = state
        if state in {"failed", "cancelled", "canceled", "error"}:
            raise SystemExit("Render stopped; preserve the receipt and inspect status.json. No retry.")
        if state in {"completed", "succeeded", "done"}:
            break
        time.sleep(10)
    else:
        raise SystemExit("Monitoring timed out; rerun with the SAME spec to resume the same job.")
    video = out / (spec["id"] + ".mp4")
    if not video.exists():
        with session.get(base + f"/api/jobs/{job_id}/outputs/0?download=1", stream=True, timeout=120) as download:
            download.raise_for_status()
            part = video.with_suffix(".mp4.part")
            with part.open("wb") as file:
                for chunk in download.iter_content(1024 * 1024):
                    file.write(chunk)
            part.replace(video)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
    gif = out / (spec["id"] + ".gif")
    if not gif.exists():
        subprocess.run([sys.executable, str(Path(__file__).with_name("video_to_wechat_gif.py")),
                        str(video), str(gif), "--duration", "5.125", "--speed", "1.25",
                        "--fps", "15", "--label", spec["label"], "--font", str(args.font)], check=True)
    contact = out / "contact.jpg"
    if not contact.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                        "fps=2,scale=192:192,tile=5x2", "-frames:v", "1", str(contact)], check=True)
    save(out / "review-required.json", {"status": "needs_visual_review", "auto_rerender": False,
                                        "video": video.name, "gif": gif.name})
    print("Downloaded and packaged; visual review required: " + str(out), flush=True)


if __name__ == "__main__":
    main()
