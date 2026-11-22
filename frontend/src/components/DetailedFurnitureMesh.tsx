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
      // Ignored
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

  const renderGeometry = () => {
    // =========================================================================
    // 0. LLM DYNAMIC 3D MESH (HIGHEST PRIORITY)
    // When the LLM generates geometric parts, render the LLM's custom 3D model!
    // =========================================================================
    if (object.parts && Array.isArray(object.parts) && object.parts.length > 0) {
      return (
        <group position={[0, -height / 2, 0]}>
          {object.parts.map((part, idx) => (
            <mesh
              key={idx}
              position={part.position || [0, 0, 0]}
              rotation={part.rotation || [0, 0, 0]}
              scale={part.scale || [1, 1, 1]}
              castShadow
              receiveShadow
            >
              {renderPartGeometry(part.shape, part.args)}
              <meshStandardMaterial
                color={part.color || primaryColor}
                roughness={part.roughness ?? 0.6}
                metalness={part.metalness ?? 0.1}
                transparent={Boolean(part.opacity !== undefined && part.opacity < 1)}
                opacity={part.opacity ?? 1.0}
                side={part.shape?.toLowerCase() === 'plane' ? THREE.DoubleSide : THREE.FrontSide}
              />
            </mesh>
          ))}
        </group>
      );
    }

    const cat = (object.category || 'decor').toLowerCase();
    const nameLower = (object.name || '').toLowerCase();
    const descLower = (object.description || '').toLowerCase();
    const features = object.features || [];

    // =========================================================================
    // 1. EXECUTIVE OFFICE DESK (Slab gable panels, modesty panel, light oak laminate)
    // =========================================================================
    const isExecutiveDesk =
      nameLower.includes('desk') ||
      descLower.includes('desk') ||
      descLower.includes('gable') ||
      features.some((f) => f.includes('gable') || f.includes('modesty') || f.includes('tabletop'));

    if (isExecutiveDesk && (cat === 'table' || cat === 'desk')) {
      const topThick = 0.03;
      const gableThick = 0.025;
      const modestyThick = 0.02;
      const modestyH = height * 0.65;
      const woodColor = primaryColor || '#c5a785';

      return (
        <group position={[0, -height / 2, 0]}>
          {/* Main Top Work Surface with subtle front/side overhang */}
          <mesh position={[0, height - topThick / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, topThick, depth]} />
            <meshStandardMaterial color={woodColor} roughness={0.65} metalness={0.05} />
          </mesh>

          {/* Left Vertical Slab Gable End Panel */}
          <mesh
            position={[-width / 2 + gableThick / 2, (height - topThick) / 2, 0]}
            castShadow
            receiveShadow
          >
            <boxGeometry args={[gableThick, height - topThick, depth * 0.98]} />
            <meshStandardMaterial color={woodColor} roughness={0.7} metalness={0.05} />
          </mesh>

          {/* Right Vertical Slab Gable End Panel */}
          <mesh
            position={[width / 2 - gableThick / 2, (height - topThick) / 2, 0]}
            castShadow
            receiveShadow
          >
            <boxGeometry args={[gableThick, height - topThick, depth * 0.98]} />
            <meshStandardMaterial color={woodColor} roughness={0.7} metalness={0.05} />
          </mesh>

          {/* Recessed Full-Height Modesty Panel spanning between gables */}
          <mesh
            position={[0, height - topThick - modestyH / 2, -depth * 0.25]}
            castShadow
            receiveShadow
          >
            <boxGeometry args={[width - gableThick * 2 - 0.005, modestyH, modestyThick]} />
            <meshStandardMaterial color={woodColor} roughness={0.72} metalness={0.05} />
          </mesh>

          {/* Concealed Floor Leveling Glides (4 feet) */}
          {[
            [-width / 2 + gableThick / 2, -depth * 0.42],
            [-width / 2 + gableThick / 2, depth * 0.42],
            [width / 2 - gableThick / 2, -depth * 0.42],
            [width / 2 - gableThick / 2, depth * 0.42],
          ].map(([gx, gz], idx) => (
            <mesh key={idx} position={[gx, 0.008, gz]}>
              <cylinderGeometry args={[0.016, 0.018, 0.016, 12]} />
              <meshStandardMaterial color="#18181b" roughness={0.5} metalness={0.8} />
            </mesh>
          ))}

          {/* Corner Cable Pass-through Grommet Accent */}
          <mesh position={[width * 0.38, height - topThick / 2 + 0.001, -depth * 0.35]}>
            <cylinderGeometry args={[0.03, 0.03, topThick + 0.002, 24]} />
            <meshStandardMaterial color="#27272a" roughness={0.4} metalness={0.7} />
          </mesh>
        </group>
      );
    }

    // =========================================================================
    // 2. OFFICE STORAGE CREDENZA / LOW CABINETS (Drawers, doors, plinth, metal pulls)
    // =========================================================================
    const isCredenza =
      cat === 'bookshelf' ||
      nameLower.includes('credenza') ||
      nameLower.includes('cabinet') ||
      descLower.includes('credenza') ||
      descLower.includes('cabinet') ||
      nameLower.includes('storage') ||
      descLower.includes('storage');

    if (isCredenza && (cat === 'bookshelf' || cat === 'table' || cat === 'decor')) {
      const woodColor = primaryColor || '#c5a785';
      const plinthH = 0.05;
      const topThick = 0.025;
      const bodyH = height - plinthH - topThick;
      const drawerH = bodyH * 0.38;
      const doorH = bodyH * 0.62;

      return (
        <group position={[0, -height / 2, 0]}>
          {/* Recessed Plinth Kickboard Base */}
          <mesh position={[0, plinthH / 2, 0]} castShadow>
            <boxGeometry args={[width * 0.96, plinthH, depth * 0.92]} />
            <meshStandardMaterial color="#18181b" roughness={0.8} />
          </mesh>

          {/* Main Carcass Body */}
          <mesh position={[0, plinthH + bodyH / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[width, bodyH, depth]} />
            <meshStandardMaterial color={woodColor} roughness={0.68} metalness={0.05} />
          </mesh>

          {/* Overhanging Top Worksurface Slab */}
          <mesh position={[0, height - topThick / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[width + 0.015, topThick, depth + 0.015]} />
            <meshStandardMaterial color={woodColor} roughness={0.62} metalness={0.05} />
          </mesh>

          {/* Upper Drawer Row Faceplates with 3D reveal gap */}
          {[-width * 0.25, width * 0.25].map((dx, idx) => (
            <group key={`drawer_${idx}`} position={[dx, plinthH + doorH + drawerH / 2, depth / 2 + 0.005]}>
              <mesh castShadow>
                <boxGeometry args={[width * 0.48, drawerH - 0.01, 0.018]} />
                <meshStandardMaterial color={woodColor} roughness={0.65} />
              </mesh>
              {/* Brushed Aluminum Horizontal Finger Pull Handle */}
              <mesh position={[0, 0, 0.015]} castShadow>
                <boxGeometry args={[width * 0.18, 0.012, 0.012]} />
                <meshStandardMaterial color="#e4e4e7" metalness={0.9} roughness={0.2} />
              </mesh>
            </group>
          ))}

          {/* Lower Door Row Faceplates with split seam */}
          {[-width * 0.25, width * 0.25].map((dx, idx) => (
            <group key={`door_${idx}`} position={[dx, plinthH + doorH / 2, depth / 2 + 0.005]}>
              <mesh castShadow>
                <boxGeometry args={[width * 0.48, doorH - 0.01, 0.018]} />
                <meshStandardMaterial color={woodColor} roughness={0.65} />
              </mesh>
              {/* Brushed Aluminum Vertical Pull Handle */}
              <mesh position={[idx === 0 ? width * 0.18 : -width * 0.18, doorH * 0.25, 0.015]} castShadow>
                <boxGeometry args={[0.012, 0.12, 0.012]} />
                <meshStandardMaterial color="#e4e4e7" metalness={0.9} roughness={0.2} />
              </mesh>
            </group>
          ))}
        </group>
      );
    }

    // =========================================================================
    // 3. ERGONOMIC OFFICE CHAIR / SWIVEL CHAIR / MESH VISITOR CHAIR
    // =========================================================================
    const isOfficeChair =
      cat === 'chair' ||
      nameLower.includes('chair') ||
      descLower.includes('chair') ||
      nameLower.includes('swivel');

    if (isOfficeChair) {
      const isExecutive =
        nameLower.includes('swivel') ||
        nameLower.includes('executive') ||
        descLower.includes('mesh') ||
        descLower.includes('visitor');

      if (isExecutive) {
        const starRadius = Math.min(width, depth) * 0.48;
        const seatY = height * 0.46;
        const seatThick = 0.07;
        const backH = height * 0.52;
        const upholsteryColor = primaryColor && primaryColor !== '#888888' ? primaryColor : '#9ca3af';

        return (
          <group position={[0, -height / 2, 0]}>
            {/* 5-Star Caster Base Hub */}
            <mesh position={[0, 0.06, 0]} castShadow>
              <cylinderGeometry args={[0.045, 0.045, 0.06, 24]} />
              <meshStandardMaterial color="#18181b" roughness={0.4} metalness={0.7} />
            </mesh>

            {/* 5 Radial Star-Legs + Dual Caster Wheels */}
            {[0, 72, 144, 216, 288].map((angleDeg, idx) => {
              const rad = (angleDeg * Math.PI) / 180;
              const legLen = starRadius;
              const lx = Math.sin(rad) * (legLen / 2);
              const lz = Math.cos(rad) * (legLen / 2);
              const tipX = Math.sin(rad) * legLen;
              const tipZ = Math.cos(rad) * legLen;

              return (
                <group key={idx}>
                  {/* Radial Leg Beam */}
                  <mesh
                    position={[lx, 0.05, lz]}
                    rotation={[0, rad, 0]}
                    castShadow
                  >
                    <boxGeometry args={[0.024, 0.02, legLen]} />
                    <meshStandardMaterial color="#18181b" roughness={0.4} metalness={0.7} />
                  </mesh>
                  {/* Black Dual Caster Wheel at tip */}
                  <mesh position={[tipX, 0.025, tipZ]} castShadow>
                    <sphereGeometry args={[0.024, 12, 12]} />
                    <meshStandardMaterial color="#09090b" roughness={0.8} />
                  </mesh>
                </group>
              );
            })}

            {/* Telescoping Chrome Pneumatic Gas-Lift Cylinder Column */}
            <mesh position={[0, seatY * 0.55, 0]} castShadow>
              <cylinderGeometry args={[0.022, 0.025, seatY * 0.75, 20]} />
              <meshStandardMaterial color="#e4e4e7" roughness={0.2} metalness={0.9} />
            </mesh>
            <mesh position={[0, 0.12, 0]} castShadow>
              <cylinderGeometry args={[0.032, 0.035, 0.12, 20]} />
              <meshStandardMaterial color="#18181b" roughness={0.6} />
            </mesh>

            {/* Under-Seat Heavy Steel Mechanism Box */}
            <mesh position={[0, seatY - seatThick * 0.6, 0]} castShadow>
              <boxGeometry args={[width * 0.38, 0.045, depth * 0.42]} />
              <meshStandardMaterial color="#18181b" roughness={0.5} metalness={0.8} />
            </mesh>
            {/* Tilt Adjustment Paddle Wand */}
            <mesh position={[width * 0.22, seatY - seatThick * 0.6, 0]}>
              <cylinderGeometry args={[0.006, 0.006, 0.14, 8]} />
              <meshStandardMaterial color="#18181b" />
            </mesh>

            {/* Contoured Ergonomic Seat Cushion with Waterfall Front */}
            <group position={[0, seatY, 0]}>
              <mesh castShadow receiveShadow>
                <boxGeometry args={[width * 0.88, seatThick, depth * 0.84]} />
                <meshStandardMaterial color={upholsteryColor} roughness={0.75} />
              </mesh>
              {/* Waterfall front lip curve */}
              <mesh position={[0, -0.01, depth * 0.42]} rotation={[0, 0, Math.PI / 2]} castShadow>
                <cylinderGeometry args={[0.025, 0.025, width * 0.88, 16]} />
                <meshStandardMaterial color={upholsteryColor} roughness={0.75} />
              </mesh>
            </group>

            {/* Ergonomic Curved Mesh Backrest Assembly */}
            <group position={[0, seatY + backH * 0.55, -depth * 0.38]}>
              {/* Outer Perimeter Structural Frame */}
              <mesh castShadow>
                <boxGeometry args={[width * 0.82, backH, 0.03]} />
                <meshStandardMaterial color="#18181b" roughness={0.4} metalness={0.3} />
              </mesh>
              {/* Breathable Translucent Mesh Inner Weave Screen */}
              <mesh position={[0, 0, 0.005]} receiveShadow>
                <planeGeometry args={[width * 0.74, backH * 0.88]} />
                <meshStandardMaterial
                  color="#4b5563"
                  roughness={0.85}
                  transparent
                  opacity={0.88}
                  side={THREE.DoubleSide}
                />
              </mesh>
              {/* Horizontal Lumbar Support Bar behind mesh */}
              <mesh position={[0, -backH * 0.22, -0.015]} castShadow>
                <boxGeometry args={[width * 0.72, 0.05, 0.02]} />
                <meshStandardMaterial color="#27272a" roughness={0.6} metalness={0.4} />
              </mesh>
            </group>

            {/* Ergonomic Loop Armrests (Left & Right) */}
            {[-width * 0.44, width * 0.44].map((ax, idx) => (
              <group key={`arm_${idx}`} position={[ax, seatY + 0.12, 0]}>
                {/* Armrest Vertical Struts */}
                <mesh position={[0, 0, -depth * 0.15]} castShadow>
                  <boxGeometry args={[0.024, 0.22, 0.03]} />
                  <meshStandardMaterial color="#18181b" roughness={0.5} metalness={0.4} />
                </mesh>
                {/* Contoured Padded Arm-Cap */}
                <mesh position={[0, 0.11, 0]} castShadow>
                  <boxGeometry args={[0.055, 0.025, depth * 0.55]} />
                  <meshStandardMaterial color="#09090b" roughness={0.6} />
                </mesh>
              </group>
            ))}
          </group>
        );
      }

      // Standard side/visitor chair
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

    // =========================================================================
    // 4. DESKTOP LASER PRINTER (Two-tone casing, paper tray, catch flap, screen)
    // =========================================================================
    if (nameLower.includes('printer') || descLower.includes('printer')) {
      const pW = width || 0.36;
      const pH = height || 0.25;
      const pD = depth || 0.32;

      return (
        <group position={[0, -pH / 2, 0]}>
          {/* Main Printer Body Chassis (Light Grey / Off-White) */}
          <mesh position={[0, pH * 0.55, 0]} castShadow receiveShadow>
            <boxGeometry args={[pW, pH * 0.75, pD]} />
            <meshStandardMaterial color="#e4e4e7" roughness={0.35} metalness={0.1} />
          </mesh>

          {/* Dark Charcoal Base & Lower Paper Intake Drawer */}
          <mesh position={[0, pH * 0.12, 0]} castShadow>
            <boxGeometry args={[pW * 0.98, pH * 0.22, pD * 0.98]} />
            <meshStandardMaterial color="#27272a" roughness={0.5} />
          </mesh>

          {/* Recessed Paper Output Cavity Throat */}
          <mesh position={[0, pH * 0.58, pD * 0.32]}>
            <boxGeometry args={[pW * 0.75, pH * 0.25, pD * 0.38]} />
            <meshStandardMaterial color="#18181b" roughness={0.7} />
          </mesh>

          {/* Extended Angled Paper Output Catch Tray */}
          <mesh
            position={[0, pH * 0.46, pD * 0.52]}
            rotation={[Math.PI * 0.06, 0, 0]}
            castShadow
          >
            <boxGeometry args={[pW * 0.65, 0.008, pD * 0.35]} />
            <meshStandardMaterial color="#3f3f46" roughness={0.4} metalness={0.3} />
          </mesh>

          {/* Slanted Top Right Control Panel Console */}
          <group position={[pW * 0.32, pH * 0.92, -pD * 0.2]}>
            {/* Status Monochrome LCD Display */}
            <mesh position={[0, 0.005, 0]}>
              <boxGeometry args={[pW * 0.22, 0.006, pD * 0.18]} />
              <meshStandardMaterial color="#0284c7" roughness={0.2} metalness={0.4} />
            </mesh>
            {/* Tactile Rubber Power & Cancel Buttons */}
            <mesh position={[0, 0.007, pD * 0.14]}>
              <boxGeometry args={[pW * 0.18, 0.005, 0.025]} />
              <meshStandardMaterial color="#10b981" roughness={0.5} />
            </mesh>
          </group>
        </group>
      );
    }

    // =========================================================================
    // 5. OFFICE LANDLINE TELEPHONE (Slanted base, dial keypad, handset, cradle)
    // =========================================================================
    if (
      nameLower.includes('telephone') ||
      descLower.includes('telephone') ||
      nameLower.includes('landline') ||
      (cat === 'phone' && nameLower.includes('office'))
    ) {
      const tW = width || 0.2;
      const tH = height || 0.16;
      const tD = depth || 0.22;

      return (
        <group position={[0, -tH / 2, 0]}>
          {/* Angled Console Base Wedge */}
          <group position={[0, tH * 0.35, 0]} rotation={[-Math.PI * 0.12, 0, 0]}>
            <mesh castShadow receiveShadow>
              <boxGeometry args={[tW, tH * 0.5, tD]} />
              <meshStandardMaterial color="#18181b" roughness={0.5} metalness={0.2} />
            </mesh>

            {/* Angled Numeric Keypad (12 3D Buttons Matrix) */}
            <group position={[-tW * 0.15, tH * 0.26, tD * 0.08]}>
              {[-0.035, 0, 0.035].map((bx, col) =>
                [-0.045, -0.015, 0.015, 0.045].map((bz, row) => (
                  <mesh key={`${col}_${row}`} position={[bx, 0.006, bz]}>
                    <boxGeometry args={[0.022, 0.008, 0.02]} />
                    <meshStandardMaterial color="#3f3f46" roughness={0.4} />
                  </mesh>
                ))
              )}
            </group>

            {/* Backlit Status LCD Screen Pane */}
            <mesh position={[-tW * 0.15, tH * 0.26, -tD * 0.28]}>
              <boxGeometry args={[tW * 0.52, 0.006, tD * 0.25]} />
              <meshStandardMaterial color="#0ea5e9" roughness={0.15} metalness={0.3} />
            </mesh>
          </group>

          {/* Sculpted Telephone Handset Resting on Left Cradle */}
          <group position={[tW * 0.28, tH * 0.55, 0]} rotation={[-Math.PI * 0.12, 0, 0]}>
            {/* Earpiece */}
            <mesh position={[0, 0.02, -tD * 0.32]} castShadow>
              <boxGeometry args={[0.05, 0.035, 0.065]} />
              <meshStandardMaterial color="#18181b" roughness={0.4} />
            </mesh>
            {/* Handle Grip Bar */}
            <mesh position={[0, 0.028, 0]} castShadow>
              <boxGeometry args={[0.034, 0.024, tD * 0.55]} />
              <meshStandardMaterial color="#18181b" roughness={0.4} />
            </mesh>
            {/* Mouthpiece */}
            <mesh position={[0, 0.02, tD * 0.32]} castShadow>
              <boxGeometry args={[0.05, 0.035, 0.065]} />
              <meshStandardMaterial color="#18181b" roughness={0.4} />
            </mesh>
          </group>
        </group>
      );
    }

    // =========================================================================
    // 6. STAINLESS STEEL INSULATED WATER BOTTLE (Brushed metal flask, screw cap)
    // =========================================================================
    if (nameLower.includes('bottle') || descLower.includes('bottle') || descLower.includes('flask')) {
      const bW = width || 0.08;
      const bH = height || 0.28;
      const radius = bW / 2;

      return (
        <group position={[0, -bH / 2, 0]}>
          {/* Main Cylindrical Bottle Body (Brushed Stainless Steel) */}
          <mesh position={[0, bH * 0.42, 0]} castShadow receiveShadow>
            <cylinderGeometry args={[radius, radius, bH * 0.72, 32]} />
            <meshStandardMaterial color="#e4e4e7" metalness={0.94} roughness={0.18} />
          </mesh>

          {/* Tapered Conical Shoulder */}
          <mesh position={[0, bH * 0.82, 0]} castShadow>
            <cylinderGeometry args={[radius * 0.55, radius, bH * 0.1, 32]} />
            <meshStandardMaterial color="#e4e4e7" metalness={0.94} roughness={0.18} />
          </mesh>

          {/* Threaded Neck Rim */}
          <mesh position={[0, bH * 0.89, 0]}>
            <cylinderGeometry args={[radius * 0.55, radius * 0.55, bH * 0.05, 32]} />
            <meshStandardMaterial color="#d4d4d8" metalness={0.9} roughness={0.25} />
          </mesh>

          {/* Heavy-Duty Insulated Screw Cap Lid with Knurled Texture */}
          <mesh position={[0, bH * 0.94, 0]} castShadow>
            <cylinderGeometry args={[radius * 0.62, radius * 0.62, bH * 0.09, 32]} />
            <meshStandardMaterial color="#18181b" roughness={0.5} metalness={0.6} />
          </mesh>

          {/* Foldable Steel Loop Handle on Top */}
          <mesh position={[0, bH * 0.99, 0]} rotation={[0, 0, Math.PI / 2]}>
            <torusGeometry args={[radius * 0.35, 0.005, 12, 24]} />
            <meshStandardMaterial color="#e4e4e7" metalness={0.95} roughness={0.2} />
          </mesh>
        </group>
      );
    }

    // =========================================================================
    // 7. OPEN SILVER CLAMSHELL LAPTOP (Unibody aluminum, keyboard well, display)
    // =========================================================================
    if (nameLower.includes('laptop') || descLower.includes('laptop') || cat === 'laptop') {
      const lW = width || 0.36;
      const lH = height || 0.24;
      const lD = depth || 0.25;
      const baseThick = 0.015;

      return (
        <group position={[0, -lH / 2, 0]}>
          {/* Milled Aluminum Bottom Chassis Base */}
          <mesh position={[0, baseThick / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[lW, baseThick, lD]} />
            <meshStandardMaterial color="#d4d4d8" metalness={0.88} roughness={0.25} />
          </mesh>

          {/* Recessed Dark Keyboard Well & Chiclet Keys Grid */}
          <mesh position={[0, baseThick + 0.0005, -lD * 0.12]}>
            <planeGeometry args={[lW * 0.88, lD * 0.52]} />
            <meshStandardMaterial color="#09090b" roughness={0.6} />
          </mesh>

          {/* Glass Multi-Touch Trackpad */}
          <mesh position={[0, baseThick + 0.0005, lD * 0.26]}>
            <planeGeometry args={[lW * 0.38, lD * 0.28]} />
            <meshStandardMaterial color="#cbd5e1" roughness={0.2} metalness={0.3} />
          </mesh>

          {/* Angled Display Lid opened at ~115 degrees */}
          <group position={[0, baseThick, -lD / 2]} rotation={[-Math.PI * 0.18, 0, 0]}>
            {/* Outer Aluminum Display Shell */}
            <mesh position={[0, lD * 0.48, 0]} castShadow>
              <boxGeometry args={[lW, lD * 0.95, 0.008]} />
              <meshStandardMaterial color="#d4d4d8" metalness={0.88} roughness={0.25} />
            </mesh>
            {/* High-Contrast Glowing 16:10 Display Screen */}
            <mesh position={[0, lD * 0.48, 0.005]} receiveShadow>
              <planeGeometry args={[lW * 0.92, lD * 0.86]} />
              <meshStandardMaterial color="#0f172a" roughness={0.1} metalness={0.8} />
            </mesh>
          </group>
        </group>
      );
    }

    // =========================================================================
    // 8. OFFICE BACKPACK / BAG (Ballistic nylon folds, zipper pouches, straps)
    // =========================================================================
    if (nameLower.includes('backpack') || descLower.includes('backpack') || nameLower.includes('bag')) {
      const bW = width || 0.45;
      const bH = height || 0.2;
      const bD = depth || 0.34;

      return (
        <group position={[0, -bH / 2, 0]}>
          {/* Main Contoured Pack Body in Matte Woven Nylon */}
          <mesh position={[0, bH * 0.48, 0]} castShadow receiveShadow>
            <boxGeometry args={[bW * 0.85, bH * 0.85, bD * 0.85]} />
            <meshStandardMaterial color="#18181b" roughness={0.92} />
          </mesh>

          {/* Front Utility Zippered Pouch */}
          <mesh position={[0, bH * 0.38, bD * 0.38]} castShadow>
            <boxGeometry args={[bW * 0.72, bH * 0.6, bD * 0.22]} />
            <meshStandardMaterial color="#27272a" roughness={0.88} />
          </mesh>

          {/* Reinforced Top Grab Handle */}
          <mesh position={[0, bH * 0.95, -bD * 0.15]}>
            <boxGeometry args={[bW * 0.25, 0.02, 0.03]} />
            <meshStandardMaterial color="#09090b" roughness={0.7} />
          </mesh>

          {/* Padded Ergonomic Shoulder Straps draped flat */}
          {[-bW * 0.25, bW * 0.25].map((sx, idx) => (
            <mesh key={idx} position={[sx, bH * 0.15, -bD * 0.32]} rotation={[0.1, 0, 0]}>
              <boxGeometry args={[0.06, 0.015, bD * 0.6]} />
              <meshStandardMaterial color="#3f3f46" roughness={0.95} />
            </mesh>
          ))}
        </group>
      );
    }

    // =========================================================================
    // 9. WOODEN AWARD TROPHY PLAQUE (Beveled pedestal, brass medallion plate)
    // =========================================================================
    if (
      nameLower.includes('plaque') ||
      descLower.includes('plaque') ||
      nameLower.includes('award') ||
      descLower.includes('award')
    ) {
      const tW = width || 0.15;
      const tH = height || 0.22;
      const tD = depth || 0.08;

      return (
        <group position={[0, -tH / 2, 0]}>
          {/* Beveled Dark Walnut Wooden Base Pedestal */}
          <mesh position={[0, 0.02, 0]} castShadow>
            <boxGeometry args={[tW * 0.9, 0.04, tD * 0.9]} />
            <meshStandardMaterial color="#451a03" roughness={0.5} />
          </mesh>

          {/* Vertical Upright Trophy Shield Body */}
          <mesh position={[0, tH * 0.55, 0]} castShadow>
            <boxGeometry args={[tW * 0.75, tH * 0.85, 0.025]} />
            <meshStandardMaterial color="#5c3a21" roughness={0.45} />
          </mesh>

          {/* Circular Brushed Brass / Gold Medallion Disc */}
          <mesh position={[0, tH * 0.68, 0.015]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <cylinderGeometry args={[tW * 0.22, tW * 0.22, 0.008, 32]} />
            <meshStandardMaterial color="#eab308" metalness={0.88} roughness={0.22} />
          </mesh>

          {/* Engraved Inset Text Plate */}
          <mesh position={[0, tH * 0.35, 0.014]}>
            <boxGeometry args={[tW * 0.55, 0.035, 0.004]} />
            <meshStandardMaterial color="#ca8a04" metalness={0.8} roughness={0.3} />
          </mesh>
        </group>
      );
    }

    // =========================================================================
    // 10. STACK OF OFFICE BINDERS & FOLDERS (Multi-colored spines, labeled paper)
    // =========================================================================
    if (
      nameLower.includes('folder') ||
      descLower.includes('folder') ||
      nameLower.includes('binder') ||
      nameLower.includes('book') ||
      descLower.includes('book')
    ) {
      const fW = width || 0.42;
      const fH = height || 0.12;
      const fD = depth || 0.32;
      const colors = ['#2563eb', '#eab308', '#dc2626', '#18181b'];
      const count = 4;
      const layerH = fH / count;

      return (
        <group position={[0, -fH / 2, 0]}>
          {colors.map((col, idx) => (
            <group
              key={idx}
              position={[0, idx * layerH + layerH / 2, 0]}
              rotation={[0, (idx - 1.5) * 0.04, 0]}
            >
              {/* Folder Cover Slab */}
              <mesh castShadow receiveShadow>
                <boxGeometry args={[fW * 0.96, layerH * 0.9, fD * 0.96]} />
                <meshStandardMaterial color={col} roughness={0.65} />
              </mesh>
              {/* White Spine Label Insert */}
              <mesh position={[-fW * 0.48, 0, 0]}>
                <boxGeometry args={[0.004, layerH * 0.65, fD * 0.55]} />
                <meshStandardMaterial color="#f8fafc" roughness={0.8} />
              </mesh>
              {/* Inner Cream Paper Page Bulk Edge */}
              <mesh position={[fW * 0.02, 0, fD * 0.02]}>
                <boxGeometry args={[fW * 0.9, layerH * 0.75, fD * 0.9]} />
                <meshStandardMaterial color="#fef08a" roughness={0.9} />
              </mesh>
            </group>
          ))}
        </group>
      );
    }

    // =========================================================================
    // 11. SMARTPHONE (Rounded aerospace aluminum chassis, dark glass display)
    // =========================================================================
    if (cat === 'phone' || nameLower.includes('smartphone') || nameLower.includes('mobile')) {
      const pW = width || 0.08;
      const pH = height || 0.012;
      const pD = depth || 0.16;

      return (
        <group position={[0, -pH / 2, 0]}>
          {/* Rounded Aluminum Chassis */}
          <mesh position={[0, pH / 2, 0]} castShadow>
            <boxGeometry args={[pW, pH, pD]} />
            <meshStandardMaterial color="#18181b" roughness={0.2} metalness={0.8} />
          </mesh>
          {/* Edge-to-Edge Ceramic Glass Front Display */}
          <mesh position={[0, pH + 0.0005, 0]} receiveShadow>
            <planeGeometry args={[pW * 0.92, pD * 0.94]} />
            <meshStandardMaterial color="#09090b" roughness={0.08} metalness={0.9} />
          </mesh>
          {/* Rear Camera Island with Sapphire Lens Discs */}
          <mesh position={[pW * 0.25, pH + 0.0012, -pD * 0.32]} castShadow>
            <boxGeometry args={[pW * 0.35, 0.002, pD * 0.25]} />
            <meshStandardMaterial color="#27272a" roughness={0.3} metalness={0.7} />
          </mesh>
        </group>
      );
    }

    // =========================================================================
    // 12. WALL SCHEDULE SHEET / PRINTED DOCUMENT / WALL ART
    // =========================================================================
    if (
      nameLower.includes('schedule') ||
      descLower.includes('schedule') ||
      (cat === 'art' && nameLower.includes('sheet'))
    ) {
      const sW = width || 0.21;
      const sH = height || 0.3;
      const sD = Math.max(depth || 0.01, 0.008);

      return (
        <group position={[0, -sH / 2, 0]}>
          {/* Crisp White A4 Document Sheet */}
          <mesh position={[0, sH / 2, 0]} castShadow>
            <boxGeometry args={[sW, sH, sD]} />
            <meshStandardMaterial color="#ffffff" roughness={0.9} />
          </mesh>
          {/* Printed Header Banner */}
          <mesh position={[0, sH * 0.88, sD / 2 + 0.001]}>
            <planeGeometry args={[sW * 0.85, sH * 0.08]} />
            <meshStandardMaterial color="#1e3a8a" roughness={0.8} />
          </mesh>
          {/* Tabular Grid Schedule Lines */}
          {[0.7, 0.55, 0.4, 0.25, 0.1].map((ratio, idx) => (
            <mesh key={idx} position={[0, sH * ratio, sD / 2 + 0.001]}>
              <planeGeometry args={[sW * 0.85, 0.002]} />
              <meshStandardMaterial color="#94a3b8" />
            </mesh>
          ))}
          {/* Translucent Mounting Tape Tabs */}
          {[-sW * 0.38, sW * 0.38].map((tx, idx) => (
            <mesh key={idx} position={[tx, sH * 0.98, sD / 2 + 0.002]}>
              <planeGeometry args={[0.025, 0.015]} />
              <meshStandardMaterial color="#fef3c7" transparent opacity={0.65} />
            </mesh>
          ))}
        </group>
      );
    }

    // =========================================================================
    // 13. PRINTED MAGAZINE / BROCHURE (Bound booklet with glossy cover)
    // =========================================================================
    if (nameLower.includes('magazine') || descLower.includes('magazine') || nameLower.includes('brochure')) {
      const mW = width || 0.24;
      const mH = height || 0.02;
      const mD = depth || 0.3;

      return (
        <group position={[0, -mH / 2, 0]}>
          {/* Dark Glossy Printed Cover */}
          <mesh position={[0, mH / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[mW, mH, mD]} />
            <meshStandardMaterial color="#0f172a" roughness={0.3} metalness={0.2} />
          </mesh>
          {/* Inner Page Paper Bulk Edge */}
          <mesh position={[mW * 0.02, mH / 2, 0]}>
            <boxGeometry args={[mW * 0.94, mH * 0.85, mD * 0.96]} />
            <meshStandardMaterial color="#f8fafc" roughness={0.85} />
          </mesh>
        </group>
      );
    }

    // =========================================================================
    // 14. SOFA
    // =========================================================================
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
            [width * 0.42, depth * 0.42],
          ].map(([lx, lz], idx) => (
            <mesh key={idx} position={[lx, 0.06, lz]} castShadow>
              <cylinderGeometry args={[0.02, 0.015, 0.12, 12]} />
              <meshStandardMaterial color="#18181b" metalness={0.8} roughness={0.3} />
            </mesh>
          ))}
        </group>
      );
    }

    // =========================================================================
    // 15. STANDARD TABLE (Fallback if not executive desk)
    // =========================================================================
    if (cat === 'table' || cat === 'coffee_table') {
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

    // =========================================================================
    // 16. BED
    // =========================================================================
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

    // =========================================================================
    // 17. LAMP
    // =========================================================================
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

    // =========================================================================
    // 18. TV UNIT
    // =========================================================================
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

    // =========================================================================
    // 19. PLANT
    // =========================================================================
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

    // =========================================================================
    // 20. RUG
    // =========================================================================
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

    // =========================================================================
    // 21. ART / WALL ART (Framed Painting)
    // =========================================================================
    if (cat === 'art' || cat.includes('art') || cat.includes('painting')) {
      const artDepth = Math.max(depth, 0.04);
      return (
        <group position={[0, -height / 2, 0]}>
          <mesh position={[0, height / 2, 0]} castShadow>
            <boxGeometry args={[width, height, artDepth]} />
            <meshStandardMaterial color="#18181b" roughness={0.4} metalness={0.2} />
          </mesh>
          <mesh position={[0, height / 2, artDepth / 2 + 0.005]} receiveShadow>
            <planeGeometry args={[width * 0.9, height * 0.9]} />
            <meshStandardMaterial color={primaryColor || '#d4d4d8'} roughness={0.85} />
          </mesh>
        </group>
      );
    }

    // =========================================================================
    // 22. DEFAULT ARCHITECTURAL FALLBACK
    // =========================================================================
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
