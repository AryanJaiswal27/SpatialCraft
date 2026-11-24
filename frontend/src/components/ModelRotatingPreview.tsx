import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { MeshPart, Dimensions3D } from '../types';
import { Box } from 'lucide-react';

interface Props {
  parts: MeshPart[];
  dimensions: Dimensions3D;
  color: string;
  name: string;
}

const renderPartGeometry = (shape: string, args: any[] = []) => {
  switch (shape?.toLowerCase()) {
    case 'cylinder':
      return <cylinderGeometry args={(args as any) || [0.05, 0.05, 0.1, 16]} />;
    case 'sphere':
      return <sphereGeometry args={(args as any) || [0.05, 16, 16]} />;
    case 'cone':
      return <coneGeometry args={(args as any) || [0.05, 0.1, 16]} />;
    case 'torus':
      return <torusGeometry args={(args as any) || [0.05, 0.015, 12, 24]} />;
    case 'plane':
      return <planeGeometry args={(args as any) || [0.1, 0.1]} />;
    case 'box':
    default:
      return <boxGeometry args={(args as any) || [0.1, 0.1, 0.1]} />;
  }
};

const RotatingTurntable: React.FC<{
  parts: MeshPart[];
  dimensions: Dimensions3D;
  fallbackColor: string;
}> = ({ parts, dimensions, fallbackColor }) => {
  const groupRef = useRef<THREE.Group>(null);
  const { width = 1, height = 1, depth = 1 } = dimensions || {};

  // Normalize scale so any model fits nicely within preview bounds
  const maxDim = Math.max(width, height, depth, 0.4);
  const scale = 1.45 / maxDim;

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.95; // ~0.95 rad/sec turntable spin
    }
  });

  return (
    <group ref={groupRef}>
      {/* Outer scaling to normalize viewport fit */}
      <group scale={[scale, scale, scale]}>
        {/* Center the object's vertical midpoint at Y = 0 */}
        <group position={[0, -height / 2, 0]}>
          {parts.map((part, idx) => (
            <mesh
              key={idx}
              position={part.position || [0, 0, 0]}
              rotation={part.rotation || [0, 0, 0]}
              scale={part.scale || [1, 1, 1]}
            >
              {renderPartGeometry(part.shape, part.args)}
              <meshStandardMaterial
                color={part.color || fallbackColor}
                roughness={part.roughness ?? 0.6}
                metalness={part.metalness ?? 0.1}
                transparent={Boolean(part.opacity !== undefined && part.opacity < 1)}
                opacity={part.opacity ?? 1.0}
                side={part.shape?.toLowerCase() === 'plane' ? THREE.DoubleSide : THREE.FrontSide}
              />
            </mesh>
          ))}
        </group>
      </group>
    </group>
  );
};

export const ModelRotatingPreview: React.FC<Props> = ({ parts, dimensions, color }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    // Use IntersectionObserver so only visible cards mount active WebGL contexts
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsInView(entry.isIntersecting);
      },
      { rootMargin: '100px', threshold: 0.05 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className="w-full h-24 sm:h-28 relative bg-zinc-950/80 border border-zinc-800/80 overflow-hidden flex items-center justify-center pointer-events-none select-none"
    >
      {/* Subtle CAD grid / reticle lines */}
      <div className="absolute inset-0 bg-[radial-gradient(#27272a_1px,transparent_1px)] [background-size:12px_12px] opacity-40 -z-10" />

      {isInView ? (
        <Canvas
          dpr={[1, 1.5]}
          gl={{
            alpha: true,
            antialias: false,
            powerPreference: 'low-power',
          }}
          camera={{ position: [0, 0.9, 2.2], fov: 42 }}
        >
          <ambientLight intensity={1.1} />
          <directionalLight position={[3, 4, 3]} intensity={1.3} />
          <directionalLight position={[-3, -1, -2]} intensity={0.4} />

          <RotatingTurntable parts={parts} dimensions={dimensions} fallbackColor={color} />
        </Canvas>
      ) : (
        <div className="flex flex-col items-center gap-1 text-zinc-700">
          <Box className="w-6 h-6 animate-pulse" />
          <span className="text-[8px] font-mono tracking-widest uppercase">3D PREVIEW</span>
        </div>
      )}

      {/* Subtle corner CAD tick marks */}
      <div className="absolute top-1 left-1 w-1.5 h-1.5 border-t border-l border-zinc-700 pointer-events-none" />
      <div className="absolute top-1 right-1 w-1.5 h-1.5 border-t border-r border-zinc-700 pointer-events-none" />
      <div className="absolute bottom-1 left-1 w-1.5 h-1.5 border-b border-l border-zinc-700 pointer-events-none" />
      <div className="absolute bottom-1 right-1 w-1.5 h-1.5 border-b border-r border-zinc-700 pointer-events-none" />
    </div>
  );
};
