import React, { useRef, useMemo } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';

export const GeodeMatrix3D: React.FC = () => {
  const outerGroupRef = useRef<THREE.Group>(null);
  const innerGroupRef = useRef<THREE.Group>(null);

  // Outer Geodesic Football Geometry (Icosahedron detail=1 has 80 faces, 42 vertices, 120 edges)
  const { outerEdges, outerPointsGeom, innerEdges, innerPointsGeom } = useMemo(() => {
    // Outer Geode (Football Polyhedron)
    const icosaGeom = new THREE.IcosahedronGeometry(2.0, 1);
    const outerEdgesGeom = new THREE.EdgesGeometry(icosaGeom);

    // Inner Concentric Core
    const innerIcosaGeom = new THREE.IcosahedronGeometry(1.15, 0);
    const innerEdgesGeom = new THREE.EdgesGeometry(innerIcosaGeom);

    return {
      outerEdges: outerEdgesGeom,
      outerPointsGeom: icosaGeom,
      innerEdges: innerEdgesGeom,
      innerPointsGeom: innerIcosaGeom,
    };
  }, []);

  useFrame((_, delta) => {
    if (outerGroupRef.current) {
      outerGroupRef.current.rotation.y += delta * 0.28;
      outerGroupRef.current.rotation.x += delta * 0.12;
    }
    if (innerGroupRef.current) {
      innerGroupRef.current.rotation.y -= delta * 0.42;
      innerGroupRef.current.rotation.z += delta * 0.22;
    }
  });

  return (
    <group position={[0, 0.4, 0]}>
      {/* Outer Rotating Geodesic Football (Edges & Vertices ONLY) */}
      <group ref={outerGroupRef}>
        {/* Crisp Architectural Edges */}
        <lineSegments geometry={outerEdges}>
          <lineBasicMaterial color="#f4f4f5" transparent opacity={0.7} />
        </lineSegments>

        {/* Floating Vertices */}
        <points geometry={outerPointsGeom}>
          <pointsMaterial
            color="#ffffff"
            size={0.075}
            sizeAttenuation
            transparent
            opacity={0.95}
          />
        </points>
      </group>

      {/* Inner Concentric Core Geode (Counter-rotating) */}
      <group ref={innerGroupRef}>
        <lineSegments geometry={innerEdges}>
          <lineBasicMaterial color="#71717a" transparent opacity={0.5} />
        </lineSegments>

        <points geometry={innerPointsGeom}>
          <pointsMaterial
            color="#a1a1aa"
            size={0.06}
            sizeAttenuation
            transparent
            opacity={0.8}
          />
        </points>
      </group>

      {/* Holographic Ground CAD Coordinate Ring & Polar Grid */}
      <group position={[0, -2.4, 0]}>
        {/* Polar radial ticks */}
        <polarGridHelper args={[4.5, 16, 8, 64, '#3f3f46', '#18181b']} />

        {/* Outer Telemetry Compass Ring */}
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[4.45, 4.48, 64]} />
          <meshBasicMaterial color="#52525b" transparent opacity={0.4} side={THREE.DoubleSide} />
        </mesh>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[2.8, 2.82, 48]} />
          <meshBasicMaterial color="#3f3f46" transparent opacity={0.3} side={THREE.DoubleSide} />
        </mesh>
      </group>
    </group>
  );
};
