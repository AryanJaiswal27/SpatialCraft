import asyncio
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, BrowserContext

from ..config import ROOT_DIR, UPLOADS_DIR, SCENES_DIR
from .browser_targets import LLM_TARGET_CONFIGS
from .browser_prompt import generate_spatial_prompt, parse_llm_json_response, build_scene_from_parsed_data
from .scene_service import save_scene, get_scene
from .cropper import crop_objects_from_image

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = ROOT_DIR / "browser_profile"

async def automate_llm_in_browser(
    target: str,
    image_path: Path,
    scene_id: str,
    status_callback=None
) -> Optional[Dict[str, Any]]:
    """
    Physically automates Google Chrome:
    1. Opens or focuses the selected LLM website (ChatGPT, Claude, Gemini, DeepSeek).
    2. Uploads the image file via the attachment input.
    3. Types the spatial prompt into the prompt box.
    4. Clicks Send.
    5. Waits for generation to complete and extracts the JSON output.
    """
    config = LLM_TARGET_CONFIGS.get(target.lower())
    if not config:
        raise ValueError(f"Unknown target LLM: {target}. Must be chatgpt, claude, gemini, or deepseek.")

    def log_status(msg: str):
        print(f"[{config['name']} Automation] {msg}")
        if status_callback:
            status_callback(msg)

    log_status(f"Initializing browser session for {config['name']}...")
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = None
        context = None
        is_cdp = False
        # Step 1: Check if user has an active Chrome instance running with remote debugging port 9222
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222", timeout=2500)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            is_cdp = True
            log_status("Connected directly to user's running Chrome with full login session!")
        except Exception:
            # Step 2: Fall back to persistent profile
            log_status(f"Launching persistent Chrome profile at {USER_DATA_DIR.name}...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
                headless=False,
                viewport={"width": 1280, "height": 850},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized"
                ]
            )

        page = None
        if is_cdp:
            # Look for an existing tab with this LLM already open
            target_domain = config["url"].split("//")[-1].split("/")[0]
            for p_tab in context.pages:
                if target_domain in p_tab.url:
                    page = p_tab
                    log_status(f"Reusing active {config['name']} tab: {page.url}")
                    try:
                        await page.bring_to_front()
                    except Exception:
                        pass
                    break

        if not page:
            page = await context.new_page() if is_cdp else (context.pages[0] if context.pages else await context.new_page())
            log_status(f"Navigating to {config['url']}...")
            await page.goto(config["url"], wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2)

        # Check if the page is currently on a login / sign-in screen or Cloudflare challenge
        current_url = page.url.lower()
        title = ""
        try:
            title = (await page.title()).lower()
        except Exception:
            pass

        is_cf = "__cf_chl" in current_url or "just a moment" in title or "cloudflare" in title or "challenge" in current_url
        is_auth = "accounts.google.com" in current_url or "login" in current_url or "signin" in current_url or "auth" in current_url

        if is_cf:
            log_status(f"[SECURITY CHALLENGE] Cloudflare verification active on {config['name']}. Please click the checkbox / verify in the visible Chrome window!")
            for _ in range(30):
                await asyncio.sleep(2)
                try:
                    cur_title = (await page.title()).lower()
                    if "__cf_chl" not in page.url.lower() and "just a moment" not in cur_title:
                        log_status("[VERIFICATION SUCCESS] Challenge passed. Resuming automated reconstruction...")
                        await asyncio.sleep(2)
                        break
                except Exception:
                    pass
        elif is_auth:
            log_status(f"[AUTH REQUIRED] {config['name']} is currently at login screen. Please sign in in the visible browser window!")
            for _ in range(30):
                await asyncio.sleep(2)
                if "accounts.google.com" not in page.url.lower() and "login" not in page.url.lower() and "auth" not in page.url.lower():
                    log_status("[AUTH SUCCESS] Login detected. Resuming automated reconstruction...")
                    await asyncio.sleep(2)
                    break

        # 1. Handle file attachment
        log_status("Locating image upload input...")
        file_input = None
        for sel in config["file_input_selectors"]:
            try:
                el = await page.wait_for_selector(sel, state="attached", timeout=1500)
                if el:
                    file_input = el
                    break
            except Exception:
                continue

        # If file input is hidden behind an attach button, click the button first
        if not file_input:
            for attach_sel in config["attach_button_selectors"]:
                try:
                    btn = await page.wait_for_selector(attach_sel, state="visible", timeout=2500)
                    if btn:
                        log_status(f"Clicked attach button: {attach_sel}")
                        await btn.click()
                        await asyncio.sleep(1.2)
                        break
                except Exception:
                    continue

            for sel in config["file_input_selectors"]:
                try:
                    el = await page.wait_for_selector(sel, state="attached", timeout=3000)
                    if el:
                        file_input = el
                        break
                except Exception:
                    continue

        if file_input:
            log_status(f"Attaching image: {image_path.name}")
            await file_input.set_input_files(str(image_path))
            await asyncio.sleep(3.5) # Allow image thumbnail upload to settle
            try:
                await page.keyboard.press("Escape")
            except Exception:
                pass
        else:
            log_status("Warning: Could not locate file input for image attachment.")

        # 2. Input the Spatial Prompt
        prompt_text = generate_spatial_prompt()
        log_status("Typing 3D Spatial Reconstruction prompt...")

        prompt_box = None
        for psel in config["prompt_input_selectors"]:
            try:
                box = await page.wait_for_selector(psel, state="visible", timeout=3000)
                if box:
                    prompt_box = box
                    break
            except Exception:
                continue

        if not prompt_box:
            log_status("Could not locate prompt input. Please ensure you are logged in.")
            return None

        await prompt_box.click()
        await asyncio.sleep(0.5)

        # Clear existing text and insert prompt cleanly
        try:
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
        except Exception:
            pass

        try:
            await page.keyboard.insert_text(prompt_text)
        except Exception:
            try:
                await prompt_box.fill(prompt_text)
            except Exception:
                await page.evaluate("""([sel, text]) => {
                    const el = document.querySelector(sel);
                    if (el) {
                        el.innerText = text;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""", [config["prompt_input_selectors"][0], prompt_text])

        await asyncio.sleep(1)

        # 3. Click Send Button
        log_status("Clicking Send button...")
        send_clicked = False
        for ssel in config["send_button_selectors"]:
            try:
                sbtn = await page.wait_for_selector(ssel, state="visible", timeout=2500)
                if sbtn and await sbtn.is_enabled():
                    await sbtn.click()
                    send_clicked = True
                    log_status(f"Sent prompt via: {ssel}")
                    break
            except Exception:
                continue

        if not send_clicked:
            log_status("Sending via Enter key fallback...")
            try:
                await prompt_box.press("Enter")
            except Exception:
                await page.keyboard.press("Enter")

        # 4. Wait for response generation to complete
        log_status("Waiting for LLM to stream 3D room data...")
        await asyncio.sleep(6) # Initial wait for streaming to begin

        # Wait until stop button disappears or response completes
        max_wait_seconds = 90
        waited = 0
        while waited < max_wait_seconds:
            is_streaming = False
            for stop_sel in config["stop_button_selectors"]:
                try:
                    stop_btn = await page.query_selector(stop_sel)
                    if stop_btn and await stop_btn.is_visible():
                        is_streaming = True
                        break
                except Exception:
                    pass

            if not is_streaming and waited > 6:
                # Finished streaming!
                log_status("LLM has completed generating response.")
                break

            await asyncio.sleep(2)
            waited += 2

        # 5. Extract response text
        log_status("Extracting generated 3D data...")
        raw_output = ""
        for resp_sel in config["response_selectors"]:
            try:
                responses = await page.query_selector_all(resp_sel)
                if responses:
                    last_resp = responses[-1]
                    raw_output = await last_resp.inner_text()
                    if "{" in raw_output and "objects" in raw_output:
                        break
            except Exception:
                continue

        if not raw_output:
            # Fallback: get entire page text or code blocks
            code_blocks = await page.query_selector_all("pre, code, .code-block")
            for cb in reversed(code_blocks):
                txt = await cb.inner_text()
                if "room" in txt and "objects" in txt:
                    raw_output = txt
                    break

        if not raw_output:
            try:
                body_txt = await page.evaluate("() => document.body.innerText")
                if "{" in body_txt and "objects" in body_txt:
                    raw_output = body_txt
            except Exception:
                pass

        # Save raw output to storage/scenes
        raw_output_path = SCENES_DIR / f"{scene_id}_raw.txt"
        with open(raw_output_path, "w", encoding="utf-8") as f:
            f.write(raw_output)

        parsed_data = parse_llm_json_response(raw_output)
        if not parsed_data:
            log_status("Warning: Could not automatically parse JSON from output.")
            return None

        # Build scene graph
        image_url = f"/api/uploads/{image_path.name}"
        scene = build_scene_from_parsed_data(scene_id, image_url, parsed_data)
        
        # Crop objects from image
        crop_objects_from_image(image_path, scene_id, scene.objects)
        
        save_scene(scene)
        log_status(f"Scene {scene_id} generated successfully with {len(scene.objects)} objects!")
        return scene.model_dump()

