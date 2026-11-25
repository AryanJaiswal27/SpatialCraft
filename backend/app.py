import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .config import UPLOADS_DIR, ROOT_UPLOADS_DIR, CROPS_DIR, SCENES_DIR, STATIC_DIR, HOST, PORT, ROOT_DIR, TUNNEL_URL_FILE
from .models import SceneGraph, PromptEditRequest, UpdateObjectRequest, SceneObject
from .services.scene_service import (
    save_scene, get_scene, list_scenes, update_object,
    delete_object, add_object, apply_natural_language_edit,
    verify_and_ground_scene
)
from .services.browser_prompt import (
    generate_spatial_prompt, parse_llm_json_response, build_scene_from_parsed_data
)
from .services.cropper import crop_objects_from_image
from .services.antigravity_prompter import (
    generate_antigravity_object_prompt,
    build_antigravity_scene_refinement_plan
)
from .services.antigravity_builder import (
    build_antigravity_fallback_scene,
    refine_object_with_antigravity_cad,
    run_antigravity_full_scene_build_and_refine
)

app = FastAPI(title="SpatialCraft Unified Studio", version="1.0.0")

# Enable GZip compression for instant mobile asset delivery
app.add_middleware(GZipMiddleware, minimum_size=500)

# Enable CORS for mobile browsers and tunneling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

# Active WebSocket connections for live mobile progress notifications
active_sockets: Dict[str, List[WebSocket]] = {}
PHYSICAL_CONFIG_PATH = ROOT_DIR / "physical_clicks_config.json"
physical_jobs_queue: List[Dict[str, Any]] = []

def ensure_presets_in_config(data: Dict[str, Any]) -> Dict[str, Any]:
    if "presets" not in data or not isinstance(data.get("presets"), dict):
        old_targets = data.get("targets", {})
        old_delays = data.get("delays", {})
        data["active_preset"] = "gemini"
        data["presets"] = {
            "gemini": {
                "id": "gemini",
                "label": "Google Gemini",
                "browser_url": "https://gemini.google.com",
                "targets": old_targets,
                "delays": old_delays,
                "last_calibrated_at": data.get("last_calibrated_at")
            },
            "chatgpt": {
                "id": "chatgpt",
                "label": "OpenAI ChatGPT",
                "browser_url": "https://chatgpt.com",
                "targets": dict(old_targets),
                "delays": dict(old_delays),
                "last_calibrated_at": None
            },
            "deepseek": {
                "id": "deepseek",
                "label": "DeepSeek Chat",
                "browser_url": "https://chat.deepseek.com",
                "targets": dict(old_targets),
                "delays": dict(old_delays),
                "last_calibrated_at": None
            }
        }
    active_id = data.get("active_preset", "gemini")
    presets = data.get("presets", {})
    if active_id in presets:
        data["targets"] = presets[active_id].get("targets", data.get("targets", {}))
        data["delays"] = presets[active_id].get("delays", data.get("delays", {}))
    return data

@app.get("/api/physical_clicks/config")
async def get_physical_config():
    if PHYSICAL_CONFIG_PATH.exists():
        try:
            with open(PHYSICAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            ensure_presets_in_config(data)
            return data
        except Exception:
            pass
    return {"screen": {"width": 1920, "height": 1080}, "active_preset": "gemini", "presets": {}, "targets": {}, "delays": {}}

@app.post("/api/physical_clicks/config")
async def update_physical_config(data: Dict[str, Any]):
    try:
        ensure_presets_in_config(data)
        with open(PHYSICAL_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"status": "ok", "message": "Physical click calibration updated", "active_preset": data.get("active_preset", "gemini")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/physical_clicks/preset/{preset_name}/activate")
async def activate_physical_preset(preset_name: str):
    """Switches the active LLM calibration preset (gemini, chatgpt, deepseek)."""
    if PHYSICAL_CONFIG_PATH.exists():
        try:
            with open(PHYSICAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            ensure_presets_in_config(data)
            pid = preset_name.lower().strip()
            if pid in data.get("presets", {}):
                data["active_preset"] = pid
                data["targets"] = data["presets"][pid].get("targets", {})
                data["delays"] = data["presets"][pid].get("delays", {})
                with open(PHYSICAL_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                return {"status": "ok", "active_preset": pid, "message": f"Activated preset '{data['presets'][pid].get('label', pid)}'"}
            else:
                raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found. Available: {list(data.get('presets', {}).keys())}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="Configuration file not found")

@app.get("/api/physical_clicks/queue")
async def get_physical_queue():
    return {"queue": physical_jobs_queue, "count": len(physical_jobs_queue)}

@app.get("/api/physical_clicks/queue/poll")
async def poll_physical_queue():
    if physical_jobs_queue:
        job = physical_jobs_queue.pop(0)
        return job
    return {}

@app.post("/api/physical_clicks/queue")
async def enqueue_physical_job(data: Dict[str, Any]):
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job = {
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat(),
        **data
    }
    job["job_id"] = job_id
    physical_jobs_queue.append(job)
    return {"status": "queued", "job_id": job_id}

@app.post("/api/physical_clicks/test_target")
async def test_physical_target(data: Dict[str, Any]):
    """Enqueues an interactive hover test for a calibrated target coordinate."""
    target_key = data.get("target")
    job_id = f"test_{uuid.uuid4().hex[:8]}"
    job = {
        "job_id": job_id,
        "job_type": "test_hover",
        "target_key": target_key,
        "coords": data.get("coords"),
        "created_at": datetime.utcnow().isoformat()
    }
    physical_jobs_queue.append(job)
    return {"status": "queued", "job_id": job_id}

@app.post("/api/physical_clicks/queue/{job_id}/complete")
async def complete_physical_job(job_id: str, data: Dict[str, Any]):
    return {"status": "completed", "job_id": job_id}

@app.post("/api/scene/{scene_id}/refine")
async def trigger_scene_refinement(scene_id: str, payload: Optional[Dict[str, Any]] = None):
    scene = get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    payload = payload or {}
    object_id = payload.get("object_id")
    job_id = f"job_{uuid.uuid4().hex[:8]}"

    if object_id:
        obj = next((o for o in scene.objects if o.id == object_id), None)
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
        job = {
            "job_id": job_id,
            "job_type": "refine_single",
            "scene_id": scene_id,
            "object_data": obj.model_dump(),
            "created_at": datetime.utcnow().isoformat()
        }
    else:
        # None = refine ALL objects in the scene sequentially
        max_items = payload.get("max_items")
        job = {
            "job_id": job_id,
            "job_type": "refine_loop",
            "scene_id": scene_id,
            "max_items": max_items,
            "created_at": datetime.utcnow().isoformat()
        }

    physical_jobs_queue.append(job)
    total_str = f"up to {job['max_items']} objects" if job.get("max_items") else "ALL objects"
    await broadcast_status(scene_id, f"[ANTIGRAVITY] Sequential Refinement Enqueued ({total_str})...", "progress")
    return {"status": "queued", "job_id": job_id, "job_type": job["job_type"]}

@app.post("/api/scene/{scene_id}/verify_placement")
async def verify_scene_placement_endpoint(scene_id: str):
    scene = get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    verified_scene = verify_and_ground_scene(scene)
    await broadcast_status(scene_id, "[ANTIGRAVITY] Verified all objects: 0 floating, all grounded & detailed meshes confirmed!", "done")
    return verified_scene

@app.post("/api/scene/{scene_id}/antigravity_backup_build")
async def trigger_antigravity_backup_build(scene_id: str):
    scene = get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    image_path = None
    if scene.image_url:
        img_name = Path(scene.image_url).name
        for p in [UPLOADS_DIR / img_name, ROOT_UPLOADS_DIR / img_name]:
            if p.exists():
                image_path = p
                break

    if not image_path:
        raise HTTPException(status_code=400, detail="Original room image not found for this scene")

    def cb(msg: str):
        asyncio.create_task(broadcast_status(scene_id, msg, "progress"))

    await broadcast_status(scene_id, "[ANTIGRAVITY BACKUP] Beginning autonomous 3D reconstruction...", "start")
    loop = asyncio.get_event_loop()
    updated_scene = await loop.run_in_executor(
        None,
        lambda: run_antigravity_full_scene_build_and_refine(scene_id, image_path, status_cb=cb)
    )
    await broadcast_status(scene_id, "3D Room Reconstructed by Antigravity!", "done")
    return updated_scene

@app.post("/api/scene/{scene_id}/object/{object_id}/antigravity_refine")
async def trigger_antigravity_object_refine(scene_id: str, object_id: str):
    scene = get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    target = next((o for o in scene.objects if o.id == object_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Object not found")

    loop = asyncio.get_event_loop()
    updated_scene = await loop.run_in_executor(
        None,
        lambda: refine_object_with_antigravity_cad(scene_id, object_id)
    )
    if not updated_scene:
        raise HTTPException(status_code=500, detail="Failed to refine object")

    await broadcast_status(scene_id, f"[ANTIGRAVITY] Refined 3D mesh for '{target.name}'", "progress")
    return updated_scene

async def broadcast_status(scene_id: str, message: str, stage: str = "progress"):
    sockets = active_sockets.get(scene_id, [])
    payload = {"scene_id": scene_id, "message": message, "stage": stage, "timestamp": datetime.utcnow().isoformat()}
    disconnected = []
    for ws in list(sockets):
        try:
            await ws.send_json(payload)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in sockets:
            sockets.remove(ws)

@app.websocket("/ws/{scene_id}")
async def websocket_endpoint(websocket: WebSocket, scene_id: str):
    await websocket.accept()
    if scene_id not in active_sockets:
        active_sockets[scene_id] = []
    active_sockets[scene_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if scene_id in active_sockets and websocket in active_sockets[scene_id]:
            active_sockets[scene_id].remove(websocket)

@app.get("/api/tunnel_url")
async def get_tunnel_url_endpoint():
    if TUNNEL_URL_FILE.exists():
        try:
            url = TUNNEL_URL_FILE.read_text(encoding="utf-8").strip()
            return {"url": url}
        except Exception:
            pass
    return {"url": None}

@app.get("/api/logs")
async def get_logs_endpoint(limit: int = 80):
    """Returns recent background execution and pipeline logs."""
    log_file = ROOT_DIR / "pipeline.log"
    lines = []
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                lines = [l.strip() for l in all_lines[-limit:] if l.strip()]
        except Exception as e:
            lines = [f"[LOG ERROR] {e}"]
    else:
        # Fallback to checking active task logs
        lines = ["[SYS] Pipeline daemon initialized. Ready for events."]
    return {"logs": lines, "count": len(lines)}

# Physical LLM Presets (gemini, chatgpt, deepseek)
@app.get("/api/engine")
async def get_engine_endpoint():
    cfg = {}
    if PHYSICAL_CONFIG_PATH.exists():
        try:
            with open(PHYSICAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    return {"engine": cfg.get("active_preset", "gemini")}

@app.post("/api/engine")
async def set_engine_endpoint(data: Dict[str, str]):
    engine = data.get("engine", "gemini").lower()
    if PHYSICAL_CONFIG_PATH.exists():
        try:
            with open(PHYSICAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["active_preset"] = engine
            with open(PHYSICAL_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass
    return {"engine": engine}

@app.post("/api/upload")
async def upload_room_image(
    file: UploadFile = File(...),
    target_llm: str = Form("gemini"),
    auto_automate: bool = Form(True)
):
    scene_id = f"scene_{uuid.uuid4().hex[:8]}"
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    saved_filename = f"{scene_id}_{int(datetime.utcnow().timestamp())}{ext}"
    saved_path = UPLOADS_DIR / saved_filename
    root_saved_path = ROOT_UPLOADS_DIR / saved_filename

    contents = await file.read()
    with open(saved_path, "wb") as f:
        f.write(contents)

    # Register in .processed_uploads.json so folder watcher does not duplicate the automation
    processed_tracker = ROOT_DIR / ".processed_uploads.json"
    try:
        current_set = set()
        if processed_tracker.exists():
            import json as _json
            current_set = set(_json.loads(processed_tracker.read_text(encoding="utf-8")))
        current_set.add(saved_filename)
        processed_tracker.write_text(_json.dumps(list(current_set)), encoding="utf-8")
    except Exception:
        pass

    with open(root_saved_path, "wb") as f:
        f.write(contents)

    # Save prompt file to disk for inspection
    prompt_path = UPLOADS_DIR / f"{scene_id}_prompt.txt"
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(generate_spatial_prompt())

    # Create initial scene state
    scene = SceneGraph(
        scene_id=scene_id,
        name=f"Capture // {file.filename}",
        image_url=f"/api/uploads/{saved_filename}",
        status="processing",
        status_message=f"Starting browser automation with {target_llm.capitalize()}..."
    )
    save_scene(scene)

    # All room capture options are Physical Click Ingestions (Gemini, ChatGPT, DeepSeek)
    preset_name = target_llm.lower() if target_llm.lower() in ("gemini", "chatgpt", "deepseek") else "gemini"

    # Automatically activate this preset in physical_clicks_config.json
    try:
        if PHYSICAL_CONFIG_PATH.exists():
            with open(PHYSICAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
            ensure_presets_in_config(cfg_data)
            if preset_name in cfg_data.get("presets", {}):
                cfg_data["active_preset"] = preset_name
                cfg_data["targets"] = cfg_data["presets"][preset_name].get("targets", {})
                cfg_data["delays"] = cfg_data["presets"][preset_name].get("delays", {})
                with open(PHYSICAL_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(cfg_data, f, indent=2)
    except Exception as e:
        print(f"[PRESET SYNC ERROR] {e}")

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    physical_jobs_queue.append({
        "job_id": job_id,
        "job_type": "initial_reconstruction",
        "preset": preset_name,
        "scene_id": scene_id,
        "prompt": generate_spatial_prompt(),
        "image_path": str(saved_path.resolve()),
        "created_at": datetime.utcnow().isoformat()
    })
    cur_scene = get_scene(scene_id)
    if cur_scene:
        cur_scene.status_message = f"Awaiting physical click execution on desktop daemon for {preset_name.capitalize()}..."
        save_scene(cur_scene)
    asyncio.create_task(broadcast_status(scene_id, f"[PHYSICAL] Job queued for desktop mouse execution on {preset_name.capitalize()}...", "progress"))

    # 5-MINUTE BACKUP WATCHDOG: If no output is received from browser LLM within 5 minutes,
    # Antigravity autonomously builds the scene and executes the refinement loop over all objects!
    async def scene_5min_backup_watchdog():
        await asyncio.sleep(300)  # 300 seconds = 5 minutes
        cur_scene = get_scene(scene_id)
        if cur_scene and (cur_scene.status in ("processing", "waiting_payload") or len(cur_scene.objects) == 0):
            print(f"\n[ANTIGRAVITY WATCHDOG // 5-MIN TIMEOUT] Scene {scene_id} received no browser LLM output within 5 minutes.")
            print(f"[ANTIGRAVITY WATCHDOG] Activating autonomous 3D CAD reconstruction backup...")
            def cb(msg: str):
                asyncio.create_task(broadcast_status(scene_id, msg, "progress"))
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: run_antigravity_full_scene_build_and_refine(scene_id, saved_path, status_cb=cb)
            )

    asyncio.create_task(scene_5min_backup_watchdog())

    return {
        "scene_id": scene_id,
        "image_url": f"/api/uploads/{saved_filename}",
        "status": "processing",
        "target_llm": target_llm,
        "prompt": generate_spatial_prompt()
    }

@app.get("/api/scene/{scene_id}")
async def get_scene_endpoint(scene_id: str):
    scene = get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene

@app.get("/api/scenes")
async def list_scenes_endpoint():
    return list_scenes()

@app.get("/api/scene/{scene_id}/antigravity_plan")
async def get_antigravity_plan_endpoint(scene_id: str):
    scene = get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    plan = build_antigravity_scene_refinement_plan(scene)
    return {"scene_id": scene_id, "total_objects": len(plan), "plan": plan}

@app.get("/api/scene/{scene_id}/object/{object_id}/antigravity_prompt")
async def get_antigravity_object_prompt_endpoint(scene_id: str, object_id: str):
    scene = get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    obj = next((o for o in scene.objects if o.id == object_id), None)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    prompt = generate_antigravity_object_prompt(obj, scene=scene)
    return {
        "scene_id": scene_id,
        "object_id": object_id,
        "object_name": obj.name,
        "category": obj.category,
        "prompt": prompt
    }

@app.put("/api/scene/{scene_id}/object/{object_id}")
async def update_scene_object(scene_id: str, object_id: str, update: UpdateObjectRequest):
    updated = update_object(scene_id, object_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Object or Scene not found")
    target_obj = next((o for o in updated.objects if o.id == object_id), None)
    obj_name = target_obj.name if target_obj else object_id
    await broadcast_status(scene_id, f"[ANTIGRAVITY] Refined '{obj_name}' in 3D scene", "progress")
    return updated

@app.delete("/api/scene/{scene_id}/object/{object_id}")
async def delete_scene_object(scene_id: str, object_id: str):
    updated = delete_object(scene_id, object_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Object or Scene not found")
    return updated

@app.post("/api/scene/{scene_id}/object")
async def add_scene_object(scene_id: str, obj: SceneObject):
    updated = add_object(scene_id, obj)
    if not updated:
        raise HTTPException(status_code=404, detail="Scene not found")
    return updated

@app.post("/api/scene/{scene_id}/prompt")
async def edit_scene_via_prompt(scene_id: str, request: PromptEditRequest):
    updated = apply_natural_language_edit(scene_id, request.prompt)
    if not updated:
        raise HTTPException(status_code=404, detail="Scene not found")
    return updated

@app.post("/api/scene/{scene_id}/submit_raw_output")
async def submit_raw_output(scene_id: str, payload: Dict[str, Any]):
    raw_text = payload.get("raw_text", "")
    target_id = f"scene_{uuid.uuid4().hex[:8]}" if (not scene_id or scene_id == "home") else scene_id
    scene = get_scene(target_id)
    image_url = payload.get("image_url") or (scene.image_url if (scene and scene.image_url) else "")

    parsed_data = parse_llm_json_response(raw_text)
    if not parsed_data:
        raise HTTPException(status_code=400, detail="Could not parse valid 3D JSON from submitted text")

    new_scene = build_scene_from_parsed_data(target_id, image_url, parsed_data)

    if image_url:
        img_name = Path(image_url).name
        local_img = UPLOADS_DIR / img_name
        if local_img.exists():
            crop_objects_from_image(local_img, target_id, new_scene.objects)

    # Immediately ground objects cleanly and synthesize multi-part CSG geometry so
    # initial 3D reconstruction renders faithfully with zero blank/black boxes!
    new_scene = verify_and_ground_scene(new_scene)
    save_scene(new_scene)
    await broadcast_status(target_id, "3D Room Updated!", "done")
    return new_scene

# Static storage endpoints
@app.get("/api/uploads/{filename}")
async def serve_upload(filename: str):
    path = UPLOADS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Upload file not found")
    return FileResponse(path)

@app.get("/api/crops/{filename}")
async def serve_crop(filename: str):
    path = CROPS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Crop file not found")
    return FileResponse(path)

@app.get("/qr.png")
async def serve_qr():
    qr_p = ROOT_DIR / "mobile_qr.png"
    if qr_p.exists():
        return FileResponse(qr_p)
    raise HTTPException(status_code=404, detail="QR code not found")

# Mount production pre-built assets
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

# SPA Fallback: Serves pre-built dist/index.html instantly
@app.get("/{full_path:path}")
async def serve_spa_frontend(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("ws/"):
        raise HTTPException(status_code=404, detail="API route not found")
    file_path = FRONTEND_DIST / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"status": "SpatialCraft API Online. Frontend building..."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=True)
