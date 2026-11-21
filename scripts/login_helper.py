import asyncio
import os
import sys
import ctypes
from pathlib import Path
from playwright.async_api import async_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROOT_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = ROOT_DIR / "browser_profile"

user32 = ctypes.windll.user32

def bring_chrome_to_front():
    try:
        import psutil
        chrome_pids = set()
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if p.info['name'] and 'chrome' in p.info['name'].lower():
                    cmd = " ".join(p.info['cmdline'] or [])
                    if 'browser_profile' in cmd:
                        chrome_pids.add(p.info['pid'])
            except Exception:
                pass
        
        hwnds = []
        def enum_cb(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                lpdw_pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw_pid))
                if lpdw_pid.value in chrome_pids:
                    hwnds.append(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        
        for h in hwnds:
            user32.ShowWindow(h, 9)  # SW_RESTORE
            user32.SetForegroundWindow(h)
    except Exception as e:
        pass

async def check_chatgpt(page) -> bool:
    try:
        url = page.url.lower()
        if "__cf_chl" in url or "auth0" in url or "login" in url or "auth" in url:
            return False
        
        # Check for profile button (only visible when logged in)
        user_menu = await page.query_selector("[data-testid='profile-button'], button[aria-label*='User profile'], [data-testid='user-menu-button'], button[aria-label*='Account']")
        if user_menu:
            return True
            
        # Check if Log in button is NOT present and prompt is present
        login_btns = await page.query_selector_all("button:has-text('Log in'), a:has-text('Log in'), [data-testid='login-button']")
        prompt = await page.query_selector("textarea, #prompt-textarea, [contenteditable='true']")
        if prompt and len(login_btns) == 0:
            return True
            
        return False
    except Exception:
        return False

async def check_deepseek(page) -> bool:
    try:
        url = page.url.lower()
        if "sign_in" in url or "login" in url:
            return False
        
        # DeepSeek when logged out shows sign_in form or login button
        login_btn = await page.query_selector("button:has-text('Log In'), button:has-text('Sign In'), button:has-text('登录'), a[href*='sign_in']")
        prompt = await page.query_selector("textarea, [contenteditable='true'], input[placeholder*='Message']")
        
        if prompt and not login_btn:
            return True
            
        return False
    except Exception:
        return False

async def main():
    print("=" * 65, flush=True)
    print("  SPATIALCRAFT // LLM AUTHENTICATION WIZARD", flush=True)
    print("=" * 65, flush=True)
    print(f"Profile: {USER_DATA_DIR.name}", flush=True)
    print("Opening visible Google Chrome window on your screen...", flush=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
            headless=False,
            viewport=None,  # Crucial: None gives full native desktop window
            args=[
                "--disable-blink-features=AutomationControlled",
                "--window-size=1280,850",
                "--window-position=50,50",
                "--new-window",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )

        # Tab 1: ChatGPT
        p_chatgpt = context.pages[0] if context.pages else await context.new_page()
        print("\n[Tab 1] Loading https://chatgpt.com ...", flush=True)
        try:
            await p_chatgpt.goto("https://chatgpt.com", wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"ChatGPT loading notice: {e}", flush=True)

        # Tab 2: DeepSeek
        p_deepseek = await context.new_page()
        print("[Tab 2] Loading https://chat.deepseek.com ...", flush=True)
        try:
            await p_deepseek.goto("https://chat.deepseek.com", wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"DeepSeek loading notice: {e}", flush=True)

        # Bring ChatGPT tab to front
        try:
            await p_chatgpt.bring_to_front()
        except Exception:
            pass

        # Bring native Chrome window to foreground
        await asyncio.sleep(1)
        bring_chrome_to_front()

        print("\n" + "=" * 65, flush=True)
        print("ACTION REQUIRED IN THE CHROME WINDOW ON YOUR SCREEN:", flush=True)
        print("  1. ChatGPT tab: Solve any Cloudflare check and Log In.", flush=True)
        print("  2. DeepSeek tab: Click tab, solve verification, and Log In.", flush=True)
        print("=" * 65, flush=True)
        print("Actively waiting for your logins...", flush=True)

        chatgpt_ok = False
        deepseek_ok = False

        # Monitor loop for up to 15 minutes (450 iterations * 2s)
        for step in range(1, 451):
            await asyncio.sleep(2)

            if not context.pages:
                print("\nBrowser was closed. Exiting wizard.", flush=True)
                break

            if not chatgpt_ok:
                if await check_chatgpt(p_chatgpt):
                    chatgpt_ok = True
                    print("\n>>> [SUCCESS] ChatGPT login detected! Auth session captured.", flush=True)

            if not deepseek_ok:
                if await check_deepseek(p_deepseek):
                    deepseek_ok = True
                    print("\n>>> [SUCCESS] DeepSeek login detected! Auth session captured.", flush=True)

            if chatgpt_ok and deepseek_ok:
                print("\n" + "=" * 65, flush=True)
                print(">>> SUCCESS: BOTH CHATGPT AND DEEPSEEK ARE LOGGED IN! <<<", flush=True)
                print("All credentials and tokens are saved permanently to disk.", flush=True)
                print("SpatialCraft can now reconstruct rooms with Gemini, ChatGPT, AND DeepSeek!", flush=True)
                print("=" * 65, flush=True)
                print("Flushing cookies to disk (waiting 10s)...", flush=True)
                await asyncio.sleep(10)
                break

            if step % 8 == 0:
                cg = "LOGGED IN" if chatgpt_ok else "Waiting..."
                ds = "LOGGED IN" if deepseek_ok else "Waiting..."
                print(f"[{step*2}s] Status -> ChatGPT: [{cg}] | DeepSeek: [{ds}]", flush=True)

        try:
            await context.close()
        except Exception:
            pass
        print("Setup complete! Browser closed.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
