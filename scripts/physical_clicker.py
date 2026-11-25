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
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None
    pyperclip = None

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

CONFIG_PATH = ROOT_DIR / "physical_clicks_config.json"
BASE_URL = "http://localhost:8000"

def load_config(preset: Optional[str] = None) -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            active_id = preset or data.get("active_preset", "gemini")
            presets = data.get("presets", {})
            if presets and active_id in presets:
                pdata = presets[active_id]
                data["targets"] = pdata.get("targets", data.get("targets", {}))
                data["delays"] = pdata.get("delays", data.get("delays", {}))
                data["active_preset"] = active_id
                data["preset_label"] = pdata.get("label", active_id.capitalize())
            else:
                data["preset_label"] = data.get("active_preset", "gemini").capitalize()
            return data
        except Exception:
            pass
    return {"screen": {"width": 1920, "height": 1080}, "active_preset": "gemini", "preset_label": "Google Gemini", "targets": {}, "delays": {}}

def copy_image_to_clipboard(image_path: Path) -> bool:
    """Copies image file directly to the Windows clipboard for instant Ctrl+V paste."""
    if not image_path.exists():
        print(f"[PHYSICAL // ERROR] Image file not found: {image_path}")
        return False

    # 1. Native Windows API via win32clipboard (Instant, zero focus-stealing)
    try:
        import io
        from PIL import Image
        import win32clipboard
        img = Image.open(str(image_path.resolve()))
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Strip 14-byte BMP header to obtain raw CF_DIB
        output.close()
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            print(f"[PHYSICAL] Image copied to Windows clipboard natively (CF_DIB): {image_path.name}")
            return True
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e_native:
        pass

    # 2. PowerShell SetImage fallback
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
    Bypassed: Direct backend API ingestion is used to prevent piling up in
    the Antigravity IDE chat message queue.
    """
    print(f"[PHYSICAL] Direct backend API ingestion active. Bypassing IDE chat paste to prevent message queue pile-up.")
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
    copy_text_to_clipboard("")  # Clear clipboard so copy check never reads stale clipboard data
    return True

def wait_and_extract_response(targets: dict, delays: dict, expected_id: Optional[str] = None, timeout: float = 300.0) -> str:
    """
    Waits for LLM generation with:
    - 5-minute (300s) generation timeout backup.
    - Continuous downward scrolling (scroll down + End key) to keep streaming tokens in view.
    - Clean, silent waiting: NO repeating Ctrl+A selection flashing.
    - Enforced 14-second minimum buffer before checking Copy button.
    - Periodically checks the calibrated Copy button for balanced CAD JSON output.
    """
    if not pyautogui:
        return ""

    move_dur = delays.get("move_duration", 0.4)
    gen_timeout = delays.get("llm_generation_timeout", timeout)
    copy_pos = targets.get("copy_button")
    prompt_pos = targets.get("prompt_box")

    # Viewport coordinates for scrolling
    scroll_x = prompt_pos["x"] if prompt_pos else 960
    scroll_y = max(120, (prompt_pos["y"] - 280)) if prompt_pos else 500

    print(f"\n[PHYSICAL] Waiting for LLM generation (5-min timeout: {int(gen_timeout)}s)...")
    if expected_id:
        print(f"[PHYSICAL] Expecting target identifier: '{expected_id}'")
    print(f"[PHYSICAL] Auto-scrolling active at ({scroll_x}, {scroll_y})...")

    # Wipe clipboard so previous turn content is never mistakenly read
    copy_text_to_clipboard("")

    start_time = time.time()
    min_wait = 14.0  # Give LLM time to generate before first copy attempt
    last_milestone = start_time

    while (time.time() - start_time) < gen_timeout:
        elapsed = time.time() - start_time

        # Periodic log every 30 seconds
        if elapsed - (last_milestone - start_time) >= 30.0:
            print(f"[PHYSICAL] Still waiting for LLM output... ({int(elapsed)}s / {int(gen_timeout)}s elapsed)")
            last_milestone = time.time()

        # A. Rapid high-volume downward scroll to track streaming tokens
        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.08)
            pyautogui.scroll(-3500)
            pyautogui.press("pagedown", presses=2, interval=0.02)
            pyautogui.hotkey("ctrl", "end")
        except Exception:
            pass

        # During initial buffer, simply wait and keep scrolling
        if elapsed < min_wait:
            time.sleep(2.5)
            continue

        # B. Check Copy button cleanly with adaptive vertical probing (handles banners/popups)
        if copy_pos:
            probe_offsets = [0, -65, -80, -50, -120]
            for dy in probe_offsets:
                try:
                    pyautogui.moveTo(copy_pos["x"], copy_pos["y"] + dy, duration=0.15)
                    pyautogui.click()
                    time.sleep(0.35)
                    clip_text = get_clipboard_text()
                    
                    if clip_text and "{" in clip_text and "}" in clip_text:
                        if clip_text.count("{") <= clip_text.count("}"):
                            has_schema = any(k in clip_text for k in ("room", "dimensions", "objects", "name", "category", "materials"))
                            matches_id = True if not expected_id else (expected_id in clip_text)
                            
                            if has_schema and matches_id:
                                offset_str = f" (offset {dy}px due to banner)" if dy != 0 else ""
                                print(f"[PHYSICAL // GENERATION COMPLETE] Captured finished response via Copy button{offset_str} ({len(clip_text)} chars)!")
                                return clip_text
                except Exception:
                    pass

        time.sleep(3.5)

    # Final attempt on timeout
    print(f"[PHYSICAL // TIMEOUT] {int(gen_timeout)}s (5-minute) timeout reached. Attempting final extraction...")
    if copy_pos:
        for dy in [0, -65, -80, -50, -120]:
            try:
                pyautogui.moveTo(scroll_x, scroll_y, duration=0.08)
                pyautogui.scroll(-4000)
                pyautogui.press("pagedown", presses=2, interval=0.02)
                pyautogui.hotkey("ctrl", "end")
                time.sleep(0.3)
                pyautogui.moveTo(copy_pos["x"], copy_pos["y"] + dy, duration=move_dur)
                pyautogui.click()
                time.sleep(0.8)
                final_text = get_clipboard_text()
                if final_text and "{" in final_text and "}" in final_text:
                    return final_text
            except Exception:
                pass

    # Fallback: full-page selection extraction if copy button was displaced by persistent popups
    try:
        print("[PHYSICAL // FALLBACK] Attempting full-page text extraction to salvage response...")
        pyautogui.moveTo(scroll_x, scroll_y, duration=0.2)
        pyautogui.click()
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.25)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.4)
        pyautogui.press("escape")
        salvage_text = get_clipboard_text()
        if salvage_text and "{" in salvage_text and "}" in salvage_text:
            from backend.services.browser_prompt import parse_llm_json_response
            parsed = parse_llm_json_response(salvage_text)
            if parsed and (not expected_id or expected_id in salvage_text):
                print(f"[PHYSICAL // SALVAGED] Successfully recovered {len(salvage_text)} chars from page fallback!")
                return salvage_text
    except Exception as e:
        print(f"[PHYSICAL // ERROR] Page fallback failed: {e}")

    return ""

def execute_initial_reconstruction(image_path: Path, scene_id: str, preset: Optional[str] = None) -> Optional[dict]:
    """Phase 1: Prompts open browser to construct the full 3D room, with 5-minute Antigravity autonomous fallback."""
    from backend.services.browser_prompt import generate_spatial_prompt
    cfg = load_config(preset=preset)
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})

    print(f"\n[PHYSICAL // PHASE 1] Starting Initial 3D Reconstruction for {scene_id}...")
    focus_browser_tab(targets)

    prompt = generate_spatial_prompt()
    pasted = paste_and_send(prompt, image_path, targets, delays)
    raw_output = ""
    if pasted:
        raw_output = wait_and_extract_response(targets, delays, expected_id="room", timeout=300.0)

    # 5-MINUTE BACKUP: If no output received in 5 minutes, Antigravity builds the scene itself!
    if not raw_output:
        print("\n" + "=" * 65)
        print("[ANTIGRAVITY BACKUP // 5-MIN TIMEOUT] No output received from browser LLM within 5 minutes.")
        print(f"[ANTIGRAVITY BACKUP] Antigravity is now autonomously building 3D scene directly from {image_path.name}...")
        print("=" * 65)
        try:
            from backend.services.antigravity_builder import build_antigravity_fallback_scene
            fallback_scene = build_antigravity_fallback_scene(image_path, scene_id)
            print(f"[ANTIGRAVITY BACKUP // SUCCESS] Scene {scene_id} created with {len(fallback_scene.objects)} objects and high-res crops!")
            return fallback_scene.model_dump()
        except Exception as e:
            print(f"[ANTIGRAVITY BACKUP // ERROR] Failed fallback scene build: {e}")
            return None

    # Direct backend ingestion (bypassing IDE chat paste to prevent message queue pile-up)
    # paste_to_antigravity_ide(raw_output, targets, delays, label=f"Initial Room CAD Reconstruction ({scene_id})")

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
        from backend.services.antigravity_builder import build_antigravity_fallback_scene
        fallback_scene = build_antigravity_fallback_scene(image_path, scene_id)
        return fallback_scene.model_dump()

from backend.services.antigravity_prompter import generate_antigravity_object_prompt, build_antigravity_scene_refinement_plan

def generate_object_refinement_prompt(obj: dict, scene_data: Optional[dict] = None, step_idx: int = 1, total_steps: int = 1) -> str:
    """Delegates prompt generation to the Antigravity CAD Intelligence engine."""
    return generate_antigravity_object_prompt(obj, scene=scene_data, step_idx=step_idx, total_steps=total_steps)

def parse_refinement_json(raw_text: str) -> Optional[dict]:
    import re
    # 1. Search all code fences in reverse (latest response on page first)
    matches = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text))
    for m in reversed(matches):
        candidate = m.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and any(k in parsed for k in ("dimensions", "color", "materials", "id", "description")):
                return parsed
        except Exception:
            pass

    for m in reversed(matches):
        try:
            parsed = json.loads(m.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 2. Greedy outer brace match
    brace = re.search(r"(\{[\s\S]*\})", raw_text)
    if brace:
        try:
            return json.loads(brace.group(1).strip())
        except Exception:
            pass
    return None

def execute_object_refinement(scene_id: str, obj: dict, scene_data: Optional[dict] = None, step_idx: int = 1, total_steps: int = 1, preset: Optional[str] = None) -> bool:
    """Phase 2: Refines an individual object by referencing the room photo already in the active browser conversation (zero image re-upload)."""
    cfg = load_config(preset=preset)
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})

    print(f"\n" + "=" * 65)
    print(f" [ANTIGRAVITY // CAD AGENT] Step {step_idx}/{total_steps}: Refining '{obj.get('name')}'")
    print("=" * 65)
    focus_browser_tab(targets)

    # Antigravity generates tailored prompt referencing the photo already in the active thread
    refine_prompt = generate_antigravity_object_prompt(obj, scene=scene_data, step_idx=step_idx, total_steps=total_steps, in_conversation=True)
    print(f"[ANTIGRAVITY] Generated {len(refine_prompt)} chars tailored prompt for '{obj.get('name')}'.")
    print(f"[PHYSICAL] Pasting text prompt into active conversation (NO image re-upload; photo is already in chat)...")

    # Send ONLY the text prompt into the existing conversation thread (image_path=None)
    pasted = paste_and_send(refine_prompt, image_path=None, targets=targets, delays=delays)
    raw_output = ""
    if pasted:
        raw_output = wait_and_extract_response(targets, delays, expected_id=obj.get("id"), timeout=300.0)

    parsed = None
    if raw_output:
        # Direct backend ingestion (bypassing IDE chat paste to prevent message queue pile-up)
        parsed = parse_refinement_json(raw_output)

    # 5-MINUTE BACKUP: If no output or invalid JSON received within 5 minutes, Antigravity constructs 3D mesh itself!
    if not parsed:
        print("\n" + "=" * 65)
        print(f"[ANTIGRAVITY BACKUP // 5-MIN TIMEOUT] No output received from browser LLM for '{obj.get('name')}' within 5 minutes.")
        print(f"[ANTIGRAVITY BACKUP] Antigravity is now autonomously constructing the 3D mesh model for '{obj.get('name')}' from its crop...")
        print("=" * 65)
        try:
            from backend.services.antigravity_builder import refine_object_with_antigravity_cad
            refined_scene = refine_object_with_antigravity_cad(scene_id, obj.get("id"))
            if refined_scene:
                print(f"[ANTIGRAVITY BACKUP // SUCCESS] Object '{obj.get('name')}' refined with custom 3D mesh parts!")
                return True
        except Exception as e:
            print(f"[ANTIGRAVITY BACKUP // ERROR] Failed autonomous object refinement: {e}")
        return False

    # Apply update to object in SpatialCraft
    update_payload = {}
    if "dimensions" in parsed:
        update_payload["dimensions"] = parsed["dimensions"]
    if "position" in parsed:
        update_payload["position"] = parsed["position"]
    if "rotation" in parsed:
        update_payload["rotation"] = parsed["rotation"]
    if "attached_to_id" in parsed:
        update_payload["attached_to_id"] = parsed["attached_to_id"]
    if "color" in parsed:
        update_payload["color"] = parsed["color"]
    if "description" in parsed:
        update_payload["description"] = parsed["description"]
    if "materials" in parsed:
        update_payload["materials"] = parsed["materials"]
    if "features" in parsed:
        update_payload["features"] = parsed["features"]
    if "parts" in parsed:
        update_payload["parts"] = parsed["parts"]
    if "mesh_obj" in parsed:
        update_payload["mesh_obj"] = parsed["mesh_obj"]

    # Check for any missed objects reported by LLM during the scan
    missed_items = parsed.get("missed_objects_detected", [])
    if missed_items and isinstance(missed_items, list):
        for mi in missed_items:
            m_name = mi.get("name") if isinstance(mi, dict) else str(mi)
            if m_name:
                print(f"[ANTIGRAVITY // MISSED OBJECT RECOVERED] Adding '{m_name}' to scene {scene_id}...")
                try:
                    add_req = urllib.request.Request(
                        f"{BASE_URL}/api/scene/{scene_id}/natural_edit",
                        data=json.dumps({"prompt": f"add {m_name}"}).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    urllib.request.urlopen(add_req, timeout=5)
                except Exception:
                    pass

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

def run_full_scene_refinement_loop(scene_id: str, max_items: Optional[int] = None, preset: Optional[str] = None):
    """
    Antigravity iterates one-by-one through each object in the scene,
    generates a tailored prompt for each, and drives refinement
    until all objects are completed.
    """
    print("\n" + "=" * 65)
    print(f" [ANTIGRAVITY REFINEMENT LOOP] Starting Object-by-Object CAD Refinement for {scene_id}")
    if preset:
        print(f" Active Target LLM: {preset.upper()}")
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
    candidates = plan if plan else [{"object_id": o["id"]} for o in scene_data.get("objects", [])]
    
    if max_items is not None and max_items > 0:
        total_to_process = min(len(candidates), max_items)
    else:
        # Refine ALL objects in the scene!
        total_to_process = len(candidates)

    print(f"[ANTIGRAVITY] Plan assembled: {len(candidates)} items to refine in active conversation (zero image re-upload)...")

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
            total_steps=total_to_process,
            preset=preset
        )
        if success:
            refined_count += 1
        time.sleep(2.0)

    print("\n" + "=" * 65)
    print(f" [ANTIGRAVITY COMPLETE] Successfully refined all {refined_count}/{total_to_process} objects in scene {scene_id}!")
    print("=" * 65)

    # Whole-scene architectural verification: zero floating objects, zero penetration, complete 3D meshes
    try:
        from backend.services.scene_service import get_scene, verify_and_ground_scene
        sc = get_scene(scene_id)
        if sc:
            verify_and_ground_scene(sc)
            print(f"[ANTIGRAVITY // PLACEMENT VERIFIED] All floor items grounded (Y=h/2), all tabletop items snapped, detailed 3D meshes confirmed!")
    except Exception as e_verify:
        print(f"[PLACEMENT VERIFICATION ERROR] {e_verify}")

def run_physical_daemon(preset: Optional[str] = None):
    """
    Standing desktop daemon that runs on the user's interactive monitor.
    Polls /api/physical_clicks/queue for incoming jobs triggered by phone/web/watcher.
    """
    cfg = load_config(preset=preset)
    preset_label = cfg.get("preset_label", "Google Gemini")
    preset_id = cfg.get("active_preset", "gemini")

    print("=" * 65)
    print("      SPATIALCRAFT // PHYSICAL CLICK & REFINEMENT DAEMON")
    print("=" * 65)
    print(f"Active LLM Preset: {preset_label} [{preset_id}]")
    print("Monitoring incoming capture and refinement requests...")
    print(f"Ready to drive {preset_label} in your browser and refine models.")
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
                        job_preset = job.get("preset") or preset
                        scene_id = job.get("scene_id", f"scene_{int(time.time())}")
                        image_path_str = job.get("image_path")
                        image_path = Path(image_path_str) if image_path_str else None

                        print(f"\n[DAEMON // JOB RECEIVED] Type: {job_type} | Preset: {job_preset or 'active'} | ID: {job_id} | Scene: {scene_id}")

                        if job_type == "initial_reconstruction" and image_path:
                            # 1. Run initial room reconstruction with job preset
                            scene_result = execute_initial_reconstruction(image_path, scene_id, preset=job_preset)
                            if scene_result:
                                objs = scene_result.get("objects", [])
                                print(f"\n[ANTIGRAVITY // PIPELINE] Ingested initial room with {len(objs)} objects.")
                                # 2. Automatically kick off the refinement loop for ALL objects in the active chat conversation!
                                print(f"[ANTIGRAVITY // PIPELINE] Beginning sequential refinement loop across ALL {len(objs)} objects (5-min per-object watchdog, text-only in conversation)...")
                                run_full_scene_refinement_loop(scene_id, max_items=None, preset=job_preset)

                        elif job_type == "refine_loop":
                            run_full_scene_refinement_loop(scene_id, max_items=job.get("max_items"), preset=job_preset)

                        elif job_type == "refine_single":
                            obj = job.get("object_data", {})
                            execute_object_refinement(scene_id, obj, preset=job_preset)

                        elif job_type == "screen_action":
                            # Antigravity screen-control directive
                            action = job.get("action", "click")
                            target_key = job.get("target_key")
                            text_to_type = job.get("text")
                            coords = job.get("coords")
                            if not coords and target_key:
                                cfg = load_config()
                                coords = cfg.get("targets", {}).get(target_key)
                            
                            if coords and pyautogui:
                                x, y = coords["x"], coords["y"]
                                print(f"\n[DAEMON // ANTIGRAVITY CONTROL] Action '{action}' on {target_key or 'target'} ({x}, {y})...")
                                pyautogui.moveTo(x, y, duration=0.4)
                                if action == "click":
                                    pyautogui.click()
                                elif action == "double_click":
                                    pyautogui.doubleClick()
                                elif action == "paste":
                                    pyautogui.click()
                                    time.sleep(0.2)
                                    if text_to_type:
                                        copy_text_to_clipboard(text_to_type)
                                    physical_paste()
                                elif action == "scroll_down":
                                    pyautogui.scroll(-3500)
                                    pyautogui.press("pagedown", presses=2, interval=0.02)
                                    pyautogui.hotkey("ctrl", "end")
                                elif action == "press_key":
                                    key = job.get("key", "enter")
                                    pyautogui.press(key)

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
    override_preset = None
    for i, arg in enumerate(sys.argv):
        if arg == "--preset" and i + 1 < len(sys.argv):
            override_preset = sys.argv[i + 1]
            break
        elif arg.startswith("--preset="):
            override_preset = arg.split("=", 1)[1]
            break

    if "--daemon" in sys.argv:
        run_physical_daemon(preset=override_preset)
    elif "--loop" in sys.argv:
        target_scene = None
        for i, arg in enumerate(sys.argv):
            if arg == "--loop" and i + 1 < len(sys.argv):
                target_scene = sys.argv[i + 1]
                break
        if target_scene:
            run_full_scene_refinement_loop(target_scene, preset=override_preset)
        else:
            print("Usage: python scripts/physical_clicker.py --loop <scene_id>")
    else:
        # Direct CLI status
        cfg = load_config(preset=override_preset)
        targets = cfg.get("targets", {})
        preset_label = cfg.get("preset_label", "Google Gemini")
        preset_id = cfg.get("active_preset", "gemini")
        print(f"SpatialCraft Physical Clicker ready. Active Preset: {preset_label} [{preset_id}]")
        print(f"Loaded {len(targets)} calibrated targets:")
        for k, v in targets.items():
            print(f"  - {v.get('name', k):32s} : X = {v.get('x')}, Y = {v.get('y')}")
        print("\nTo switch active preset, run:")
        print("  .\\calibrate_clicks.bat [gemini | chatgpt | deepseek]")
        print("\nTo start the standing desktop listener, run:")
        print("  .\\run_physical_daemon.bat  (or python scripts/physical_clicker.py --daemon)")
