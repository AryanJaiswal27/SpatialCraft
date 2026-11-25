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

def activate_preset(preset_name: str) -> bool:
    if not CONFIG_PATH.exists():
        return False
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        pid = preset_name.lower().strip()
        presets = data.get("presets", {})
        if pid in presets:
            data["active_preset"] = pid
            data["targets"] = presets[pid].get("targets", {})
            data["delays"] = presets[pid].get("delays", {})
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[PRESET] Successfully activated preset: {presets[pid].get('label', pid)} ({pid})")
            return True
        else:
            print(f"[ERROR] Preset '{preset_name}' not found. Available presets: {list(presets.keys())}")
            return False
    except Exception as e:
        print(f"[ERROR] Could not switch preset: {e}")
        return False

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

def _focus_window_by_title(keywords: list[str], exclude_keywords: Optional[list[str]] = None) -> bool:
    """Focuses an existing visible Windows window and verifies foreground activation."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        SW_RESTORE = 9
        SW_SHOW = 5
        excludes = [ex.lower() for ex in (exclude_keywords or [])]

        def _get_title(hwnd) -> str:
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return ""
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value

        def _matches(title_lower: str) -> bool:
            if not title_lower:
                return False
            if excludes and any(ex in title_lower for ex in excludes):
                return False
            return any(kw in title_lower for kw in keywords)

        fg_hwnd = user32.GetForegroundWindow()
        if fg_hwnd and _matches(_get_title(fg_hwnd).lower()):
            return True

        matches = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _enum_cb(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                title = _get_title(hwnd)
                if _matches(title.lower()):
                    matches.append((hwnd, title))
            return True

        user32.EnumWindows(WNDENUMPROC(_enum_cb), 0)
        if not matches:
            return False

        target_hwnd, target_title = matches[0]
        if user32.IsIconic(target_hwnd):
            user32.ShowWindow(target_hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(target_hwnd, SW_SHOW)

        fg_now = user32.GetForegroundWindow()
        fg_tid = user32.GetWindowThreadProcessId(fg_now, None) if fg_now else 0
        cur_tid = kernel32.GetCurrentThreadId()
        attached = False
        if fg_tid and cur_tid and fg_tid != cur_tid:
            attached = bool(user32.AttachThreadInput(fg_tid, cur_tid, True))
        try:
            user32.BringWindowToTop(target_hwnd)
            user32.SetForegroundWindow(target_hwnd)
        finally:
            if attached:
                user32.AttachThreadInput(fg_tid, cur_tid, False)

        time.sleep(0.15)
        if user32.GetForegroundWindow() == target_hwnd:
            print(f"[SCREEN CONTROL] Focused window by title: '{target_title}'")
            return True
        return False
    except Exception:
        return False

def focus_target(target_key: str, delay: Optional[float] = None):
    cfg = load_config()
    delays = cfg.get("delays", {})
    hold = float(delay) if delay is not None else float(delays.get("click_settle", 1.0))
    if target_key == "browser_tab" and _focus_window_by_title(
        ["google chrome", "microsoft edge", "chrome", "edge", "firefox", "brave"],
        exclude_keywords=["antigravity", "visual studio code"]
    ):
        time.sleep(0.5)
        return True
    if target_key == "antigravity_header" and _focus_window_by_title(
        ["antigravity"],
        exclude_keywords=["chrome", "edge", "firefox", "brave"]
    ):
        time.sleep(0.5)
        return True
    targets = cfg.get("targets", {})
    t = targets.get(target_key)
    if not t or not pyautogui:
        print(f"[ERROR] Target '{target_key}' not found or uncalibrated.")
        return False
    x, y = t["x"], t["y"]
    print(f"[SCREEN CONTROL] Clicking {target_key} at ({x}, {y}) and holding {hold:.0f}s...")
    pyautogui.moveTo(x, y, duration=0.35)
    pyautogui.click()
    time.sleep(hold)
    return True

def scroll_down(amount: int = -3500):
    cfg = load_config()
    prompt_pos = cfg.get("targets", {}).get("prompt_box", {"x": 960, "y": 900})
    scroll_x = prompt_pos["x"]
    scroll_y = max(120, prompt_pos["y"] - 280)
    if pyautogui:
        pyautogui.moveTo(scroll_x, scroll_y, duration=0.15)
        pyautogui.scroll(amount)
        time.sleep(0.25)
        pyautogui.scroll(amount)
        pyautogui.press("pagedown", presses=2, interval=0.05)
        pyautogui.hotkey("ctrl", "end")
        print(f"[SCREEN CONTROL] Scrolled down at ({scroll_x}, {scroll_y}).")

def _capture_region_signature(bbox: tuple[int, int, int, int]):
    """Captures a lightweight grayscale 160x90 thumbnail of the chat response region (zero clicks)."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=bbox)
        return img.convert("L").resize((160, 90))
    except Exception:
        return None

def _frame_change_ratio(prev_img, cur_img) -> float:
    """Returns fraction of pixels that changed significantly (>12/255) between two grayscale thumbnails."""
    if prev_img is None or cur_img is None:
        return 1.0
    try:
        from PIL import ImageChops
        diff = ImageChops.difference(prev_img, cur_img)
        hist = diff.histogram()
        unchanged = sum(hist[:13])
        total = max(1, diff.width * diff.height)
        return max(0.0, (total - unchanged) / total)
    except Exception:
        return 1.0

def wait_for_llm(timeout: float = 360.0, min_wait: float = 10.0, expected_id: Optional[str] = None) -> str:
    """
    Waits adaptively for LLM generation using zero-click visual stream stability detection:
    1. Short initial wait (default 10s).
    2. Quiet downward scrolling while watching response + Copy toolbar pixels.
    3. Clicks Copy button ONCE once stream pixels stabilize (~6s unchanged) with cooldown.
    """
    cfg = load_config()
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})
    copy_pos = targets.get("copy_button")
    prompt_pos = targets.get("prompt_box", {"x": 960, "y": 900})
    scroll_x = prompt_pos["x"]
    scroll_y = max(120, prompt_pos["y"] - 280)
    copy_x = copy_pos["x"] if copy_pos else scroll_x
    copy_y = copy_pos["y"] if copy_pos else max(160, scroll_y + 180)
    prompt_y = prompt_pos["y"]

    bbox_x1 = max(80, min(scroll_x - 220, copy_x - 100))
    bbox_x2 = min(1840, max(scroll_x + 220, copy_x + 360))
    bbox_y2 = max(copy_y + 28, prompt_y - 35)
    bbox_y1 = max(100, min(copy_y - 180, bbox_y2 - 220))
    watch_bbox = (bbox_x1, bbox_y1, max(bbox_x1 + 120, bbox_x2), max(bbox_y1 + 80, bbox_y2))

    eff_min_wait = float(delays.get("min_generation_wait", min_wait))
    eff_timeout = float(delays.get("llm_generation_timeout", timeout))

    print(f"\n[SCREEN CONTROL] Adaptive stream-end watch (Initial buffer: {int(eff_min_wait)}s, Max timeout: {int(eff_timeout)}s)...")
    if expected_id:
        print(f"                 Expecting target identifier: '{expected_id}'")

    copy_text_to_clipboard("")
    start_time = time.time()

    while (time.time() - start_time) < eff_min_wait:
        time.sleep(min(2.0, max(0.2, eff_min_wait - (time.time() - start_time))))

    prev_frame = None
    stable_streak = 0
    last_click_time = 0.0
    click_cooldown = 20.0
    max_unclicked_gap = 45.0

    while (time.time() - start_time) < eff_timeout:
        now = time.time()
        elapsed = now - start_time

        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.15)
            pyautogui.scroll(-3500)
            time.sleep(0.35)
            pyautogui.press("pagedown")
            pyautogui.hotkey("ctrl", "end")
            time.sleep(0.5)
        except Exception:
            pass

        cur_frame = _capture_region_signature(watch_bbox)
        delta = _frame_change_ratio(prev_frame, cur_frame) if prev_frame is not None else None
        prev_frame = cur_frame

        if cur_frame is None:
            ready_to_click = (now - last_click_time) >= click_cooldown
        else:
            if delta is not None and delta > 0.002:
                stable_streak = 0
            elif delta is not None:
                stable_streak += 1
            since_last_click = (now - last_click_time) if last_click_time > 0 else elapsed
            ready_to_click = bool(copy_pos) and ((stable_streak >= 2 and (since_last_click >= click_cooldown or last_click_time == 0.0)) or since_last_click >= max_unclicked_gap)

        if ready_to_click and copy_pos:
            try:
                pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=0.25)
                pyautogui.click()
                last_click_time = time.time()
                stable_streak = 0
                prev_frame = None
                time.sleep(0.8)
                clip_text = get_clipboard_text()
                if clip_text and "{" in clip_text and "}" in clip_text:
                    if clip_text.count("{") <= clip_text.count("}"):
                        has_schema = any(k in clip_text for k in ("room", "dimensions", "objects", "name", "category", "materials"))
                        matches_id = True if not expected_id else (expected_id in clip_text)
                        if has_schema and matches_id:
                            print(f"[SUCCESS] Captured response via Copy button in {int(elapsed)}s ({len(clip_text)} chars)!")
                            return clip_text
            except Exception:
                last_click_time = time.time()

        time.sleep(3.0)

    # Final attempt on timeout
    print(f"[TIMEOUT] {int(eff_timeout)}s reached. Taking final copy...")
    if copy_pos:
        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.2)
            pyautogui.scroll(-4000)
            time.sleep(0.3)
            pyautogui.press("pagedown", presses=2, interval=0.05)
            pyautogui.hotkey("ctrl", "end")
            time.sleep(1.0)
            pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=0.3)
            pyautogui.click()
            time.sleep(0.8)
            final_clip = get_clipboard_text()
            if final_clip and "{" in final_clip and "}" in final_clip:
                return final_clip
        except Exception:
            pass

    # Fallback: full-page selection extraction if copy button was displaced
    try:
        print("[FALLBACK] Attempting full-page text extraction to salvage response...")
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
            return salvage_text
    except Exception as e:
        print(f"[ERROR] Page fallback failed: {e}")

    return ""

def paste_to_ide_chat(text: str) -> bool:
    """
    Bypassed: Direct backend API ingestion is used to prevent piling up in
    the Antigravity IDE chat message queue.
    """
    print("[SCREEN CONTROL] Direct backend API ingestion active. Bypassing IDE chat paste to prevent message queue pile-up.")
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
    delays = cfg.get("delays", {})
    hold = float(delays.get("click_settle", 1.0))
    img_settle = float(delays.get("image_upload_settle", 8.0))

    # 1. Bring Browser to front
    focus_target("browser_tab", delay=hold)

    # 2. Focus prompt box & paste text
    focus_target("prompt_box", delay=hold)
    copy_text_to_clipboard(prompt)
    time.sleep(0.15)
    physical_paste()
    time.sleep(0.6)

    # 3. Paste image crop & hold 8s to upload image
    if crop_path.exists():
        print(f"[SCREEN CONTROL] Pasting 2D crop: {crop_name}...")
        copy_image_to_clipboard(crop_path)
        time.sleep(0.2)
        physical_paste()
        print(f"[SCREEN CONTROL] Holding {img_settle:.0f}s for image upload...")
        time.sleep(img_settle)

    # 4. Click send button & Enter
    focus_target("send_button", delay=hold)
    pyautogui.press("enter")
    copy_text_to_clipboard("") # Clear clipboard
    print(f"[SCREEN CONTROL] Dispatched prompt for '{obj_name}' to Gemini!")

    # 5. Adaptive wait via stream-end visual stability detection
    raw_response = wait_for_llm(timeout=360.0, min_wait=10.0, expected_id=obj_id)
    if not raw_response:
        print(f"\n[ANTIGRAVITY BACKUP // 5-MIN TIMEOUT] No response captured from browser LLM for {obj_id} within 5 minutes.")
        print(f"[ANTIGRAVITY BACKUP] Constructing 3D CAD mesh model autonomously from crop...")
        try:
            from backend.services.antigravity_builder import refine_object_with_antigravity_cad
            refined = refine_object_with_antigravity_cad(scene_id, obj_id)
            if refined:
                print(f"[ANTIGRAVITY BACKUP // SUCCESS] '{obj_name}' refined with custom 3D mesh parts!")
                return True
        except Exception as e:
            print(f"[ANTIGRAVITY BACKUP // ERROR] {e}")
        return False

    # 6. Direct backend ingestion (bypassing IDE chat paste to prevent message queue pile-up)
    # paste_to_ide_chat(...)

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
        if "materials" in parsed:
            update_body["materials"] = parsed["materials"]
        if "features" in parsed:
            update_body["features"] = parsed["features"]
        if "parts" in parsed:
            update_body["parts"] = parsed["parts"]
        if "mesh_obj" in parsed:
            update_body["mesh_obj"] = parsed["mesh_obj"]

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
    wait_parser.add_argument("--timeout", type=float, default=360.0)
    wait_parser.add_argument("--min-wait", type=float, default=10.0)
    wait_parser.add_argument("--expected", type=str, default=None)

    refine_parser = subparsers.add_parser("refine_step")
    refine_parser.add_argument("scene_id", help="Scene ID")
    refine_parser.add_argument("step", type=int, help="Step index (1-based)")

    preset_parser = subparsers.add_parser("preset")
    preset_parser.add_argument("name", help="Preset identifier to activate (e.g. gemini, chatgpt, deepseek)")

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
    elif args.command == "preset":
        activate_preset(args.name)
    elif args.command == "wait_response":
        res = wait_for_llm(timeout=args.timeout, min_wait=args.min_wait, expected_id=args.expected)
        print("\nExtracted Output:\n" + res)
    elif args.command == "refine_step":
        run_single_refinement_step(args.scene_id, args.step)
    elif args.command == "status":
        cfg = load_config()
        targets = cfg.get("targets", {})
        preset_label = cfg.get("preset_label", "Google Gemini")
        preset_id = cfg.get("active_preset", "gemini")
        print(f"Antigravity Screen Controller ready. Screen: {cfg.get('screen')}")
        print(f"Active Preset: {preset_label} [{preset_id}]")
        print("Calibrated Targets for Active Preset:")
        for k, v in targets.items():
            print(f"  - {v.get('name', k):30s} : X = {v.get('x')}, Y = {v.get('y')}")
        presets = cfg.get("presets", {})
        if presets:
            print("\nAvailable Presets:")
            for pid, pdata in presets.items():
                marker = " [ACTIVE]" if pid == preset_id else ""
                print(f"  * {pdata.get('label', pid):20s} ({pid}){marker}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
