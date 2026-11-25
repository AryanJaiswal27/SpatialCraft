import { create } from 'zustand';
import * as THREE from 'three';
import { exportSceneGlb, exportSceneJson } from '../utils/exporter';
import type { SceneGraph, LLMTarget, Vector3D, ActiveModal, SceneObject, Dimensions3D } from '../types';

interface SceneState {
  scene: SceneGraph | null;
  selectedObjectId: string | null;
  targetLLM: LLMTarget;
  isUploading: boolean;
  uploadStatus: string;
  uploadLogs: string[];
  isPrompting: boolean;
  activeModal: ActiveModal;
  availableScenes: any[];
  isInteracting: boolean;
  sceneThreeRef: THREE.Scene | null;

  setIsInteracting: (interacting: boolean) => void;
  setSceneThreeRef: (ref: THREE.Scene | null) => void;
  setAvailableScenes: (scenes: any[]) => void;
  refreshAvailableScenes: () => Promise<void>;
  loadSceneById: (sceneId: string) => Promise<void>;
  exportGlb: () => void;
  exportJson: () => void;

  setScene: (scene: SceneGraph) => void;
  selectObject: (id: string | null) => void;
  setTargetLLM: (target: LLMTarget) => void;
  setActiveModal: (modal: ActiveModal) => void;
  setUploading: (uploading: boolean, status?: string) => void;
  addUploadLog: (log: string) => void;

  fetchScene: (sceneId: string) => Promise<void>;
  updateObjectPosition: (objId: string, newPos: Vector3D) => Promise<void>;
  rotateObject: (objId: string, deltaDegrees?: number) => Promise<void>;
  attachObject: (childId: string, parentId: string) => Promise<void>;
  detachObject: (childId: string) => Promise<void>;
  deleteObject: (objId: string) => Promise<void>;
  addObject: (template: Partial<SceneObject> & { dimensions: Dimensions3D; category?: string; name?: string }, position?: Vector3D) => Promise<void>;
  sendPromptEdit: (prompt: string) => Promise<void>;
}

export const useSceneStore = create<SceneState>((set, get) => ({
  scene: null,
  selectedObjectId: null,
  targetLLM: 'gemini',
  isUploading: false,
  uploadStatus: '',
  uploadLogs: [],
  isPrompting: false,
  activeModal: 'none',
  availableScenes: [],
  isInteracting: false,
  sceneThreeRef: null,

  setIsInteracting: (isInteracting) => set({ isInteracting }),
  setSceneThreeRef: (sceneThreeRef) => set({ sceneThreeRef }),
  setAvailableScenes: (availableScenes) => set({ availableScenes }),
  refreshAvailableScenes: async () => {
    try {
      const res = await fetch('/api/scenes');
      if (res.ok) {
        const scenes = await res.json();
        set({ availableScenes: scenes });
      }
    } catch (e) {
      console.error('Failed to refresh scenes:', e);
    }
  },
  loadSceneById: async (sceneId: string) => {
    try {
      const res = await fetch(`/api/scene/${sceneId}`);
      if (res.ok) {
        const data: SceneGraph = await res.json();
        set({ scene: data, selectedObjectId: null });
      }
    } catch (e) {
      console.error('Failed to load scene:', e);
    }
  },

  exportGlb: () => {
    const ref = get().sceneThreeRef;
    const currentScene = get().scene;
    if (ref) {
      exportSceneGlb(ref, `${currentScene?.scene_id || 'reconstructed_room'}.glb`);
    }
  },

  exportJson: () => {
    const currentScene = get().scene;
    if (currentScene) {
      exportSceneJson(currentScene);
    }
  },

  setScene: (scene) => set({ scene }),
  selectObject: (id) => set({ selectedObjectId: id }),
  setTargetLLM: (targetLLM) => set({ targetLLM }),
  setActiveModal: (activeModal) => set({ activeModal }),
  setUploading: (isUploading, uploadStatus = '') => set({ isUploading, uploadStatus }),
  addUploadLog: (log) => set((state) => ({ uploadLogs: [...state.uploadLogs, log] })),

  fetchScene: async (sceneId: string) => {
    try {
      const res = await fetch(`/api/scene/${sceneId}`);
      if (res.ok) {
        const data: SceneGraph = await res.json();
        set({ scene: data });
      }
    } catch (e) {
      console.error('Failed to fetch scene:', e);
    }
  },

  updateObjectPosition: async (objId: string, newPos: Vector3D) => {
    const scene = get().scene;
    if (!scene) return;

    const targetObj = scene.objects.find((o) => o.id === objId);
    if (!targetObj) return;

    const dx = newPos.x - targetObj.position.x;
    const dy = newPos.y - targetObj.position.y;
    const dz = newPos.z - targetObj.position.z;

    // Propagate translation to target AND any child objects stuck to it
    const updatedObjects = scene.objects.map((obj) => {
      if (obj.id === objId) {
        return { ...obj, position: newPos };
      }
      if (obj.attached_to_id === objId) {
        return {
          ...obj,
          position: {
            x: Math.round((obj.position.x + dx) * 1000) / 1000,
            y: Math.round((obj.position.y + dy) * 1000) / 1000,
            z: Math.round((obj.position.z + dz) * 1000) / 1000,
          },
        };
      }
      return obj;
    });

    set({ scene: { ...scene, objects: updatedObjects } });

    try {
      await fetch(`/api/scene/${scene.scene_id}/object/${objId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: newPos }),
      });
    } catch (e) {
      console.error('Failed to persist object position:', e);
    }
  },

  rotateObject: async (objId: string, deltaDegrees = 45) => {
    const scene = get().scene;
    if (!scene) return;

    const targetObj = scene.objects.find((o) => o.id === objId);
    if (!targetObj) return;

    const newYaw = ((targetObj.rotation.yaw || 0) + deltaDegrees) % 360;
    const newRot = { ...targetObj.rotation, yaw: newYaw };

    const rad = (deltaDegrees * Math.PI) / 180;
    const cosTheta = Math.cos(rad);
    const sinTheta = Math.sin(rad);

    // Propagate rotation to target AND rotate any attached children around parent center
    const updatedObjects = scene.objects.map((obj) => {
      if (obj.id === objId) {
        return { ...obj, rotation: newRot };
      }
      if (obj.attached_to_id === objId) {
        const relX = obj.position.x - targetObj.position.x;
        const relZ = obj.position.z - targetObj.position.z;
        const rotX = relX * cosTheta - relZ * sinTheta;
        const rotZ = relX * sinTheta + relZ * cosTheta;

        return {
          ...obj,
          position: {
            x: Math.round((targetObj.position.x + rotX) * 1000) / 1000,
            y: obj.position.y,
            z: Math.round((targetObj.position.z + rotZ) * 1000) / 1000,
          },
          rotation: {
            ...obj.rotation,
            yaw: Math.round(((obj.rotation.yaw || 0) + deltaDegrees) % 360),
          },
        };
      }
      return obj;
    });

    set({ scene: { ...scene, objects: updatedObjects } });

    try {
      await fetch(`/api/scene/${scene.scene_id}/object/${objId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rotation: newRot }),
      });
    } catch (e) {
      console.error('Failed to persist object rotation:', e);
    }
  },

  attachObject: async (childId: string, parentId: string) => {
    const scene = get().scene;
    if (!scene) return;

    const parent = scene.objects.find((o) => o.id === parentId);
    const child = scene.objects.find((o) => o.id === childId);
    if (!parent || !child) return;

    // Snap child vertically flush to the parent surface
    const snappedY = Math.round(
      (parent.position.y + (parent.dimensions.height / 2) + (child.dimensions.height / 2)) * 1000
    ) / 1000;

    const newPos = { ...child.position, y: snappedY };

    const updatedObjects = scene.objects.map((obj) =>
      obj.id === childId ? { ...obj, attached_to_id: parentId, position: newPos } : obj
    );
    set({ scene: { ...scene, objects: updatedObjects } });

    try {
      await fetch(`/api/scene/${scene.scene_id}/object/${childId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attached_to_id: parentId, position: newPos }),
      });
    } catch (e) {
      console.error('Failed to persist attachment:', e);
    }
  },

  detachObject: async (childId: string) => {
    const scene = get().scene;
    if (!scene) return;

    const updatedObjects = scene.objects.map((obj) =>
      obj.id === childId ? { ...obj, attached_to_id: null } : obj
    );
    set({ scene: { ...scene, objects: updatedObjects } });

    try {
      await fetch(`/api/scene/${scene.scene_id}/object/${childId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attached_to_id: 'none' }),
      });
    } catch (e) {
      console.error('Failed to detach object:', e);
    }
  },

  deleteObject: async (objId: string) => {
    const scene = get().scene;
    if (!scene) return;

    // Unstick any children whose parent was deleted
    const updatedObjects = scene.objects
      .filter((obj) => obj.id !== objId)
      .map((obj) => (obj.attached_to_id === objId ? { ...obj, attached_to_id: null } : obj));

    set({ scene: { ...scene, objects: updatedObjects }, selectedObjectId: null });

    try {
      await fetch(`/api/scene/${scene.scene_id}/object/${objId}`, {
        method: 'DELETE',
      });
    } catch (e) {
      console.error('Failed to delete object:', e);
    }
  },

  addObject: async (template, position) => {
    let currentScene = get().scene;
    if (!currentScene || currentScene.scene_id === 'home') {
      const newSceneId = `scene_${Date.now().toString(36)}`;
      currentScene = {
        scene_id: newSceneId,
        name: 'CUSTOM ROOM TWIN',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'ready',
        room: {
          dimensions: { width: 5.0, height: 2.8, depth: 5.0 },
          floor: { material: 'slate', color: '#18181b' },
          walls: { material: 'matte_plaster', color: '#27272a' },
          ceiling: { material: 'matte_plaster', color: '#3f3f46' },
        },
        objects: [],
      };
      set({ scene: currentScene });
    }

    const h = template.dimensions?.height || 0.8;
    const defaultY = Number((h / 2).toFixed(3));

    const dropPos: Vector3D = position
      ? {
          x: Number(position.x.toFixed(2)),
          y: Math.max(defaultY, Number(position.y.toFixed(2))),
          z: Number(position.z.toFixed(2)),
        }
      : {
          x: Number(((Math.random() - 0.5) * 0.4).toFixed(2)),
          y: defaultY,
          z: Number(((Math.random() - 0.5) * 0.4).toFixed(2)),
        };

    const newObj: SceneObject = {
      id: `obj_${template.category || 'decor'}_${Date.now().toString(36)}`,
      name: template.name || 'New Object',
      category: template.category || 'decor',
      description: template.description || '',
      position: dropPos,
      rotation: { yaw: 0 },
      dimensions: template.dimensions,
      color: template.color || '#71717a',
      parts: template.parts || [],
    };

    const updatedObjects = [...(currentScene.objects || []), newObj];
    const updatedScene: SceneGraph = {
      ...currentScene,
      objects: updatedObjects,
      updated_at: new Date().toISOString(),
    };

    set({ scene: updatedScene, selectedObjectId: newObj.id });

    try {
      await fetch(`/api/scene/${updatedScene.scene_id}/object`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newObj),
      });

      const verifyRes = await fetch(`/api/scene/${updatedScene.scene_id}/verify_placement`, {
        method: 'POST',
      });
      if (verifyRes.ok) {
        const verifiedData = await verifyRes.json();
        const syncedScene = verifiedData?.scene_id ? verifiedData : verifiedData?.scene;
        if (syncedScene) {
          set({ scene: syncedScene });
          get().refreshAvailableScenes();
        }
      }
    } catch (e) {
      console.error('Failed to sync added object with server:', e);
    }
  },

  sendPromptEdit: async (prompt: string) => {
    const scene = get().scene;
    if (!scene) return;

    set({ isPrompting: true });
    try {
      const res = await fetch(`/api/scene/${scene.scene_id}/prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      if (res.ok) {
        const updatedScene: SceneGraph = await res.json();
        set({ scene: updatedScene });
      } else {
        console.warn('Prompt edit request returned status:', res.status);
      }
    } catch (e) {
      console.error('Failed to send prompt edit:', e);
    } finally {
      set({ isPrompting: false });
    }
  },
}));
