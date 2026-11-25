export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

export interface Dimensions3D {
  width: number;
  height: number;
  depth: number;
}

export interface Rotation3D {
  yaw: number;
  pitch?: number;
  roll?: number;
}

export interface RoomSurface {
  material: string;
  color: string;
  texture_url?: string;
}

export interface RoomConfig {
  dimensions: Dimensions3D;
  floor: RoomSurface;
  walls: RoomSurface;
  ceiling: RoomSurface;
}

export interface MeshPart {
  name?: string;
  shape: 'box' | 'cylinder' | 'sphere' | 'cone' | 'torus' | 'plane';
  args?: any[];
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: [number, number, number];
  color?: string;
  roughness?: number;
  metalness?: number;
  opacity?: number;
  transparent?: boolean;
  emissive?: string;
  emissiveIntensity?: number;
}

export interface SceneObject {
  id: string;
  name: string;
  category: 'sofa' | 'table' | 'chair' | 'bed' | 'lamp' | 'plant' | 'tv_unit' | 'bookshelf' | 'rug' | 'art' | 'decor' | string;
  description?: string;
  position: Vector3D;
  rotation: Rotation3D;
  dimensions: Dimensions3D;
  color: string;
  model_type?: string;
  model_url?: string;
  box_2d?: number[];
  crop_url?: string;
  attached_to_id?: string | null;
  relative_position?: Vector3D | null;
  relative_yaw?: number | null;
  materials?: Record<string, string>;
  features?: string[];
  parts?: MeshPart[];
  mesh_obj?: string;
}

export interface SceneGraph {
  scene_id: string;
  name: string;
  image_url?: string;
  room: RoomConfig;
  objects: SceneObject[];
  created_at: string;
  updated_at: string;
  status: 'processing' | 'ready' | 'failed';
  status_message?: string;
}

export type LLMTarget = 'gemini' | 'chatgpt' | 'deepseek' | 'antigravity' | 'physical' | 'claude';

export type ActiveModal = 'none' | 'upload' | 'chat' | 'scenes' | 'manual_paste' | 'qr' | 'logs' | 'calibration' | 'antigravity' | 'guide' | 'models';


