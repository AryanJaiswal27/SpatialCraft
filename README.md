# 🛋️ SpatialCraft: Single-Image AI 3D Room Reconstruction & Physical CAD Studio

Reconstruct interactive 3D digital twin rooms from a single photograph using AI, with browser-automated LLM integration (**ChatGPT**, **Claude**, **Gemini**, and **DeepSeek**), **Physical Desktop Mouse Clicking & Screen Calibration**, **Iterative Object Refinement Loops**, **Hierarchical Furniture Attachment (Stick/Unstick)**, and real-time 3D touch manipulation over the public internet.

> **Documentation Links**:
> - [PROJECT_EXPLAINED.md](file:///C:/Users/Aryan/Desktop/SpatialCraft/PROJECT_EXPLAINED.md): Complete system architecture, dataflows, CAD coordinate standards, and exhaustive file-by-file manifest.
> - [PROMPT_HISTORY.md](file:///C:/Users/Aryan/Desktop/SpatialCraft/PROMPT_HISTORY.md): Full chronological history of all 44 user prompts and project evolution.
> - [SETUP_AND_USAGE_GUIDE.md](file:///C:/Users/Aryan/Desktop/SpatialCraft/SETUP_AND_USAGE_GUIDE.md): Operational setup guide, calibration instructions, and CLI cheat sheet.

---

## 🌟 Key Features

1. **3D Reconstruction from a Single Smartphone Photo**:
   - Capture or upload a photo of your room from any phone over cellular or Wi-Fi.
   - SpatialCraft physically switches to your open browser, attaches the photo, types the CAD reconstruction prompt, and submits it to **ChatGPT**, **Gemini**, **Claude**, or **DeepSeek**.
   - Extracts the 3D room boundaries and furniture coordinates into an interactive WebGL digital twin.

2. **Physical Desktop Clicking & Screen Calibration**:
   - Run `calibrate_clicks.bat` to teach Antigravity the exact $(X, Y)$ screen coordinates of your open browser window.
   - Run `run_physical_daemon.bat` to have Antigravity physically click, paste images, prompt your LLM, copy responses, and refine objects without login friction.

3. **Iterative Refinement Loop (Zoomed-In Crop Feedback)**:
   - SpatialCraft automatically crops every recognized furniture piece into `backend/storage/crops/`.
   - The refinement engine loops through each crop, feeding it back into the open chat to extract high-precision centimeter dimensions, materials, and fine details.

4. **Hierarchical Object Sticking & Unsticking**:
   - Stick small objects (phones, laptops, plants, lamps) onto tables or desks: they automatically snap vertically and **orbit and translate synchronously** with the parent furniture!
   - Snap wall art or mirrors flush against room walls.
   - Command `"Unstick all"` or tap `[UNSTICK]` to return to independent motion.

5. **3D Geode Matrix Core**:
   - Zero placeholder/dummy furniture on startup. Displays an 80-face dual geodesic football polyhedron showing strictly edges and vertices until a real room is captured.

6. **Interactive Mobile Touch CAD & glTF Export**:
   - Touch drag, rotate 45°, 4-way metric nudge pad, and natural language CAD modifications.
   - 1-Click export to standard **.GLB** (binary glTF 2.0 for Blender/Unity) and **.JSON**.

---

## 🚀 Quick Start Commands

### 1. Launch the Server & Public Tunnel
Double-click `run_spatialcraft.bat` or run in PowerShell:
```powershell
.\venv\Scripts\python.exe scripts\pipeline.py
```
*Starts FastAPI on Port 8000, establishes Cloudflare Tunnel, and prints your live public mobile URL.*

### 2. Calibrate Physical Screen Coordinates (One-Time)
Double-click `calibrate_clicks.bat` or run:
```powershell
.\venv\Scripts\python.exe scripts\calibrate_clicks.py
```
*Hover your mouse over the Prompt Box, Attach Button, Send Button, and Copy Button, pressing Space to lock.*

### 3. Start the Physical Click & Refinement Daemon
Double-click `run_physical_daemon.bat` or run:
```powershell
.\venv\Scripts\python.exe scripts\physical_clicker.py --daemon
```
*Listens for incoming room captures, pastes images into your open browser, and runs the iterative refinement loop.*

---

## 📂 Project Architecture

```
SpatialCraft/
├── backend/
│   ├── app.py                     # FastAPI server with WebSocket status & REST API
│   ├── config.py                  # Directory paths and server settings
│   ├── models.py                  # Pydantic models for 3D coordinates & scene graph
│   ├── services/
│   │   ├── browser_automation.py  # Playwright Chrome driver
│   │   ├── browser_targets.py     # Selectors for ChatGPT, Claude, Gemini, DeepSeek
│   │   ├── browser_prompt.py      # Spatial prompt generator & robust JSON parser
│   │   ├── cropper.py             # 2D object segmenter & EXIF transpose cropper
│   │   └── scene_service.py       # Transform propagation, sticking, & CAD parser
│   └── storage/
│       ├── uploads/               # Raw photos uploaded from mobile
│       ├── crops/                 # Segmented high-res furniture crops
│       └── scenes/                # scene.json digital twins
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SceneViewport3D.tsx        # Three.js 3D Canvas
│   │   │   ├── GeodeMatrix3D.tsx          # Geodesic football polyhedron home state
│   │   │   ├── DetailedFurnitureMesh.tsx  # Selectable furniture with attachment indicator
│   │   │   ├── RoomMesh.tsx               # Floor, boundary walls, and CAD metric grid
│   │   │   ├── MobileHeader.tsx           # Brand header, room switcher & LLM dropdown
│   │   │   ├── MobileBottomControls.tsx   # Touch inspector, stick/unstick & dock
│   │   │   ├── CalibrationModal.tsx       # Physical screen coordinates editor
│   │   │   ├── UploadModal.tsx            # Camera capture & physical clicks selector
│   │   │   ├── ChatPromptDrawer.tsx       # Natural language CAD command interpreter
│   │   │   ├── ManualPasteModal.tsx       # 2-step direct JSON ingestion fallback
│   │   │   ├── LogsModal.tsx              # Monochromatic telemetry console
│   │   │   └── QrModal.tsx                # Mobile ingress QR code & URL endpoints
│   │   ├── hooks/
│   │   │   └── useSceneStore.ts           # Zustand state store with transform propagation
│   │   └── types.ts                       # TypeScript schemas
│   └── package.json
├── scripts/
│   ├── pipeline.py                # Unified server, tunnel supervisor, & watchdog
│   ├── calibrate_clicks.py        # Interactive terminal coordinate calibrator
│   ├── physical_clicker.py        # Physical mouse driver & iterative refinement loop
│   ├── test_suite.py              # 10-point automated backend test suite
│   └── cloudflared.exe            # Cloudflare tunnel binary
├── run_spatialcraft.bat           # 1-Click production pipeline launcher
├── calibrate_clicks.bat           # 1-Click screen coordinate calibration
├── run_physical_daemon.bat        # 1-Click physical click & refinement daemon
└── physical_clicks_config.json    # Calibrated screen coordinates
```

---

## 🛠️ Operational Modes

| Mode | Trigger | Description |
| :--- | :--- | :--- |
| **Physical Clicks** | `run_physical_daemon.bat` | Uses calibrated screen coordinates to click and paste directly into your open browser window. Loops through cropped images to refine details. |
| **Browser Automation** | In-App Engine Selector | Uses Playwright to drive Chrome headless or via persistent profile (`browser_profile/`). |
| **Direct JSON Ingestion** | `PAYLOAD` Button | 1-Click copy of the CAD prompt to paste into any chat, followed by instant JSON twin rendering. |

---

## 📱 Mobile Cheat Sheet

- **Orbit / Rotate**: 1-finger drag on background.
- **Pinch Zoom**: 2 fingers pinch in/out.
- **Move Furniture**: Touch and drag selected object across floor plane (smooth offset tracking).
- **Stick to Table**: Select item (phone, laptop) -> tap **`[STICK TO TABLE]`**.
- **Unstick**: Tap **`[UNSTICK]`** in the object inspector.
- **Refine Details**: Tap **`[REFINE]`** on an object or dock to send cropped photo back to browser.
- **CAD Commands**: Tap **COMMAND** to execute natural language layout transformations.
