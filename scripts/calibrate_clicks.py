import os
import sys
import time
import json
import msvcrt
from pathlib import Path

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

try:
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "physical_clicks_config.json"

DEFAULT_PRESET_METADATA = {
    "gemini": {
        "id": "gemini",
        "label": "Google Gemini",
        "browser_url": "https://gemini.google.com",
        "tab_hint": "Hover over your Google Gemini browser tab or taskbar icon.",
        "input_hint": "Hover inside Gemini prompt input composer box (Ctrl+V paste target).",
        "send_hint": "Hover over Gemini send button arrow.",
        "copy_hint": "Hover over Gemini Copy response button icon at the bottom of the response."
    },
    "chatgpt": {
        "id": "chatgpt",
        "label": "OpenAI ChatGPT",
        "browser_url": "https://chatgpt.com",
        "tab_hint": "Hover over your ChatGPT browser tab or taskbar icon.",
        "input_hint": "Hover inside ChatGPT message input box (Ctrl+V paste target).",
        "send_hint": "Hover over ChatGPT send button arrow.",
        "copy_hint": "Hover over ChatGPT Copy response button icon at bottom of message."
    },
    "deepseek": {
        "id": "deepseek",
        "label": "DeepSeek Chat",
        "browser_url": "https://chat.deepseek.com",
        "tab_hint": "Hover over your DeepSeek browser tab or taskbar icon.",
        "input_hint": "Hover inside DeepSeek message textarea (Ctrl+V paste target).",
        "send_hint": "Hover over DeepSeek send button arrow.",
        "copy_hint": "Hover over DeepSeek Copy response button icon at bottom of message."
    }
}

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure presets structure
            if "presets" not in data or not isinstance(data.get("presets"), dict):
                old_targets = data.get("targets", {})
                old_delays = data.get("delays", {})
                data["active_preset"] = "gemini"
                data["presets"] = {
                    pid: {
                        "id": pid,
                        "label": meta["label"],
                        "browser_url": meta["browser_url"],
                        "targets": dict(old_targets) if pid == "gemini" else {},
                        "delays": dict(old_delays),
                        "last_calibrated_at": data.get("last_calibrated_at") if pid == "gemini" else None
                    }
                    for pid, meta in DEFAULT_PRESET_METADATA.items()
                }
            return data
        except Exception:
            pass
    return {
        "screen": {"width": 1920, "height": 1080},
        "active_preset": "gemini",
        "presets": {
            pid: {
                "id": pid,
                "label": meta["label"],
                "browser_url": meta["browser_url"],
                "targets": {},
                "delays": {"click_settle": 0.3, "image_upload_settle": 3.0, "llm_generation_timeout": 120.0, "move_duration": 0.4},
                "last_calibrated_at": None
            }
            for pid, meta in DEFAULT_PRESET_METADATA.items()
        },
        "targets": {},
        "delays": {}
    }

def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print(f"\n[CONFIG SAVED] Calibration written to: {CONFIG_PATH.name}")

def get_mouse_pos():
    if pyautogui:
        pos = pyautogui.position()
        return pos.x, pos.y
    else:
        import ctypes
        from ctypes import wintypes
        class POINT(ctypes.Structure):
            _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

def capture_target_coordinate(target_key: str, title: str, description: str) -> tuple[int, int]:
    """
    Calibrates a single screen target with NO forced timer.
    Takes as much time as the user needs until [SPACE] or [ENTER] is pressed.
    """
    while True:
        print("\n" + "=" * 70)
        print(f" TARGET: {title}")
        print("=" * 70)
        for line in description.splitlines():
            print(f"  {line}")
        print("-" * 70)
        print("  >> Move your mouse cursor to this target on your screen.")
        print("  >> Take your time. Press [SPACE] or [ENTER] when cursor is in position.")
        print("  >> (Press [ESC] at any time to cancel calibration.)\n")

        # Clear any buffered keystrokes
        while msvcrt.kbhit():
            msvcrt.getch()

        last_x, last_y = 0, 0
        while True:
            cur_x, cur_y = get_mouse_pos()
            last_x, last_y = cur_x, cur_y

            # Check for user input
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b' ', b'\r', b'\n'):
                    break
                elif key == b'\x1b': # ESC
                    print("\n\n[CALIBRATION CANCELLED] Exiting without saving.")
                    sys.exit(0)

            sys.stdout.write(f"\r  [TRACKING CURSOR]  X = {cur_x:4d}  |  Y = {cur_y:4d}   (Hover and press [SPACE] to lock)   ")
            sys.stdout.flush()
            time.sleep(0.06)

        print(f"\n\n  ==> [COORDINATE RECORDED]: X = {last_x}, Y = {last_y}")

        # Verification & Confirmation option
        print("  Press [ENTER] to confirm and advance, or [R] to re-position this target: ", end="", flush=True)
        choice = b''
        while True:
            if msvcrt.kbhit():
                choice = msvcrt.getch()
                break
            time.sleep(0.05)

        if choice in (b'r', b'R'):
            print("RETRY")
            print("  Restarting position capture for this target...")
            time.sleep(0.5)
            continue
        else:
            print("CONFIRMED")
            return last_x, last_y

def run_antigravity_verification_simulation(targets: dict, preset_label: str = ""):
    """
    Visually visits all calibrated targets on the user's screen.
    """
    if not pyautogui:
        return

    print("\n" + "=" * 70)
    print(f"      ANTIGRAVITY CALIBRATION // LIVE VISUAL VERIFICATION [{preset_label or 'ACTIVE'}]")
    print("=" * 70)
    print("Antigravity will now guide your mouse to each calibrated target on screen.")
    print("Starting in 3 seconds. Please do not touch your mouse...")
    for i in range(3, 0, -1):
        print(f"  Starting in {i}...", flush=True)
        time.sleep(1.0)

    order = ["browser_tab", "prompt_box", "send_button", "copy_button", "antigravity_header", "ide_chat_box"]
    for key in order:
        t = targets.get(key)
        if t and (t.get("x", 0) > 0 or t.get("y", 0) > 0):
            x, y = t["x"], t["y"]
            title = t.get("name", key)
            print(f"\n  >> Moving to {title} (X={x}, Y={y})...")
            pyautogui.moveTo(x, y, duration=0.8)
            time.sleep(0.2)
            # Gentle visual pulse
            pyautogui.moveRel(4, 0, duration=0.1)
            pyautogui.moveRel(-8, 0, duration=0.1)
            pyautogui.moveRel(4, 0, duration=0.1)
            time.sleep(1.0)

    print("\n" + "=" * 70)
    print(" [VERIFICATION SUCCESS] Antigravity verified active coordinates!")
    print("=" * 70)

def get_target_order_for_preset(preset_id: str, label: str):
    meta = DEFAULT_PRESET_METADATA.get(preset_id, {
        "label": label,
        "tab_hint": f"Hover over your {label} browser tab or taskbar icon.",
        "input_hint": f"Hover inside {label} message prompt input box.",
        "send_hint": f"Hover over {label} send button arrow.",
        "copy_hint": f"Hover over {label} Copy response button icon."
    })
    return [
        (
            "browser_tab",
            f"01. {meta['label'].upper()} TAB / HEADER",
            f"{meta['tab_hint']}\nAntigravity clicks here to bring {meta['label']} to the foreground."
        ),
        (
            "prompt_box",
            f"02. {meta['label'].upper()} CHAT INPUT",
            f"{meta['input_hint']}\nAntigravity clicks here to paste images (Ctrl+V) and CAD prompts."
        ),
        (
            "send_button",
            f"03. {meta['label'].upper()} SEND BUTTON",
            f"{meta['send_hint']}\nAntigravity clicks here to dispatch prompts to {meta['label']}."
        ),
        (
            "copy_button",
            f"04. {meta['label'].upper()} COPY BUTTON",
            f"{meta['copy_hint']}\nAntigravity clicks here to extract the generated 3D CAD data."
        ),
        (
            "antigravity_header",
            "05. ANTIGRAVITY WINDOW / TOP HEADER",
            "Hover over the top title bar or tab header of this Antigravity IDE window.\nAntigravity clicks here to bring the IDE window to the top/foreground."
        ),
        (
            "ide_chat_box",
            "06. ANTIGRAVITY IDE CHAT INPUT",
            "Hover inside the chat input box at the bottom of this Antigravity IDE window.\nAntigravity clicks here to paste the browser's LLM response directly into this chat."
        )
    ]

def run_calibration():
    cfg = load_config()

    if pyautogui:
        sw, sh = pyautogui.size()
        cfg["screen"] = {"width": sw, "height": sh}

    active_id = cfg.get("active_preset", "gemini")
    presets = cfg.setdefault("presets", {})

    print("=" * 70)
    print("      SPATIALCRAFT // MULTI-LLM SCREEN CALIBRATION WIZARD")
    print("=" * 70)
    print("This utility calibrates physical mouse coordinates on your monitor")
    print("for Google Gemini, OpenAI ChatGPT, DeepSeek Chat, or Custom LLMs,")
    print("allowing Antigravity to drive each browser window and paste responses")
    print("directly into this Antigravity IDE chat window.\n")

    # 1. Preset Selection
    target_preset = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        arg_val = sys.argv[1].lower().strip()
        if arg_val in presets or arg_val in DEFAULT_PRESET_METADATA:
            target_preset = arg_val

    if not target_preset:
        print(f"Current Active Preset: [{presets.get(active_id, {}).get('label', active_id.upper())}]")
        print("\nSelect LLM Preset to Calibrate:")
        preset_keys = ["gemini", "chatgpt", "deepseek"]
        for idx, pk in enumerate(preset_keys, 1):
            pdata = presets.get(pk, DEFAULT_PRESET_METADATA.get(pk, {}))
            label = pdata.get("label", pk.capitalize())
            active_flag = "  <-- [ACTIVE PRESET]" if pk == active_id else ""
            print(f"  [{idx}] {label:24s} ({pk}){active_flag}")
        print("  [4] Custom LLM Preset (create new or calibrate other)")
        print("  [V] Live Visual Verification of current active coordinates")

        sel = input("\nSelect preset option [1-4 / V] (default 1): ").strip().upper()
        if sel == "V":
            active_targets = presets.get(active_id, {}).get("targets", cfg.get("targets", {}))
            run_antigravity_verification_simulation(active_targets, presets.get(active_id, {}).get("label", active_id))
            return
        elif sel == "2":
            target_preset = "chatgpt"
        elif sel == "3":
            target_preset = "deepseek"
        elif sel == "4":
            custom_id = input("Enter custom preset identifier (e.g. claude, mistral): ").strip().lower()
            if not custom_id:
                custom_id = "custom"
            custom_label = input(f"Enter display label for '{custom_id}' (e.g. Anthropic Claude): ").strip()
            if not custom_label:
                custom_label = custom_id.capitalize()
            presets.setdefault(custom_id, {
                "id": custom_id,
                "label": custom_label,
                "browser_url": "",
                "targets": {},
                "delays": {"click_settle": 0.3, "image_upload_settle": 3.0, "llm_generation_timeout": 120.0, "move_duration": 0.4},
                "last_calibrated_at": None
            })
            target_preset = custom_id
        else:
            target_preset = "gemini"

    preset_obj = presets.setdefault(target_preset, DEFAULT_PRESET_METADATA.get(target_preset, {
        "id": target_preset,
        "label": target_preset.capitalize(),
        "browser_url": "",
        "targets": {},
        "delays": {"click_settle": 0.3, "image_upload_settle": 3.0, "llm_generation_timeout": 120.0, "move_duration": 0.4},
        "last_calibrated_at": None
    }))

    preset_label = preset_obj.get("label", target_preset.capitalize())
    print("\n" + "=" * 70)
    print(f" CALIBRATING PRESET: {preset_label.upper()} [{target_preset}]")
    print("=" * 70)

    # Pre-fill Antigravity Header & IDE Chat Box from any existing calibration
    existing_preset_targets = preset_obj.setdefault("targets", {})
    all_targets_across_presets = {}
    for p in presets.values():
        all_targets_across_presets.update(p.get("targets", {}))
    all_targets_across_presets.update(cfg.get("targets", {}))

    for ag_key in ("antigravity_header", "ide_chat_box"):
        if ag_key not in existing_preset_targets or (existing_preset_targets[ag_key].get("x", 0) == 0):
            if ag_key in all_targets_across_presets and all_targets_across_presets[ag_key].get("x", 0) > 0:
                existing_preset_targets[ag_key] = dict(all_targets_across_presets[ag_key])

    targets_order = get_target_order_for_preset(target_preset, preset_label)

    print("\nCurrent Coordinates for this Preset:")
    for idx, (k, title, _) in enumerate(targets_order, 1):
        t = existing_preset_targets.get(k, {})
        x, y = t.get("x", 0), t.get("y", 0)
        status = f"X = {x:4d}, Y = {y:4d}" if (x or y) else "NOT CALIBRATED"
        print(f"  [{idx}] {title:35s} : {status}")

    print("\nCalibration Scope:")
    print("  [A] Calibrate ALL targets (1 through 6) [RECOMMENDED]")
    print("  [B] Calibrate Browser targets only (1 through 4: tab, input, send, copy)")
    print("  [1-6] Calibrate a single target number")
    print("  [V] Visual test existing coordinates without changes")

    scope_choice = input("\nSelect option (default B): ").strip().upper()
    if scope_choice == "V":
        run_antigravity_verification_simulation(existing_preset_targets, preset_label)
        return
    elif scope_choice == "A":
        targets_to_calibrate = targets_order
    elif scope_choice in ("1", "2", "3", "4", "5", "6"):
        target_idx = int(scope_choice) - 1
        targets_to_calibrate = [targets_order[target_idx]]
    else:
        # Default: Browser targets 1 to 4
        targets_to_calibrate = targets_order[:4]

    print(f"\nPlease arrange your {preset_label} browser window on your screen now.")
    input("\nPress [ENTER] when ready to begin calibration...")

    for key, title, desc in targets_to_calibrate:
        x, y = capture_target_coordinate(key, title, desc)
        if key not in existing_preset_targets:
            existing_preset_targets[key] = {}
        existing_preset_targets[key]["name"] = title
        existing_preset_targets[key]["x"] = x
        existing_preset_targets[key]["y"] = y
        existing_preset_targets[key]["description"] = desc

    from datetime import datetime
    preset_obj["last_calibrated_at"] = datetime.utcnow().isoformat()
    presets[target_preset] = preset_obj

    # Ask if this preset should be active
    activate = "y"
    if active_id != target_preset:
        print(f"\nMake '{preset_label}' the ACTIVE automation preset for the desktop daemon? (Y/n): ", end="", flush=True)
        try:
            user_act = input().strip().lower()
            if user_act in ("n", "no"):
                activate = "n"
        except Exception:
            pass

    if activate != "n":
        cfg["active_preset"] = target_preset
        cfg["targets"] = existing_preset_targets
        cfg["delays"] = preset_obj.get("delays", cfg.get("delays", {}))
        print(f"\n[ACTIVE PRESET] '{preset_label}' is now the active LLM automation target!")
    else:
        # Keep existing active
        cfg["targets"] = presets.get(active_id, {}).get("targets", cfg.get("targets", {}))

    cfg["last_calibrated_at"] = datetime.utcnow().isoformat()
    save_config(cfg)

    print("\n" + "=" * 70)
    print(f" [PRESET CALIBRATED] {preset_label} Coordinates Recorded Successfully!")
    print("=" * 70)
    for k, v in existing_preset_targets.items():
        print(f"  - {v.get('name', k):35s} : X = {v.get('x'):4d}, Y = {v.get('y'):4d}")

    # Prompt for visual verification run
    print("\nWould you like Antigravity to run a visual hover test of these calibrated spots? (Y/n): ", end="", flush=True)
    ans = "y"
    try:
        raw_ans = input().strip().lower()
        if raw_ans in ("n", "no"):
            ans = "n"
    except Exception:
        pass

    if ans != "n":
        run_antigravity_verification_simulation(existing_preset_targets, preset_label)

    print(f"\nSetup complete for {preset_label}! Run 'run_physical_daemon.bat' to begin automated reconstruction.")

if __name__ == "__main__":
    run_calibration()
