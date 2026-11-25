import React, { useMemo } from 'react';
import * as THREE from 'three';
import type { RoomConfig } from '../types';

interface Props {
  room: RoomConfig;
}

function hexLuminance(hex: string): number {
  const clean = hex.replace('#', '');
  if (clean.length !== 6) return 0.5;
  const r = parseInt(clean.slice(0, 2), 16) / 255;
  const g = parseInt(clean.slice(2, 4), 16) / 255;
  const b = parseInt(clean.slice(4, 6), 16) / 255;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export const RoomMesh: React.FC<Props> = ({ room }) => {
  const { width = 5.0, height = 2.8, depth = 5.0 } = room.dimensions || {};
  const floorColor = room.floor?.color || '#d8d0c5';
  const floorMat = (room.floor?.material || '').toLowerCase();
  const wallColor = room.walls?.color || '#f4f2ed';
  const ceilingColor = room.ceiling?.color || '#faf8f5';

  const halfW = width / 2;
  const halfD = depth / 2;

  const isPolishedFloor =
    floorMat.includes('polished') ||
    floorMat.includes('vitrified') ||
    floorMat.includes('glossy') ||
    floorMat.includes('marble') ||
    floorMat.includes('tile');

  const isLightFloor = hexLuminance(floorColor) > 0.45;
  const isLightWall = hexLuminance(wallColor) > 0.45;
  const baseboardColor = isLightWall ? '#e2dbd2' : '#27272a';
  const gridColor = isLightFloor ? '#9e9589' : '#3f3f46';

  // Exact rectangular floor grid clipped cleanly to width x depth (zero overhang outside room)
  const floorGridGeometry = useMemo(() => {
    const step = isPolishedFloor ? 0.6 : 0.5;
    const vertices: number[] = [];

    for (let x = -halfW + step; x < halfW - 0.01; x += step) {
      vertices.push(x, 0.002, -halfD, x, 0.002, halfD);
    }
    for (let z = -halfD + step; z < halfD - 0.01; z += step) {
      vertices.push(-halfW, 0.002, z, halfW, 0.002, z);
    }

    // Perimeter border hairline
    vertices.push(
      -halfW, 0.002, -halfD, halfW, 0.002, -halfD,
      halfW, 0.002, -halfD, halfW, 0.002, halfD,
      halfW, 0.002, halfD, -halfW, 0.002, halfD,
      -halfW, 0.002, halfD, -halfW, 0.002, -halfD
    );

    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    return geom;
  }, [width, depth, halfW, halfD, isPolishedFloor]);

  return (
    <group>
      {/* Floor Plate */}
      <mesh position={[0, 0, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[width, depth]} />
        <meshStandardMaterial
          color={floorColor}
          roughness={isPolishedFloor ? 0.22 : 0.65}
          metalness={isPolishedFloor ? 0.08 : 0.05}
        />
      </mesh>

      {/* Clipped Architectural Tile / Scale Lines */}
      <lineSegments geometry={floorGridGeometry}>
        <lineBasicMaterial color={gridColor} transparent opacity={isPolishedFloor ? 0.22 : 0.28} />
      </lineSegments>

      {/* Back Boundary Wall (faces +Z into room) */}
      <mesh position={[0, height / 2, -halfD]} receiveShadow>
        <planeGeometry args={[width, height]} />
        <meshStandardMaterial color={wallColor} roughness={0.85} side={THREE.FrontSide} />
      </mesh>

      {/* Left Boundary Wall (faces +X into room) */}
      <mesh position={[-halfW, height / 2, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[depth, height]} />
        <meshStandardMaterial color={wallColor} roughness={0.85} side={THREE.FrontSide} />
      </mesh>

      {/* Right Boundary Wall (faces -X into room; auto-culls when viewing from outside right) */}
      <mesh position={[halfW, height / 2, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[depth, height]} />
        <meshStandardMaterial color={wallColor} roughness={0.85} side={THREE.FrontSide} />
      </mesh>

      {/* Ceiling Plane (faces -Y downward; auto-culls when orbiting above, never blocks top-down view) */}
      <mesh position={[0, height, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, depth]} />
        <meshStandardMaterial color={ceilingColor} roughness={0.9} side={THREE.FrontSide} />
      </mesh>

      {/* Subtle Warm Cove Ceiling Perimeter Accent Trim */}
      <mesh position={[0, height - 0.02, -halfD + 0.35]}>
        <boxGeometry args={[Math.max(1.2, width * 0.72), 0.015, 0.03]} />
        <meshStandardMaterial color="#fff3d6" emissive="#ffd98e" emissiveIntensity={0.45} roughness={0.3} />
      </mesh>

      {/* Architectural Baseboard Trims matching room palette */}
      <mesh position={[0, 0.035, -halfD + 0.006]}>
        <boxGeometry args={[width, 0.07, 0.012]} />
        <meshStandardMaterial color={baseboardColor} roughness={0.55} />
      </mesh>
      <mesh position={[-halfW + 0.006, 0.035, 0]}>
        <boxGeometry args={[0.012, 0.07, depth]} />
        <meshStandardMaterial color={baseboardColor} roughness={0.55} />
      </mesh>
      <mesh position={[halfW - 0.006, 0.035, 0]}>
        <boxGeometry args={[0.012, 0.07, depth]} />
        <meshStandardMaterial color={baseboardColor} roughness={0.55} />
      </mesh>
    </group>
  );
};
