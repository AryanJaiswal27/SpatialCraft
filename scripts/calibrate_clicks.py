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

TARGETS_ORDER = [
    (
        "browser_tab",
        "01. BROWSER TAB / HEADER",
        "Hover over your browser tab header (e.g. ChatGPT, Gemini, Claude tab).\n"
        "Antigravity clicks here to bring your browser window to the foreground."
    ),
    (
        "prompt_box",
        "02. CHAT COMPOSER / PROMPT BOX",
        "Hover inside the message composer textarea.\n"
        "Antigravity clicks here to paste images (Ctrl+V) and paste CAD prompts."
    ),
    (
        "send_button",
        "03. SEND / SUBMIT BUTTON",
        "Hover over the send arrow / submit button.\n"
        "Antigravity clicks here to dispatch prompts to the LLM."
    ),
    (
        "copy_button",
        "04. COPY RESPONSE BUTTON",
        "Hover over the copy response icon at the bottom of the LLM output.\n"
        "Antigravity clicks here to extract the generated 3D CAD data."
    ),
    (
        "antigravity_header",
        "05. ANTIGRAVITY WINDOW / TOP HEADER",
        "Hover over the top title bar or tab header of this Antigravity IDE window.\n"
        "Antigravity clicks here to bring the IDE window to the top/foreground."
    ),
    (
        "ide_chat_box",
        "06. ANTIGRAVITY IDE CHAT INPUT",
        "Hover inside the chat input box at the bottom of this Antigravity IDE window.\n"
        "Antigravity clicks here to paste the browser's LLM response directly into this chat."
    )
]

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"screen": {"width": 1920, "height": 1080}, "targets": {}, "delays": {}}

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
    Allows instant retry ([R]) before confirming.
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

def run_antigravity_verification_simulation(targets: dict):
    """
    Visually visits all calibrated targets on the user's screen
    to demonstrate and verify where Antigravity will click.
    """
    if not pyautogui:
        return

    print("\n" + "=" * 70)
    print("      ANTIGRAVITY CALIBRATION // LIVE VISUAL VERIFICATION")
    print("=" * 70)
    print("Antigravity will now guide your mouse to each target on screen.")
    print("Starting in 3 seconds. Please do not touch your mouse...")
    for i in range(3, 0, -1):
        print(f"  Starting in {i}...", flush=True)
        time.sleep(1.0)

    for key, title, _ in TARGETS_ORDER:
        t = targets.get(key)
        if t and (t.get("x", 0) > 0 or t.get("y", 0) > 0):
            x, y = t["x"], t["y"]
            print(f"\n  >> Moving to {title} (X={x}, Y={y})...")
            pyautogui.moveTo(x, y, duration=0.8)
            time.sleep(0.2)
            # Gentle visual pulse (small circle)
            pyautogui.moveRel(4, 0, duration=0.1)
            pyautogui.moveRel(-8, 0, duration=0.1)
            pyautogui.moveRel(4, 0, duration=0.1)
            time.sleep(1.2)

    print("\n" + "=" * 70)
    print(" [VERIFICATION SUCCESS] Antigravity verified all active coordinates!")
    print("=" * 70)

def run_calibration():
    print("=" * 70)
    print("      SPATIALCRAFT // ANTIGRAVITY GUIDED SCREEN CALIBRATOR")
    print("=" * 70)
    print("This utility calibrates physical mouse coordinates on your monitor")
    print("so Antigravity can drive your open browser (ChatGPT, Gemini, Claude, DeepSeek)")
    print("AND paste responses directly into this Antigravity IDE chat window.")
    print("There is NO countdown timer — take as much time as you need for each spot.\n")

    cfg = load_config()
    if pyautogui:
        sw, sh = pyautogui.size()
        cfg["screen"] = {"width": sw, "height": sh}
        print(f"Detected Display Resolution: {sw}x{sh}")

    existing_targets = cfg.get("targets", {})
    has_existing = any(t.get("x", 0) > 0 for t in existing_targets.values())

    targets_to_calibrate = TARGETS_ORDER

    if has_existing:
        print("\nExisting Calibrated Targets:")
        for idx, (k, title, _) in enumerate(TARGETS_ORDER, 1):
            t = existing_targets.get(k, {})
            x, y = t.get("x", 0), t.get("y", 0)
            status = f"X = {x:4d}, Y = {y:4d}" if (x or y) else "NOT CALIBRATED"
            print(f"  [{idx}] {title:32s} : {status}")

        print("\nCalibration Options:")
        print("  [A] Calibrate ALL targets (1 through 6)")
        ag_header = existing_targets.get("antigravity_header", {})
        if not ag_header.get("x") and not ag_header.get("y"):
            print("  [5] Calibrate Target 5 only (Antigravity Window / Top Header) [RECOMMENDED]")
        else:
            print("  [5] Re-calibrate Target 5 (Antigravity Window / Top Header)")
        print("  [6] Re-calibrate Target 6 (Antigravity IDE Chat Input)")
        print("  [1-6] Calibrate a single specific target number")
        print("  [V] Jump straight to Live Visual Verification of existing coordinates")
        
        choice = input("\nSelect option (default A): ").strip().upper()
        if choice == "V":
            run_antigravity_verification_simulation(existing_targets)
            return
        elif choice in ("1", "2", "3", "4", "5", "6"):
            target_idx = int(choice) - 1
            targets_to_calibrate = [TARGETS_ORDER[target_idx]]
            print(f"\nSelected single target: {targets_to_calibrate[0][1]}")

    print("\nPlease arrange your windows on your screen now.")
    input("\nPress [ENTER] when ready to begin calibration...")

    targets = dict(existing_targets)

    for key, title, desc in targets_to_calibrate:
        x, y = capture_target_coordinate(key, title, desc)
        if key not in targets:
            targets[key] = {}
        targets[key]["name"] = title
        targets[key]["x"] = x
        targets[key]["y"] = y
        targets[key]["description"] = desc

    from datetime import datetime
    cfg["targets"] = targets
    cfg["last_calibrated_at"] = datetime.utcnow().isoformat()
    save_config(cfg)

    print("\n" + "=" * 70)
    print(" [CALIBRATION COMPLETE] Coordinates recorded successfully!")
    print("=" * 70)
    for k, v in targets.items():
        print(f"  - {v.get('name', k):32s} : X = {v.get('x'):4d}, Y = {v.get('y'):4d}")

    # Prompt for visual verification run
    print("\nWould you like Antigravity to run a visual hover test of calibrated spots? (Y/n): ", end="", flush=True)
    ans = "y"
    try:
        raw_ans = input().strip().lower()
        if raw_ans in ("n", "no"):
            ans = "n"
    except Exception:
        pass

    if ans != "n":
        run_antigravity_verification_simulation(targets)

    print("\nSetup complete! You can now run 'run_physical_daemon.bat' to begin automated reconstruction.")

if __name__ == "__main__":
    run_calibration()
