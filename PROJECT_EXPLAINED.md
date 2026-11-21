# SPATIALCRAFT // COMPREHENSIVE ARCHITECTURE & FILE MANIFEST
### In-Depth System Blueprint, Operational Dataflows, Coordinate Standards & Complete File Dictionary

---

## 1. PROJECT OVERVIEW & ARCHITECTURAL PHILOSOPHY

**SpatialCraft** is an end-to-end, mobile-first 3D digital twin room reconstruction studio. It translates a single photograph captured on a standard smartphone into an interactive, photorealistic, metric-accurate CAD scene graph.

SpatialCraft is architected on three core tenets:
1. **Zero-API Physical Desktop LLM Automation**: Instead of requiring paid API keys or exposing developers to rate limits and anti-bot challenges, SpatialCraft drives the user's open desktop browser (ChatGPT, Gemini, Claude, DeepSeek) through calibrated physical mouse coordinates and Windows clipboard data transfer (`Ctrl+V`).
2. **Antigravity CAD Intelligence Director**: Antigravity orchestrates an iterative, object-by-object refinement loop. It inspects every furniture item's category, bounding box, and contact surfaces, engineers tailored architectural prompts, and refines metric bounds down to millimeters.
3. **Hierarchical 3D Scene Graph Engine**: Implements CAD-grade parent-child kinematic attachments (e.g., phones/laptops sticking to tables; wall art snapping to walls), with recursive transform propagation and cycle protection.

---

## 2. THE COMPLETE END-TO-END SYSTEM FLOW

```
[Smartphone Camera]
         │
         ▼  (HTTPS / WSS via Cloudflare Ingress)
[FastAPI Backend :8000]
         │
         ├─▶ Saves photo to uploads/ & generates high-res crops/
         ├─▶ Ingests scene graph into backend/storage/scenes/
         └─▶ Enqueues job to /api/physical_clicks/queue
                 │
                 ▼
[Physical Desktop Clicker Daemon]
  ┌─────────────────────────────────────────────────────────────┐
  │ PHASE 1: INITIAL ROOM RECONSTRUCTION                        │
  │  1. Brings open browser tab to foreground.                  │
  │  2. Copies room photo to Windows Clipboard (SetImage).      │
  │  3. Clicks composer & pastes image via Ctrl+V.              │
  │  4. Copies master CAD prompt & pastes via Ctrl+V.           │
  │  5. Clicks Send -> Waits for completion -> Clicks Copy.     │
  │  6. SpatialCraft parses 3D JSON & renders room model.       │
  └─────────────────────────────────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ PHASE 2: ANTIGRAVITY OBJECT-BY-OBJECT REFINEMENT LOOP       │
  │  Loops for Object 1 through Object N (ALL objects):         │
  │  1. Antigravity inspects object semantics & attachments.    │
  │  2. Generates bespoke CAD prompt for this specific item.    │
  │  3. Copies item's zoomed 2D crop (storage/crops/) to clip.  │
  │  4. Pastes crop via Ctrl+V -> Pastes tailored CAD prompt.   │
  │  5. Dispatches -> Detects completion -> Extracts output.    │
  │  6. Updates object dimensions, materials, and colors live.  │
  │  7. Broadcasts WebSocket progress to connected mobile view. │
  └─────────────────────────────────────────────────────────────┘
                 │
                 ▼
[Interactive 3D Touch Viewport (Three.js / React Three Fiber)]
  - Orbit, pan, pinch-to-zoom with touch isolation.
  - 4-way metric nudge, YAW rotation, CAD inspector dock.
  - Hierarchical sticking/unsticking (table moves carry phone).
  - 1-click glTF (.GLB) and JSON scene graph export.
```

---

## 3. 3D COORDINATE SYSTEM & CAD CONVENTIONS

- **Ground Level**: Floor plane is fixed at $Y = 0.0\,\text{m}$.
- **Object Elevational Center**: The $Y$ coordinate represents the center of mass ($Y = \text{height} / 2$), ensuring procedural boxes and imported glTF meshes rest flush on surfaces without clipping or hovering.
- **Horizontal Metric Grid**:
  - Room origin is $(X = 0, Z = 0)$ on the floor.
  - $X$: Ranges from $-\text{width}/2$ (West wall) to $+\text{width}/2$ (East wall).
  - $Z$: Ranges from $-\text{depth}/2$ (North/far wall) to $+\text{depth}/2$ (South/camera-near wall).
  - Rotation ($\text{Yaw}$): Counter-clockwise degrees around the vertical $Y$ axis ($0^\circ, 45^\circ, 90^\circ, 180^\circ, 270^\circ$).

---

## 4. COMPLETE FILE-BY-FILE MANIFEST

### Root Directory

| File | Purpose & Role |
| :--- | :--- |
| `run_spatialcraft.bat` | **Main Application Launcher**. Starts the unified supervisor pipeline (`pipeline.py`), which launches the FastAPI server, Cloudflare tunnel, static frontend delivery, and file watcher. |
| `run_physical_daemon.bat` | **Desktop Automation Launcher**. Spawns `physical_clicker.py --daemon` on the user's interactive desktop (`WinSta0\Default`), listening for jobs and driving physical clicks. |
| `calibrate_antigravity.bat` | **Unhurried Screen Calibrator Launcher**. Runs `calibrate_clicks.py` with zero countdown timers, letting the user position their cursor and lock coordinates using `[SPACE]`. |
| `calibrate_clicks.bat` | Alternate shortcut to the screen calibrator. |
| `login_helper.bat` | **Browser Profile Authenticator**. Launches an isolated Chrome instance with `browser_profile/` allowing one-time manual sign-in to ChatGPT, Claude, Gemini, or DeepSeek for Mode B CDP automation. |
| `physical_clicks_config.json` | **Screen Matrix Configuration**. Stores display resolution ($1920 \times 1080$), monitor $(X, Y)$ coordinates for the 5 targets (`browser_tab`, `prompt_box`, `send_button`, `copy_button`, `ide_chat_box`), and timing delays. |
| `mobile_qr.png` | **Dynamic Ingress QR Code**. Auto-generated upon pipeline startup, encoding the live Cloudflare public URL for 1-second mobile smartphone onboarding. |
| `LATEST_TUNNEL_URL.txt` | Text file containing the active Cloudflare ingress URL (e.g. `https://...trycloudflare.com`). |
| `.processed_uploads.json` | Hash tracker preventing the folder watcher from re-processing existing room photos. |
| `pipeline.log` | Persistent execution log capturing daemon output, request telemetry, and error traces. |
| `SETUP_AND_USAGE_GUIDE.md` | Exhaustive user operational guide, CLI reference, and troubleshooting cheat sheet. |
| `README.md` | GitHub repository overview, architectural highlights, and quickstart documentation. |
| `giga prompt.txt` | Original project requirements specification. |

---

### Backend Directory (`backend/`)

| File | Purpose & Role |
| :--- | :--- |
| `backend/app.py` | **FastAPI Application & API Gateway**. Defines REST endpoints (`/api/scenes`, `/api/upload`, `/api/physical_clicks/*`, `/api/scene/{id}/antigravity_plan`), WebSocket endpoint (`/ws/{scene_id}`), static file serving, and GZip compression. |
| `backend/config.py` | **Central Configuration Module**. Defines filesystem paths (`UPLOADS_DIR`, `CROPS_DIR`, `SCENES_DIR`), default host/port settings, and engine state management (`get_current_engine`, `set_current_engine`). |
| `backend/models.py` | **Pydantic Data Schemas**. Strongly-typed definitions for `Vector3D`, `Dimensions3D`, `Rotation3D`, `RoomSurface`, `RoomConfig`, `SceneObject`, `SceneGraph`, and request bodies. |
| `backend/requirements.txt` | Python dependency specifications (`fastapi`, `uvicorn`, `pydantic`, `pyautogui`, `pillow`, `qrcode`, `playwright`, etc.). |

#### Backend Services (`backend/services/`)

| File | Purpose & Role |
| :--- | :--- |
| `backend/services/antigravity_prompter.py` | **Antigravity CAD Intelligence Director**. Contains category-specific architectural heuristics (ergonomics, joinery, materials, dimensions) and builds the prioritized sequential refinement plan (`build_antigravity_scene_refinement_plan`). |
| `backend/services/scene_service.py` | **Scene Graph Business Logic**. Handles scene persistence, object CRUD, natural language CAD parsing (`stick phone to table`, `unstick all`), and recursive parent-child transform propagation (`propagate_parent_transforms`). |
| `backend/services/cropper.py` | **2D High-Resolution Object Cropper**. Uses Pillow to inspect EXIF orientation tags, slice normalized 2D bounding boxes `[ymin, xmin, ymax, xmax]` from the room photo, apply 5% padding, and save crops to `storage/crops/`. |
| `backend/services/browser_prompt.py` | **Spatial Master Prompts & Response Parser**. Contains the master spatial room reconstruction system prompt, robust regex JSON extractors, and dictionary-to-SceneGraph compilers. |
| `backend/services/browser_automation.py` | **Mode B Playwright CDP Driver**. Automates Chromium via Chrome DevTools Protocol, supporting headless/headful automation of Gemini, Claude, ChatGPT, and DeepSeek. |

#### Storage Directories (`backend/storage/`)

| Directory | Purpose & Role |
| :--- | :--- |
| `backend/storage/scenes/` | Persistent JSON files storing individual 3D scene graphs (`scene_1ac6c4e9.json`). |
| `backend/storage/crops/` | High-resolution cropped `.jpg` files for individual furniture items (`scene_1ac6c4e9_obj_main_desk.jpg`). |
| `backend/storage/uploads/` | Original room photographs uploaded via mobile, web, or file drop. |

---

### Scripts Directory (`scripts/`)

| File | Purpose & Role |
| :--- | :--- |
| `scripts/pipeline.py` | **Unified Supervisor Pipeline**. Starts FastAPI backend on port 8000, supervises `cloudflared.exe`, monitors tunnel health, runs `uploads/` folder watcher, and auto-heals crashed child processes. |
| `scripts/physical_clicker.py` | **Desktop Clicker & Refinement Daemon**. Executes physical mouse clicks, clipboard image pasting (`Ctrl+V`), prompt delivery, output extraction, live dispatch to the Antigravity IDE chat composer, and the continuous Antigravity object refinement loop across ALL objects. |
| `scripts/calibrate_clicks.py` | **Unhurried Screen Calibrator**. Interactive CLI tool allowing the user to hover over 5 screen points without a timer, lock with `[SPACE]`, retry with `[R]`, select specific targets (e.g. Target 5 only), and run an automated visual verification hover test. |
| `scripts/antigravity_loop.py` | **CLI Loop Inspector**. Command-line utility to preview Antigravity CAD prompts across all objects in any scene, or trigger the physical refinement queue via `--execute`. |
| `scripts/test_suite.py` | **Automated 12-Point Test Suite**. Integration test verifying scene retrieval, CAD NLP sticking/unsticking, transform propagation, static asset serving, and Antigravity plan/prompt generation. |
| `scripts/login_helper.py` | Interactive script that launches Chrome with `browser_profile/` so the user can sign in to LLMs for Mode B. |
| `scripts/cloudflared.exe` | Standalone Cloudflare Tunnel binary establishing public HTTP/2 mobile ingress without port forwarding. |

---

### Frontend Directory (`frontend/`)

| File | Purpose & Role |
| :--- | :--- |
| `frontend/src/App.tsx` | **Application Root Component**. Mounts the 3D viewport, header, bottom dock, modal dialogs, handles deep-linking (`?scene=...`), and initializes scene state. |
| `frontend/src/types.ts` | **Frontend TypeScript Definitions**. Declares types for `SceneGraph`, `SceneObject`, `Vector3D`, `ActiveModal`, and `LLMTarget`. |
| `frontend/src/hooks/useSceneStore.ts` | **Zustand State Store**. Manages reactive global state: active scene, selected object, camera modes, modals, WebSocket connection, object transforms, and glTF/JSON export. |
| `frontend/src/components/SceneViewport3D.tsx` | **Three.js / React Three Fiber Viewport**. Renders the 3D room, lighting, procedural furniture meshes, selection bounding boxes, floor grid, drag planes, and the Rotating Geode Core. |
| `frontend/src/components/MobileHeader.tsx` | **Monochromatic Top Navigation Bar**. Displays telemetry indicators, engine selector (`Physical Clicks`, `Gemini`, `ChatGPT`), Cloudflare URL badge, and quick modal triggers. |
| `frontend/src/components/MobileBottomControls.tsx` | **Responsive Bottom CAD Dock & Inspector**. Adapts between Home mode (geode core), Scene dock (Command, Capture, Payload, Refine, Export), and Object Inspector (Yaw, Nudge pad, Stick to Table, Detach). |
| `frontend/src/components/AntigravityModal.tsx` | **Antigravity CAD Intelligence Modal**. Displays the prioritized object refinement hierarchy, high-res crop previews, Antigravity's tailored prompts, and 1-click execution. |
| `frontend/src/components/CalibrationModal.tsx` | **Physical Click Calibration Modal**. UI dialog to view/edit screen coordinates, save matrix, and test cursor positions via live **TEST** hover buttons. |
| `frontend/src/components/UploadModal.tsx` | **Capture & Upload Dialog**. Allows mobile camera snaps, file uploads, engine selection, and direct access to calibration. |
| `frontend/src/components/ManualPasteModal.tsx` | **2-Step Payload Ingestion Modal**. Offline fallback to copy the CAD prompt and paste returned raw LLM JSON. |
| `frontend/src/components/ChatPromptDrawer.tsx` | **Natural Language CAD Terminal**. Command drawer to submit text prompts (`stick laptop to table`, `rotate sofa 90`, `unstick all`). |
| `frontend/src/components/QrModal.tsx` | **Mobile Connect Modal**. Displays high-resolution QR code and copyable public tunnel URL. |
| `frontend/src/components/LogsModal.tsx` | **Live System Telemetry Modal**. Streams daemon execution logs and background job statuses. |
| `frontend/dist/` | **Pre-Built Production SPA Distribution**. Compiled static assets served directly by FastAPI. |

---

## 5. SUMMARY OF KEY DIRECTORIES

| Directory | Contents |
| :--- | :--- |
| `backend/` | Python FastAPI application, REST endpoints, WebSocket hubs, and services. |
| `backend/services/` | Antigravity prompter, scene service, cropper, and prompt templates. |
| `backend/storage/` | Persistent room scenes (`scenes/`), furniture crops (`crops/`), and uploads (`uploads/`). |
| `frontend/` | React 19, TypeScript, Tailwind CSS, Three.js, React Three Fiber source code. |
| `frontend/dist/` | Optimized production pre-built HTML/JS/CSS assets. |
| `scripts/` | Cleaned operational automation scripts, supervisor pipeline, and calibrators. |
| `browser_profile/` | Persistent Chrome user data directory for Playwright CDP automation. |
| `uploads/` | Root hot-folder monitored by the pipeline file watcher. |
