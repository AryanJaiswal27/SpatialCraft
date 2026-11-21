import React from 'react';
import * as THREE from 'three';
import type { RoomConfig } from '../types';

interface Props {
  room: RoomConfig;
}

export const RoomMesh: React.FC<Props> = ({ room }) => {
  const { width = 5.0, height = 2.8, depth = 5.0 } = room.dimensions || {};
  const floorColor = room.floor?.color || '#18181b';
  const wallColor = room.walls?.color || '#121215';

  const halfW = width / 2;
  const halfD = depth / 2;

  return (
    <group>
      {/* Floor Plate */}
      <mesh position={[0, 0, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[width, depth]} />
        <meshStandardMaterial color={floorColor} roughness={0.6} metalness={0.1} />
      </mesh>

      {/* CAD Scale Metric Grid */}
      <gridHelper
        args={[Math.max(width, depth), Math.round(Math.max(width, depth) * 2), '#52525b', '#27272a']}
        position={[0, 0.001, 0]}
      />

      {/* Back Boundary Wall */}
      <mesh position={[0, height / 2, -halfD]} receiveShadow>
        <planeGeometry args={[width, height]} />
        <meshStandardMaterial color={wallColor} roughness={0.9} />
      </mesh>

      {/* Left Boundary Wall */}
      <mesh position={[-halfW, height / 2, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[depth, height]} />
        <meshStandardMaterial color={wallColor} roughness={0.9} />
      </mesh>

      {/* Right Boundary Wall (Backside for camera visibility) */}
      <mesh position={[halfW, height / 2, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[depth, height]} />
        <meshStandardMaterial color={wallColor} roughness={0.9} side={THREE.BackSide} />
      </mesh>

      {/* Baseboard Trims */}
      <mesh position={[0, 0.04, -halfD + 0.005]}>
        <boxGeometry args={[width, 0.08, 0.01]} />
        <meshStandardMaterial color="#27272a" roughness={0.5} />
      </mesh>
      <mesh position={[-halfW + 0.005, 0.04, 0]}>
        <boxGeometry args={[0.01, 0.08, depth]} />
        <meshStandardMaterial color="#27272a" roughness={0.5} />
      </mesh>
    </group>
  );
};
