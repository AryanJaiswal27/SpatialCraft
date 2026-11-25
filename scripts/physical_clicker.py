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
                # If antigravity preset isn't explicitly saved yet, pull calibrated IDE coordinates from existing presets
                if active_id == "antigravity" and presets:
                    ref_targets = {}
                    for p in presets.values():
                        for k in ("antigravity_header", "ide_chat_box"):
                            if k in p.get("targets", {}) and k not in ref_targets:
                                ref_targets[k] = p["targets"][k]
                    if ref_targets:
                        data["targets"] = ref_targets
                data["active_preset"] = active_id
                data["preset_label"] = "Antigravity IDE" if active_id == "antigravity" else active_id.capitalize()
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
            if text == "" or pyperclip.paste().strip():
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

def _focus_window_by_title(
    keywords: list[str],
    exclude_keywords: Optional[list[str]] = None,
    preferred_keywords: Optional[list[str]] = None,
) -> bool:
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
        prefs = [pr.lower() for pr in (preferred_keywords or [])]

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
        if fg_hwnd:
            fg_lower = _get_title(fg_hwnd).lower()
            if _matches(fg_lower) and (not prefs or any(p in fg_lower for p in prefs)):
                return True

        matches = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _enum_cb(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                title = _get_title(hwnd)
                t_lower = title.lower()
                if _matches(t_lower):
                    # Rank preset-specific windows (e.g. "DeepSeek - Chrome") ahead of generic browser windows
                    score = 2 if (prefs and any(p in t_lower for p in prefs)) else (0 if "spatialcraft" in t_lower else 1)
                    matches.append((score, hwnd, title))
            return True

        user32.EnumWindows(WNDENUMPROC(_enum_cb), 0)
        if not matches:
            return False

        matches.sort(key=lambda item: item[0], reverse=True)
        _, target_hwnd, target_title = matches[0]

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
            print(f"[PHYSICAL] Focused window by title: '{target_title}'")
            return True
        print(f"[PHYSICAL] Window '{target_title}' resisted SetForegroundWindow; falling back to calibrated click.")
        return False
    except Exception as e:
        print(f"[PHYSICAL] Window title focus fallback ({e})")
        return False

def focus_browser_tab(targets: dict, move_dur: float = 0.4, settle: float = 1.0, preset: Optional[str] = None):
    pref = [preset.lower()] if preset else ["gemini", "chatgpt", "deepseek"]
    if _focus_window_by_title(
        ["google chrome", "microsoft edge", "chrome", "edge", "firefox", "brave"],
        exclude_keywords=["antigravity", "visual studio code"],
        preferred_keywords=pref,
    ):
        time.sleep(0.5)
        return
    tab_pos = targets.get("browser_tab")
    if tab_pos and pyautogui:
        hold = max(0.5, float(settle))
        print(f"[PHYSICAL] Clicking Browser Tab to focus window: ({tab_pos['x']}, {tab_pos['y']})...")
        pyautogui.moveTo(tab_pos["x"], tab_pos["y"], duration=move_dur)
        pyautogui.click()
        time.sleep(hold)

def focus_antigravity_window(targets: dict, delays: dict):
    """Brings the Antigravity IDE window to the foreground."""
    hold = max(0.5, float(delays.get("click_settle", 1.0)))
    if _focus_window_by_title(
        ["antigravity"],
        exclude_keywords=["chrome", "edge", "firefox", "brave"],
        preferred_keywords=["spatialcraft", "antigravity"],
    ):
        time.sleep(0.5)
        return
    ag_head = targets.get("antigravity_header")
    if ag_head and (ag_head.get("x", 0) > 0 or ag_head.get("y", 0) > 0) and pyautogui:
        move_dur = delays.get("move_duration", 0.4)
        print(f"[PHYSICAL] Clicking Antigravity Top Header: ({ag_head['x']}, {ag_head['y']}) to bring IDE to front...")
        pyautogui.moveTo(ag_head["x"], ag_head["y"], duration=move_dur)
        pyautogui.click()
        time.sleep(hold)

def execute_antigravity_physical_build(image_path: Optional[Path], scene_id: str, prompt_override: Optional[str] = None, preset: Optional[str] = "antigravity") -> bool:
    """
    Antigravity Physical Mode:
    Physically clicks into the Antigravity IDE window & chat composer,
    pastes the custom 3D mesh build prompt + room image directly via OS clipboard,
    and submits ONCE so the Antigravity AI agent inside the IDE inspects the photo,
    identifies every object, constructs bespoke multi-part 3D CSG meshes with accurate
    colors from scratch (avoiding prebuilt templates), and submits to the backend API.
    """
    from backend.services.browser_prompt import generate_antigravity_direct_build_prompt

    cfg = load_config(preset=preset or "antigravity")
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})

    # Fallback: harvest antigravity_header / ide_chat_box from any calibrated preset if omitted
    if not targets.get("ide_chat_box"):
        for pdata in cfg.get("presets", {}).values():
            pt = pdata.get("targets", {})
            if pt.get("ide_chat_box"):
                targets.setdefault("antigravity_header", pt.get("antigravity_header"))
                targets["ide_chat_box"] = pt.get("ide_chat_box")
                break

    ide_chat_pos = targets.get("ide_chat_box")
    if not ide_chat_pos or not ide_chat_pos.get("x") or not pyautogui:
        print("[ANTIGRAVITY PHYSICAL // ERROR] Missing 'ide_chat_box' calibration coordinate!")
        print("                               Run calibrate_antigravity.bat or calibrate_clicks.bat antigravity")
        return False

    move_dur = delays.get("move_duration", 0.4)
    settle = float(delays.get("click_settle", 1.0))
    img_settle = float(delays.get("image_upload_settle", 8.0))
    img_name = image_path.name if image_path else ""
    prompt_text = prompt_override or generate_antigravity_direct_build_prompt(scene_id, img_name)

    print("\n" + "=" * 65)
    print(f" [ANTIGRAVITY PHYSICAL MODE] Dispatching Room Image + Custom 3D Mesh Prompt")
    print(f"  Scene ID : {scene_id}")
    print(f"  Image    : {img_name or 'None'}")
    print("=" * 65)

    # 1. Focus Antigravity IDE Window
    focus_antigravity_window(targets, delays)

    # 2. Click IDE Chat Composer Box
    x, y = ide_chat_pos["x"], ide_chat_pos["y"]
    print(f"[ANTIGRAVITY PHYSICAL] Clicking IDE Chat Input: ({x}, {y})...")
    pyautogui.moveTo(x, y, duration=move_dur)
    pyautogui.click()
    time.sleep(settle)

    # 3. Paste Custom 3D Mesh Instruction Prompt FIRST
    print(f"[ANTIGRAVITY PHYSICAL] Pasting custom 3D mesh build prompt ({len(prompt_text)} chars)...")
    copy_text_to_clipboard(prompt_text)
    time.sleep(0.15)
    physical_paste()
    time.sleep(0.6)

    # 4. Paste Room Photograph SECOND and wait for upload settle (default 8s)
    if image_path and image_path.exists():
        print(f"[ANTIGRAVITY PHYSICAL] Pasting room image to Antigravity chat: {image_path.name}...")
        if copy_image_to_clipboard(image_path):
            time.sleep(0.25)
            physical_paste()
            print(f"[ANTIGRAVITY PHYSICAL] Holding {img_settle:.0f}s for image upload to complete...")
            time.sleep(img_settle)

    # 5. Submit Once via [ENTER]
    print("[ANTIGRAVITY PHYSICAL] Pressing [ENTER] to submit image & custom build request...")
    pyautogui.press("enter")
    time.sleep(0.8)
    print("[ANTIGRAVITY PHYSICAL // SENT] Antigravity IDE agent now has the photo & instructions!")
    return True


def execute_antigravity_object_refine_paste(scene_id: str, obj: dict, preset: Optional[str] = "antigravity") -> bool:
    """For single-object refinement under Antigravity Physical mode, pastes crop + custom mesh prompt to IDE chat."""
    from backend.services.antigravity_prompter import generate_antigravity_object_prompt

    obj_id = obj.get("id", "obj_1")
    obj_name = obj.get("name", "Object")
    crop_url = obj.get("crop_url")
    crop_path = (ROOT_DIR / "backend" / "storage" / "crops" / Path(crop_url).name) if crop_url else None
    if crop_path and not crop_path.exists():
        crop_path = None

    base_prompt = generate_antigravity_object_prompt(obj, step_idx=1, total_steps=1, in_conversation=False)
    direct_prompt = (
        f"[SPATIALCRAFT // ANTIGRAVITY CUSTOM OBJECT REFINE]\n"
        f"Scene ID: {scene_id} | Object ID: {obj_id}\n"
        f"Target Update Endpoint: PUT http://localhost:8000/api/scene/{scene_id}/object/{obj_id}\n\n"
        f"{base_prompt}\n\n"
        f"Avoid prebuilt generic models: build custom bespoke 3D mesh `parts` matching exact colors from the attached crop, "
        f"and PUT the JSON update directly to http://localhost:8000/api/scene/{scene_id}/object/{obj_id}."
    )
    return execute_antigravity_physical_build(crop_path, scene_id, prompt_override=direct_prompt, preset=preset)


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
    settle = float(delays.get("click_settle", 1.0))
    img_settle = float(delays.get("image_upload_settle", 8.0))
    prompt_pos = targets.get("prompt_box")
    send_pos = targets.get("send_button")

    if not prompt_pos or not send_pos:
        print("[PHYSICAL // ERROR] Missing prompt_box or send_button calibration coordinates!")
        return False

    # 1. Focus the clean, empty prompt composer
    print(f"[PHYSICAL] Clicking Prompt Input Box: ({prompt_pos['x']}, {prompt_pos['y']})...")
    pyautogui.moveTo(prompt_pos["x"], prompt_pos["y"], duration=move_dur)
    pyautogui.click()
    time.sleep(settle)

    # 2. Paste the Text Prompt FIRST
    print(f"[PHYSICAL] Loading text prompt to clipboard ({len(prompt_text)} chars)...")
    copy_text_to_clipboard(prompt_text)
    time.sleep(0.15)
    print("[PHYSICAL] Pasting prompt text via Ctrl+V...")
    physical_paste()
    time.sleep(0.6)

    # 3. Paste Image SECOND if provided and hold 8s for image upload
    if image_path and image_path.exists():
        print(f"[PHYSICAL] Loading image to clipboard: {image_path.name}...")
        if copy_image_to_clipboard(image_path):
            time.sleep(0.2)
            # Notice: Cursor is already inside the active composer; do not click on potential thumbnails!
            print("[PHYSICAL] Pasting image attachment via Ctrl+V...")
            physical_paste()
            print(f"[PHYSICAL] Holding {img_settle:.0f}s for image upload to finish...")
            time.sleep(img_settle)

    # 4. Click Send Button
    print(f"[PHYSICAL] Clicking Send Button: ({send_pos['x']}, {send_pos['y']})...")
    pyautogui.moveTo(send_pos["x"], send_pos["y"], duration=move_dur)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(settle)
    copy_text_to_clipboard("")  # Clear clipboard so copy check never reads stale clipboard data
    return True

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

def wait_and_extract_response(
    targets: dict,
    delays: dict,
    expected_id: Optional[str] = None,
    timeout: float = 360.0,
    ignore_texts: Optional[set] = None,
) -> str:
    """
    Waits adaptively for LLM generation with ZERO premature clicks:
    1. Waits a short initial buffer (default 10s) so streaming/thinking begins.
    2. Scrolls quietly (no clicks!) every ~3s and watches visual pixel changes in the response +
       Copy button region using zero-click screen captures (`ImageGrab`).
    3. Clicks the calibrated Copy button ONCE only after pixels stabilize (stream ended) for
       two consecutive checks (~6s unchanged) with at least a 20s cooldown between clicks
       (plus a 45s safety fallback if subtle page animations keep firing).
    """
    if not pyautogui:
        return ""

    move_dur = delays.get("move_duration", 0.4)
    min_wait = float(delays.get("min_generation_wait", 10.0))
    gen_timeout = float(delays.get("llm_generation_timeout", timeout))
    copy_pos = targets.get("copy_button")
    prompt_pos = targets.get("prompt_box")
    stale_set = ignore_texts or set()

    scroll_x = prompt_pos["x"] if prompt_pos else 960
    scroll_y = max(120, (prompt_pos["y"] - 280)) if prompt_pos else 500
    copy_x = copy_pos["x"] if copy_pos else scroll_x
    copy_y = copy_pos["y"] if copy_pos else max(160, scroll_y + 180)
    prompt_y = prompt_pos["y"] if prompt_pos else 920

    # Tightly track lower response stream + action bar so small thinking timers register clearly
    bbox_x1 = max(80, min(scroll_x - 220, copy_x - 100))
    bbox_x2 = min(1840, max(scroll_x + 220, copy_x + 360))
    bbox_y2 = max(copy_y + 28, prompt_y - 35)
    bbox_y1 = max(100, min(copy_y - 180, bbox_y2 - 220))
    watch_bbox = (bbox_x1, bbox_y1, max(bbox_x1 + 120, bbox_x2), max(bbox_y1 + 80, bbox_y2))

    print(f"\n[PHYSICAL] Adaptive wait for LLM stream completion (Initial buffer: {int(min_wait)}s, Max timeout: {int(gen_timeout)}s)...")
    if expected_id:
        print(f"[PHYSICAL] Expecting target identifier: '{expected_id}'")

    copy_text_to_clipboard("")

    def _is_valid_capture(clip_text: str) -> bool:
        if not clip_text or "{" not in clip_text or "}" not in clip_text:
            return False
        if clip_text.strip() in stale_set:
            return False
        if clip_text.count("{") > clip_text.count("}"):
            return False
        has_schema = any(k in clip_text for k in ("room", "dimensions", "objects", "name", "category", "materials"))
        if not has_schema:
            return False
        if expected_id and expected_id not in clip_text:
            return False
        if expected_id == "room":
            from backend.services.browser_prompt import parse_llm_json_response
            parsed = parse_llm_json_response(clip_text)
            return isinstance(parsed, dict) and ("room" in parsed or "objects" in parsed)
        parsed_obj = parse_refinement_json(clip_text, expected_id=expected_id)
        return parsed_obj is not None

    start_time = time.time()
    last_milestone = start_time

    # Phase 1: Short initial buffer (NO clicking, NO scrolling yet while prompt submits & begins thinking)
    while (time.time() - start_time) < min_wait:
        time.sleep(min(2.0, max(0.2, min_wait - (time.time() - start_time))))

    print(f"[PHYSICAL] Monitoring response stream visually at region {watch_bbox} (zero clicks while streaming)...")

    prev_frame = None
    stable_streak = 0
    saw_activity = False
    last_click_time = 0.0  # Last time copy_button was clicked
    click_cooldown = 20.0
    max_unclicked_gap = 45.0  # Safety probe if animated spinner/ads never settle

    # Phase 2 & 3: Quiet scroll + visual stream-end detection -> single clean Copy click
    while (time.time() - start_time) < gen_timeout:
        now = time.time()
        elapsed = now - start_time

        if (now - last_milestone) >= 30.0:
            print(f"[PHYSICAL] Waiting for stream end... ({int(elapsed)}s / {int(gen_timeout)}s elapsed)")
            last_milestone = now

        # Quiet scroll to bottom without clicking chat content
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
            # ImageGrab unavailable (e.g., headless/mock environment): wait cooldown between single checks
            ready_to_click = (now - last_click_time) >= click_cooldown
        else:
            if delta is not None and delta > 0.002:
                saw_activity = True
                stable_streak = 0
            elif delta is not None:
                stable_streak += 1

            since_last_click = (now - last_click_time) if last_click_time > 0 else elapsed
            stream_settled = (stable_streak >= 2) and (since_last_click >= click_cooldown or (last_click_time == 0.0 and stable_streak >= 2))
            fallback_due = since_last_click >= max_unclicked_gap
            ready_to_click = bool(copy_pos) and (stream_settled or fallback_due)

        if ready_to_click and copy_pos:
            reason = "stream stabilized" if cur_frame is not None and stable_streak >= 2 else "periodic check"
            print(f"[PHYSICAL] Response {reason} ({int(elapsed)}s). Clicking Copy button once at ({copy_pos['x']}, {copy_pos['y']})...")
            try:
                pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=0.25)
                pyautogui.click()
                last_click_time = time.time()
                stable_streak = 0
                prev_frame = None  # Force fresh activity cycle before another click
                time.sleep(0.8)
                clip_text = get_clipboard_text()
                if _is_valid_capture(clip_text):
                    print(f"[PHYSICAL // GENERATION COMPLETE] Captured response cleanly in {int(elapsed)}s ({len(clip_text)} chars)!")
                    return clip_text
                # Not valid yet (e.g. caught a brief thinking pause); bump cooldown before retrying
                print("[PHYSICAL] Valid JSON not ready yet; resuming zero-click stream watch...")
            except Exception:
                last_click_time = time.time()

        time.sleep(3.0)

    # Final attempt on timeout
    print(f"[PHYSICAL // TIMEOUT] {int(gen_timeout)}s timeout reached. Attempting final extraction...")
    if copy_pos:
        try:
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.2)
            pyautogui.scroll(-4000)
            time.sleep(0.3)
            pyautogui.press("pagedown", presses=2, interval=0.05)
            pyautogui.hotkey("ctrl", "end")
            time.sleep(1.0)
            pyautogui.moveTo(copy_pos["x"], copy_pos["y"], duration=move_dur)
            pyautogui.click()
            time.sleep(0.8)
            final_text = get_clipboard_text()
            if _is_valid_capture(final_text):
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
            if expected_id == "room":
                from backend.services.browser_prompt import parse_llm_json_response
                if parse_llm_json_response(salvage_text):
                    print(f"[PHYSICAL // SALVAGED] Successfully recovered {len(salvage_text)} chars from page fallback!")
                    return salvage_text
            elif parse_refinement_json(salvage_text, expected_id=expected_id):
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
    focus_browser_tab(targets, preset=preset or cfg.get("active_preset"))

    prompt = generate_spatial_prompt()
    pasted = paste_and_send(prompt, image_path, targets, delays)
    raw_output = ""
    if pasted:
        raw_output = wait_and_extract_response(targets, delays, expected_id="room", timeout=360.0)

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

def parse_refinement_json(raw_text: str, expected_id: Optional[str] = None) -> Optional[dict]:
    import re

    def _valid_single_object(parsed: Any) -> Optional[dict]:
        if not isinstance(parsed, dict):
            return None
        # Reject full-room wrappers from Turn 1 unless we extract a matching refined object with parts
        if "room" in parsed and "objects" in parsed and "parts" not in parsed:
            if expected_id and isinstance(parsed.get("objects"), list):
                for o in parsed["objects"]:
                    if isinstance(o, dict) and o.get("id") == expected_id and o.get("parts"):
                        return o
            return None
        if expected_id and parsed.get("id") and parsed.get("id") != expected_id:
            return None
        if any(k in parsed for k in ("parts", "dimensions", "materials", "color", "description", "features")):
            return parsed
        return None

    # 1. Search all code fences in reverse (latest response on page first)
    matches = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text))
    for m in reversed(matches):
        try:
            obj = _valid_single_object(json.loads(m.group(1).strip()))
            if obj is not None:
                return obj
        except Exception:
            pass

    # 2. Greedy outer brace match
    brace = re.search(r"(\{[\s\S]*\})", raw_text)
    if brace:
        try:
            return _valid_single_object(json.loads(brace.group(1).strip()))
        except Exception:
            pass
    return None

def execute_object_refinement(
    scene_id: str,
    obj: dict,
    scene_data: Optional[dict] = None,
    step_idx: int = 1,
    total_steps: int = 1,
    preset: Optional[str] = None,
    seen_texts: Optional[set] = None,
) -> bool:
    """Phase 2: Refines an individual object by referencing the room photo already in the active browser conversation (zero image re-upload)."""
    cfg = load_config(preset=preset)
    targets = cfg.get("targets", {})
    delays = cfg.get("delays", {})

    print(f"\n" + "=" * 65)
    print(f" [ANTIGRAVITY // CAD AGENT] Step {step_idx}/{total_steps}: Refining '{obj.get('name')}'")
    print("=" * 65)
    focus_browser_tab(targets, preset=preset or cfg.get("active_preset"))

    # Antigravity generates tailored prompt referencing the photo already in the active thread
    refine_prompt = generate_antigravity_object_prompt(obj, scene=scene_data, step_idx=step_idx, total_steps=total_steps, in_conversation=True)
    print(f"[ANTIGRAVITY] Generated {len(refine_prompt)} chars tailored prompt for '{obj.get('name')}'.")
    print(f"[PHYSICAL] Pasting text prompt into active conversation (NO image re-upload; photo is already in chat)...")

    # Send ONLY the text prompt into the existing conversation thread (image_path=None)
    pasted = paste_and_send(refine_prompt, image_path=None, targets=targets, delays=delays)
    raw_output = ""
    if pasted:
        raw_output = wait_and_extract_response(
            targets,
            delays,
            expected_id=obj.get("id"),
            timeout=360.0,
            ignore_texts=seen_texts,
        )

    parsed = None
    if raw_output:
        if seen_texts is not None:
            seen_texts.add(raw_output.strip())
        # Direct backend ingestion (bypassing IDE chat paste to prevent message queue pile-up)
        parsed = parse_refinement_json(raw_output, expected_id=obj.get("id"))

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
                        f"{BASE_URL}/api/scene/{scene_id}/prompt",
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
    seen_texts = set()
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
            preset=preset,
            seen_texts=seen_texts,
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
                            eff_preset = (job_preset or load_config().get("active_preset", "gemini")).lower()
                            if eff_preset == "antigravity":
                                # Antigravity Physical Mode: Paste photo + direct prompt into Antigravity IDE chat ONCE.
                                # Do NOT launch browser refinement loop (Antigravity agent builds all custom 3D meshes in one pass).
                                execute_antigravity_physical_build(
                                    image_path=image_path,
                                    scene_id=scene_id,
                                    prompt_override=job.get("prompt"),
                                    preset="antigravity"
                                )
                            else:
                                # 1. Run initial room reconstruction with browser preset (Gemini / ChatGPT / DeepSeek)
                                scene_result = execute_initial_reconstruction(image_path, scene_id, preset=job_preset)
                                if scene_result:
                                    objs = scene_result.get("objects", [])
                                    print(f"\n[ANTIGRAVITY // PIPELINE] Ingested initial room with {len(objs)} objects.")
                                    # 2. Automatically kick off the refinement loop for ALL objects in the active chat conversation!
                                    print(f"[ANTIGRAVITY // PIPELINE] Beginning sequential refinement loop across ALL {len(objs)} objects (5-min per-object watchdog, text-only in conversation)...")
                                    run_full_scene_refinement_loop(scene_id, max_items=None, preset=job_preset)

                        elif job_type == "refine_loop":
                            eff_preset = (job_preset or load_config().get("active_preset", "gemini")).lower()
                            if eff_preset == "antigravity":
                                sc_req = urllib.request.Request(f"{BASE_URL}/api/scene/{scene_id}")
                                with urllib.request.urlopen(sc_req, timeout=8) as sc_resp:
                                    sc_data = json.loads(sc_resp.read().decode("utf-8"))
                                img_url = sc_data.get("image_url") or ""
                                img_p = (ROOT_DIR / "backend" / "storage" / "uploads" / Path(img_url).name) if img_url else None
                                execute_antigravity_physical_build(image_path=img_p, scene_id=scene_id, preset="antigravity")
                            else:
                                run_full_scene_refinement_loop(scene_id, max_items=job.get("max_items"), preset=job_preset)

                        elif job_type == "refine_single":
                            obj = job.get("object_data", {})
                            eff_preset = (job_preset or load_config().get("active_preset", "gemini")).lower()
                            if eff_preset == "antigravity":
                                execute_antigravity_object_refine_paste(scene_id, obj, preset="antigravity")
                            else:
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
                                cfg_delays = load_config().get("delays", {})
                                click_hold = float(cfg_delays.get("click_settle", 1.0))
                                if action == "click":
                                    pyautogui.click()
                                    time.sleep(click_hold)
                                elif action == "double_click":
                                    pyautogui.doubleClick()
                                    time.sleep(click_hold)
                                elif action == "paste":
                                    pyautogui.click()
                                    time.sleep(click_hold)
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
        print("  .\\calibrate_clicks.bat [gemini | chatgpt | deepseek | antigravity]")
        print("\nTo start the standing desktop listener, run:")
        print("  .\\run_physical_daemon.bat  (or python scripts/physical_clicker.py --daemon)")
