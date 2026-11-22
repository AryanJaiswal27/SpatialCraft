import json
import uuid
import re
import math
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..config import SCENES_DIR, UPLOADS_DIR
from ..models import SceneGraph, SceneObject, UpdateObjectRequest, Vector3D, Rotation3D, Dimensions3D

def get_scene_path(scene_id: str) -> Path:
    return SCENES_DIR / f"{scene_id}.json"

def save_scene(scene: SceneGraph) -> Path:
    scene.updated_at = datetime.utcnow().isoformat()
    if not scene.created_at:
        scene.created_at = scene.updated_at
    path = get_scene_path(scene.scene_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(scene.model_dump_json(indent=2))
    return path

def get_scene(scene_id: str) -> Optional[SceneGraph]:
    path = get_scene_path(scene_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SceneGraph(**data)

def list_scenes() -> List[Dict[str, Any]]:
    scenes = []
    for file in SCENES_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                scenes.append({
                    "scene_id": data.get("scene_id"),
                    "name": data.get("name"),
                    "image_url": data.get("image_url"),
                    "objects_count": len(data.get("objects", [])),
                    "created_at": data.get("created_at"),
                    "status": data.get("status")
                })
        except Exception:
            continue
    scenes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return scenes

def propagate_parent_transforms(scene: SceneGraph, parent_id: str, dx: float, dy: float, dz: float, delta_yaw: float = 0.0, visited: Optional[set] = None):
    """
    Propagates translations and yaw rotations from a parent object to all attached child objects.
    Maintains relative local position and orientation with cycle protection.
    """
    if dx == 0.0 and dy == 0.0 and dz == 0.0 and delta_yaw == 0.0:
        return

    if visited is None:
        visited = set()
    if parent_id in visited:
        return
    visited.add(parent_id)

    parent = next((o for o in scene.objects if o.id == parent_id), None)
    if not parent:
        return

    rad = math.radians(delta_yaw)
    cos_theta = math.cos(rad)
    sin_theta = math.sin(rad)

    for child in scene.objects:
        if getattr(child, "attached_to_id", None) == parent_id and child.id not in visited:
            # 1. Translate with parent
            child.position.x = round(child.position.x + dx, 3)
            child.position.y = round(child.position.y + dy, 3)
            child.position.z = round(child.position.z + dz, 3)

            # 2. Rotate child around parent center if yaw changed
            if delta_yaw != 0.0:
                rel_x = child.position.x - parent.position.x
                rel_z = child.position.z - parent.position.z
                rot_x = rel_x * cos_theta - rel_z * sin_theta
                rot_z = rel_x * sin_theta + rel_z * cos_theta
                child.position.x = round(parent.position.x + rot_x, 3)
                child.position.z = round(parent.position.z + rot_z, 3)
                child.rotation.yaw = round(((child.rotation.yaw or 0.0) + delta_yaw) % 360, 2)

            # Recurse for nested attachments with cycle prevention
            propagate_parent_transforms(scene, child.id, dx, dy, dz, delta_yaw, visited)

def update_object(scene_id: str, object_id: str, update: UpdateObjectRequest) -> Optional[SceneGraph]:
    scene = get_scene(scene_id)
    if not scene:
        return None

    target = next((o for o in scene.objects if o.id == object_id), None)
    if not target:
        return None

    dx, dy, dz = 0.0, 0.0, 0.0
    delta_yaw = 0.0

    if update.position is not None:
        dx = update.position.x - target.position.x
        dy = update.position.y - target.position.y
        dz = update.position.z - target.position.z
        target.position = update.position

    if update.rotation is not None:
        old_yaw = target.rotation.yaw or 0.0
        new_yaw = update.rotation.yaw or 0.0
        delta_yaw = new_yaw - old_yaw
        target.rotation = update.rotation

    if update.dimensions is not None:
        target.dimensions = update.dimensions

    if update.color is not None:
        target.color = update.color

    if getattr(update, "name", None) is not None:
        target.name = update.name
    if getattr(update, "description", None) is not None:
        target.description = update.description
    if getattr(update, "materials", None) is not None:
        setattr(target, "materials", update.materials)
    if getattr(update, "features", None) is not None:
        setattr(target, "features", update.features)
    if getattr(update, "parts", None) is not None:
        setattr(target, "parts", update.parts)
    if getattr(update, "mesh_obj", None) is not None:
        setattr(target, "mesh_obj", update.mesh_obj)

    # Handle attached_to_id explicitly (checking model_fields_set for null/None vs omitted)
    if hasattr(update, "model_fields_set") and "attached_to_id" in update.model_fields_set:
        val = update.attached_to_id
        target.attached_to_id = None if (val is None or val in ("none", "", "null")) else val
    elif update.attached_to_id is not None:
        target.attached_to_id = None if update.attached_to_id in ("none", "", "null") else update.attached_to_id

    # Propagate movement & rotation to any attached objects
    propagate_parent_transforms(scene, object_id, dx, dy, dz, delta_yaw)

    save_scene(scene)
    return scene

def delete_object(scene_id: str, object_id: str) -> Optional[SceneGraph]:
    scene = get_scene(scene_id)
    if not scene:
        return None

    # Unstick children if their parent is deleted
    for obj in scene.objects:
        if getattr(obj, "attached_to_id", None) == object_id:
            obj.attached_to_id = None

    scene.objects = [obj for obj in scene.objects if obj.id != object_id]
    save_scene(scene)
    return scene

def add_object(scene_id: str, obj: SceneObject) -> Optional[SceneGraph]:
    scene = get_scene(scene_id)
    if not scene:
        return None

    scene.objects.append(obj)
    save_scene(scene)
    return scene

def find_matching_parent_object(objects: List[SceneObject], prompt_lower: str) -> Optional[SceneObject]:
    """Finds the most suitable parent surface object based on keywords in prompt."""
    surface_keywords = ["table", "desk", "console", "unit", "shelf", "bookshelf", "counter", "sofa", "bed"]
    prompt_surfaces = [kw for kw in surface_keywords if kw in prompt_lower]

    for kw in prompt_surfaces:
        for obj in objects:
            if kw == obj.category or kw in obj.name.lower():
                return obj

    # Fallback to any table or desk in scene
    return next((o for o in objects if o.category in ("table", "desk", "tv_unit")), None)

def find_matching_child_object(objects: List[SceneObject], prompt_lower: str, exclude_id: Optional[str] = None) -> Optional[SceneObject]:
    """Finds the intended child object mentioned in the prompt."""
    target_keywords = ["phone", "smartphone", "laptop", "computer", "plant", "lamp", "light", "cup", "mug", "art", "frame", "painting", "decor", "book", "chair", "armchair", "sofa", "couch", "rug"]
    prompt_targets = [kw for kw in target_keywords if kw in prompt_lower]

    for kw in prompt_targets:
        for obj in objects:
            if exclude_id and obj.id == exclude_id:
                continue
            if kw == obj.category or kw in obj.name.lower():
                return obj

    for obj in objects:
        if exclude_id and obj.id == exclude_id:
            continue
        if obj.category in prompt_lower:
            return obj

    for obj in objects:
        if exclude_id and obj.id == exclude_id:
            continue
        for w in obj.name.lower().split():
            if len(w) >= 4 and w in prompt_lower and w not in ("table", "desk", "wall", "room"):
                return obj

    return None

def apply_natural_language_edit(scene_id: str, prompt: str) -> Optional[SceneGraph]:
    """
    Interprets natural language CAD and spatial layout commands:
    - Translation: "Move sofa left by 1m", "Translate table X +0.5"
    - Scaling: "Double the size of the rug", "Scale plant up"
    - Rotation: "Rotate table 90 deg", "Turn armchair 45"
    - Attachment/Sticking: "Stick phone to table", "Snap art to north wall"
    - Unstick/Detachment: "Unstick phone", "Detach plant", "Unstick all"
    - Tabletop items: "Place a phone on the coffee table", "Add laptop on desk"
    - Material & Colors: "Set wall color to #dedad3", "Make sofa charcoal"
    - Room resize: "Set room width to 6m", "Resize room 6 by 6"
    - Add/Delete: "Add a floor lamp", "Remove the chair"
    """
    scene = get_scene(scene_id)
    if not scene:
        return None

    prompt_clean = prompt.strip()
    prompt_lower = prompt_clean.lower()

    # 1. Color palette mapping
    color_map = {
        "black": "#18181b", "white": "#f4f4f5", "charcoal": "#27272a", "slate": "#3f3f46",
        "zinc": "#52525b", "steel": "#71717a", "light gray": "#a1a1aa", "dark": "#09090b",
        "sand": "#c4a482", "beige": "#dedad3", "wood": "#3e2723", "oak": "#8c6239",
        "green": "#3f4e43", "olive": "#4a5342", "navy": "#1e293b", "terracotta": "#8c4a38"
    }

    # Direct hex code extraction
    hex_match = re.search(r"#(?:[0-9a-fA-F]{3}){1,2}\b", prompt_clean)
    extracted_hex = hex_match.group(0) if hex_match else None

    # Check wall recolor
    if "wall" in prompt_lower and not ("stick" in prompt_lower or "snap" in prompt_lower or "hang" in prompt_lower):
        if extracted_hex:
            scene.room.walls.color = extracted_hex
            save_scene(scene)
            return scene
        for cname, chex in color_map.items():
            if cname in prompt_lower:
                scene.room.walls.color = chex
                save_scene(scene)
                return scene

    # Check floor recolor
    if "floor" in prompt_lower:
        if extracted_hex:
            scene.room.floor.color = extracted_hex
            save_scene(scene)
            return scene
        for cname, chex in color_map.items():
            if cname in prompt_lower:
                scene.room.floor.color = chex
                save_scene(scene)
                return scene

    # Check room dimension modifications
    dim_match = re.search(r"(?:room|dimensions?).*?(\d+(?:\.\d+)?)\s*(?:m|meters)?\s*(?:by|x|\*)\s*(\d+(?:\.\d+)?)", prompt_lower)
    if dim_match:
        scene.room.dimensions.width = float(dim_match.group(1))
        scene.room.dimensions.depth = float(dim_match.group(2))
        save_scene(scene)
        return scene

    # 2. UNSTICK / DETACH DIRECTIVES
    if "unstick" in prompt_lower or "detach" in prompt_lower or "unlink" in prompt_lower:
        if "all" in prompt_lower or "everything" in prompt_lower:
            for obj in scene.objects:
                obj.attached_to_id = None
            save_scene(scene)
            return scene

        # Unstick specific target or first attached object
        unstick_target = None
        for obj in scene.objects:
            if obj.category in prompt_lower or obj.name.lower() in prompt_lower or any(word in obj.name.lower() for word in prompt_lower.split()):
                if getattr(obj, "attached_to_id", None):
                    unstick_target = obj
                    break

        if not unstick_target:
            # Fallback to any object that is currently attached
            unstick_target = next((o for o in scene.objects if getattr(o, "attached_to_id", None)), None)

        if unstick_target:
            unstick_target.attached_to_id = None
            save_scene(scene)
            return scene

    # 3. STICK / ATTACH DIRECTIVES (e.g. "stick phone to table", "snap mirror to wall")
    if "stick" in prompt_lower or "attach" in prompt_lower or "snap" in prompt_lower or "hang" in prompt_lower or "mount" in prompt_lower:
        # Check if sticking to a wall
        if "wall" in prompt_lower:
            wall_name = "wall_north"
            room_w = scene.room.dimensions.width
            room_d = scene.room.dimensions.depth

            if "north" in prompt_lower or "back" in prompt_lower:
                wall_name = "wall_north"
            elif "south" in prompt_lower or "front" in prompt_lower:
                wall_name = "wall_south"
            elif "west" in prompt_lower or "left" in prompt_lower:
                wall_name = "wall_west"
            elif "east" in prompt_lower or "right" in prompt_lower:
                wall_name = "wall_east"

            # Find target object to stick to wall
            wall_target = None
            for obj in scene.objects:
                if any(k in prompt_lower for k in [obj.category, obj.name.lower(), "art", "decor", "mirror", "frame", "clock", "tv"]):
                    wall_target = obj
                    break

            if not wall_target and scene.objects:
                wall_target = scene.objects[-1]

            if wall_target:
                wall_target.attached_to_id = wall_name
                # Snap to wall plane
                obj_depth = wall_target.dimensions.depth or 0.1
                obj_width = wall_target.dimensions.width or 0.8
                if wall_name == "wall_north":
                    wall_target.position.z = round(-room_d / 2 + obj_depth / 2 + 0.02, 3)
                    wall_target.rotation.yaw = 0.0
                elif wall_name == "wall_south":
                    wall_target.position.z = round(room_d / 2 - obj_depth / 2 - 0.02, 3)
                    wall_target.rotation.yaw = 180.0
                elif wall_name == "wall_west":
                    wall_target.position.x = round(-room_w / 2 + obj_depth / 2 + 0.02, 3)
                    wall_target.rotation.yaw = 90.0
                elif wall_name == "wall_east":
                    wall_target.position.x = round(room_w / 2 - obj_depth / 2 - 0.02, 3)
                    wall_target.rotation.yaw = 270.0

                save_scene(scene)
                return scene

        # Check if sticking an object to another object (e.g. child to parent table)
        parent_obj = find_matching_parent_object(scene.objects, prompt_lower)
        if parent_obj:
            child_obj = find_matching_child_object(scene.objects, prompt_lower, exclude_id=parent_obj.id)
            if child_obj:
                child_obj.attached_to_id = parent_obj.id
                # Snap child directly onto top surface of parent
                child_obj.position.x = parent_obj.position.x
                child_obj.position.z = parent_obj.position.z
                child_obj.position.y = round(parent_obj.position.y + (parent_obj.dimensions.height / 2) + (child_obj.dimensions.height / 2), 3)
                save_scene(scene)
                return scene

    # 4. ELEMENT INJECTION WITH AUTO-ATTACHMENT (e.g. "place a phone on the coffee table", "add laptop on desk")
    if "place" in prompt_lower or "put" in prompt_lower or "add" in prompt_lower or "insert" in prompt_lower:
        # Check if placing on a surface
        surface_parent = None
        if "on" in prompt_lower or "top" in prompt_lower:
            surface_parent = find_matching_parent_object(scene.objects, prompt_lower)

        # Detect specific item to create
        item_configs = {
            "phone": {"name": "Smartphone", "category": "phone", "dims": (0.08, 0.012, 0.16), "color": "#18181b"},
            "laptop": {"name": "Ultrabook Laptop", "category": "laptop", "dims": (0.32, 0.02, 0.22), "color": "#71717a"},
            "cup": {"name": "Ceramic Coffee Mug", "category": "decor", "dims": (0.1, 0.11, 0.1), "color": "#f4f4f5"},
            "plant": {"name": "Potted Ceramic Plant", "category": "plant", "dims": (0.28, 0.35, 0.28), "color": "#3f4e43"},
            "lamp": {"name": "Minimalist Table Lamp", "category": "lamp", "dims": (0.25, 0.45, 0.25), "color": "#e4e4e7"},
            "art": {"name": "Framed Canvas Art", "category": "art", "dims": (0.8, 1.0, 0.06), "color": "#27272a"},
            "rug": {"name": "Woven Area Rug", "category": "rug", "dims": (2.4, 0.02, 1.8), "color": "#dedad3"},
            "chair": {"name": "Accent Armchair", "category": "chair", "dims": (0.85, 0.85, 0.85), "color": "#3f3f46"},
            "table": {"name": "Low Coffee Table", "category": "table", "dims": (1.2, 0.45, 0.7), "color": "#8c6239"},
            "sofa": {"name": "Three-Seater Sofa", "category": "sofa", "dims": (2.2, 0.85, 0.95), "color": "#52525b"},
        }

        matched_key = None
        for key in item_configs:
            if key in prompt_lower:
                matched_key = key
                break

        if matched_key:
            cfg = item_configs[matched_key]
            dims = Dimensions3D(width=cfg["dims"][0], height=cfg["dims"][1], depth=cfg["dims"][2])
            new_id = f"obj_{matched_key}_{uuid.uuid4().hex[:6]}"

            if surface_parent:
                # Place directly on top of parent surface
                pos_x = surface_parent.position.x
                pos_z = surface_parent.position.z
                pos_y = round(surface_parent.position.y + (surface_parent.dimensions.height / 2) + (dims.height / 2), 3)
                attached_id = surface_parent.id
            else:
                pos_x = 0.0
                pos_z = 0.0
                pos_y = round(dims.height / 2, 3)
                attached_id = None

            new_obj = SceneObject(
                id=new_id,
                name=cfg["name"],
                category=cfg["category"],
                position=Vector3D(x=pos_x, y=pos_y, z=pos_z),
                dimensions=dims,
                color=cfg["color"],
                attached_to_id=attached_id
            )
            scene.objects.append(new_obj)
            save_scene(scene)
            return scene

    # 5. GENERAL TARGETED MODIFICATIONS
    target_category = None
    for cat in ["sofa", "couch", "table", "chair", "armchair", "bed", "lamp", "plant", "rug", "desk", "tv", "console", "bookshelf", "phone", "laptop", "art"]:
        if cat in prompt_lower:
            target_category = "sofa" if cat == "couch" else ("chair" if cat == "armchair" else ("tv_unit" if (cat == "tv" or cat == "console") else cat))
            break

    target_obj = None
    if target_category:
        for obj in scene.objects:
            if obj.category == target_category or target_category in obj.name.lower():
                target_obj = obj
                break

    # Deletion directive
    if "delete" in prompt_lower or "remove" in prompt_lower:
        if target_obj:
            return delete_object(scene_id, target_obj.id)

    # Scaling directive
    if target_obj and ("scale" in prompt_lower or "size" in prompt_lower or "bigger" in prompt_lower or "smaller" in prompt_lower):
        scale_factor = 1.2
        if "double" in prompt_lower:
            scale_factor = 2.0
        elif "smaller" in prompt_lower or "half" in prompt_lower or "shrink" in prompt_lower:
            scale_factor = 0.75
        elif "bigger" in prompt_lower or "enlarge" in prompt_lower:
            scale_factor = 1.3
        else:
            num_match = re.search(r"(\d+(?:\.\d+)?)", prompt_lower)
            if num_match:
                scale_factor = float(num_match.group(1))

        target_obj.dimensions.width = round(target_obj.dimensions.width * scale_factor, 3)
        target_obj.dimensions.depth = round(target_obj.dimensions.depth * scale_factor, 3)
        save_scene(scene)
        return scene

    # Numerical translation detection
    dist_val = 0.5
    num_match = re.search(r"[-+]?\d+(?:\.\d+)?", prompt_lower)
    if num_match:
        try:
            dist_val = abs(float(num_match.group(0)))
        except Exception:
            dist_val = 0.5

    # Translation directive with Child Propagation
    if target_obj and ("move" in prompt_lower or "translate" in prompt_lower or "shift" in prompt_lower or "push" in prompt_lower):
        dx, dy, dz = 0.0, 0.0, 0.0
        if "left" in prompt_lower or "x -" in prompt_lower or "-x" in prompt_lower:
            dx = -dist_val
        elif "right" in prompt_lower or "x +" in prompt_lower or "+x" in prompt_lower:
            dx = dist_val
        elif "back" in prompt_lower or "away" in prompt_lower or "z -" in prompt_lower:
            dz = -dist_val
        elif "forward" in prompt_lower or "closer" in prompt_lower or "z +" in prompt_lower:
            dz = dist_val
        elif "center" in prompt_lower:
            dx = -target_obj.position.x
            dz = -target_obj.position.z

        target_obj.position.x = round(target_obj.position.x + dx, 3)
        target_obj.position.y = round(target_obj.position.y + dy, 3)
        target_obj.position.z = round(target_obj.position.z + dz, 3)

        # Propagate movement to attached children!
        propagate_parent_transforms(scene, target_obj.id, dx, dy, dz, 0.0)

        save_scene(scene)
        return scene

    # Rotation directive with Child Propagation
    if target_obj and ("rotate" in prompt_lower or "turn" in prompt_lower or "yaw" in prompt_lower):
        angle = 45.0
        deg_match = re.search(r"(\d+)\s*(?:deg|degrees)?", prompt_lower)
        if deg_match:
            try:
                angle = float(deg_match.group(1))
            except Exception:
                angle = 45.0
        target_obj.rotation.yaw = round(((target_obj.rotation.yaw or 0.0) + angle) % 360, 2)

        # Propagate rotation around parent center to attached children!
        propagate_parent_transforms(scene, target_obj.id, 0.0, 0.0, 0.0, angle)

        save_scene(scene)
        return scene

    # Recolor object
    if target_obj:
        if extracted_hex:
            target_obj.color = extracted_hex
            save_scene(scene)
            return scene
        for cname, chex in color_map.items():
            if cname in prompt_lower:
                target_obj.color = chex
                save_scene(scene)
                return scene

    return scene
