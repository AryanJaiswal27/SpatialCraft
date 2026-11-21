"""
SpatialCraft // Antigravity Loop CLI
Inspects scenes object-by-object and runs the Antigravity CAD prompt generation loop.
"""

import sys
import json
import urllib.request
import argparse
from pathlib import Path

# Force unbuffered stdout
sys.stdout.reconfigure(line_buffering=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_URL = "http://localhost:8000"

def get_latest_scene_id() -> str:
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/scenes")
        with urllib.request.urlopen(req, timeout=5) as resp:
            scenes = json.loads(resp.read().decode("utf-8"))
            if scenes:
                return scenes[0]["scene_id"]
    except Exception as e:
        print(f"[ERROR] Could not fetch scenes: {e}")
    return "scene_1ac6c4e9"

def run_antigravity_inspection(scene_id: str, dry_run: bool = False, execute: bool = False):
    print("=" * 70)
    print("      SPATIALCRAFT // ANTIGRAVITY CAD INTELLIGENCE LOOP")
    print("=" * 70)
    print(f"Target Scene ID: {scene_id}")

    try:
        req = urllib.request.Request(f"{BASE_URL}/api/scene/{scene_id}/antigravity_plan")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not retrieve Antigravity plan for {scene_id}: {e}")
        return

    plan = data.get("plan", [])
    total = len(plan)
    print(f"\n[ANTIGRAVITY] Scene contains {total} objects arranged by structural hierarchy.\n")

    for step in plan:
        idx = step["step"]
        obj_name = step["object_name"]
        cat = step["category"]
        crop = step.get("crop_url") or "None"
        prompt = step["antigravity_prompt"]

        print(f"----------------------------------------------------------------------")
        print(f" [{idx:02d}/{total:02d}] OBJECT: {obj_name.upper()} (Category: {cat})")
        print(f"       Crop URL: {crop}")
        print(f"----------------------------------------------------------------------")
        print(f"  >> Antigravity CAD Directives Preview:")
        for line in prompt.splitlines()[:16]:
            print(f"     {line}")
        print(f"     ... ({len(prompt)} total characters)")
        print()

    if execute:
        print("\n[ANTIGRAVITY] Initiating physical desktop refinement loop...")
        try:
            req_data = json.dumps({"max_items": total}).encode("utf-8")
            post_req = urllib.request.Request(
                f"{BASE_URL}/api/scene/{scene_id}/refine",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(post_req, timeout=8) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                print(f"[ANTIGRAVITY // QUEUED] Refinement job {res.get('job_id')} added to queue!")
        except Exception as e:
            print(f"[ERROR] Triggering refinement: {e}")
    else:
        print("Run with '--execute' to enqueue physical mouse clicks on desktop daemon,")
        print("or run 'run_physical_daemon.bat' to keep listening for smartphone uploads.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity CAD Object Refinement Loop")
    parser.add_argument("--scene", type=str, help="Scene ID to inspect (default: latest)")
    parser.add_argument("--execute", action="store_true", help="Enqueue physical click refinement loop")
    parser.add_argument("--dry-run", action="store_true", help="Only preview Antigravity prompts without executing")
    args = parser.parse_args()

    scene_id = args.scene or get_latest_scene_id()
    run_antigravity_inspection(scene_id, dry_run=args.dry_run, execute=args.execute)
