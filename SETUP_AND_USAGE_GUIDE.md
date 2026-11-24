# SPATIALCRAFT // COMPREHENSIVE OPERATIONAL & USAGE GUIDE
### Single-Image 3D Spatial Twin Reconstruction, Physical Screen Automation & Mobile CAD Studio

---

## 1. SYSTEM ARCHITECTURE & STREAMLINED FLOW

SpatialCraft transforms a single smartphone photograph into an interactive 3D architectural digital twin. It uses physical desktop screen automation driving your open browser windows (Google Gemini, OpenAI ChatGPT, or DeepSeek Chat) alongside an autonomous 5-minute CAD backup engine.

```
+---------------------------------------------------------------------------------------+
|                                    MOBILE SMARTPHONE                                  |
|   - 3D Touch Viewport (Three.js / React Three Fiber)                                  |
|   - Camera Capture with 3 Physical Buttons: Gemini, ChatGPT, DeepSeek                 |
|   - CAD Hierarchical Controls (Stick to Table, Snap Wall, Unstick, Nudge, Rotate)      |
|   - Antigravity CAD Director Loop Inspector (AGY PLAN)                                |
+---------------------------------------------------------------------------------------+
                                           │
                                HTTPS / WSS (Cloudflare Ingress)
                                           ▼
+---------------------------------------------------------------------------------------+
|                           SPATIALCRAFT PIPELINE (PORT 8000)                          |
|   - FastAPI Server + GZip Compression + Production React SPA Serving                  |
|   - Cloudflare Tunnel Supervisor with Auto-Healing Watchdog                           |
|   - Automated 2D Object Cropper (`crops/`) with EXIF Transpose Orientation           |
|   - 5-Minute Autonomous Watchdog Timer & Scene Fallback Generator                     |
|   - Physical Click Job Queue (`/api/physical_clicks/queue`)                          |
+---------------------------------------------------------------------------------------+
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
+--------------------------------------------------+ +----------------------------------+
|           PHYSICAL DESKTOP CLICK DAEMON          | |     ANTIGRAVITY CAD BACKUP       |
|  - Windows Cursor & Keystroke Automation         | |  - 5-Minute Autonomous Trigger   |
|  - Multi-LLM Presets (Gemini, ChatGPT, DeepSeek) | |  - Dominant Palette Extraction    |
|  - Clipboard Direct Paste (Ctrl+V)               | |  - Auto 2D Crop Generation       |
|  - Continuous Downward Token Auto-Scroll         | |  - High-Detail CSG Part Builder  |
|  - Sequential Object Refinement Loop             | |    (10-25 parts per object)      |
+--------------------------------------------------+ +----------------------------------+
                         │                                   │
                         ▼                                   ▼
+---------------------------------------------------------------------------------------+
|                                  OPEN BROWSER WINDOW                                  |
|      Google Gemini (gemini.google.com)  |  OpenAI ChatGPT (chatgpt.com)               |
|                           DeepSeek Chat (chat.deepseek.com)                           |
+---------------------------------------------------------------------------------------+
```

---

## 2. PREREQUISITES

Ensure the following runtimes are installed on your Windows machine:
1. **Python**: v3.10+ (available at `python --version`)
2. **Node.js**: v18.0+ (available at `node -v`)
3. **Web Browser**: Standard installation with tabs open to Gemini, ChatGPT, or DeepSeek.

---

## 3. QUICK-START GUIDE (4 SIMPLE STEPS)

### Step 1: Start the Production Server & Cloudflare Tunnel
In PowerShell in the project directory, run:
```powershell
.\run_spatialcraft.bat
```
*(Or execute `.\venv\Scripts\python.exe scripts\pipeline.py`)*

*What this runs:*
- Starts the unified FastAPI backend on `http://localhost:8000`.
- Launches the Cloudflare Tunnel (`cloudflared.exe`) and prints your live public mobile URL.
- Automatically generates and saves `mobile_qr.png` and `tunnel_url.json`.
- Starts the uploads folder watcher and health-check watchdog.

---

### Step 2: Calibrate Screen Click Coordinates for Your LLM
To let the desktop daemon move the mouse, paste images, and copy responses:

```powershell
# For Google Gemini (Default):
.\calibrate_clicks.bat gemini

# For OpenAI ChatGPT:
.\calibrate_clicks.bat chatgpt

# For DeepSeek Chat:
.\calibrate_clicks.bat deepseek
```
*(Remember the `.\` prefix required by PowerShell!)*

Select **`[B] Calibrate Browser targets only`** to quickly calibrate targets 1 to 4 in 15 seconds:
- **Target 1: Browser Window / Tab**: Tab header or taskbar icon to bring the window to the foreground.
- **Target 2: Prompt Input Box**: Chat composer textarea (both photos and text prompts are pasted directly here via `Ctrl+V`).
- **Target 3: Send Button**: The send arrow or submit button.
- **Target 4: Copy Response Button**: The copy answer icon at the bottom of the LLM response.

Coordinates are stored in `physical_clicks_config.json`. You can also visually inspect and test hovers in the web app by clicking the **Mouse Pointer** icon in the header.

---

### Step 3: Start the Desktop Physical Click Daemon
In your interactive PowerShell terminal, run:
```powershell
.\run_physical_daemon.bat
```
*(Keep this window open in the background so it can physically move the mouse and paste prompts whenever a capture or refinement is queued).*

---

### Step 4: Capture Room from Phone or Desktop
1. Scan the QR code with your smartphone camera (tap the **`[QR]`** icon in the top header).
2. Tap the white **`[CAPTURE ROOM]`** button on the bottom dock.
3. Select your preferred physical target:
   - **Physical on Gemini** (`gemini.google.com`)
   - **Physical on ChatGPT** (`chatgpt.com`)
   - **Physical on DeepSeek** (`chat.deepseek.com`)
4. Take a photo or upload an image file and tap **INGEST & RECONSTRUCT 3D TWIN**.
5. The desktop daemon automatically brings your browser to the foreground, pastes the image and spatial CAD prompt, clicks Send, extracts the balanced 3D JSON, and builds the room!

---

## 4. THE 5-MINUTE AUTONOMOUS ANTIGRAVITY CAD BACKUP GUARANTEE

The system has a built-in autonomous fallback loop:
```
1) Image and prompt into browser LLM
2) Antigravity gets output
3) Antigravity takes individual objects and tells browser llm to improve it one by one
4) Step 3 repeats
5) If nothing received in 5 mins, Antigravity itself builds the scene, looping over individual objects and improving them using the image
```

### How the Backup Works:
- **Generation Timeout**: Configured to **5 minutes (300 seconds)** across all presets and daemon loops.
- **Initial Reconstruction Fallback**: If the browser LLM does not produce balanced output within 5 minutes (due to network timeout, CAPTCHA, or tab minimization):
  1. Antigravity autonomously analyzes the room photo using PIL.
  2. Extracts dominant floor and wall color palettes.
  3. Reconstructs the 3D room boundaries and object placements.
  4. Automatically crops high-resolution images for every detected object into `backend/storage/crops/`.
- **Object Refinement Fallback**: When looping through individual objects, if the browser LLM fails to output within 5 minutes:
  1. Antigravity analyzes the object's cropped image.
  2. Constructs a rich, multi-part 3D CSG mesh (`parts` array with 10 to 25 geometric components) tailored specifically to the furniture category and dimensions.
  3. Updates the object in the scene live!

---

## 5. DYNAMIC 3D MESH GENERATION (PARTS DECOMPOSITION)

Every furniture item can be represented as an array of constructive solid geometry `parts` (`box`, `cylinder`, `sphere`, `cone`, `torus`, `plane`):

| Category | Typical Number of Parts | Decomposed 3D Mesh Components |
| :--- | :---: | :--- |
| **Desk / Table** | 10 parts | Tabletop slab, edge banding, vertical slab gable panels, recessed modesty panel, 4 floor leveling glides, cable pass-through grommet ring. |
| **Ergonomic Chair** | 19 parts | Contoured seat cushion, curved backrest, lumbar support pad, left/right armrest stalks + soft pads, pneumatic cylinder, 5-point star base legs, 5 caster wheels. |
| **Sofa / Couch** | 11 parts | Heavy plinth chassis, left/right track armrests, 2-3 deep seat cushions, 2-3 backrest cushions with piping, 4 corner legs. |
| **Laptop** | 5 parts | Aluminum unibody base, recessed dark keyboard well, multi-touch trackpad, angled display lid (pitch ~115°), glass retina screen. |
| **Smartphone** | 3 parts | Unibody metallic chassis, edge-to-edge dark glass OLED screen, rear camera island bump. |
| **Monitor** | 4 parts | Widescreen screen panel, matte display, vertical stand column, weighted base plate. |
| **Task Lamp** | 10 parts | Weighted circular base, slender upright stem, lamp shade diffuser, warm glowing emitter core. |
| **Potted Plant** | 7 parts | Ceramic planter pot, organic dark soil disk, multiple angled foliage leaf fronds. |
| **Floor Rug** | 2 parts | Large woven area rug body, perimeter binding trim. |
| **Wall Art** | 3 parts | Outer gallery frame molding, white archival matting border, inner canvas artwork. |

---

## 6. CAD VIEWPORT TOUCH & MOUSE CONTROLS

### Viewport Navigation
- **Orbit Camera**: 1-Finger Drag (Touch) / Left-Click Drag (Mouse)
- **Zoom In/Out**: Pinch (Touch) / Scroll Wheel (Mouse)
- **Pan Viewport**: 2-Finger Drag (Touch) / Right-Click Drag (Mouse)

### Object Manipulation
- **Select Object**: Tap any furniture piece in the 3D scene to open the CAD Inspector.
- **Drag along Floor**: Touch and drag selected piece across the floor plane. (Features elevation compensation and zero touch jumping).
- **YAW +45°**: Rotates the piece 45 degrees clockwise around its vertical Y-axis.
- **4-Way Nudge Pad**: Metric positioning fine-tuner in increments of $\pm 0.2\,\text{m}$.
- **Delete**: Removes the piece from the scene graph.

### Hierarchical Parent-Child Attachments
- **Stick to Table**:
  - Select a tabletop item (laptop, smartphone, lamp, coffee cup).
  - Tap **`[STICK TO TABLE]`**. The child snaps vertically flush to the table's top surface.
  - When moving or rotating the table, child objects **synchronously translate and orbit with the table**!
- **Snap Wall**:
  - Tap **`[SNAP WALL]`** to snap paintings, wall clocks, or media consoles flush against the nearest boundary wall.
- **Unstick**:
  - Tap **`[UNSTICK]`** to detach the child object back to independent floor motion.

---

## 7. ANTIGRAVITY CAD PROMPTER & REFINEMENT LOOP

- **Inspect Plan (`AGY PLAN`)**: Tap **`AGY PLAN`** in the bottom dock to view the prioritized sequence of objects, high-resolution cropped photos, and tailored prompts.
- **Refine Entire Scene (`REFINE`)**: Tap **`REFINE`** in the bottom dock to sequentially loop over all furniture items in the room.
- **Refine Single Object**: In the object inspector, tap **`[REFINE]`** to upgrade that specific piece.

---

## 8. EXPORTING 3D MODELS

From the **`EXPORT`** option in the bottom dock:
- **Download .GLB**: Exports a standard binary glTF 2.0 file containing all meshes, parts, PBR materials, textures, and lighting. Imports directly into **Blender**, **Unity**, **Unreal Engine**, **WebXR**, or **Apple Reality Composer**.
- **Download .JSON**: Exports the complete Pydantic Scene Graph hierarchy with exact metric dimensions, positions, yaw angles, bounding boxes, and attachment parent IDs.

---

## 9. NATURAL LANGUAGE COMMAND REFERENCE

Open the **COMMAND** drawer (`Terminal` button) or submit via API:

| Command | Action |
| :--- | :--- |
| `Place a phone on table` | Injects a procedural smartphone resting directly on top of the desk and links them hierarchically. |
| `Place a laptop on desk` | Injects an ultrabook with keyboard and display resting flush on the desk. |
| `Stick phone to table` | Links the existing phone to the table with elevation auto-snapping. |
| `Snap art to north wall` | Snaps canvas art flush against the north boundary wall. |
| `Unstick all` | Detaches all objects in the room to independent motion. |
| `Translate sofa X -0.5m` | Translates the sofa left by $0.5\,\text{m}$ (propagating movement to attached cushions/items). |
| `Rotate coffee table 90 deg` | Rotates table 90° clockwise (orbiting all tabletop objects around the table center). |
| `Set wall color to #dedad3` | Updates the matte plaster wall material tint. |
| `Insert floor lamp` | Adds a procedural stainless-steel floor lamp with active lighting. |
| `Remove selected furniture` | Deletes the targeted piece and unsticks any children. |

---

## 10. CLI COMMAND CHEAT SHEET

| Operation | PowerShell Command |
| :--- | :--- |
| **Start Everything** | `.\run_spatialcraft.bat` |
| **Calibrate Gemini** | `.\calibrate_clicks.bat gemini` |
| **Calibrate ChatGPT** | `.\calibrate_clicks.bat chatgpt` |
| **Calibrate DeepSeek** | `.\calibrate_clicks.bat deepseek` |
| **Start Click Daemon** | `.\run_physical_daemon.bat` |
| **Rebuild Frontend** | `npm --prefix frontend run build` |
| **Test Suite** | `.\venv\Scripts\python.exe scripts\test_suite.py` |
