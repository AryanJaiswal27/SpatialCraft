import os
import sys
import time
import json
import urllib.request
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

try:
    import pyautogui
    import pyperclip
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None
    pyperclip = None

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

CONFIG_PATH = ROOT_DIR / "physical_clicks_config.json"
BASE_URL = "http://localhost:8000"

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def copy_image_to_clipboard(image_path: Path) -> bool:
    """Copies image file directly to the Windows clipboard for instant Ctrl+V paste."""
    if not image_path.exists():
        print(f"[PHYSICAL // ERROR] Image file not found: {image_path}")
        return False

    abs_path = str(image_path.resolve())
    ps_cmd = f"""
    Add-Type -AssemblyName System.Windows.Forms;
    [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{abs_path}'));
    """
    try:
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[PHYSICAL] Image copied to Windows clipboard: {image_path.name}")
            return True
        else:
            print(f"[PHYSICAL // ERROR] PowerShell SetImage error: {res.stderr}")
            return False
    except Exception as e:
        print(f"[PHYSICAL // ERROR] Failed copying image to clipboard: {e}")
        return False

def copy_text_to_clipboard(text: str) -> bool:
    try:
        if pyperclip:
            pyperclip.copy(text)
            if pyperclip.paste().strip():
                return True
    except Exception:
        pass
    try:
        p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
        p.communicate(text.encode("utf-8"))
        return True
    except Exception:
        pass
    return False

def get_clipboard_text() -> str:
    if pyperclip:
        try:
            return pyperclip.paste()
        except Exception:
            pass
    try:
        return subprocess.check_output(["powershell", "-Command", "Get-Clipboard"], text=True)
    except Exception:
        return ""

def physical_paste():
    """Simulates realistic physical Ctrl+V with hold times so rich-text chat composers register the keystroke."""
    time.sleep(0.12)
    pyautogui.keyDown("ctrl")
    time.sleep(0.14)
    pyautogui.press("v")
    time.sleep(0.14)
    pyautogui.keyUp("ctrl")
    time.sleep(0.25)

def focus_browser_tab(targets: dict, move_dur: float = 0.4, settle: float = 0.3):
    tab_pos = targets.get("browser_tab")
    if tab_pos and pyautogui:
        print(f"[PHYSICAL] Clicking Browser Tab to focus window: ({tab_pos['x']}, {tab_pos['y']})...")
        pyautogui.moveTo(tab_pos["x"], tab_pos["y"], duration=move_dur)
        pyautogui.click()
        time.sleep(settle + 0.3)

def focus_antigravity_window(targets: dict, delays: dict):
    """Brings the Antigravity IDE window to the foreground by clicking its top header/tab."""
    ag_head = targets.get("antigravity_header")
    if ag_head and (ag_head.get("x", 0) > 0 or ag_head.get("y", 0) > 0) and pyautogui:
        move_dur = delays.get("move_duration", 0.4)
        settle = delays.get("click_settle", 0.3)
        print(f"[PHYSICAL] Clicking Antigravity Top Header: ({ag_head['x']}, {ag_head['y']}) to bring IDE to front...")
        pyautogui.moveTo(ag_head["x"], ag_head["y"], duration=move_dur)
        pyautogui.click()
        time.sleep(settle + 0.3)

def paste_to_antigravity_ide(text: str, targets: dict, delays: dict, label: str = "") -> bool:
    """
    Pastes the extracted LLM web response directly into the Antigravity IDE chat composer,
    and presses Enter to submit it into this active IDE conversation.
    """
    ide_chat_pos = targets.get("ide_chat_box")
    if not ide_chat_pos or not ide_chat_pos.get("x") or not pyautogui:
        print(f"[PHYSICAL] Target 6 (ide_chat_box) not calibrated - skipping paste into Antigravity IDE.")
        print(f"           (Run calibrate_antigravity.bat to calibrate the IDE chat composer)")
        return False

    move_dur = delays.get("move_duration", 0.4)
    settle = delays.get("click_settle", 0.3)

    print("\n" + "=" * 65)
    print(f" [PHYSICAL -> ANTIGRAVITY IDE] Dispatching Web Response to IDE Chat...")
    if label:
        print(f"  Context: {label}")
    print("=" * 65)

    # 1. Bring Antigravity IDE to the top first!
    focus_antigravity_window(targets, delays)

    # 2. Ensure clipboard has the response text
    copy_text_to_clipboard(text)
    time.sleep(0.15)

    # 3. Click to focus Antigravity IDE Chat input box at the bottom
    x, y = ide_chat_pos["x"], ide_chat_pos["y"]
    print(f"[PHYSICAL] Clicking Antigravity IDE Chat Box: ({x}, {y})...")
    pyautogui.moveTo(x, y, duration=move_dur)
    pyautogui.click()
    time.sleep(settle + 0.2)

    # 4. Select all (Ctrl+A) so any leftover draft text is replaced cleanly
    pyautogui.keyDown("ctrl")
    pyautogui.press("a")
    pyautogui.keyUp("ctrl")
    time.sleep(0.1)

    # 5. Paste via Ctrl+V
    print(f"[PHYSICAL] Pasting response ({len(text)} chars) into IDE composer...")
    physical_paste()
    time.sleep(0.3)

    # 6. Submit via Enter
    print("[PHYSICAL] Pressing [ENTER] to submit message to Antigravity AI...")
    pyautogui.press("enter")
    time.sleep(1.0)
    print("[PHYSICAL -> ANTIGRAVITY IDE] Successfully posted web response into Antigravity IDE!\n")
    return True

def paste_and_send(prompt_text: str, image_path: Optional[Path], targets: dict, delays: dict) -> bool:
    """
    Performs the physical click sequence:
    1. Focuses the prompt input box cleanly when empty.
    2. Pastes the CAD text prompt FIRST (guaranteed text injection into textarea).
    3. Pastes the image SECOND (attaches without thumbnail collision or focus loss).
    4. Waits for image attachment to settle, then clicks Send.
    """
    if not pyautogui:
        return False

    move_dur = delays.get("move_duration", 0.4)
    settle = delays.get("click_settle", 0.3)
    prompt_pos = targets.get("prompt_box")
    send_pos = targets.get("send_button")

    if not prompt_pos or not send_pos:
        print("[PHYSICAL // ERROR] Missing prompt_box or send_button calibration coordinates!")
        return False

    # 1. Focus the clean, empty prompt composer
    print(f"[PHYSICAL] Clicking Prompt Input Box: ({prompt_pos['x']}, {prompt_pos['y']})...")
    pyautogui.moveTo(prompt_pos["x"], prompt_pos["y"], duration=move_dur)
    pyautogui.click()
    time.sleep(settle + 0.2)

    # 2. Paste the Text Prompt FIRST
    print(f"[PHYSICAL] Loading text prompt to clipboard ({len(prompt_text)} chars)...")
    copy_text_to_clipboard(prompt_text)
    time.sleep(0.15)
    print("[PHYSICAL] Pasting prompt text via Ctrl+V...")
    physical_paste()
    time.sleep(settle + 0.3)

    # 3. Paste Image SECOND if provided
    if image_path and image_path.exists():
        print(f"[PHYSICAL] Loading image to clipboard: {image_path.name}...")
        if copy_image_to_clipboard(image_path):
            time.sleep(0.2)
            # Notice: Cursor is already inside the active composer; do not click on potential thumbnails!
            print("[PHYSICAL] Pasting image attachment via Ctrl+V...")
            physical_paste()
            img_settle = delays.get("image_upload_settle", 3.5)
            print(f"[PHYSICAL] Waiting {img_settle}s for image to attach...")
            time.sleep(img_settle)

    # 4. Click Send Button
    print(f"[PHYSICAL] Clicking Send Button: ({send_pos['x']}, {send_pos['y']})...")
    pyautogui.moveTo(send_pos["x"], send_pos["y"], duration=move_dur)
    pyautogui.click()
    time.sleep(settle)

    # Fallback Enter key
    time.sleep(0.2)
    pyautogui.press("enter")
    return True

def wait_and_extract_response(targets: dict, delays: dict) -> str:
    """
    Waits for LLM generation with:
    - 2-minute (120s) generation timeout.
    - Continuous downward scrolling (pyautogui.scroll + End key) to keep generating tokens in view.
    - Periodic 'Ctrl+A' page inspection trick to track live streaming progress and extract CAD JSON.
    - Dynamic completion guard checking balanced JSON braces and response stability.
    """
    if not pyautogui:
        return ""

    from backend.services.browser_prompt import parse_llm_json_response

    move_dur = delays.get("move_duration", 0.4)
    gen_timeout = delays.get("llm_generation_timeout", 120.0)
    copy_pos = targets.get("copy_button")
    prompt_pos = targets.get("prompt_box")

    # Viewport coordinates for scrolling and page content
    scroll_x = prompt_pos["x"] if prompt_pos else 960
    scroll_y = max(120, (prompt_pos["y"] - 280)) if prompt_pos else 500

    print(f"\n[PHYSICAL] Monitoring LLM generation (2-min timeout: {int(gen_timeout)}s)...")
    print(f"[PHYSICAL] Auto-scrolling active at ({scroll_x}, {scroll_y}) with Ctrl+A streaming inspection...")
    start_time = time.time()
    
    # Initial buffer for generation to start
    time.sleep(3.5)

    last_len = 0
    stable_count = 0

    while (time.time() - start_time) < gen_timeout:
        elapsed = time.time() - start_time

        # 1. Continuous scroll down to track streaming tokens and keep copy button in view
        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.1)
            pyautogui.scroll(-450)
            pyautogui.press("end")
        except Exception:
            pass

        time.sleep(0.25)

        # 2. Check Copy button if calibrated
        if copy_pos:
            try:
                pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=move_dur)
                pyautogui.click()
                time.sleep(0.4)
                clip_text = get_clipboard_text()
                
                # Check if complete JSON is present
                if clip_text and "{" in clip_text and "}" in clip_text:
                    if any(k in clip_text for k in ("room", "dimensions", "objects", "name", "category")):
                        # Verify code fence closed or balanced braces
                        if clip_text.count("{") <= clip_text.count("}"):
                            print(f"[PHYSICAL // GENERATION COMPLETE] Captured finished response via Copy button ({len(clip_text)} chars)!")
                            return clip_text
            except Exception:
                pass

        # 3. Ctrl+A page snapshot trick to inspect streaming progress
        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.1)
            pyautogui.click()
            time.sleep(0.08)
            pyautogui.keyDown("ctrl")
            pyautogui.press("a")
            pyautogui.keyUp("ctrl")
            time.sleep(0.08)
            pyautogui.keyDown("ctrl")
            pyautogui.press("c")
            pyautogui.keyUp("ctrl")
            time.sleep(0.08)
            pyautogui.press("escape")  # Instantly dismiss highlight
            time.sleep(0.1)

            page_text = get_clipboard_text()
            if page_text:
                cur_len = len(page_text)
                if cur_len > last_len:
                    delta = cur_len - last_len
                    print(f"[PHYSICAL // STREAMING] +{delta} chars ({cur_len} total) | Scrolling down... [{int(elapsed)}s/{int(gen_timeout)}s]")
                    last_len = cur_len
                    stable_count = 0
                elif cur_len == last_len and cur_len > 150:
                    stable_count += 1
                    print(f"[PHYSICAL // STREAMING] Generation steady ({stable_count * 2.5:.0f}s unchanged) [{int(elapsed)}s/{int(gen_timeout)}s]")

                # If text has stopped changing for ~5 seconds (2 cycles) and contains a complete room/object CAD model:
                if stable_count >= 2:
                    parsed = parse_llm_json_response(page_text)
                    if parsed and any(k in parsed for k in ("room", "objects", "dimensions", "name")):
                        print(f"[PHYSICAL // GENERATION COMPLETE] Detected finished CAD response via Ctrl+A inspection ({cur_len} chars)!")
                        # Try one final click on copy button since we scrolled to the end
                        if copy_pos:
                            pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=move_dur)
                            pyautogui.click()
                            time.sleep(0.5)
                            final_clip = get_clipboard_text()
                            if final_clip and "{" in final_clip and "}" in final_clip and final_clip.count("{") <= final_clip.count("}"):
                                return final_clip
                        # Fallback: format parsed JSON nicely
                        return json.dumps(parsed, indent=2)
        except Exception:
            pass

        time.sleep(1.8)

    # Final attempt fallback after 120s timeout
    print("[PHYSICAL // TIMEOUT] 2-minute timeout reached. Attempting final extraction...")
    if copy_pos:
        try:
            pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=move_dur)
            pyautogui.click()
            time.sleep(0.8)
            final_text = get_clipboard_text()
            if final_text:
                return final_text
        except Exception:
            pass

    return ""

def execute_initial_reconstruction(image_path: Path, scene_id: str) -> Optional[dict]:
    """Phase 1: Prompts open browser to construct the full 3D room."""
    from backend.services.browser_prompt import generate_spatial_prompt
    cfg = load_config()
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})

    print(f"\n[PHYSICAL // PHASE 1] Starting Initial 3D Reconstruction for {scene_id}...")
    focus_browser_tab(targets)

    prompt = generate_spatial_prompt()
    if not paste_and_send(prompt, image_path, targets, delays):
        return None

    raw_output = wait_and_extract_response(targets, delays)
    if not raw_output:
        print("[PHYSICAL // ERROR] No output extracted from browser.")
        return None

    # Step 1: Dispatch to Antigravity IDE Chat Composer if calibrated
    paste_to_antigravity_ide(raw_output, targets, delays, label=f"Initial Room CAD Reconstruction ({scene_id})")

    print(f"[PHYSICAL] Extracted initial output ({len(raw_output)} chars). Ingesting to SpatialCraft...")
    try:
        req_data = json.dumps({
            "raw_text": raw_output,
            "image_url": f"/api/uploads/{image_path.name}"
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/scene/{scene_id}/submit_raw_output",
            data=req_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            scene_data = json.loads(resp.read().decode("utf-8"))
            print(f"[PHYSICAL // SUCCESS] Scene {scene_id} created with {len(scene_data.get('objects', []))} objects!")
            return scene_data
    except Exception as e:
        print(f"[PHYSICAL // ERROR] Ingesting initial reconstruction: {e}")
        return None

from backend.services.antigravity_prompter import generate_antigravity_object_prompt, build_antigravity_scene_refinement_plan

def generate_object_refinement_prompt(obj: dict, scene_data: Optional[dict] = None, step_idx: int = 1, total_steps: int = 1) -> str:
    """Delegates prompt generation to the Antigravity CAD Intelligence engine."""
    return generate_antigravity_object_prompt(obj, scene=scene_data, step_idx=step_idx, total_steps=total_steps)

def parse_refinement_json(raw_text: str) -> Optional[dict]:
    import re
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass
    brace = re.search(r"(\{[\s\S]*\})", raw_text)
    if brace:
        try:
            return json.loads(brace.group(1).strip())
        except Exception:
            pass
    return None

def execute_object_refinement(scene_id: str, obj: dict, scene_data: Optional[dict] = None, step_idx: int = 1, total_steps: int = 1) -> bool:
    """Phase 2: Refines an individual object using Antigravity's tailored prompt and 2D crop."""
    crop_url = obj.get("crop_url")
    if not crop_url:
        print(f"[PHYSICAL // SKIP] Object {obj.get('id')} has no cropped image.")
        return False

    crop_name = Path(crop_url).name
    crop_path = ROOT_DIR / "backend" / "storage" / "crops" / crop_name
    if not crop_path.exists():
        crop_path = ROOT_DIR / "storage" / "crops" / crop_name

    if not crop_path.exists():
        print(f"[PHYSICAL // SKIP] Crop file not found on disk: {crop_name}")
        return False

    cfg = load_config()
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})

    print(f"\n" + "=" * 65)
    print(f" [ANTIGRAVITY // CAD AGENT] Step {step_idx}/{total_steps}: Analyzing '{obj.get('name')}'")
    print("=" * 65)
    focus_browser_tab(targets)

    # Antigravity generates tailored prompt for this specific object
    refine_prompt = generate_antigravity_object_prompt(obj, scene=scene_data, step_idx=step_idx, total_steps=total_steps)
    print(f"[ANTIGRAVITY] Generated {len(refine_prompt)} chars tailored prompt for {obj.get('name')}.")
    print(f"[PHYSICAL] Pasting image crop ({crop_path.name}) + Antigravity prompt to browser...")

    if not paste_and_send(refine_prompt, crop_path, targets, delays):
        return False

    raw_output = wait_and_extract_response(targets, delays)
    if not raw_output:
        print(f"[PHYSICAL // WARN] Could not extract refinement output for {obj.get('id')}")
        return False

    # Dispatch to Antigravity IDE Chat Composer if calibrated
    paste_to_antigravity_ide(raw_output, targets, delays, label=f"Refinement Step {step_idx}/{total_steps} for '{obj.get('name')}'")

    parsed = parse_refinement_json(raw_output)
    if not parsed:
        print(f"[PHYSICAL // WARN] Could not parse refined JSON for {obj.get('id')}")
        return False

    # Apply update to object in SpatialCraft
    update_payload = {}
    if "dimensions" in parsed:
        update_payload["dimensions"] = parsed["dimensions"]
    if "color" in parsed:
        update_payload["color"] = parsed["color"]
    if "description" in parsed:
        update_payload["description"] = parsed["description"]

    try:
        put_data = json.dumps(update_payload).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/scene/{scene_id}/object/{obj.get('id')}",
            data=put_data,
            headers={"Content-Type": "application/json"},
            method="PUT"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[ANTIGRAVITY // SUCCESS] Object '{obj.get('name')}' refined in 3D scene! (Status: {resp.status})")
            return True
    except Exception as e:
        print(f"[PHYSICAL // ERROR] Updating refined object: {e}")
        return False

def run_full_scene_refinement_loop(scene_id: str, max_items: Optional[int] = None):
    """
    Antigravity iterates one-by-one through each object in the scene,
    generates a tailored prompt for each, and drives refinement
    until all objects are completed.
    """
    print("\n" + "=" * 65)
    print(f" [ANTIGRAVITY REFINEMENT LOOP] Starting Object-by-Object CAD Refinement for {scene_id}")
    print("=" * 65)

    try:
        req = urllib.request.Request(f"{BASE_URL}/api/scene/{scene_id}")
        with urllib.request.urlopen(req, timeout=8) as resp:
            scene_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ANTIGRAVITY // ERROR] Could not fetch scene {scene_id}: {e}")
        return

    # Use Antigravity's prioritized architectural plan
    plan = build_antigravity_scene_refinement_plan(scene_data)
    candidates = [step for step in plan if step.get("crop_url")]
    
    if max_items is not None and max_items > 0:
        total_to_process = min(len(candidates), max_items)
    else:
        # Refine ALL objects in the scene!
        total_to_process = len(candidates)

    print(f"[ANTIGRAVITY] Plan assembled: {len(plan)} total items, {len(candidates)} have crops. Refining ALL {total_to_process} objects...")

    refined_count = 0
    objects_by_id = {o["id"]: o for o in scene_data.get("objects", [])}

    for idx, step in enumerate(candidates[:total_to_process], 1):
        obj_id = step["object_id"]
        obj = objects_by_id.get(obj_id)
        if not obj:
            continue

        success = execute_object_refinement(
            scene_id=scene_id,
            obj=obj,
            scene_data=scene_data,
            step_idx=idx,
            total_steps=total_to_process
        )
        if success:
            refined_count += 1
        time.sleep(2.0)

    print("\n" + "=" * 65)
    print(f" [ANTIGRAVITY COMPLETE] Successfully refined all {refined_count}/{total_to_process} objects in scene {scene_id}!")
    print("=" * 65)

def run_physical_daemon():
    """
    Standing desktop daemon that runs on the user's interactive monitor.
    Polls /api/physical_clicks/queue for incoming jobs triggered by phone/web/watcher.
    """
    print("=" * 65)
    print("      SPATIALCRAFT // PHYSICAL CLICK & REFINEMENT DAEMON")
    print("=" * 65)
    print("Monitoring incoming capture and refinement requests...")
    print("Ready to paste into your open browser and refine models.")
    print("Press Ctrl+C to terminate.\n")

    while True:
        try:
            poll_req = urllib.request.Request(f"{BASE_URL}/api/physical_clicks/queue/poll")
            with urllib.request.urlopen(poll_req, timeout=5) as resp:
                if resp.status == 200:
                    job = json.loads(resp.read().decode("utf-8"))
                    if job and job.get("job_id"):
                        job_id = job["job_id"]
                        job_type = job.get("job_type", "initial_reconstruction")
                        scene_id = job.get("scene_id", f"scene_{int(time.time())}")
                        image_path_str = job.get("image_path")
                        image_path = Path(image_path_str) if image_path_str else None

                        print(f"\n[DAEMON // JOB RECEIVED] Type: {job_type} | ID: {job_id} | Scene: {scene_id}")

                        if job_type == "initial_reconstruction" and image_path:
                            # 1. Run initial room reconstruction
                            scene_result = execute_initial_reconstruction(image_path, scene_id)
                            # 2. Automatically kick off the refinement loop for ALL objects!
                            if scene_result:
                                print(f"\n[ANTIGRAVITY // PIPELINE] Ingested initial room. Beginning sequential refinement across ALL objects...")
                                run_full_scene_refinement_loop(scene_id, max_items=None)

                        elif job_type == "refine_loop":
                            run_full_scene_refinement_loop(scene_id, max_items=job.get("max_items"))

                        elif job_type == "refine_single":
                            obj = job.get("object_data", {})
                            execute_object_refinement(scene_id, obj)

                        elif job_type == "test_hover":
                            target_key = job.get("target_key")
                            coords = job.get("coords")
                            if not coords and target_key:
                                cfg = load_config()
                                coords = cfg.get("targets", {}).get(target_key)
                            if coords and pyautogui:
                                x, y = coords["x"], coords["y"]
                                print(f"\n[DAEMON // TEST HOVER] Moving cursor to {target_key or 'target'}: X={x}, Y={y}...")
                                pyautogui.moveTo(x, y, duration=0.6)
                                pyautogui.moveRel(4, 0, duration=0.1)
                                pyautogui.moveRel(-8, 0, duration=0.1)
                                pyautogui.moveRel(4, 0, duration=0.1)

                        # Acknowledge job completion
                        ack_data = json.dumps({"job_id": job_id, "status": "completed"}).encode("utf-8")
                        ack_req = urllib.request.Request(
                            f"{BASE_URL}/api/physical_clicks/queue/{job_id}/complete",
                            data=ack_data,
                            headers={"Content-Type": "application/json"}
                        )
                        urllib.request.urlopen(ack_req, timeout=5)

        except urllib.error.URLError:
            pass # Backend starting up
        except Exception as e:
            print(f"[DAEMON POLL ERROR] {e}")

        time.sleep(1.5)

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        run_physical_daemon()
    else:
        # Direct CLI status
        cfg = load_config()
        targets = cfg.get("targets", {})
        print(f"SpatialCraft Physical Clicker ready. Loaded {len(targets)} calibrated targets.")
        for k, v in targets.items():
            print(f"  - {v.get('name', k):28s} : X = {v.get('x')}, Y = {v.get('y')}")
        print("\nTo start the standing desktop listener, run:")
        print("  .\\run_physical_daemon.bat  (or python scripts/physical_clicker.py --daemon)")
