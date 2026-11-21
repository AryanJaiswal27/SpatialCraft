import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import * as THREE from 'three';
import type { SceneGraph } from '../types';

export const exportSceneJson = (scene: SceneGraph) => {
  const blob = new Blob([JSON.stringify(scene, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${scene.scene_id || 'room'}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

export const exportSceneGlb = (threeScene: THREE.Object3D, filename = 'reconstructed_room.glb') => {
  const exporter = new GLTFExporter();
  exporter.parse(
    threeScene,
    (gltf) => {
      const blob = new Blob([gltf as ArrayBuffer], { type: 'model/gltf-binary' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    },
    (error) => {
      console.error('Error exporting GLB:', error);
    },
    { binary: true }
  );
};

