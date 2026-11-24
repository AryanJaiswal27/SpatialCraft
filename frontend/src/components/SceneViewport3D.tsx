import React, { Suspense, useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { useSceneStore } from '../hooks/useSceneStore';
import { DetailedFurnitureMesh } from './DetailedFurnitureMesh';
import { RoomMesh } from './RoomMesh';
import { GeodeMatrix3D } from './GeodeMatrix3D';
import type { Vector3D } from '../types';

const SceneBridge: React.FC = () => {
  const { scene } = useThree();
  const setSceneThreeRef = useSceneStore((state) => state.setSceneThreeRef);
  useEffect(() => {
    setSceneThreeRef(scene);
  }, [scene, setSceneThreeRef]);
  return null;
};

const DropHandler: React.FC = () => {
  const { camera, gl } = useThree();
  const addObject = useSceneStore((state) => state.addObject);

  useEffect(() => {
    const canvas = gl.domElement;

    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer) {
        e.dataTransfer.dropEffect = 'copy';
      }
    };

    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      try {
        const raw = e.dataTransfer?.getData('application/json');
        if (!raw) return;
        const catalogItem = JSON.parse(raw);
        if (!catalogItem || !catalogItem.dimensions) return;

        const rect = canvas.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(new THREE.Vector2(x, y), camera);

        const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
        const intersectPoint = new THREE.Vector3();
        const hit = raycaster.ray.intersectPlane(groundPlane, intersectPoint);

        const dropY = catalogItem.dimensions.height / 2;
        const dropPos: Vector3D = hit
          ? {
              x: Number(intersectPoint.x.toFixed(2)),
              y: Number(dropY.toFixed(2)),
              z: Number(intersectPoint.z.toFixed(2)),
            }
          : { x: 0, y: Number(dropY.toFixed(2)), z: 0 };

        addObject(catalogItem, dropPos);
      } catch (err) {
        console.error('Failed to parse dropped 3D model:', err);
      }
    };

    canvas.addEventListener('dragover', handleDragOver);
    canvas.addEventListener('drop', handleDrop);

    return () => {
      canvas.removeEventListener('dragover', handleDragOver);
      canvas.removeEventListener('drop', handleDrop);
    };
  }, [camera, gl, addObject]);

  return null;
};

export const SceneViewport3D: React.FC = () => {
  const { scene, selectedObjectId, selectObject, updateObjectPosition, isInteracting } = useSceneStore();

  const handlePointerMissed = () => {
    selectObject(null);
  };

  // Home state condition: scene is null, 'home', or has zero objects without image upload
  const isHomeState = !scene || scene.scene_id === 'home' || (scene.objects?.length === 0 && !scene.image_url);

  return (
    <div className="w-full h-full relative bg-zinc-950 overflow-hidden select-none">
      <Canvas
        shadows
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: false, powerPreference: 'default' }}
        camera={{ position: [0, 3.8, 6.2], fov: 45, near: 0.1, far: 50 }}
        onPointerMissed={handlePointerMissed}
      >
        <Suspense fallback={null}>
          <SceneBridge />
          <DropHandler />
          {/* Neutral studio lighting */}
          <ambientLight intensity={0.9} />
          <directionalLight
            position={[5, 8, 4]}
            intensity={1.2}
            castShadow
            shadow-mapSize-width={1024}
            shadow-mapSize-height={1024}
            shadow-bias={-0.0001}
          />

          {/* Conditional 3D Render: Home Geode vs Reconstructed Room */}
          {isHomeState ? (
            <GeodeMatrix3D />
          ) : (
            <>
              {/* Room Boundaries & Floor Metric Grid */}
              {scene?.room && <RoomMesh room={scene.room} />}

              {/* Reconstructed Furniture Elements */}
              {scene?.objects?.map((obj) => (
                <DetailedFurnitureMesh
                  key={obj.id}
                  object={obj}
                  isSelected={selectedObjectId === obj.id}
                  onSelect={() => selectObject(obj.id)}
                  onDragMove={(newPos) => updateObjectPosition(obj.id, newPos)}
                />
              ))}
            </>
          )}

          {/* Touch-Optimized Mobile Controls */}
          <OrbitControls
            makeDefault
            enabled={!isInteracting}
            minDistance={1.2}
            maxDistance={14}
            maxPolarAngle={Math.PI / 2 - 0.05}
            enableDamping
            dampingFactor={0.08}
            rotateSpeed={0.7}
          />
        </Suspense>
      </Canvas>

      {/* Subtle CAD HUD Overlays */}
      {isHomeState && (
        <div className="absolute top-14 left-3 pointer-events-none font-mono text-[9px] text-zinc-500 space-y-0.5 z-10">
          <div className="text-zinc-200 font-bold tracking-wider uppercase text-[10px] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 bg-zinc-100 animate-pulse" />
            SPATIAL MATRIX CORE // ONLINE
          </div>
          <div className="text-zinc-400">GEODESIC POLYHEDRON (EDGES &amp; VERTICES)</div>
          <div className="text-zinc-600">AWAITING 2D ROOM PHOTOGRAPH CAPTURE</div>
        </div>
      )}
    </div>
  );
};
