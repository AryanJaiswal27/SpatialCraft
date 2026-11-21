import React, { useState } from 'react';
import {
  RotateCw,
  Trash2,
  X,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Terminal,
  Camera,
  FileCode2,
  Download,
  Link,
  Unlink,
  Layers,
  Sparkles,
} from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

export const MobileBottomControls: React.FC = () => {
  const {
    scene,
    selectedObjectId,
    selectObject,
    rotateObject,
    deleteObject,
    updateObjectPosition,
    attachObject,
    detachObject,
    sendPromptEdit,
    setActiveModal,
    exportGlb,
    exportJson,
    availableScenes,
    loadSceneById,
  } = useSceneStore();
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isRefining, setIsRefining] = useState(false);

  const triggerRefinementLoop = async () => {
    if (!scene?.scene_id || scene.scene_id === 'home' || isRefining) return;
    setIsRefining(true);
    try {
      await fetch(`/api/scene/${scene.scene_id}/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_items: 5 }),
      });
    } catch (e) {
      console.error('Failed to trigger refinement loop:', e);
    } finally {
      setTimeout(() => setIsRefining(false), 2000);
    }
  };

  const triggerSingleRefine = async () => {
    if (!scene?.scene_id || !selectedObject || isRefining) return;
    setIsRefining(true);
    try {
      await fetch(`/api/scene/${scene.scene_id}/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ object_id: selectedObject.id }),
      });
    } catch (e) {
      console.error('Failed to refine object:', e);
    } finally {
      setTimeout(() => setIsRefining(false), 2000);
    }
  };

  const selectedObject = scene?.objects?.find((o) => o.id === selectedObjectId);
  const isHome = !scene || scene.scene_id === 'home' || (scene.objects?.length === 0 && !scene.image_url);

  const handleNudge = (dx: number, dz: number) => {
    if (!selectedObject) return;
    updateObjectPosition(selectedObject.id, {
      x: selectedObject.position.x + dx,
      y: selectedObject.position.y,
      z: selectedObject.position.z + dz,
    });
  };

  // 1. OBJECT INSPECTOR (Responsive CAD Controls, Never Goes Out of Window)
  if (selectedObject) {
    const { width = 1, height = 1, depth = 1 } = selectedObject.dimensions || {};
    const { x = 0, y = 0, z = 0 } = selectedObject.position || {};
    const yaw = selectedObject.rotation?.yaw || 0;

    let parentLabel = '';
    if (selectedObject.attached_to_id) {
      if (selectedObject.attached_to_id.startsWith('wall_')) {
        parentLabel = selectedObject.attached_to_id.replace('wall_', '').toUpperCase() + ' WALL';
      } else {
        const parentObj = scene?.objects?.find((o) => o.id === selectedObject.attached_to_id);
        parentLabel = parentObj?.name || 'PARENT OBJECT';
      }
    }

    const potentialParent = scene?.objects?.find(
      (o) =>
        o.id !== selectedObject.id &&
        (o.category === 'table' ||
          o.category === 'coffee_table' ||
          o.category === 'desk' ||
          o.category === 'tv_unit' ||
          o.category === 'bookshelf' ||
          o.name.toLowerCase().includes('table') ||
          o.name.toLowerCase().includes('desk'))
    );

    return (
      <div className="absolute bottom-2 left-2 right-2 sm:left-auto sm:right-auto sm:w-96 sm:left-1/2 sm:-translate-x-1/2 z-20 pointer-events-auto font-mono pb-[max(0.25rem,env(safe-area-inset-bottom))]">
        <div className="bg-zinc-950/98 border border-zinc-800 p-2 sm:p-2.5 shadow-2xl space-y-1.5 backdrop-blur-xs">
          {/* Header Row: Label & Dismiss */}
          <div className="flex items-center justify-between pb-1 border-b border-zinc-800 text-[10px]">
            <div className="flex items-center gap-1.5 min-w-0 mr-1.5">
              <span className="w-1.5 h-1.5 bg-zinc-200 shrink-0" />
              <span className="font-bold text-zinc-100 uppercase tracking-wider truncate">
                {selectedObject.name}
              </span>
              <span className="text-zinc-500 text-[9px] shrink-0">
                [{selectedObject.category.toUpperCase()}]
              </span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={() => setActiveModal('antigravity')}
                className="flex items-center gap-1 px-1.5 py-0.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 font-bold text-[9px] transition-colors"
                title="Inspect Antigravity CAD prompt for this object"
              >
                <Sparkles className="w-2.5 h-2.5 text-zinc-300" />
                <span>AGY PROMPT</span>
              </button>
              {selectedObject.crop_url && (
                <button
                  type="button"
                  onClick={triggerSingleRefine}
                  disabled={isRefining}
                  className="flex items-center gap-1 px-1.5 py-0.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-100 font-bold text-[9px] transition-colors"
                  title="Refine object details using cropped image"
                >
                  <Sparkles className="w-2.5 h-2.5 text-zinc-300" />
                  <span>{isRefining ? 'QUEUED' : 'REFINE'}</span>
                </button>
              )}
              <button
                onClick={() => selectObject(null)}
                className="p-1 text-zinc-400 hover:text-zinc-100 shrink-0"
                title="Deselect"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Metric Telemetry */}
          <div className="space-y-0.5 text-[9px] text-zinc-400">
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">POS (M)</span>
              <span className="text-zinc-200">
                X: {x.toFixed(2)} | Y: {y.toFixed(2)} | Z: {z.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">BOUNDS &amp; YAW</span>
              <span className="text-zinc-200">
                {width.toFixed(2)}x{height.toFixed(2)}x{depth.toFixed(2)}m • {yaw}°
              </span>
            </div>
          </div>

          {/* Attachment / Sticking Hierarchy Row */}
          <div className="pt-1 border-t border-zinc-900 flex items-center justify-between text-[9px]">
            {selectedObject.attached_to_id ? (
              <div className="flex items-center justify-between w-full bg-zinc-900/80 px-2 py-1 border border-zinc-700 gap-1">
                <div className="flex items-center gap-1.5 min-w-0 truncate">
                  <Link className="w-3 h-3 text-zinc-300 shrink-0" />
                  <span className="text-zinc-400 truncate">
                    STUCK TO: <span className="text-zinc-100 font-bold">{parentLabel}</span>
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => detachObject(selectedObject.id)}
                  className="flex items-center gap-1 px-2 py-0.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-zinc-100 font-bold active:bg-zinc-600 shrink-0 transition-colors"
                >
                  <Unlink className="w-2.5 h-2.5 text-zinc-300" />
                  <span>UNSTICK</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between w-full text-[9px] gap-1 flex-wrap">
                <span className="text-zinc-500 text-[8px] uppercase tracking-wider shrink-0">
                  LINKING: INDEPENDENT
                </span>
                <div className="flex items-center gap-1">
                  {potentialParent && (
                    <button
                      type="button"
                      onClick={() => attachObject(selectedObject.id, potentialParent.id)}
                      className="flex items-center gap-1 px-2 py-0.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 font-bold transition-colors"
                      title={`Snap onto ${potentialParent.name}`}
                    >
                      <Link className="w-2.5 h-2.5 text-zinc-400" />
                      <span>STICK TO TABLE</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => sendPromptEdit(`stick ${selectedObject.name} to wall`)}
                    className="flex items-center gap-1 px-2 py-0.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
                    title="Snap to nearest room wall"
                  >
                    <span>SNAP WALL</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Action Pad (Direction Nudge + Rotate + Delete) */}
          <div className="flex items-center justify-between gap-1.5 pt-1 border-t border-zinc-900">
            {/* 4-Way Directional Pad */}
            <div className="flex items-center gap-0.5 bg-zinc-900 p-0.5 border border-zinc-800 shrink-0">
              <button
                onClick={() => handleNudge(-0.2, 0)}
                className="p-1.5 text-zinc-300 hover:bg-zinc-800 active:bg-zinc-700"
                title="X -0.2m"
              >
                <ArrowLeft className="w-3 h-3" />
              </button>
              <div className="flex flex-col gap-0.5">
                <button
                  onClick={() => handleNudge(0, -0.2)}
                  className="p-1 text-zinc-300 hover:bg-zinc-800 active:bg-zinc-700"
                  title="Z -0.2m"
                >
                  <ArrowUp className="w-2.5 h-2.5" />
                </button>
                <button
                  onClick={() => handleNudge(0, 0.2)}
                  className="p-1 text-zinc-300 hover:bg-zinc-800 active:bg-zinc-700"
                  title="Z +0.2m"
                >
                  <ArrowDown className="w-2.5 h-2.5" />
                </button>
              </div>
              <button
                onClick={() => handleNudge(0.2, 0)}
                className="p-1.5 text-zinc-300 hover:bg-zinc-800 active:bg-zinc-700"
                title="X +0.2m"
              >
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {/* Rotate Button */}
            <button
              onClick={() => rotateObject(selectedObject.id, 45)}
              className="flex-1 flex items-center justify-center gap-1 py-1.5 px-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 text-[10px] font-bold active:bg-zinc-700 transition-colors"
            >
              <RotateCw className="w-3 h-3" />
              <span>YAW +45°</span>
            </button>

            {/* Delete Button */}
            <button
              onClick={() => deleteObject(selectedObject.id)}
              className="p-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-100 text-[10px] active:bg-zinc-700 transition-colors shrink-0"
              title="Delete Object"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 2. HOME MATRIX CONTROLS (When on Rotating Football Geode)
  if (isHome) {
    const hasExistingScenes = availableScenes && availableScenes.length > 0;
    return (
      <div className="absolute bottom-3 left-0 right-0 z-20 flex flex-col items-center px-3 pointer-events-none font-mono pb-[max(0.25rem,env(safe-area-inset-bottom))]">
        <div className="flex flex-wrap items-center justify-center gap-1.5 bg-zinc-950/95 border border-zinc-800 p-1.5 shadow-2xl pointer-events-auto backdrop-blur-xs max-w-md w-full">
          <button
            onClick={() => setActiveModal('upload')}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-zinc-100 hover:bg-white text-zinc-950 font-bold text-[11px] transition-colors"
          >
            <Camera className="w-3.5 h-3.5" />
            <span>CAPTURE ROOM</span>
          </button>

          <button
            onClick={() => setActiveModal('manual_paste')}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 font-bold text-[11px] transition-colors"
          >
            <FileCode2 className="w-3.5 h-3.5 text-zinc-400" />
            <span>INGEST PAYLOAD</span>
          </button>

          {hasExistingScenes && (
            <button
              onClick={() => loadSceneById(availableScenes[0].scene_id)}
              className="w-full flex items-center justify-center gap-1 px-3 py-1 bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800/80 text-zinc-400 text-[9px] transition-colors"
            >
              <Layers className="w-3 h-3 text-zinc-500" />
              <span>LOAD LATEST TWIN: {availableScenes[0].name || availableScenes[0].scene_id}</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  // 3. RECONSTRUCTED ROOM DOCK (Responsive, Monochromatic CAD Bar)
  return (
    <div className="absolute bottom-2 left-0 right-0 z-20 flex justify-center px-2 pointer-events-none font-mono pb-[max(0.25rem,env(safe-area-inset-bottom))]">
      <div className="flex items-center gap-1 bg-zinc-950/98 border border-zinc-800 p-1 shadow-2xl pointer-events-auto backdrop-blur-xs max-w-sm sm:max-w-md">
        <button
          onClick={() => setActiveModal('chat')}
          className="flex items-center gap-1 px-2.5 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 font-bold text-[10px] transition-colors"
        >
          <Terminal className="w-3 h-3" />
          <span>COMMAND</span>
        </button>

        <button
          onClick={() => setActiveModal('upload')}
          className="flex items-center gap-1 px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 font-bold text-[10px] transition-colors"
        >
          <Camera className="w-3 h-3" />
          <span>CAPTURE</span>
        </button>

        <button
          onClick={() => setActiveModal('manual_paste')}
          className="flex items-center gap-1 px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 font-bold text-[10px] transition-colors"
        >
          <FileCode2 className="w-3 h-3" />
          <span>PAYLOAD</span>
        </button>

        <button
          onClick={() => setActiveModal('antigravity')}
          className="flex items-center gap-1 px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 font-bold text-[10px] transition-colors"
          title="Inspect Antigravity CAD Prompts & Plan"
        >
          <Sparkles className="w-3 h-3 text-zinc-300" />
          <span>AGY PLAN</span>
        </button>

        <button
          onClick={triggerRefinementLoop}
          disabled={isRefining}
          className="flex items-center gap-1 px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 font-bold text-[10px] transition-colors"
          title="Trigger Iterative Object Refinement Loop"
        >
          <Sparkles className="w-3 h-3 text-zinc-400" />
          <span>{isRefining ? 'LOOPING...' : 'REFINE'}</span>
        </button>

        {/* Export Dropdown */}
        <div className="relative">
          {showExportMenu && (
            <div
              className="fixed inset-0 z-40 bg-transparent"
              onClick={() => setShowExportMenu(false)}
            />
          )}
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="flex items-center gap-1 px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 font-bold text-[10px] transition-colors"
          >
            <Download className="w-3 h-3" />
            <span>EXPORT</span>
          </button>

          {showExportMenu && (
            <div className="absolute bottom-full mb-1 right-0 bg-zinc-950 border border-zinc-800 shadow-2xl p-1 min-w-[130px] flex flex-col gap-1 text-[10px] z-50">
              <button
                onClick={() => {
                  exportGlb();
                  setShowExportMenu(false);
                }}
                className="w-full text-left px-2 py-1.5 hover:bg-zinc-900 text-zinc-200 hover:text-white font-bold"
              >
                DOWNLOAD .GLB
              </button>
              <button
                onClick={() => {
                  exportJson();
                  setShowExportMenu(false);
                }}
                className="w-full text-left px-2 py-1.5 hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200"
              >
                DOWNLOAD .JSON
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
