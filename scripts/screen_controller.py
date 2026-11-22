"""
SpatialCraft // Antigravity Direct Screen Controller
Enables programmatic, turn-by-turn physical screen control for Antigravity AI
using calibrated screen coordinates.
"""

import sys
import os
import time
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import pyautogui
    import pyperclip
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None
    pyperclip = None

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

def copy_text_to_clipboard(text: str) -> bool:
    try:
        if pyperclip:
            pyperclip.copy(text)
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

def copy_image_to_clipboard(image_path: Path) -> bool:
    if not image_path.exists():
        return False
    abs_path = str(image_path.resolve())
    ps_cmd = f"""
    Add-Type -AssemblyName System.Windows.Forms;
    [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{abs_path}'));
    """
    try:
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def physical_paste():
    time.sleep(0.12)
    pyautogui.keyDown("ctrl")
    time.sleep(0.14)
    pyautogui.press("v")
    time.sleep(0.14)
    pyautogui.keyUp("ctrl")
    time.sleep(0.25)

def focus_target(target_key: str, delay: float = 0.3):
    cfg = load_config()
    targets = cfg.get("targets", {})
    t = targets.get(target_key)
    if not t or not pyautogui:
        print(f"[ERROR] Target '{target_key}' not found or uncalibrated.")
        return False
    x, y = t["x"], t["y"]
    print(f"[SCREEN CONTROL] Clicking {target_key} at ({x}, {y})...")
    pyautogui.moveTo(x, y, duration=0.35)
    pyautogui.click()
    time.sleep(delay)
    return True

def scroll_down(amount: int = -450):
    cfg = load_config()
    prompt_pos = cfg.get("targets", {}).get("prompt_box", {"x": 960, "y": 900})
    scroll_x = prompt_pos["x"]
    scroll_y = max(120, prompt_pos["y"] - 280)
    if pyautogui:
        pyautogui.moveTo(scroll_x, scroll_y, duration=0.1)
        pyautogui.scroll(amount)
        pyautogui.press("end")
        print(f"[SCREEN CONTROL] Scrolled down at ({scroll_x}, {scroll_y}) with [End] key.")

def wait_for_llm(timeout: float = 120.0, min_wait: float = 15.0, expected_id: Optional[str] = None) -> str:
    from backend.services.browser_prompt import parse_llm_json_response

    cfg = load_config()
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})
    copy_pos = targets.get("copy_button")
    prompt_pos = targets.get("prompt_box", {"x": 960, "y": 900})
    scroll_x = prompt_pos["x"]
    scroll_y = max(120, prompt_pos["y"] - 280)

    print(f"\n[SCREEN CONTROL] Waiting for LLM (Timeout: {int(timeout)}s, Min Wait: {int(min_wait)}s)...")
    if expected_id:
        print(f"                 Expecting target identifier: '{expected_id}'")

    start_time = time.time()
    
    # Baseline text snapshot
    time.sleep(1.5)
    baseline_text = ""
    try:
        pyautogui.moveTo(scroll_x, scroll_y, duration=0.1)
        pyautogui.click()
        time.sleep(0.08)
        pyautogui.keyDown("ctrl"); pyautogui.press("a"); pyautogui.keyUp("ctrl")
        time.sleep(0.08)
        pyautogui.keyDown("ctrl"); pyautogui.press("c"); pyautogui.keyUp("ctrl")
        time.sleep(0.08)
        pyautogui.press("escape")
        baseline_text = get_clipboard_text()
    except Exception:
        pass

    baseline_len = len(baseline_text)
    last_len = baseline_len
    has_streamed_new_content = False
    stable_count = 0
    consecutive_needed = 4  # ~10s stable after tokens stream

    while (time.time() - start_time) < timeout:
        elapsed = time.time() - start_time

        # Continuous downward scroll
        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.1)
            pyautogui.scroll(-450)
            pyautogui.press("end")
        except Exception:
            pass

        time.sleep(0.25)

        # Snapshot inspect
        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.1)
            pyautogui.click()
            time.sleep(0.08)
            pyautogui.keyDown("ctrl"); pyautogui.press("a"); pyautogui.keyUp("ctrl")
            time.sleep(0.08)
            pyautogui.keyDown("ctrl"); pyautogui.press("c"); pyautogui.keyUp("ctrl")
            time.sleep(0.08)
            pyautogui.press("escape")
            time.sleep(0.1)

            page_text = get_clipboard_text()
            if page_text:
                cur_len = len(page_text)
                if cur_len > last_len + 15:
                    delta = cur_len - last_len
                    has_streamed_new_content = True
                    print(f"  [STREAMING] +{delta} chars ({cur_len} total) | [{int(elapsed)}s/{int(timeout)}s]")
                    last_len = cur_len
                    stable_count = 0
                elif has_streamed_new_content and abs(cur_len - last_len) <= 15:
                    stable_count += 1
                    print(f"  [WAITING] Content steady ({stable_count}/{consecutive_needed}) | [{int(elapsed)}s/{int(timeout)}s]")
        except Exception:
            pass

        # Check if min wait has elapsed AND new tokens streamed AND stabilized
        if elapsed >= min_wait and has_streamed_new_content and stable_count >= consecutive_needed:
            # Check Copy button
            if copy_pos:
                try:
                    pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=0.3)
                    pyautogui.click()
                    time.sleep(0.4)
                    clip_text = get_clipboard_text()
                    if clip_text and "{" in clip_text and "}" in clip_text:
                        if not expected_id or (expected_id in clip_text):
                            print(f"[SUCCESS] Captured response via Copy button ({len(clip_text)} chars)!")
                            return clip_text
                except Exception:
                    pass

            # Fallback parse from page_text
            parsed = parse_llm_json_response(page_text)
            if parsed:
                if not expected_id or (expected_id in str(parsed)):
                    print(f"[SUCCESS] Extracted response from page text ({len(page_text)} chars)!")
                    return json.dumps(parsed, indent=2)

        time.sleep(2.0)

    # Final attempt on timeout
    print(f"[TIMEOUT] {int(timeout)}s reached. Taking final copy...")
    if copy_pos:
        try:
            pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=0.3)
            pyautogui.click()
            time.sleep(0.5)
            final_clip = get_clipboard_text()
            if final_clip:
                return final_clip
        except Exception:
            pass
    return ""

def paste_to_ide_chat(text: str) -> bool:
    cfg = load_config()
    targets = cfg.get("targets", {})
    ag_header = targets.get("antigravity_header")
    ide_chat = targets.get("ide_chat_box")

    if not ide_chat or not pyautogui:
        print("[ERROR] ide_chat_box not calibrated.")
        return False

    # 1. Bring Antigravity IDE to the front
    if ag_header and (ag_header.get("x", 0) > 0 or ag_header.get("y", 0) > 0):
        print(f"[SCREEN CONTROL] Clicking Antigravity Header at ({ag_header['x']}, {ag_header['y']})...")
        pyautogui.moveTo(ag_header["x"], ag_header["y"], duration=0.35)
        pyautogui.click()
        time.sleep(0.4)

    # 2. Focus Chat Input Box
    x, y = ide_chat["x"], ide_chat["y"]
    print(f"[SCREEN CONTROL] Clicking Antigravity IDE Chat Input at ({x}, {y})...")
    pyautogui.moveTo(x, y, duration=0.35)
    pyautogui.click()
    time.sleep(0.3)

    # 3. Select all and paste
    pyautogui.keyDown("ctrl"); pyautogui.press("a"); pyautogui.keyUp("ctrl")
    time.sleep(0.1)
    copy_text_to_clipboard(text)
    time.sleep(0.1)
    physical_paste()
    time.sleep(0.3)

    # 4. Press Enter to submit
    print("[SCREEN CONTROL] Pressing [ENTER] to submit message to Antigravity AI...")
    pyautogui.press("enter")
    time.sleep(1.0)
    print("[SUCCESS] Posted message into Antigravity IDE chat!")
    return True

def run_single_refinement_step(scene_id: str, step_index: int) -> bool:
    """
    Antigravity executes one full object refinement step:
    1. Fetches scene and Antigravity refinement plan.
    2. Focuses browser.
    3. Pastes prompt + crop image, clicks send.
    4. Waits with 2-min timer & auto-scroll.
    5. Copies refined CAD output.
    6. Switches to Antigravity IDE, pastes output into chat, presses Enter.
    7. Updates SpatialCraft 3D twin in sync!
    """
    import urllib.request
    from backend.services.antigravity_prompter import build_antigravity_scene_refinement_plan, generate_antigravity_object_prompt
    from backend.services.browser_prompt import parse_llm_json_response

    # Fetch scene
    req = urllib.request.Request(f"{BASE_URL}/api/scene/{scene_id}")
    with urllib.request.urlopen(req) as resp:
        scene_data = json.loads(resp.read().decode("utf-8"))

    plan = build_antigravity_scene_refinement_plan(scene_data)
    candidates = [s for s in plan if s.get("crop_url")]

    if step_index < 1 or step_index > len(candidates):
        print(f"[ERROR] Invalid step {step_index}. Scene has {len(candidates)} objects to refine.")
        return False

    step = candidates[step_index - 1]
    obj_id = step["object_id"]
    obj_name = step["object_name"]
    crop_url = step["crop_url"]
    crop_name = Path(crop_url).name
    crop_path = ROOT_DIR / "backend" / "storage" / "crops" / crop_name

    obj = next((o for o in scene_data.get("objects", []) if o["id"] == obj_id), None)
    if not obj:
        print(f"[ERROR] Object {obj_id} not found in scene.")
        return False

    print("\n" + "=" * 65)
    print(f" [ANTIGRAVITY DIRECTOR] Refinement Step {step_index}/{len(candidates)}: '{obj_name}' ({obj_id})")
    print("=" * 65)

    prompt = generate_antigravity_object_prompt(obj, scene=scene_data, step_idx=step_index, total_steps=len(candidates))

    cfg = load_config()
    targets = cfg.get("targets", {})

    # 1. Bring Browser to front
    focus_target("browser_tab", delay=0.5)

    # 2. Focus prompt box & paste text
    focus_target("prompt_box", delay=0.3)
    copy_text_to_clipboard(prompt)
    time.sleep(0.15)
    physical_paste()
    time.sleep(0.5)

    # 3. Paste image crop
    if crop_path.exists():
        print(f"[SCREEN CONTROL] Pasting 2D crop: {crop_name}...")
        copy_image_to_clipboard(crop_path)
        time.sleep(0.2)
        physical_paste()
        time.sleep(3.0) # Settle image upload

    # 4. Click send button & Enter
    focus_target("send_button", delay=0.2)
    pyautogui.press("enter")
    copy_text_to_clipboard("") # Clear clipboard
    print(f"[SCREEN CONTROL] Dispatched prompt for '{obj_name}' to Gemini!")

    # 5. Wait up to 2 min with auto-scroll & min wait
    raw_response = wait_for_llm(timeout=120.0, min_wait=14.0, expected_id=obj_id)
    if not raw_response:
        print(f"[WARN] No response captured for {obj_id}.")
        return False

    # 6. Switch to Antigravity IDE and paste response into this chat!
    paste_to_ide_chat(f"### [Refined Object CAD Output - Step {step_index}/{len(candidates)}: {obj_name}]\n\n{raw_response}")

    # 7. Update SpatialCraft 3D twin
    parsed = parse_llm_json_response(raw_response)
    if parsed:
        update_body = {}
        if "dimensions" in parsed:
            update_body["dimensions"] = parsed["dimensions"]
        if "color" in parsed:
            update_body["color"] = parsed["color"]
        if "description" in parsed:
            update_body["description"] = parsed["description"]

        put_data = json.dumps(update_body).encode("utf-8")
        put_req = urllib.request.Request(
            f"{BASE_URL}/api/scene/{scene_id}/object/{obj_id}",
            data=put_data,
            headers={"Content-Type": "application/json"},
            method="PUT"
        )
        try:
            with urllib.request.urlopen(put_req, timeout=10) as put_resp:
                print(f"[SUCCESS] SpatialCraft 3D twin updated for '{obj_name}' (Status: {put_resp.status})!")
        except Exception as e:
            print(f"[ERROR] Updating 3D twin via PUT: {e}")

    return True

def main():
    parser = argparse.ArgumentParser(description="Antigravity Direct Screen Controller")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("focus_browser")
    subparsers.add_parser("focus_ide")
    subparsers.add_parser("scroll_down")
    subparsers.add_parser("status")

    click_parser = subparsers.add_parser("click")
    click_parser.add_argument("target", help="Target key (e.g. browser_tab, prompt_box, send_button, copy_button, antigravity_header, ide_chat_box)")

    paste_parser = subparsers.add_parser("paste_to_ide")
    paste_parser.add_argument("text", help="Text to paste into Antigravity IDE chat")

    wait_parser = subparsers.add_parser("wait_response")
    wait_parser.add_argument("--timeout", type=float, default=120.0)
    wait_parser.add_argument("--min-wait", type=float, default=15.0)
    wait_parser.add_argument("--expected", type=str, default=None)

    refine_parser = subparsers.add_parser("refine_step")
    refine_parser.add_argument("scene_id", help="Scene ID")
    refine_parser.add_argument("step", type=int, help="Step index (1-based)")

    args = parser.parse_args()

    if args.command == "focus_browser":
        focus_target("browser_tab")
    elif args.command == "focus_ide":
        focus_target("antigravity_header")
    elif args.command == "scroll_down":
        scroll_down()
    elif args.command == "click":
        focus_target(args.target)
    elif args.command == "paste_to_ide":
        paste_to_ide_chat(args.text)
    elif args.command == "wait_response":
        res = wait_for_llm(timeout=args.timeout, min_wait=args.min_wait, expected_id=args.expected)
        print("\nExtracted Output:\n" + res)
    elif args.command == "refine_step":
        run_single_refinement_step(args.scene_id, args.step)
    elif args.command == "status":
        cfg = load_config()
        targets = cfg.get("targets", {})
        print(f"Antigravity Screen Controller ready. Screen: {cfg.get('screen')}")
        for k, v in targets.items():
            print(f"  - {v.get('name', k):30s} : X = {v.get('x')}, Y = {v.get('y')}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
