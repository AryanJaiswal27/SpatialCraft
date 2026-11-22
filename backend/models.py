from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class Vector3D(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

class Dimensions3D(BaseModel):
    width: float = 1.0   # X axis dimension (meters)
    height: float = 1.0  # Y axis dimension (meters)
    depth: float = 1.0   # Z axis dimension (meters)

class Rotation3D(BaseModel):
    yaw: float = 0.0     # Rotation around Y axis in degrees
    pitch: float = 0.0
    roll: float = 0.0

class RoomSurface(BaseModel):
    material: str = "wood"
    color: str = "#d4b595"
    texture_url: Optional[str] = None

class RoomConfig(BaseModel):
    dimensions: Dimensions3D = Field(default_factory=lambda: Dimensions3D(width=5.0, height=2.8, depth=5.0))
    floor: RoomSurface = Field(default_factory=lambda: RoomSurface(material="parquet", color="#c5a078"))
    walls: RoomSurface = Field(default_factory=lambda: RoomSurface(material="plaster", color="#f0eee9"))
    ceiling: RoomSurface = Field(default_factory=lambda: RoomSurface(material="plaster", color="#fafafa"))

class SceneObject(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    category: str # 'sofa', 'table', 'chair', 'bed', 'lamp', 'plant', 'tv_unit', 'rug', 'decor'
    description: str = ""
    position: Vector3D
    rotation: Rotation3D = Field(default_factory=Rotation3D)
    dimensions: Dimensions3D = Field(default_factory=Dimensions3D)
    color: str = "#888888"
    model_type: str = "procedural" # 'procedural' or 'glb'
    model_url: Optional[str] = None
    crop_url: Optional[str] = None
    box_2d: Optional[List[float]] = None # [ymin, xmin, ymax, xmax] normalized
    attached_to_id: Optional[str] = None # None or parent object ID or 'wall_north'/'wall_south'/'wall_east'/'wall_west'
    relative_position: Optional[Vector3D] = None
    relative_yaw: Optional[float] = None
    parts: Optional[List[Dict[str, Any]]] = None
    mesh_obj: Optional[str] = None

class SceneGraph(BaseModel):
    model_config = ConfigDict(extra="allow")

    scene_id: str
    name: str = "Reconstructed Room"
    image_url: Optional[str] = None
    room: RoomConfig = Field(default_factory=RoomConfig)
    objects: List[SceneObject] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    status: str = "ready" # 'processing', 'ready', 'failed'
    status_message: str = ""

class PromptEditRequest(BaseModel):
    prompt: str

class UpdateObjectRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    description: Optional[str] = None
    position: Optional[Vector3D] = None
    rotation: Optional[Rotation3D] = None
    dimensions: Optional[Dimensions3D] = None
    color: Optional[str] = None
    materials: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    parts: Optional[List[Dict[str, Any]]] = None
    mesh_obj: Optional[str] = None
    attached_to_id: Optional[str] = None
    relative_position: Optional[Vector3D] = None
    relative_yaw: Optional[float] = None
