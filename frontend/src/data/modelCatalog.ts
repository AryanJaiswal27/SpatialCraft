import type { MeshPart, Dimensions3D } from '../types';

export interface CatalogModel {
  id: string;
  name: string;
  category: 'sofa' | 'chair' | 'table' | 'bookshelf' | 'lamp' | 'plant' | 'art' | 'decor' | 'rug';
  dimensions: Dimensions3D;
  color: string;
  description: string;
  tags: string[];
  parts: MeshPart[];
}

export const MODEL_CATALOG: CatalogModel[] = [
  // =========================================================================
  // 1. SEATING
  // =========================================================================
  {
    id: "cat_exec_chair",
    name: "Ergonomic Mesh Office Chair",
    category: "chair",
    dimensions: { width: 0.68, height: 1.05, depth: 0.68 },
    color: "#71717a",
    description: "High-back ergonomic swivel chair with breathable mesh back, pneumatic gas-lift cylinder, 3D armrests, and 5-wheel star base.",
    tags: ["office", "desk", "mesh", "ergonomic"],
    parts: [
      { name: "seat_cushion", shape: "box", args: [0.52, 0.08, 0.50], position: [0.0, 0.48, 0.0], color: "#52525b", roughness: 0.8, metalness: 0.05 },
      { name: "mesh_backrest", shape: "box", args: [0.48, 0.52, 0.04], position: [0.0, 0.78, -0.22], color: "#71717a", roughness: 0.9, metalness: 0.05, opacity: 0.85, transparent: true },
      { name: "lumbar_pad", shape: "box", args: [0.38, 0.12, 0.03], position: [0.0, 0.62, -0.20], color: "#27272a", roughness: 0.9, metalness: 0.05 },
      { name: "headrest", shape: "box", args: [0.28, 0.14, 0.06], position: [0.0, 1.05, -0.20], color: "#52525b", roughness: 0.8, metalness: 0.05 },
      { name: "left_arm_stalk", shape: "box", args: [0.03, 0.22, 0.05], position: [-0.27, 0.58, 0.0], color: "#18181b", roughness: 0.4, metalness: 0.6 },
      { name: "left_arm_pad", shape: "box", args: [0.08, 0.03, 0.24], position: [-0.27, 0.70, 0.0], color: "#27272a", roughness: 0.8, metalness: 0.05 },
      { name: "right_arm_stalk", shape: "box", args: [0.03, 0.22, 0.05], position: [0.27, 0.58, 0.0], color: "#18181b", roughness: 0.4, metalness: 0.6 },
      { name: "right_arm_pad", shape: "box", args: [0.08, 0.03, 0.24], position: [0.27, 0.70, 0.0], color: "#27272a", roughness: 0.8, metalness: 0.05 },
      { name: "center_cylinder", shape: "cylinder", args: [0.035, 0.035, 0.32, 16], position: [0.0, 0.28, 0.0], color: "#18181b", roughness: 0.3, metalness: 0.8 },
      { name: "star_base_hub", shape: "cylinder", args: [0.07, 0.07, 0.04, 16], position: [0.0, 0.12, 0.0], color: "#18181b", roughness: 0.4, metalness: 0.7 },
      { name: "star_leg_1", shape: "box", args: [0.04, 0.03, 0.28], position: [0.0, 0.10, 0.14], color: "#18181b", roughness: 0.4, metalness: 0.6 },
      { name: "star_leg_2", shape: "box", args: [0.27, 0.03, 0.09], position: [0.13, 0.10, 0.04], color: "#18181b", roughness: 0.4, metalness: 0.6 },
      { name: "star_leg_3", shape: "box", args: [0.16, 0.03, -0.23], position: [0.08, 0.10, -0.11], color: "#18181b", roughness: 0.4, metalness: 0.6 },
      { name: "star_leg_4", shape: "box", args: [-0.16, 0.03, -0.23], position: [-0.08, 0.10, -0.11], color: "#18181b", roughness: 0.4, metalness: 0.6 },
      { name: "star_leg_5", shape: "box", args: [-0.27, 0.03, 0.09], position: [-0.13, 0.10, 0.04], color: "#18181b", roughness: 0.4, metalness: 0.6 },
      { name: "wheel_1", shape: "sphere", args: [0.025, 12, 12], position: [0.0, 0.03, 0.28], color: "#09090b", roughness: 0.5, metalness: 0.3 },
      { name: "wheel_2", shape: "sphere", args: [0.025, 12, 12], position: [0.26, 0.03, 0.09], color: "#09090b", roughness: 0.5, metalness: 0.3 },
      { name: "wheel_3", shape: "sphere", args: [0.025, 12, 12], position: [0.16, 0.03, -0.23], color: "#09090b", roughness: 0.5, metalness: 0.3 },
      { name: "wheel_4", shape: "sphere", args: [0.025, 12, 12], position: [-0.16, 0.03, -0.23], color: "#09090b", roughness: 0.5, metalness: 0.3 },
      { name: "wheel_5", shape: "sphere", args: [0.025, 12, 12], position: [-0.26, 0.03, 0.09], color: "#09090b", roughness: 0.5, metalness: 0.3 }
    ]
  },
  {
    id: "cat_cream_sofa",
    name: "Cream Three-Seater Sofa",
    category: "sofa",
    dimensions: { width: 2.35, height: 0.85, depth: 0.95 },
    color: "#d4cdb9",
    description: "Contemporary low-profile three-seater sofa with deep cushions, wide track armrests, and low wooden feet.",
    tags: ["living", "seating", "cream", "lounge"],
    parts: [
      { name: "base_plinth", shape: "box", args: [2.35, 0.22, 0.95], position: [0.0, 0.14, 0.0], color: "#d4cdb9", roughness: 0.85, metalness: 0.05 },
      { name: "backrest_wall", shape: "box", args: [2.35, 0.56, 0.24], position: [0.0, 0.52, -0.34], color: "#d4cdb9", roughness: 0.85, metalness: 0.05 },
      { name: "left_track_arm", shape: "box", args: [0.22, 0.52, 0.94], position: [-1.06, 0.44, 0.0], color: "#d4cdb9", roughness: 0.85, metalness: 0.05 },
      { name: "right_track_arm", shape: "box", args: [0.22, 0.52, 0.94], position: [1.06, 0.44, 0.0], color: "#d4cdb9", roughness: 0.85, metalness: 0.05 },
      { name: "seat_cushion_L", shape: "box", args: [0.62, 0.14, 0.66], position: [-0.64, 0.31, 0.08], color: "#dcd5c2", roughness: 0.9, metalness: 0.05 },
      { name: "seat_cushion_C", shape: "box", args: [0.62, 0.14, 0.66], position: [0.0, 0.31, 0.08], color: "#dcd5c2", roughness: 0.9, metalness: 0.05 },
      { name: "seat_cushion_R", shape: "box", args: [0.62, 0.14, 0.66], position: [0.64, 0.31, 0.08], color: "#dcd5c2", roughness: 0.9, metalness: 0.05 },
      { name: "back_pillow_L", shape: "box", args: [0.62, 0.34, 0.14], position: [-0.64, 0.54, -0.16], color: "#cfc6b0", roughness: 0.9, metalness: 0.05 },
      { name: "back_pillow_C", shape: "box", args: [0.62, 0.34, 0.14], position: [0.0, 0.54, -0.16], color: "#cfc6b0", roughness: 0.9, metalness: 0.05 },
      { name: "back_pillow_R", shape: "box", args: [0.62, 0.34, 0.14], position: [0.64, 0.54, -0.16], color: "#cfc6b0", roughness: 0.9, metalness: 0.05 },
      { name: "foot_FL", shape: "cylinder", args: [0.03, 0.02, 0.06, 16], position: [-1.02, 0.03, 0.38], color: "#543d2b", roughness: 0.6, metalness: 0.1 },
      { name: "foot_FR", shape: "cylinder", args: [0.03, 0.02, 0.06, 16], position: [1.02, 0.03, 0.38], color: "#543d2b", roughness: 0.6, metalness: 0.1 },
      { name: "foot_BL", shape: "cylinder", args: [0.03, 0.02, 0.06, 16], position: [-1.02, 0.03, -0.38], color: "#543d2b", roughness: 0.6, metalness: 0.1 },
      { name: "foot_BR", shape: "cylinder", args: [0.03, 0.02, 0.06, 16], position: [1.02, 0.03, -0.38], color: "#543d2b", roughness: 0.6, metalness: 0.1 }
    ]
  },
  {
    id: "cat_lounge_armchair",
    name: "Taupe Fabric Armchair",
    category: "chair",
    dimensions: { width: 0.92, height: 0.82, depth: 0.88 },
    color: "#8d8272",
    description: "Deep-seated lounge armchair upholstered in textured taupe fabric with tapered wooden legs.",
    tags: ["living", "armchair", "taupe", "lounge"],
    parts: [
      { name: "seat_base", shape: "box", args: [0.92, 0.20, 0.88], position: [0.0, 0.22, 0.0], color: "#8d8272", roughness: 0.85, metalness: 0.05 },
      { name: "cushion", shape: "box", args: [0.66, 0.14, 0.68], position: [0.0, 0.38, 0.04], color: "#9c9180", roughness: 0.9, metalness: 0.05 },
      { name: "backrest", shape: "box", args: [0.92, 0.48, 0.18], position: [0.0, 0.54, -0.34], color: "#8d8272", roughness: 0.85, metalness: 0.05 },
      { name: "left_arm", shape: "box", args: [0.14, 0.38, 0.86], position: [-0.39, 0.48, 0.0], color: "#8d8272", roughness: 0.85, metalness: 0.05 },
      { name: "right_arm", shape: "box", args: [0.14, 0.38, 0.86], position: [0.39, 0.48, 0.0], color: "#8d8272", roughness: 0.85, metalness: 0.05 },
      { name: "leg_FL", shape: "cylinder", args: [0.025, 0.015, 0.14, 16], position: [-0.36, 0.07, 0.34], color: "#4a3525", roughness: 0.6, metalness: 0.1 },
      { name: "leg_FR", shape: "cylinder", args: [0.025, 0.015, 0.14, 16], position: [0.36, 0.07, 0.34], color: "#4a3525", roughness: 0.6, metalness: 0.1 },
      { name: "leg_BL", shape: "cylinder", args: [0.025, 0.015, 0.14, 16], position: [-0.36, 0.07, -0.34], color: "#4a3525", roughness: 0.6, metalness: 0.1 },
      { name: "leg_BR", shape: "cylinder", args: [0.025, 0.015, 0.14, 16], position: [0.36, 0.07, -0.34], color: "#4a3525", roughness: 0.6, metalness: 0.1 }
    ]
  },

  // =========================================================================
  // 2. TABLES & DESKS
  // =========================================================================
  {
    id: "cat_exec_desk",
    name: "Executive Light Oak Desk",
    category: "table",
    dimensions: { width: 2.05, height: 0.75, depth: 1.15 },
    color: "#b89a74",
    description: "Large executive desk with light oak laminate top, modesty panel, side leg gables, and cable management grommet.",
    tags: ["office", "desk", "oak", "workstation"],
    parts: [
      { name: "tabletop_slab", shape: "box", args: [2.05, 0.035, 1.15], position: [0.0, 0.7325, 0.0], color: "#b89a74", roughness: 0.65, metalness: 0.05 },
      { name: "left_leg_panel", shape: "box", args: [0.045, 0.715, 1.05], position: [-0.98, 0.3575, 0.0], color: "#a5855e", roughness: 0.7, metalness: 0.05 },
      { name: "right_leg_panel", shape: "box", args: [0.045, 0.715, 1.05], position: [0.98, 0.3575, 0.0], color: "#a5855e", roughness: 0.7, metalness: 0.05 },
      { name: "modesty_panel", shape: "box", args: [1.90, 0.44, 0.025], position: [0.0, 0.48, -0.42], color: "#a5855e", roughness: 0.75, metalness: 0.05 },
      { name: "drawer_pedestal", shape: "box", args: [0.42, 0.68, 0.75], position: [0.72, 0.34, 0.10], color: "#967850", roughness: 0.7, metalness: 0.05 },
      { name: "drawer_handle_1", shape: "box", args: [0.14, 0.015, 0.025], position: [0.72, 0.58, 0.49], color: "#27272a", roughness: 0.3, metalness: 0.8 },
      { name: "drawer_handle_2", shape: "box", args: [0.14, 0.015, 0.025], position: [0.72, 0.38, 0.49], color: "#27272a", roughness: 0.3, metalness: 0.8 },
      { name: "drawer_handle_3", shape: "box", args: [0.14, 0.015, 0.025], position: [0.72, 0.18, 0.49], color: "#27272a", roughness: 0.3, metalness: 0.8 },
      { name: "cable_grommet", shape: "cylinder", args: [0.035, 0.035, 0.008, 20], position: [-0.70, 0.753, -0.38], color: "#27272a", roughness: 0.4, metalness: 0.6 }
    ]
  },
  {
    id: "cat_coffee_table",
    name: "Rustic Wood Coffee Table",
    category: "table",
    dimensions: { width: 1.40, height: 0.44, depth: 0.70 },
    color: "#9a7447",
    description: "Solid oak rectangular coffee table with lower shelf tier and four square tapered legs.",
    tags: ["living", "coffee table", "wood", "table"],
    parts: [
      { name: "top_slab", shape: "box", args: [1.40, 0.035, 0.70], position: [0.0, 0.4225, 0.0], color: "#9a7447", roughness: 0.7, metalness: 0.05 },
      { name: "lower_shelf", shape: "box", args: [1.25, 0.02, 0.58], position: [0.0, 0.15, 0.0], color: "#8a663c", roughness: 0.75, metalness: 0.05 },
      { name: "leg_FL", shape: "box", args: [0.05, 0.405, 0.05], position: [-0.64, 0.2025, 0.29], color: "#7a5933", roughness: 0.7, metalness: 0.05 },
      { name: "leg_FR", shape: "box", args: [0.05, 0.405, 0.05], position: [0.64, 0.2025, 0.29], color: "#7a5933", roughness: 0.7, metalness: 0.05 },
      { name: "leg_BL", shape: "box", args: [0.05, 0.405, 0.05], position: [-0.64, 0.2025, -0.29], color: "#7a5933", roughness: 0.7, metalness: 0.05 },
      { name: "leg_BR", shape: "box", args: [0.05, 0.405, 0.05], position: [0.64, 0.2025, -0.29], color: "#7a5933", roughness: 0.7, metalness: 0.05 }
    ]
  },
  {
    id: "cat_storage_credenza",
    name: "Rear Wooden Storage Credenza",
    category: "table",
    dimensions: { width: 2.85, height: 0.85, depth: 0.58 },
    color: "#b99a76",
    description: "Multi-door wooden office storage credenza with drawers, metal bar pulls, and laminate countertop.",
    tags: ["office", "storage", "cabinet", "credenza"],
    parts: [
      { name: "countertop", shape: "box", args: [2.85, 0.035, 0.58], position: [0.0, 0.8325, 0.0], color: "#b99a76", roughness: 0.65, metalness: 0.05 },
      { name: "cabinet_chassis", shape: "box", args: [2.80, 0.78, 0.54], position: [0.0, 0.41, 0.0], color: "#a88a66", roughness: 0.7, metalness: 0.05 },
      { name: "door_panel_1", shape: "box", args: [0.65, 0.72, 0.02], position: [-1.00, 0.41, 0.28], color: "#b99a76", roughness: 0.7, metalness: 0.05 },
      { name: "door_panel_2", shape: "box", args: [0.65, 0.72, 0.02], position: [-0.33, 0.41, 0.28], color: "#b99a76", roughness: 0.7, metalness: 0.05 },
      { name: "door_panel_3", shape: "box", args: [0.65, 0.72, 0.02], position: [0.33, 0.41, 0.28], color: "#b99a76", roughness: 0.7, metalness: 0.05 },
      { name: "door_panel_4", shape: "box", args: [0.65, 0.72, 0.02], position: [1.00, 0.41, 0.28], color: "#b99a76", roughness: 0.7, metalness: 0.05 },
      { name: "metal_pull_1", shape: "cylinder", args: [0.008, 0.008, 0.16, 12], position: [-0.70, 0.55, 0.30], color: "#27272a", roughness: 0.3, metalness: 0.8 },
      { name: "metal_pull_2", shape: "cylinder", args: [0.008, 0.008, 0.16, 12], position: [0.70, 0.55, 0.30], color: "#27272a", roughness: 0.3, metalness: 0.8 }
    ]
  },

  // =========================================================================
  // 3. STORAGE & SHELVING
  // =========================================================================
  {
    id: "cat_bookshelf",
    name: "Modern 5-Tier Bookshelf",
    category: "bookshelf",
    dimensions: { width: 0.85, height: 2.20, depth: 0.35 },
    color: "#ebe6db",
    description: "Architectural tall wooden bookshelf with 5 open horizontal tiers and clean white satin finish.",
    tags: ["storage", "bookshelf", "display", "shelves"],
    parts: [
      { name: "left_upright", shape: "box", args: [0.035, 2.20, 0.35], position: [-0.4075, 1.10, 0.0], color: "#ebe6db", roughness: 0.75, metalness: 0.05 },
      { name: "right_upright", shape: "box", args: [0.035, 2.20, 0.35], position: [0.4075, 1.10, 0.0], color: "#ebe6db", roughness: 0.75, metalness: 0.05 },
      { name: "back_panel", shape: "box", args: [0.82, 2.16, 0.015], position: [0.0, 1.10, -0.1675], color: "#dfd9ce", roughness: 0.8, metalness: 0.05 },
      { name: "shelf_tier_1", shape: "box", args: [0.78, 0.025, 0.34], position: [0.0, 0.06, 0.0], color: "#ebe6db", roughness: 0.75, metalness: 0.05 },
      { name: "shelf_tier_2", shape: "box", args: [0.78, 0.025, 0.34], position: [0.0, 0.56, 0.0], color: "#ebe6db", roughness: 0.75, metalness: 0.05 },
      { name: "shelf_tier_3", shape: "box", args: [0.78, 0.025, 0.34], position: [0.0, 1.08, 0.0], color: "#ebe6db", roughness: 0.75, metalness: 0.05 },
      { name: "shelf_tier_4", shape: "box", args: [0.78, 0.025, 0.34], position: [0.0, 1.62, 0.0], color: "#ebe6db", roughness: 0.75, metalness: 0.05 },
      { name: "shelf_tier_5", shape: "box", args: [0.78, 0.025, 0.34], position: [0.0, 2.16, 0.0], color: "#ebe6db", roughness: 0.75, metalness: 0.05 }
    ]
  },

  // =========================================================================
  // 4. LIGHTING
  // =========================================================================
  {
    id: "cat_floor_lamp",
    name: "Brass Arc Floor Lamp",
    category: "lamp",
    dimensions: { width: 0.45, height: 1.70, depth: 0.45 },
    color: "#c8b898",
    description: "Tall freestanding brushed brass floor lamp with heavy circular weighted base and large drum-shaped fabric shade.",
    tags: ["lighting", "lamp", "brass", "standing"],
    parts: [
      { name: "weighted_base", shape: "cylinder", args: [0.20, 0.22, 0.04, 24], position: [0.0, 0.02, 0.0], color: "#b5a37f", roughness: 0.35, metalness: 0.75 },
      { name: "vertical_stem", shape: "cylinder", args: [0.016, 0.016, 1.35, 16], position: [0.0, 0.70, 0.0], color: "#c8b898", roughness: 0.3, metalness: 0.8 },
      { name: "drum_shade", shape: "cylinder", args: [0.22, 0.22, 0.30, 24], position: [0.0, 1.52, 0.0], color: "#ece2cb", roughness: 0.9, metalness: 0.05 },
      { name: "bulb_finial", shape: "sphere", args: [0.04, 16, 16], position: [0.0, 1.48, 0.0], color: "#fffbeb", roughness: 0.2, metalness: 0.1 }
    ]
  },
  {
    id: "cat_table_lamp",
    name: "Ceramic Table Lamp",
    category: "lamp",
    dimensions: { width: 0.25, height: 0.42, depth: 0.25 },
    color: "#d8cebe",
    description: "Compact bedside or desk table lamp with cylindrical textured ceramic body and tapered linen shade.",
    tags: ["lighting", "desk", "lamp", "tabletop"],
    parts: [
      { name: "ceramic_body", shape: "cylinder", args: [0.07, 0.09, 0.22, 20], position: [0.0, 0.11, 0.0], color: "#d8cebe", roughness: 0.75, metalness: 0.05 },
      { name: "shade", shape: "cone", args: [0.125, 0.16, 20], position: [0.0, 0.32, 0.0], color: "#f4ede0", roughness: 0.9, metalness: 0.05 },
      { name: "finial_pin", shape: "cylinder", args: [0.008, 0.008, 0.04, 12], position: [0.0, 0.41, 0.0], color: "#a8997a", roughness: 0.3, metalness: 0.8 }
    ]
  },

  // =========================================================================
  // 5. PLANTS & NATURE
  // =========================================================================
  {
    id: "cat_fiddle_leaf",
    name: "Potted Fiddle Leaf Fig",
    category: "plant",
    dimensions: { width: 0.60, height: 1.25, depth: 0.60 },
    color: "#476839",
    description: "Lush botanical indoor fiddle leaf fig plant in modern white cylindrical ceramic pot.",
    tags: ["plant", "nature", "greenery", "foliage"],
    parts: [
      { name: "ceramic_pot", shape: "cylinder", args: [0.17, 0.14, 0.38, 20], position: [0.0, 0.19, 0.0], color: "#ede8df", roughness: 0.5, metalness: 0.1 },
      { name: "soil_bed", shape: "cylinder", args: [0.16, 0.16, 0.03, 16], position: [0.0, 0.36, 0.0], color: "#2d241e", roughness: 0.95, metalness: 0.0 },
      { name: "central_trunk", shape: "cylinder", args: [0.02, 0.025, 0.75, 12], position: [0.0, 0.72, 0.0], color: "#544335", roughness: 0.8, metalness: 0.1 },
      { name: "leaf_cluster_1", shape: "sphere", args: [0.18, 12, 12], position: [0.08, 0.85, 0.08], color: "#476839", roughness: 0.6, metalness: 0.1 },
      { name: "leaf_cluster_2", shape: "sphere", args: [0.20, 12, 12], position: [-0.08, 1.02, -0.06], color: "#537943", roughness: 0.6, metalness: 0.1 },
      { name: "leaf_cluster_top", shape: "sphere", args: [0.16, 12, 12], position: [0.02, 1.18, 0.02], color: "#5f884d", roughness: 0.6, metalness: 0.1 }
    ]
  },

  // =========================================================================
  // 6. TECH & ACCESSORIES
  // =========================================================================
  {
    id: "cat_laptop",
    name: "Silver Laptop",
    category: "decor",
    dimensions: { width: 0.35, height: 0.22, depth: 0.25 },
    color: "#b0b6bc",
    description: "Open silver anodized aluminum unibody laptop with display screen, keyboard deck, and trackpad.",
    tags: ["tech", "laptop", "office", "computer"],
    parts: [
      { name: "base_chassis", shape: "box", args: [0.35, 0.012, 0.24], position: [0.0, 0.006, 0.0], color: "#b0b6bc", roughness: 0.3, metalness: 0.8 },
      { name: "keyboard_deck", shape: "box", args: [0.30, 0.004, 0.11], position: [0.0, 0.013, -0.03], color: "#18181b", roughness: 0.7, metalness: 0.1 },
      { name: "trackpad", shape: "box", args: [0.12, 0.002, 0.07], position: [0.0, 0.0125, 0.07], color: "#9ca3af", roughness: 0.4, metalness: 0.6 },
      { name: "display_lid", shape: "box", args: [0.35, 0.22, 0.008], position: [0.0, 0.11, -0.12], color: "#b0b6bc", roughness: 0.3, metalness: 0.8 },
      { name: "display_screen", shape: "box", args: [0.33, 0.20, 0.002], position: [0.0, 0.11, -0.115], color: "#09090b", roughness: 0.1, metalness: 0.9 }
    ]
  },
  {
    id: "cat_printer",
    name: "Laser Office Printer",
    category: "decor",
    dimensions: { width: 0.44, height: 0.32, depth: 0.38 },
    color: "#c0c4c4",
    description: "Compact multifunction monochrome laser office printer with paper output tray and status screen.",
    tags: ["tech", "printer", "office", "hardware"],
    parts: [
      { name: "main_body", shape: "box", args: [0.44, 0.28, 0.38], position: [0.0, 0.14, 0.0], color: "#c0c4c4", roughness: 0.6, metalness: 0.1 },
      { name: "output_tray", shape: "box", args: [0.32, 0.02, 0.18], position: [0.0, 0.20, 0.18], color: "#3f3f46", roughness: 0.7, metalness: 0.1 },
      { name: "paper_stack", shape: "box", args: [0.24, 0.01, 0.16], position: [0.0, 0.21, 0.16], color: "#ffffff", roughness: 0.9, metalness: 0.0 },
      { name: "control_panel", shape: "box", args: [0.12, 0.02, 0.08], position: [0.14, 0.29, 0.10], color: "#18181b", roughness: 0.3, metalness: 0.5 }
    ]
  },
  {
    id: "cat_books_mug",
    name: "Art Books and Ceramic Mug",
    category: "decor",
    dimensions: { width: 0.38, height: 0.12, depth: 0.28 },
    color: "#b0a090",
    description: "Stack of architectural monographs and hardcover books with a ceramic coffee mug on top.",
    tags: ["decor", "books", "coffee", "tabletop"],
    parts: [
      { name: "book_bottom", shape: "box", args: [0.36, 0.035, 0.26], position: [0.0, 0.0175, 0.0], color: "#54463a", roughness: 0.8, metalness: 0.05 },
      { name: "book_middle", shape: "box", args: [0.32, 0.03, 0.24], position: [0.01, 0.05, 0.01], color: "#9c8470", roughness: 0.8, metalness: 0.05 },
      { name: "book_top", shape: "box", args: [0.28, 0.025, 0.22], position: [-0.01, 0.0775, -0.01], color: "#c2b09b", roughness: 0.8, metalness: 0.05 },
      { name: "coffee_mug", shape: "cylinder", args: [0.04, 0.038, 0.09, 16], position: [0.08, 0.135, 0.04], color: "#f4f4f5", roughness: 0.3, metalness: 0.1 }
    ]
  },
  {
    id: "cat_vintage_rug",
    name: "Vintage Patterned Area Rug",
    category: "rug",
    dimensions: { width: 2.80, height: 0.015, depth: 3.50 },
    color: "#c2aa8c",
    description: "Large rectangular vintage woven area rug with muted traditional motif.",
    tags: ["floor", "rug", "carpet", "textile"],
    parts: [
      { name: "rug_weave", shape: "box", args: [2.80, 0.015, 3.50], position: [0.0, 0.0075, 0.0], color: "#c2aa8c", roughness: 0.95, metalness: 0.0 }
    ]
  }
];
