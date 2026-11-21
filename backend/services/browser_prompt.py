import json
import re
from typing import Dict, Any, Optional
from ..models import SceneGraph, SceneObject, RoomConfig, RoomSurface, Dimensions3D, Vector3D, Rotation3D

SYSTEM_SPATIAL_PROMPT = """You are SpatialCraft AI, an expert 3D spatial reconstruction and interior architecture intelligence.
Your task is to analyze this room photograph and reconstruct its complete 3D digital twin with exact metric dimensions and furniture coordinates.

Analyze the room geometry, camera viewpoint, and every visible piece of furniture and interior decor.
Output ONLY a JSON block enclosed within ```json and ``` with the following exact schema:

```json
{
  "room": {
    "dimensions": { "width": 5.0, "height": 2.8, "depth": 5.0 },
    "floor": { "material": "light_oak_wood_parquet", "color": "#c4a482" },
    "walls": { "material": "matte_plaster", "color": "#f2efe9" },
    "ceiling": { "material": "matte_plaster", "color": "#fafafa" }
  },
  "objects": [
    {
      "id": "obj_sofa_1",
      "name": "Modern Grey Three-Seater Sofa",
      "category": "sofa",
      "description": "Contemporary low-profile fabric sofa with deep seat cushions and brushed metal legs",
      "position": { "x": 0.0, "y": 0.45, "z": -1.2 },
      "dimensions": { "width": 2.2, "height": 0.85, "depth": 0.95 },
      "rotation": { "yaw": 0.0 },
      "color": "#6e737b",
      "box_2d": [0.45, 0.20, 0.78, 0.80]
    }
  ]
}
```

CRITICAL 3D COORDINATE SYSTEM RULES:
1. Ground floor is y = 0. Object position 'y' should be height / 2 so the bottom sits flush on the floor.
2. Room center on the floor is (x=0, z=0).
   - x goes from -width/2 (left wall) to +width/2 (right wall).
   - z goes from -depth/2 (far back wall) to +depth/2 (near camera).
3. 'category' must be one of: "sofa", "table", "chair", "bed", "lamp", "plant", "tv_unit", "bookshelf", "rug", "art", "decor".
4. 'box_2d' is normalized [ymin, xmin, ymax, xmax] between 0.0 and 1.0 indicating where this object appears in the photo.
5. All dimensions ('width', 'height', 'depth') must be realistic real-world meters.
6. Provide EVERY recognizable piece of furniture or decor in the room.

Respond with ONLY the JSON code block.
"""

def generate_spatial_prompt() -> str:
    return SYSTEM_SPATIAL_PROMPT.strip()

def parse_llm_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts and parses JSON from raw LLM output text, handling markdown code fences,
    surrounding text, and prior chat history. Prioritizes CAD blocks with 'room' or 'objects'.
    """
    # 1. Find all ```json ... ``` blocks in reverse order (latest response first!)
    matches = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text))
    for m in reversed(matches):
        candidate = m.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and ("room" in parsed or "objects" in parsed):
                return parsed
        except json.JSONDecodeError:
            pass

    # Fallback to any valid JSON in code blocks (reverse)
    for m in reversed(matches):
        try:
            parsed = json.loads(m.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 2. Try to find raw { ... } blocks prioritizing 'room' or 'objects'
    # Look for last balanced JSON block containing 'room'
    if "room" in raw_text or "objects" in raw_text:
        # Search backwards from the end
        last_open = raw_text.rfind('{"room"')
        if last_open == -1:
            last_open = raw_text.rfind('{"objects"')
        if last_open == -1:
            last_open = raw_text.rfind('{')
        if last_open != -1:
            for end_idx in range(len(raw_text), last_open, -1):
                if raw_text[end_idx - 1] == '}':
                    try:
                        parsed = json.loads(raw_text[last_open:end_idx].strip())
                        if isinstance(parsed, dict) and ("room" in parsed or "objects" in parsed):
                            return parsed
                    except Exception:
                        pass

    # 3. Greedy outer brace match
    brace_match = re.search(r"(\{[\s\S]*\})", raw_text)
    if brace_match:
        try:
            parsed = json.loads(brace_match.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 4. Direct parse attempt
    try:
        return json.loads(raw_text.strip())
    except Exception:
        return None

def build_scene_from_parsed_data(scene_id: str, image_url: str, data: Dict[str, Any]) -> SceneGraph:
    """
    Converts parsed LLM dictionary into a strongly typed SceneGraph object.
    """
    room_data = data.get("room", {})
    dims_data = room_data.get("dimensions", {})
    floor_data = room_data.get("floor", {})
    walls_data = room_data.get("walls", {})

    room_config = RoomConfig(
        dimensions=Dimensions3D(
            width=float(dims_data.get("width", 5.0)),
            height=float(dims_data.get("height", 2.8)),
            depth=float(dims_data.get("depth", 5.0))
        ),
        floor=RoomSurface(
            material=str(floor_data.get("material", "parquet")),
            color=str(floor_data.get("color", "#c5a078"))
        ),
        walls=RoomSurface(
            material=str(walls_data.get("material", "plaster")),
            color=str(walls_data.get("color", "#f0eee9"))
        )
    )

    objects_list = []
    raw_objects = data.get("objects", [])

    for idx, obj in enumerate(raw_objects):
        obj_id = obj.get("id") or f"obj_{idx+1}"
        category = obj.get("category", "decor").lower()
        pos = obj.get("position", {})
        rot = obj.get("rotation", {})
        dims = obj.get("dimensions", {})

        height = float(dims.get("height", 1.0))
        # Ensure y rests on floor if not explicitly offset
        y_pos = float(pos.get("y", height / 2.0))

        scene_obj = SceneObject(
            id=obj_id,
            name=obj.get("name", f"{category.capitalize()} #{idx+1}"),
            category=category,
            description=obj.get("description", ""),
            position=Vector3D(
                x=float(pos.get("x", 0.0)),
                y=y_pos,
                z=float(pos.get("z", 0.0))
            ),
            rotation=Rotation3D(
                yaw=float(rot.get("yaw", 0.0))
            ),
            dimensions=Dimensions3D(
                width=float(dims.get("width", 1.0)),
                height=height,
                depth=float(dims.get("depth", 1.0))
            ),
            color=obj.get("color", "#70757a"),
            model_type="procedural",
            box_2d=obj.get("box_2d"),
            attached_to_id=obj.get("attached_to_id")
        )
        objects_list.append(scene_obj)

    # Auto-detect tabletop attachments for items resting on tables/desks
    for obj in objects_list:
        if not obj.attached_to_id and obj.category in ("decor", "plant", "lamp", "phone", "laptop", "art"):
            for parent in objects_list:
                if parent.id != obj.id and parent.category in ("table", "desk", "tv_unit", "bookshelf"):
                    p_w2 = parent.dimensions.width / 2.0
                    p_d2 = parent.dimensions.depth / 2.0
                    p_top_y = parent.position.y + (parent.dimensions.height / 2.0)
                    obj_bottom_y = obj.position.y - (obj.dimensions.height / 2.0)

                    # Check horizontal footprint containment
                    if abs(obj.position.x - parent.position.x) <= p_w2 and abs(obj.position.z - parent.position.z) <= p_d2:
                        # Check vertical contact (within 0.15m)
                        if abs(obj_bottom_y - p_top_y) <= 0.15:
                            obj.attached_to_id = parent.id
                            break

    scene = SceneGraph(
        scene_id=scene_id,
        image_url=image_url,
        room=room_config,
        objects=objects_list,
        status="ready",
        status_message="Scene reconstructed successfully"
    )
    return scene

