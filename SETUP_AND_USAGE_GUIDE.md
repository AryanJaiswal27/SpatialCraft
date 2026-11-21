# SPATIALCRAFT // COMPREHENSIVE SETUP & OPERATIONAL GUIDE
### Single-Image 3D Spatial Reconstruction, Physical Browser Automation & Interactive Mobile CAD Studio

---

## 1. SYSTEM ARCHITECTURE & WORKFLOW

SpatialCraft reconstructs interactive 3D digital twins from a single smartphone photograph, operating over public cellular networks via Cloudflare Tunnel ingress and physical desktop browser automation.

```
+---------------------------------------------------------------------------------------+
|                                    MOBILE SMARTPHONE                                   |
|   - 3D Touch Viewport (Three.js / React Three Fiber)                                   |
|   - Camera Capture & Real-Time WebSocket Telemetry HUD                                |
|   - CAD Hierarchical Controls (Stick/Unstick, Nudge, Rotate, Scale)                   |
|   - Reconstructed Room Switcher & Geode Matrix Core                                    |
+---------------------------------------------------------------------------------------+
                                           │
                                HTTPS / WSS (Public Ingress)
                                           ▼
+---------------------------------------------------------------------------------------+
|                           SPATIALCRAFT PIPELINE (PORT 8000)                           |
|   - FastAPI Server + GZip Compression + Static SPA Serving                            |
|   - Cloudflare Tunnel Supervisor (`cloudflared`) with Auto-Healing Watchdog            |
|   - Automated 2D Object Cropper (`crops/`) with EXIF Transpose Orientation            |
|   - Pydantic Scene Graph Engine with Recursive Transform Propagation                  |
|   - Physical Click Job Queue (`/api/physical_clicks/queue`)                           |
+---------------------------------------------------------------------------------------+
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
+-----------------------------------------------+ +------------------------------------+
|          PHYSICAL DESKTOP CLICKER             | |     CDP / PLAYWRIGHT DRIVER        |
|  - Windows Cursor & Keyboard Driver           | |  - Chrome DevTools Protocol        |
|  - Screen Coordinate Calibration Matrix       | |  - Automated DOM Navigation        |
|  - Clipboard Image Paste (Ctrl+V)             | |  - Gemini / Claude Automation      |
|  - Iterative Refinement Loop (Crop -> LLM)    | |  - Direct DOM Extraction           |
+-----------------------------------------------+ +------------------------------------+
                        │                                     │
                        └──────────────────┬──────────────────┘
                                           ▼
+---------------------------------------------------------------------------------------+
|                             USER'S OPEN BROWSER WINDOW                                |
|            ChatGPT (chatgpt.com)  |  Gemini (gemini.google.com)                       |
|            Claude (claude.ai)     |  DeepSeek (chat.deepseek.com)                     |
+---------------------------------------------------------------------------------------+
```

---

## 2. PREREQUISITES

Ensure the following runtimes are installed on Windows:
1. **Python**: v3.10+ (available at `python --version`)
2. **Node.js**: v18.0+ (available at `node -v`)
3. **Google Chrome**: Standard desktop installation at `C:\Program Files\Google\Chrome\Application\chrome.exe`

---

## 3. QUICK-START (STARTING THE ENTIRE SETUP)

### Step 1: Start the Production Server & Cloudflare Tunnel
In the project root, double-click **`run_spatialcraft.bat`** or execute in PowerShell:
```powershell
.\venv\Scripts\python.exe scripts\pipeline.py
```
*What this runs*:
- Starts the unified FastAPI backend on `http://0.0.0.0:8000`.
- Launches the Cloudflare Tunnel (`cloudflared.exe`) and prints your live public mobile URL.
- Automatically generates and saves `mobile_qr.png` and `tunnel_url.json`.
- Starts the `uploads/` folder watcher and health-check watchdog.

---

### Step 2: Calibrate Physical Click Screen Coordinates
To let Antigravity click, paste, and prompt directly in your open browser window:

1. Open your browser on your monitor (ChatGPT, Gemini, DeepSeek, or Claude).
2. Double-click **`calibrate_clicks.bat`** or run:
   ```powershell
   .\venv\Scripts\python.exe scripts\calibrate_clicks.py
   ```
3. Hover your mouse over each of the 4 on-screen targets and press **[SPACE]** or **[ENTER]**:
   - **Target 1: Browser Window / Tab**: Tab header to bring window to front.
   - **Target 2: Prompt Input Box**: Chat composer textarea (both photos and text prompts are pasted directly here via `Ctrl+V`).
   - **Target 3: Send Button**: The send arrow / submit button.
   - **Target 4: Copy Response Button**: The copy answer icon at the bottom of the LLM response.
4. The tool saves coordinates to `physical_clicks_config.json` and runs an optional visual hover test.

> **Tip**: Room images are copied directly to the Windows clipboard and pasted via `Ctrl+V` into the prompt box, eliminating file dialogs and reducing calibration to just 4 quick points. You can also view and manually tweak $(X, Y)$ coordinates inside the web app by clicking the **Mouse Pointer** icon in the header.

---

### Step 3: Start the Physical Click & Refinement Daemon
Double-click **`run_physical_daemon.bat`** or run:
```powershell
.\venv\Scripts\python.exe scripts\physical_clicker.py --daemon
```
*How the Antigravity refinement loop operates:*
1. **Initial 3D Reconstruction**: As soon as a photo arrives, it is pasted into the open browser to generate the initial 3D room.
2. **2D Crop Extraction**: SpatialCraft extracts high-resolution zoomed crops for every furniture item into `crops/`.
3. **Antigravity CAD Intelligence**: Antigravity steps through each furniture piece one-by-one:
   - Evaluates object category, spatial bounding box, contact surfaces, and parent/child attachments.
   - Generates a bespoke architectural prompt tailored specifically to that item (e.g. 5-star castor base vs 4-leg metal frame for chairs; chamfered edges and grommets for desks; display aspect ratio and camera bump for phones).
4. **Physical Browser Loop**: Pastes each cropped image + Antigravity's tailored prompt into your open ChatGPT / Gemini / Claude tab, extracts the response, and updates the 3D model in real time!

---

## 4. ANTIGRAVITY OBJECT-BY-OBJECT CAD PROMPT LOOP

Antigravity operates directly in the loop as the architectural CAD Director, ensuring every object is inspected and upgraded with millimeter accuracy:

```
[Initial Room 3D Twin]
         │
         ▼
[High-Res 2D Crops] ──▶ backend/storage/crops/
         │
         ▼
[Antigravity CAD Director]
  ├── Step 1: Structural Anchors (Tables, Desks, Sofas, Beds)
  ├── Step 2: Seating & Storage (Task Chairs, Bookshelves, TV Units)
  ├── Step 3: Surface Items (Monitors, Laptops, Phones, Desk Lamps)
  └── Step 4: Finishing Decor (Planters, Rugs, Wall Art)
         │
         ├─▶ Generates bespoke architectural prompt for Object #N
         ├─▶ Pastes cropped image + prompt into open browser (Ctrl+V)
         └─▶ Receives refined CAD JSON and updates 3D scene live
```

### Inspecting Prompts via CLI
To preview Antigravity's prompt generation across all objects in any scene:
```powershell
.\venv\Scripts\python.exe scripts\antigravity_loop.py
```
To trigger the physical click refinement queue across all objects:
```powershell
.\venv\Scripts\python.exe scripts\antigravity_loop.py --execute
```

### Inspecting Prompts via Mobile / Web UI
- **Dock Button (`AGY PLAN`)**: Opens the Antigravity CAD Intelligence modal showing the prioritized object list, cropped images, generated prompts, and 1-tap execution.
- **Inspector Button (`AGY PROMPT`)**: When selecting any furniture item, tap `AGY PROMPT` to view and copy its tailored Antigravity prompt.

---

## 5. THE THREE INGESTION MODES

SpatialCraft supports three distinct modes depending on your preference:

### Mode A: Physical Desktop Clicks (Recommended for Open Browser)
- **Engine**: Select `Physical Clicks` in the Capture modal.
- **How it works**: Uses the calibrated screen coordinates to drive your open, logged-in browser without login or Cloudflare blocks.
- **Refinement**: Automatically loops through cropped images (`crops/`) to upgrade individual furniture details.

### Mode B: Hands-Free Browser Automation (CDP / Playwright)
- **Engine**: Select `Gemini`, `ChatGPT`, `Claude`, or `DeepSeek`.
- **How it works**: Playwright connects to Chrome via port 9222 or launches the persistent profile in `browser_profile/`.
- **Note**: For ChatGPT/DeepSeek Cloudflare verification, run `login_helper.bat` once to sign in.

### Mode C: 2-Step Direct Ingestion (Instant Fallback)
- **Trigger**: Click **PAYLOAD** on the bottom mobile dock.
- **How it works**:
  1. Tap **COPY PROMPT** to copy the full CAD prompt with 1 click.
  2. Paste it into your personal ChatGPT/Gemini window along with your photo.
  3. Paste the returned JSON into SpatialCraft and tap **INGEST & RENDER 3D TWIN**.

---

## 5. MOBILE TOUCH CONTROLS & HIERARCHICAL ATTACHMENT

### Camera Navigation
- **1-Finger Drag**: Orbit camera around the room center.
- **Pinch**: Smooth zoom in/out.
- **2-Finger Pan**: Pan the camera view horizontally/vertically.

### Furniture Manipulation
- **Tap Object**: Selects the object and opens the responsive CAD Inspector dock.
- **Touch Drag**: Moves the object along the floor plane. (Features elevation compensation and zero touch-jumping).
- **YAW +45°**: Rotates the object clockwise around the vertical Y-axis.
- **4-Way Nudge Pad**: Fine-tune metric positions in increments of $\pm 0.2\,\text{m}$.
- **Delete**: Removes the object from the scene graph.

### Parent-Child Sticking & Attachment
- **Stick Phone/Laptop to Table**:
  - Select the phone or laptop in the 3D view.
  - In the inspector, tap **`[STICK TO TABLE]`**. The child snaps vertically flush to the tabletop.
  - When you move or rotate the table, the child object **synchronously orbits and translates with the table**!
- **Stick to Wall**:
  - Tap **`[SNAP WALL]`** or command: `"Stick art to north wall"`. Snaps flush to the nearest room wall.
- **Unsticking**:
  - In the inspector, tap **`[UNSTICK]`** to detach the object back to independent movement.
  - Command: `"Unstick all"` or `"Detach phone"`.

### Iterative Object Refinement
- **Refine Single Object**: In the inspector of any object with a cropped photo, tap **`[REFINE]`**. The daemon sends the zoomed-in crop to your open browser to refine dimensions and styling.
- **Refine Entire Scene**: In the bottom dock, tap **`[REFINE]`** to loop through all furniture items sequentially.

---

## 6. NATURAL LANGUAGE CAD COMMAND REFERENCE

Open the **COMMAND** drawer (`Terminal` button) or type via API:

| Command | Action |
| :--- | :--- |
| `Place a phone on table` | Injects a procedural smartphone resting directly on top of the desk/table and links them hierarchically. |
| `Place a laptop on desk` | Injects an ultrabook with keyboard and display resting flush on the desk. |
| `Stick phone to table` | Links the existing phone to the table with elevation auto-snapping. |
| `Snap art to north wall` | Snaps canvas art flush against the north boundary wall. |
| `Unstick all` | Detaches all objects in the room to independent motion. |
| `Translate sofa X -0.5m` | Translates the sofa left by $0.5\,\text{m}$ (propagating movement to any attached children). |
| `Rotate coffee table 90 deg`| Rotates table 90° clockwise (orbiting all tabletop objects around the table center). |
| `Set wall color to #dedad3` | Updates the matte plaster wall material tint. |
| `Insert floor lamp` | Adds a procedural stainless-steel floor lamp with active lighting. |
| `Remove selected furniture` | Deletes the targeted piece and unsticks any children. |

---

## 7. EXPORTING 3D MODELS

From the **EXPORT** button on the bottom mobile dock:
- **Download .GLB**: Generates a standard binary glTF 2.0 file including all meshes, procedural geometries, textures, materials, and lighting. Imports directly into Blender, Unity, Unreal Engine, WebXR, or Apple Reality Composer.
- **Download .JSON**: Exports the complete Pydantic Scene Graph hierarchy with exact metric coordinates, dimensions, yaw rotations, bounding boxes, and attachment IDs.

---

## 8. SUMMARY OF CLI COMMANDS

| Task | Command |
| :--- | :--- |
| **Start Everything** | `.\run_spatialcraft.bat` or `.\venv\Scripts\python.exe scripts\pipeline.py` |
| **Calibrate Clicks** | `.\calibrate_clicks.bat` or `.\venv\Scripts\python.exe scripts\calibrate_clicks.py` |
| **Start Desktop Daemon** | `.\run_physical_daemon.bat` or `.\venv\Scripts\python.exe scripts\physical_clicker.py --daemon` |
| **Authenticate Browser**| `.\login_helper.bat` |
| **Rebuild Frontend** | `npm --prefix frontend run build` |
| **Run Test Suite** | `.\venv\Scripts\python.exe scripts\test_suite.py` |
