import React, { useRef, useState } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useSceneStore } from '../hooks/useSceneStore';
import type { SceneObject } from '../types';

interface Props {
  object: SceneObject;
  isSelected: boolean;
  onSelect: () => void;
  onDragMove: (newPos: { x: number; y: number; z: number }) => void;
}

export const DetailedFurnitureMesh: React.FC<Props> = ({
  object,
  isSelected,
  onSelect,
  onDragMove,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const setIsInteracting = useSceneStore((state) => state.setIsInteracting);
  const dragPlaneRef = useRef(new THREE.Plane(new THREE.Vector3(0, 1, 0), 0));
  const planeIntersect = useRef(new THREE.Vector3());
  const dragOffset = useRef(new THREE.Vector3());

  const { width = 1.0, height = 1.0, depth = 1.0 } = object.dimensions || {};
  const yawRad = ((object.rotation?.yaw || 0) * Math.PI) / 180;
  
  // Formal muted architectural color fallback
  const primaryColor = object.color || '#3f3f46';

  useFrame(() => {
    if (!groupRef.current || isDragging) return;
    groupRef.current.position.x = THREE.MathUtils.lerp(groupRef.current.position.x, object.position.x, 0.2);
    groupRef.current.position.y = THREE.MathUtils.lerp(groupRef.current.position.y, object.position.y, 0.2);
    groupRef.current.position.z = THREE.MathUtils.lerp(groupRef.current.position.z, object.position.z, 0.2);
    groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, yawRad, 0.2);
  });

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    onSelect();
    setIsDragging(true);
    setIsInteracting(true);
    // Align horizontal drag plane with object current height
    dragPlaneRef.current.constant = -object.position.y;
    if (e.ray.intersectPlane(dragPlaneRef.current, planeIntersect.current)) {
      dragOffset.current.set(
        planeIntersect.current.x - object.position.x,
        0,
        planeIntersect.current.z - object.position.z
      );
    } else {
      dragOffset.current.set(0, 0, 0);
    }
    try {
      e.target.setPointerCapture?.(e.pointerId);
    } catch {
      // Ignored if pointer capture unsupported
    }
  };

  const handlePointerMove = (e: any) => {
    if (!isDragging) return;
    e.stopPropagation();
    if (e.ray.intersectPlane(dragPlaneRef.current, planeIntersect.current)) {
      onDragMove({
        x: Math.round((planeIntersect.current.x - dragOffset.current.x) * 1000) / 1000,
        y: object.position.y,
        z: Math.round((planeIntersect.current.z - dragOffset.current.z) * 1000) / 1000,
      });
    }
  };

  const handlePointerUp = (e: any) => {
    if (isDragging) {
      e.stopPropagation();
      setIsDragging(false);
      setIsInteracting(false);
      try {
        e.target.releasePointerCapture?.(e.pointerId);
      } catch {
        // Ignored
      }
    }
  };

  const renderGeometry = () => {
    const cat = (object.category || 'decor').toLowerCase();

    // 1. SOFA (Clean architectural proportions)
    if (cat === 'sofa') {
      const seatH = height * 0.45;
      const cushionW = (width - 0.2) / 2;
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, seatH * 0.5, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, seatH, depth]} />
            <meshStandardMaterial color={primaryColor} roughness={0.7} />
          </mesh>
          <mesh position={[-cushionW / 2, seatH + 0.05, 0.05]} castShadow>
            <boxGeometry args={[cushionW - 0.04, 0.12, depth - 0.2]} />
            <meshStandardMaterial color={primaryColor} roughness={0.8} />
          </mesh>
          <mesh position={[cushionW / 2, seatH + 0.05, 0.05]} castShadow>
            <boxGeometry args={[cushionW - 0.04, 0.12, depth - 0.2]} />
            <meshStandardMaterial color={primaryColor} roughness={0.8} />
          </mesh>
          <mesh position={[0, height * 0.7, -depth * 0.38]} castShadow>
            <boxGeometry args={[width, height * 0.55, depth * 0.25]} />
            <meshStandardMaterial color={primaryColor} roughness={0.75} />
          </mesh>
          <mesh position={[-width / 2 + 0.08, height * 0.55, 0]} castShadow>
            <boxGeometry args={[0.16, height * 0.45, depth]} />
            <meshStandardMaterial color={primaryColor} roughness={0.7} />
          </mesh>
          <mesh position={[width / 2 - 0.08, height * 0.55, 0]} castShadow>
            <boxGeometry args={[0.16, height * 0.45, depth]} />
            <meshStandardMaterial color={primaryColor} roughness={0.7} />
          </mesh>
          {[
            [-width * 0.42, -depth * 0.38],
            [width * 0.42, -depth * 0.38],
            [-width * 0.42, depth * 0.38],
            [width * 0.42, depth * 0.38],
          ].map(([lx, lz], idx) => (
            <mesh key={idx} position={[lx, 0.06, lz]} castShadow>
              <cylinderGeometry args={[0.02, 0.015, 0.12, 12]} />
              <meshStandardMaterial color="#18181b" metalness={0.8} roughness={0.3} />
            </mesh>
          ))}
        </group>
      );
    }

    // 2. TABLE / COFFEE TABLE / DESK
    if (cat === 'table' || cat === 'coffee_table' || cat === 'desk') {
      const topThick = 0.04;
      const legRadius = 0.02;
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, height - topThick / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, topThick, depth]} />
            <meshStandardMaterial color={primaryColor} roughness={0.5} metalness={0.1} />
          </mesh>
          {[
            [-width * 0.44, -depth * 0.42],
            [width * 0.44, -depth * 0.42],
            [-width * 0.44, depth * 0.42],
            [width * 0.44, depth * 0.42],
          ].map(([lx, lz], idx) => (
            <mesh key={idx} position={[lx, (height - topThick) / 2, lz]} castShadow>
              <cylinderGeometry args={[legRadius, legRadius, height - topThick, 16]} />
              <meshStandardMaterial color="#18181b" metalness={0.7} roughness={0.3} />
            </mesh>
          ))}
        </group>
      );
    }

    // 3. CHAIR
    if (cat === 'chair') {
      const seatY = height * 0.48;
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, seatY, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, 0.05, depth]} />
            <meshStandardMaterial color={primaryColor} roughness={0.7} />
          </mesh>
          <mesh position={[0, seatY + height * 0.3, -depth * 0.42]} castShadow>
            <boxGeometry args={[width * 0.9, height * 0.48, 0.04]} />
            <meshStandardMaterial color={primaryColor} roughness={0.7} />
          </mesh>
          {[
            [-width * 0.4, -depth * 0.4],
            [width * 0.4, -depth * 0.4],
            [-width * 0.4, depth * 0.4],
            [width * 0.4, depth * 0.4],
          ].map(([lx, lz], idx) => (
            <mesh key={idx} position={[lx, seatY / 2, lz]} castShadow>
              <cylinderGeometry args={[0.015, 0.012, seatY, 12]} />
              <meshStandardMaterial color="#27272a" roughness={0.5} />
            </mesh>
          ))}
        </group>
      );
    }

    // 4. BED
    if (cat === 'bed') {
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, height * 0.2, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, height * 0.3, depth]} />
            <meshStandardMaterial color="#27272a" roughness={0.6} />
          </mesh>
          <mesh position={[0, height * 0.45, 0.05]} castShadow>
            <boxGeometry args={[width - 0.1, height * 0.3, depth - 0.15]} />
            <meshStandardMaterial color="#e4e4e7" roughness={0.8} />
          </mesh>
          <mesh position={[0, height * 0.52, depth * 0.15]} castShadow>
            <boxGeometry args={[width - 0.08, height * 0.18, depth * 0.6]} />
            <meshStandardMaterial color={primaryColor} roughness={0.7} />
          </mesh>
          <mesh position={[0, height * 0.7, -depth / 2 + 0.05]} castShadow>
            <boxGeometry args={[width + 0.05, height * 0.7, 0.08]} />
            <meshStandardMaterial color={primaryColor} roughness={0.6} />
          </mesh>
          <mesh position={[-width * 0.22, height * 0.65, -depth * 0.28]} castShadow>
            <boxGeometry args={[width * 0.38, 0.1, depth * 0.22]} />
            <meshStandardMaterial color="#fafafa" roughness={0.8} />
          </mesh>
          <mesh position={[width * 0.22, height * 0.65, -depth * 0.28]} castShadow>
            <boxGeometry args={[width * 0.38, 0.1, depth * 0.22]} />
            <meshStandardMaterial color="#fafafa" roughness={0.8} />
          </mesh>
        </group>
      );
    }

    // 5. LAMP
    if (cat === 'lamp') {
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, 0.02, 0]} castShadow>
            <cylinderGeometry args={[width * 0.4, width * 0.4, 0.03, 32]} />
            <meshStandardMaterial color="#71717a" metalness={0.9} roughness={0.2} />
          </mesh>
          <mesh position={[0, height * 0.48, 0]} castShadow>
            <cylinderGeometry args={[0.012, 0.012, height * 0.9, 16]} />
            <meshStandardMaterial color="#71717a" metalness={0.9} roughness={0.2} />
          </mesh>
          <mesh position={[0, height * 0.88, 0]} castShadow>
            <cylinderGeometry args={[width * 0.4, width * 0.45, height * 0.25, 32, 1, true]} />
            <meshStandardMaterial color="#f4f4f5" roughness={0.8} side={THREE.DoubleSide} />
          </mesh>
          <pointLight position={[0, height * 0.85, 0]} intensity={1.5} distance={5} color="#fff8f0" castShadow />
        </group>
      );
    }

    // 6. TV UNIT
    if (cat === 'tv_unit') {
      const consoleH = height * 0.45;
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, consoleH / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, consoleH, depth]} />
            <meshStandardMaterial color="#18181b" roughness={0.5} />
          </mesh>
          <mesh position={[0, consoleH + 0.015, 0]} castShadow>
            <boxGeometry args={[width * 0.4, 0.015, depth * 0.35]} />
            <meshStandardMaterial color="#27272a" metalness={0.9} roughness={0.2} />
          </mesh>
          <mesh position={[0, consoleH + 0.1, 0]} castShadow>
            <cylinderGeometry args={[0.015, 0.015, 0.16, 16]} />
            <meshStandardMaterial color="#27272a" metalness={0.9} />
          </mesh>
          <mesh position={[0, consoleH + height * 0.35, 0]} castShadow>
            <boxGeometry args={[width * 0.88, height * 0.5, 0.02]} />
            <meshStandardMaterial color="#09090b" roughness={0.05} metalness={0.9} />
          </mesh>
        </group>
      );
    }

    // 7. BOOKSHELF
    if (cat === 'bookshelf') {
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, height / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, height, depth]} />
            <meshStandardMaterial color="#27272a" roughness={0.6} />
          </mesh>
          {[0.25, 0.5, 0.75].map((ratio, idx) => (
            <mesh key={idx} position={[0, height * ratio, depth * 0.02]}>
              <boxGeometry args={[width - 0.06, 0.02, depth - 0.04]} />
              <meshStandardMaterial color="#18181b" roughness={0.5} />
            </mesh>
          ))}
        </group>
      );
    }

    // 8. PLANT (Architectural stylized plant)
    if (cat === 'plant') {
      const potH = height * 0.4;
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, potH / 2, 0]} castShadow>
            <cylinderGeometry args={[width * 0.35, width * 0.28, potH, 24]} />
            <meshStandardMaterial color="#52525b" roughness={0.8} />
          </mesh>
          <mesh position={[0, potH * 0.95, 0]}>
            <cylinderGeometry args={[width * 0.33, width * 0.33, 0.02, 24]} />
            <meshStandardMaterial color="#18181b" roughness={0.9} />
          </mesh>
          {[
            [0, potH + 0.15, 0, 0],
            [-0.08, potH + 0.22, 0.06, 0.25],
            [0.08, potH + 0.25, -0.05, -0.2],
          ].map(([fx, fy, fz, rotZ], idx) => (
            <mesh key={idx} position={[fx, fy, fz]} rotation={[0, idx * 1.5, rotZ]} castShadow>
              <sphereGeometry args={[width * 0.22, 12, 12]} scale={[1, 1.3, 0.25]} />
              <meshStandardMaterial color="#3f4e43" roughness={0.6} />
            </mesh>
          ))}
        </group>
      );
    }

    // 9. RUG
    if (cat === 'rug') {
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, 0.003, 0]} receiveShadow>
            <boxGeometry args={[width, 0.006, depth]} />
            <meshStandardMaterial color={primaryColor} roughness={0.9} />
          </mesh>
        </group>
      );
    }

    // 10. ART / WALL ART / DECOR
    if (cat === 'art' || cat === 'decor' || cat.includes('art') || cat.includes('painting')) {
      const artDepth = Math.max(depth, 0.04);
      return (
        <group position={[0, -height / 2, 0]}>
          {/* Outer Sleek Floating Frame */}
          <mesh position={[0, height / 2, 0]} castShadow>
            <boxGeometry args={[width, height, artDepth]} />
            <meshStandardMaterial color="#18181b" roughness={0.4} metalness={0.2} />
          </mesh>
          {/* Canvas Surface with Matting */}
          <mesh position={[0, height / 2, artDepth / 2 + 0.005]} receiveShadow>
            <planeGeometry args={[width * 0.9, height * 0.9]} />
            <meshStandardMaterial color={primaryColor || '#d4d4d8'} roughness={0.85} />
          </mesh>
        </group>
      );
    }

    // 11. PHONE / SMARTPHONE
    if (cat === 'phone' || cat === 'smartphone' || cat === 'mobile') {
      const pW = width || 0.08;
      const pH = height || 0.012;
      const pD = depth || 0.16;
      return (
        <group position={[0, -pH / 2, 0]}>
          {/* Phone Chassis */}
          <mesh position={[0, pH / 2, 0]} castShadow>
            <boxGeometry args={[pW, pH, pD]} />
            <meshStandardMaterial color="#18181b" roughness={0.2} metalness={0.8} />
          </mesh>
          {/* Glass Display */}
          <mesh position={[0, pH + 0.0005, 0]} receiveShadow>
            <planeGeometry args={[pW * 0.92, pD * 0.94]} />
            <meshStandardMaterial color="#09090b" roughness={0.08} metalness={0.9} />
          </mesh>
          {/* Camera Bump */}
          <mesh position={[pW * 0.25, pH + 0.001, -pD * 0.32]} castShadow>
            <boxGeometry args={[pW * 0.35, 0.002, pD * 0.25]} />
            <meshStandardMaterial color="#27272a" roughness={0.3} metalness={0.7} />
          </mesh>
        </group>
      );
    }

    // 12. LAPTOP
    if (cat === 'laptop') {
      const lW = width || 0.32;
      const lH = height || 0.02;
      const lD = depth || 0.22;
      return (
        <group position={[0, -lH / 2, 0]}>
          {/* Keyboard Chassis Base */}
          <mesh position={[0, lH * 0.3, 0]} castShadow>
            <boxGeometry args={[lW, lH * 0.5, lD]} />
            <meshStandardMaterial color="#3f3f46" roughness={0.3} metalness={0.6} />
          </mesh>
          {/* Angled Screen Display */}
          <group position={[0, lH * 0.6, -lD / 2]} rotation={[-Math.PI / 6, 0, 0]}>
            <mesh position={[0, lD * 0.45, 0]} castShadow>
              <boxGeometry args={[lW, lD * 0.9, 0.008]} />
              <meshStandardMaterial color="#18181b" roughness={0.2} metalness={0.8} />
            </mesh>
            <mesh position={[0, lD * 0.45, 0.005]} receiveShadow>
              <planeGeometry args={[lW * 0.92, lD * 0.82]} />
              <meshStandardMaterial color="#09090b" roughness={0.08} metalness={0.9} />
            </mesh>
          </group>
        </group>
      );
    }

    // DEFAULT
    return (
      <group position={[0, -height / 2, 0]}>
        <mesh position={[0, height / 2, 0]} castShadow receiveShadow>
          <boxGeometry args={[width, height, depth]} />
          <meshStandardMaterial color={primaryColor} roughness={0.5} />
        </mesh>
      </group>
    );
  };

  return (
    <group
      ref={groupRef}
      position={[object.position.x, object.position.y, object.position.z]}
      rotation={[0, yawRad, 0]}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerOver={() => setIsHovered(true)}
      onPointerOut={() => setIsHovered(false)}
    >
      {renderGeometry()}

      {/* Formal Selection Box / Ring (Crisp White Monochromatic Indicator) */}
      {isSelected && (
        <group position={[0, -height / 2 + 0.005, 0]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[Math.max(width, depth) * 0.65, Math.max(width, depth) * 0.68, 4]} />
            <meshBasicMaterial color="#ffffff" side={THREE.DoubleSide} />
          </mesh>
        </group>
      )}

      {/* Attached / Stuck Anchor Ring Indicator */}
      {object.attached_to_id && (
        <group position={[0, -height / 2 + 0.002, 0]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[Math.max(width, depth) * 0.52, Math.max(width, depth) * 0.55, 16]} />
            <meshBasicMaterial color="#a1a1aa" side={THREE.DoubleSide} transparent opacity={0.6} />
          </mesh>
        </group>
      )}

      {/* Subtle Hover Wire */}
      {isHovered && !isSelected && (
        <group position={[0, -height / 2 + 0.005, 0]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[Math.max(width, depth) * 0.65, Math.max(width, depth) * 0.67, 4]} />
            <meshBasicMaterial color="#71717a" side={THREE.DoubleSide} transparent opacity={0.6} />
          </mesh>
        </group>
      )}
    </group>
  );
};
