"""
SpatialCraft // Antigravity CAD Intelligence & Prompt Generation Engine
Directs iterative fine-grained 3D furniture reconstruction object-by-object.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

CATEGORY_INSPECTION_DIRECTIVES = {
    "chair": (
        "1. Examine ergonomic structure: lumbar curvature, backrest height (low/mid/high with headrest), and armrest design (fixed/3D adjustable/armless).\n"
        "2. Identify base mechanism: 5-wheel star base with pneumatic gas-lift cylinder vs 4-leg metal/wood frame vs sled base.\n"
        "3. Specify real-world materials: breathable mesh weave, high-density molded foam, top-grain leather, or brushed aluminum/matte nylon."
    ),
    "table": (
        "1. Examine tabletop thickness (e.g. 25-45mm solid wood, glass, or stone laminate) and edge profile (chamfered, bullnose, square).\n"
        "2. Analyze substructure & legs: dual-motor sit-stand columns, steel hairpin legs, trestle frame, or 4 solid timber legs.\n"
        "3. Detect functional hardware: cable pass-through grommets, modesty panel, or integrated under-desk drawers.\n"
        "4. Verify standard ergonomic height: desk/workstation typically 0.72m - 0.76m, coffee table 0.40m - 0.48m."
    ),
    "sofa": (
        "1. Analyze cushion topology: number of seat cushions (single bench, 2-seat, 3-seat), back cushion firmness, tufting, and seam piping.\n"
        "2. Inspect armrest geometry: wide block track arms, slope arms, tuxedo high arms, or slender modernist arms.\n"
        "3. Determine leg clearance: floating on low-profile 50-100mm turned wood/metal peg legs vs ground-flush recessed plinth base.\n"
        "4. Specify upholstery: textured bouclé, linen weave, velvet, or distressed leather with exact hex code."
    ),
    "bed": (
        "1. Analyze headboard architecture: vertical channel tufted fabric, minimalist wood panel, winged headboard, or low-profile platform.\n"
        "2. Detail mattress & bedding: mattress thickness (0.25m - 0.35m), duvet drape, pillow layout, and side rail overhang.\n"
        "3. Inspect base: floating platform bed with inset LED glow vs exposed wooden legs vs upholstered frame."
    ),
    "phone": (
        "1. Enforce precise handheld millimeter scale: typically width 0.070 - 0.078m, height 0.145 - 0.165m, depth 0.007 - 0.009m.\n"
        "2. Inspect device features: display bezel, camera bump module, and matte glass or brushed titanium chassis finish.\n"
        "3. Confirm surface resting orientation: lies flat or angled on parent desk/table top."
    ),
    "laptop": (
        "1. Enforce exact laptop metric dimensions: width 0.30 - 0.36m, open height 0.20 - 0.25m, depth 0.22 - 0.25m.\n"
        "2. Analyze posture: screen lid open at 100-120 degree angle vs clamshell closed flat on table surface.\n"
        "3. Materials: anodized aluminum unibody (e.g. Space Grey #2f3033, Silver #d8d9dc, Midnight #1a1e24)."
    ),
    "monitor": (
        "1. Enforce panel dimensions: width 0.54 - 0.72m (24 to 32 inch) or 0.80 - 1.05m (ultrawide 21:9), height 0.32 - 0.45m.\n"
        "2. Inspect stand: vertical ergonomic column + rectangular/V-shaped weighted footplate vs articulated monitor arm clamped to desk.\n"
        "3. Note bezel thickness (micro-edge vs industrial) and panel curvature (flat vs 1500R/1800R curved)."
    ),
    "tv_unit": (
        "1. Enforce media console proportions: width 1.4 - 2.2m, low height 0.40 - 0.55m, depth 0.40 - 0.48m.\n"
        "2. Identify bay compartments: open media console shelves, slatted acoustic tambour doors, or soft-close drawers.\n"
        "3. Legs & mounting: wall-hung floating credenza vs tapered metal stiletto feet."
    ),
    "bookshelf": (
        "1. Analyze shelving grid: number of vertical tiers (3 to 6 shelves), horizontal partitions, and open frame vs solid backing.\n"
        "2. Material & joinery: industrial black powder-coated steel frame with oak shelves, or monolithic lacquered white MDF.\n"
        "3. Inspect contents: book stacks, decor ceramics, sculptures, and negative space rhythm."
    ),
    "lamp": (
        "1. Analyze shade silhouette: drum shade, tapered cone, opaline glass globe, or directed spotlight cowl.\n"
        "2. Stem & base structure: slender brass stem, arched cantilever arc, heavy turned stone base, or tripod wood legs.\n"
        "3. Lighting tone: warm ambient glow (2700K #ffe4b5) or cool task illumination."
    ),
    "plant": (
        "1. Pot & planter: cylindrical ceramic planter, ribbed concrete pot, or woven seagrass basket.\n"
        "2. Botanical geometry: foliage canopy height, leaf geometry (broad monstera leaves, upright snake plant blades, weeping ficus), and soil clearance."
    ),
    "rug": (
        "1. Dimensions: enforce large planar floor coverage (width 2.0 - 3.5m, height 0.015 - 0.03m, depth 1.6 - 2.8m).\n"
        "2. Weave texture: low-pile geometric Berber, hand-tufted wool, or flat-woven jute with edge fringe."
    ),
    "art": (
        "1. Frame architecture: slim floating aluminum gallery frame, ornate timber moulding, or frameless gallery-wrapped canvas.\n"
        "2. Wall flushness: thickness 0.02 - 0.05m, mounted flush against wall surface."
    ),
    "decor": (
        "1. Inspect organic or sculptural form: ceramic vase, candle holder, architectural bowl, or tray.\n"
        "2. Precision scale: sub-meter dimensions (0.10m - 0.40m), high-resolution material finish (matte stoneware, polished chrome, smoked glass)."
    )
}

DEFAULT_INSPECTION_DIRECTIVE = (
    "1. Refine its exact real-world metric dimensions (width, height, depth in meters) with millimeter precision.\n"
    "2. Identify its dominant material and exact hex color code.\n"
    "3. Provide a concise, highly detailed CAD description including form, base, joinery, and architectural styling."
)

def generate_antigravity_object_prompt(obj: Any, scene: Optional[Any] = None, step_idx: int = 1, total_steps: int = 1) -> str:
    """
    Generates a deeply targeted, intelligent CAD prompt engineered by Antigravity
    to refine a single furniture piece based on its cropped image and spatial relations.
    """
    if isinstance(obj, dict):
        obj_id = obj.get("id", "obj_1")
        name = obj.get("name", "Furniture Piece")
        category = obj.get("category", "decor").lower()
        dims = obj.get("dimensions", {})
        pos = obj.get("position", {})
        rot = obj.get("rotation", {})
        color = obj.get("color", "#70757a")
        desc = obj.get("description", "")
        attached_to = obj.get("attached_to_id")
    else:
        obj_id = getattr(obj, "id", "obj_1")
        name = getattr(obj, "name", "Furniture Piece")
        category = getattr(obj, "category", "decor").lower()
        dims_obj = getattr(obj, "dimensions", None)
        dims = {"width": dims_obj.width, "height": dims_obj.height, "depth": dims_obj.depth} if dims_obj else {}
        pos_obj = getattr(obj, "position", None)
        pos = {"x": pos_obj.x, "y": pos_obj.y, "z": pos_obj.z} if pos_obj else {}
        rot_obj = getattr(obj, "rotation", None)
        rot = {"yaw": rot_obj.yaw} if rot_obj else {}
        color = getattr(obj, "color", "#70757a")
        desc = getattr(obj, "description", "")
        attached_to = getattr(obj, "attached_to_id", None)

    w = dims.get("width", 1.0)
    h = dims.get("height", 1.0)
    d = dims.get("depth", 1.0)

    # Heuristic category match
    matched_directive = DEFAULT_INSPECTION_DIRECTIVE
    for cat_key, directive in CATEGORY_INSPECTION_DIRECTIVES.items():
        if cat_key in category or cat_key in name.lower():
            matched_directive = directive
            break

    # Contextual spatial relationships
    context_notes = []
    if attached_to:
        context_notes.append(f"- This object is currently attached to parent '{attached_to}' (rests directly on top surface).")
    
    # Check if this object acts as a parent to other items
    child_items = []
    if scene:
        scene_objs = getattr(scene, "objects", []) if not isinstance(scene, dict) else scene.get("objects", [])
        for o in scene_objs:
            o_att = getattr(o, "attached_to_id", None) if not isinstance(o, dict) else o.get("attached_to_id")
            o_name = getattr(o, "name", None) if not isinstance(o, dict) else o.get("name")
            if o_att == obj_id:
                child_items.append(o_name or "item")
    if child_items:
        context_notes.append(f"- This object is a parent support holding: {', '.join(child_items)}. Ensure top surface is flat and properly scaled.")

    context_str = "\n".join(context_notes) if context_notes else "- Freestanding in the room space."

    prompt = f"""You are SpatialCraft AI CAD Director, powered by Google Antigravity.
Your objective is fine-grained, high-fidelity 3D CAD architectural refinement of an individual furniture piece.

[TARGET OBJECT]
- Name: "{name}"
- ID: "{obj_id}"
- Category: "{category}"
- Current Initial Dimensions: Width = {w:.3f}m, Height = {h:.3f}m, Depth = {d:.3f}m
- Current Estimated Color: {color}
- Spatial Context:
{context_str}

[IMAGE INPUT]
The attached image is an isolated, high-resolution cropped photograph of '{name}' extracted directly from the room scan.

[ANTIGRAVITY ARCHITECTURAL DIRECTIVES]
Analyze the cropped image carefully and execute these CAD refinements:
{matched_directive}

[3D MESH GENERATION REQUIREMENT - BUILD FROM FRESH]
You must CONSTRUCT THE COMPLETE 3D MESH MODEL for '{name}' FROM FRESH to mimic the cropped photograph as closely as possible.
- Build the 3D model directly from scratch based on THIS SPECIFIC PHOTOGRAPHED PIECE.
- Inspect the cropped photo carefully: observe its specific joinery, leg design, cushions, handles, panels, and materials.
- DO NOT use a generic pre-baked template. Build all mesh parts from scratch based on this specific item.
- Only in an absolute emergency should default generic shapes be used.

Decompose the photographed object into its individual 3D structural components as an array of 'parts':
- 'name': human-readable part name (e.g. 'tabletop', 'left_gable', 'modesty_panel', 'drawer_1', 'seat_cushion', 'backrest_mesh', 'caster_base', 'printer_chassis', 'keypad', etc.)
- 'shape': one of 'box', 'cylinder', 'sphere', 'cone', 'torus', 'plane'
- 'args': metric dimensions array:
    * 'box': [width, height, depth]
    * 'cylinder': [radiusTop, radiusBottom, height, radialSegments]
    * 'sphere': [radius, widthSegments, heightSegments]
    * 'cone': [radius, height, radialSegments]
    * 'torus': [radius, tube, radialSegments, tubularSegments]
    * 'plane': [width, height]
- 'position': [x, y, z] relative to the base of the object:
    * x is centered at 0 (-width/2 to +width/2)
    * y = 0 is bottom resting surface, y goes up to height
    * z is centered at 0 (-depth/2 to +depth/2)
- 'rotation': [rx, ry, rz] in radians (optional, default [0, 0, 0])
- 'color': hex color code (e.g. "#c5a785", "#18181b", "#e4e4e7")
- 'roughness': 0.0 to 1.0 (e.g. 0.2 for shiny metal/glass, 0.7 for matte wood/fabric)
- 'metalness': 0.0 to 1.0 (e.g. 0.9 for chrome/aluminum, 0.05 for wood/plastic)
- 'opacity': 0.0 to 1.0 (optional, default 1.0; use 0.85 for breathable mesh or glass)

Provide between 5 and 25 parts to construct a complete, high-fidelity 3D mesh that accurately reproduces the photographed piece.

[STRICT OUTPUT FORMAT]
Respond ONLY with a valid JSON block enclosed in ```json and ```. Do not include markdown preamble or conversational commentary.

```json
{{
  "id": "{obj_id}",
  "name": "{name}",
  "category": "{category}",
  "dimensions": {{
    "width": {w},
    "height": {h},
    "depth": {d}
  }},
  "color": "{color}",
  "description": "Exhaustive CAD description with geometry, materials, and legs/cushions...",
  "materials": {{
    "primary": "material_name_here",
    "secondary": "accent_material_here"
  }},
  "features": [
    "feature_1",
    "feature_2"
  ],
  "parts": [
    {{
      "name": "part_name",
      "shape": "box",
      "args": [0.5, 0.03, 0.5],
      "position": [0.0, 0.015, 0.0],
      "rotation": [0.0, 0.0, 0.0],
      "color": "{color}",
      "roughness": 0.65,
      "metalness": 0.05
    }}
  ]
}}
```
"""
    return prompt.strip()


def build_antigravity_scene_refinement_plan(scene: Any) -> List[Dict[str, Any]]:
    """
    Builds a prioritized, sequential object-by-object refinement plan for the entire scene.
    Orders structural anchors first, followed by seating, surfaces, attached objects, and decor.
    """
    objects = getattr(scene, "objects", []) if not isinstance(scene, dict) else scene.get("objects", [])
    
    # Priority sorting weights
    priority_order = {
        "table": 1, "desk": 1, "bed": 1, "sofa": 1,
        "chair": 2, "bookshelf": 2, "tv_unit": 2, "cabinet": 2,
        "monitor": 3, "laptop": 3, "phone": 3, "lamp": 3,
        "plant": 4, "rug": 4, "art": 5, "decor": 5
    }

    def get_priority(o):
        cat = getattr(o, "category", "") if not isinstance(o, dict) else o.get("category", "")
        for k, v in priority_order.items():
            if k in cat.lower():
                return v
        return 6

    sorted_objs = sorted(objects, key=get_priority)
    total = len(sorted_objs)

    plan = []
    for idx, obj in enumerate(sorted_objs, 1):
        obj_dict = obj.model_dump() if hasattr(obj, "model_dump") else (obj if isinstance(obj, dict) else vars(obj))
        prompt = generate_antigravity_object_prompt(obj, scene=scene, step_idx=idx, total_steps=total)
        plan.append({
            "step": idx,
            "total_steps": total,
            "object_id": obj_dict.get("id"),
            "object_name": obj_dict.get("name"),
            "category": obj_dict.get("category"),
            "crop_url": obj_dict.get("crop_url"),
            "antigravity_prompt": prompt
        })

    return plan
