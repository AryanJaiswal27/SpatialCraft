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

from .config import UPLOADS_DIR, ROOT_UPLOADS_DIR, CROPS_DIR, SCENES_DIR, STATIC_DIR, HOST, PORT, ROOT_DIR, TUNNEL_URL_FILE, get_current_engine, set_current_engine
from .models import SceneGraph, PromptEditRequest, UpdateObjectRequest, SceneObject
from .services.scene_service import (
    save_scene, get_scene, list_scenes, update_object,
    delete_object, add_object, apply_natural_language_edit
)
from .services.browser_prompt import (
    generate_spatial_prompt, parse_llm_json_response, build_scene_from_parsed_data
)
from .services.cropper import crop_objects_from_image
from .services.browser_automation import automate_llm_in_browser
from .services.antigravity_prompter import (
    generate_antigravity_object_prompt,
    build_antigravity_scene_refinement_plan
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

@app.get("/api/physical_clicks/config")
async def get_physical_config():
    if PHYSICAL_CONFIG_PATH.exists():
        try:
            with open(PHYSICAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"screen": {"width": 1920, "height": 1080}, "targets": {}, "delays": {}}

@app.post("/api/physical_clicks/config")
async def update_physical_config(data: Dict[str, Any]):
    try:
        with open(PHYSICAL_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"status": "ok", "message": "Physical click calibration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        "job_type": data.get("job_type", "initial_reconstruction"),
        "scene_id": data.get("scene_id"),
        "prompt": data.get("prompt", ""),
        "image_path": data.get("image_path"),
        "created_at": datetime.utcnow().isoformat()
    }
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

@app.get("/api/engine")
async def get_engine_endpoint():
    return {"engine": get_current_engine()}

@app.post("/api/engine")
async def set_engine_endpoint(data: Dict[str, str]):
    engine = data.get("engine", "gemini")
    set_current_engine(engine)
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

    if target_llm == "physical":
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        physical_jobs_queue.append({
            "job_id": job_id,
            "job_type": "initial_reconstruction",
            "scene_id": scene_id,
            "prompt": generate_spatial_prompt(),
            "image_path": str(saved_path.resolve()),
            "created_at": datetime.utcnow().isoformat()
        })
        cur_scene = get_scene(scene_id)
        if cur_scene:
            cur_scene.status_message = "Awaiting physical click execution on desktop daemon..."
            save_scene(cur_scene)
        asyncio.create_task(broadcast_status(scene_id, "[PHYSICAL] Job queued for desktop mouse execution...", "progress"))
    elif auto_automate:
        async def run_bg_automation():
            try:
                def cb(msg: str):
                    asyncio.create_task(broadcast_status(scene_id, msg, stage="progress"))

                await broadcast_status(scene_id, f"Opening browser for {target_llm.upper()}...", "start")
                result = await automate_llm_in_browser(
                    target=target_llm,
                    image_path=saved_path,
                    scene_id=scene_id,
                    status_callback=cb
                )
                if result:
                    await broadcast_status(scene_id, "3D Room Reconstructed!", "done")
                else:
                    cur_scene = get_scene(scene_id)
                    if cur_scene and cur_scene.status == "processing":
                        cur_scene.status = "waiting_payload"
                        cur_scene.status_message = f"{target_llm.upper()} login/verification required. Tap PAYLOAD to ingest output."
                        save_scene(cur_scene)
                    await broadcast_status(scene_id, "Awaiting prompt/login in browser.", "waiting")
            except Exception as e:
                print(f"Browser automation background error: {e}")
                await broadcast_status(scene_id, f"Automation paused: {str(e)}", "error")

        asyncio.create_task(run_bg_automation())

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
    image_url = scene.image_url if (scene and scene.image_url) else ""

    parsed_data = parse_llm_json_response(raw_text)
    if not parsed_data:
        raise HTTPException(status_code=400, detail="Could not parse valid 3D JSON from submitted text")

    new_scene = build_scene_from_parsed_data(target_id, image_url, parsed_data)

    if image_url:
        img_name = Path(image_url).name
        local_img = UPLOADS_DIR / img_name
        if local_img.exists():
            crop_objects_from_image(local_img, target_id, new_scene.objects)

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
