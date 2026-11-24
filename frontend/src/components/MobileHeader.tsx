import React, { useState } from 'react';
import { Camera, ChevronDown, Check, QrCode, Terminal, Layers, Box, MousePointerClick, HelpCircle } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';
import type { LLMTarget, SceneGraph } from '../types';

const HOME_GEODE_SCENE: SceneGraph = {
  scene_id: 'home',
  name: 'SPATIAL MATRIX (HOME)',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  status: 'ready',
  room: {
    dimensions: { width: 5.0, height: 2.8, depth: 5.0 },
    floor: { material: 'slate', color: '#09090b' },
    walls: { material: 'matte_plaster', color: '#09090b' },
    ceiling: { material: 'matte_plaster', color: '#09090b' },
  },
  objects: [],
};

export const MobileHeader: React.FC = () => {
  const { targetLLM, setTargetLLM, setActiveModal, scene, setScene, availableScenes, loadSceneById } = useSceneStore();
  const [showLLMMenu, setShowLLMMenu] = useState(false);
  const [showSceneMenu, setShowSceneMenu] = useState(false);

  const targets: { id: LLMTarget; name: string }[] = [
    { id: 'gemini', name: 'Gemini (Physical)' },
    { id: 'chatgpt', name: 'ChatGPT (Physical)' },
    { id: 'deepseek', name: 'DeepSeek (Physical)' },
  ];

  const currentTarget = targets.find((t) => t.id === targetLLM) || targets[0];
  const isHome = !scene || scene.scene_id === 'home';

  return (
    <>
      {(showSceneMenu || showLLMMenu) && (
        <div
          className="fixed inset-0 z-25 bg-transparent"
          onClick={() => {
            setShowSceneMenu(false);
            setShowLLMMenu(false);
          }}
        />
      )}
      <header className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-2 sm:px-3 py-1.5 pt-[max(0.375rem,env(safe-area-inset-top))] bg-zinc-950/95 border-b border-zinc-800 text-xs select-none backdrop-blur-xs font-mono">
      {/* Left: Brand & Room Matrix Switcher */}
      <div className="flex items-center gap-1.5 min-w-0 mr-1">
        <div className="w-2 h-2 bg-zinc-100 shrink-0" />
        <span className="font-bold text-zinc-100 tracking-wider uppercase text-[11px] shrink-0 hidden xs:inline">
          SpatialCraft
        </span>

        {/* Scene / Room Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setShowSceneMenu(!showSceneMenu);
              setShowLLMMenu(false);
            }}
            className="flex items-center gap-1 px-1.5 py-0.5 bg-zinc-900 border border-zinc-800 text-[9px] text-zinc-300 hover:border-zinc-600 active:bg-zinc-800 transition-colors max-w-[110px] sm:max-w-[140px] truncate"
            title="Switch Between Reconstructed Rooms or Home Matrix"
          >
            {isHome ? (
              <Box className="w-2.5 h-2.5 text-zinc-400 shrink-0" />
            ) : (
              <Layers className="w-2.5 h-2.5 text-zinc-400 shrink-0" />
            )}
            <span className="truncate">
              {isHome ? 'GEODE' : `${scene?.scene_id?.slice(-6)} (${scene?.objects?.length || 0})`}
            </span>
            <ChevronDown className="w-2.5 h-2.5 text-zinc-500 shrink-0" />
          </button>

          {showSceneMenu && (
            <div className="absolute left-0 top-full mt-1 w-52 sm:w-60 bg-zinc-950 border border-zinc-800 shadow-2xl p-1 z-50 font-mono max-h-[70vh] overflow-y-auto">
              <div className="px-2 py-1 text-[8px] font-bold text-zinc-500 uppercase tracking-wider border-b border-zinc-800 mb-1">
                Room Switcher
              </div>

              {/* Home State Geode Option */}
              <button
                type="button"
                onClick={() => {
                  setScene(HOME_GEODE_SCENE);
                  setShowSceneMenu(false);
                }}
                className={`w-full flex items-center justify-between px-2 py-1.5 text-[10px] text-left transition-colors mb-1 ${
                  isHome ? 'bg-zinc-800 text-zinc-100 font-bold' : 'text-zinc-400 hover:bg-zinc-900'
                }`}
              >
                <div className="flex items-center gap-1.5 truncate">
                  <Box className="w-3 h-3 text-zinc-400 shrink-0" />
                  <span className="truncate">HOME // GEODE MATRIX</span>
                </div>
                {isHome && <Check className="w-3 h-3 text-zinc-100 shrink-0" />}
              </button>

              <div className="px-2 py-0.5 text-[8px] font-bold text-zinc-600 uppercase tracking-wider border-t border-zinc-900 my-0.5">
                Captured Digital Twins
              </div>

              {availableScenes && availableScenes.length > 0 ? (
                availableScenes.map((s: any) => (
                  <button
                    key={s.scene_id}
                    onClick={() => {
                      loadSceneById(s.scene_id);
                      setShowSceneMenu(false);
                    }}
                    className={`w-full flex items-center justify-between px-2 py-1.5 text-[10px] text-left transition-colors ${
                      scene?.scene_id === s.scene_id
                        ? 'bg-zinc-800 text-zinc-100 font-bold'
                        : 'text-zinc-400 hover:bg-zinc-900'
                    }`}
                  >
                    <div className="flex flex-col truncate">
                      <span className="truncate">{s.name || s.scene_id}</span>
                      <span className="text-[8px] text-zinc-500">
                        {s.objects_count || 0} objects • {s.scene_id.slice(-8)}
                      </span>
                    </div>
                    {scene?.scene_id === s.scene_id && (
                      <Check className="w-3 h-3 text-zinc-100 shrink-0 ml-1" />
                    )}
                  </button>
                ))
              ) : (
                <div className="px-2 py-2 text-[9px] text-zinc-600 italic">No rooms captured yet.</div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Right: Engine Selector & Actions */}
      <div className="flex items-center gap-1 shrink-0">
        {/* Target Engine Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setShowLLMMenu(!showLLMMenu);
              setShowSceneMenu(false);
            }}
            className="flex items-center gap-1 px-1.5 py-1 bg-zinc-900 border border-zinc-800 text-[10px] text-zinc-300 hover:border-zinc-700 active:bg-zinc-800 transition-colors"
          >
            <span className="font-bold text-zinc-100 uppercase text-[9px] sm:text-[10px]">
              {currentTarget.name}
            </span>
            <ChevronDown className="w-2.5 h-2.5 text-zinc-500" />
          </button>

          {showLLMMenu && (
            <div className="absolute right-0 top-full mt-1 w-40 bg-zinc-950 border border-zinc-800 shadow-2xl p-1 z-50 font-mono">
              <div className="px-2 py-1 text-[8px] font-bold text-zinc-500 uppercase tracking-wider border-b border-zinc-800 mb-1">
                Automation Driver
              </div>
              {targets.map((t) => (
                <button
                  key={t.id}
                  onClick={() => {
                    setTargetLLM(t.id);
                    setShowLLMMenu(false);
                  }}
                  className={`w-full flex items-center justify-between px-2 py-1.5 text-[10px] text-left transition-colors ${
                    targetLLM === t.id
                      ? 'bg-zinc-800 text-zinc-100 font-bold'
                      : 'text-zinc-400 hover:bg-zinc-900'
                  }`}
                >
                  <span>{t.name}</span>
                  {targetLLM === t.id && <Check className="w-3 h-3 text-zinc-100" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Console / Telemetry Modal Trigger */}
        <button
          onClick={() => setActiveModal('logs')}
          className="p-1.5 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 transition-colors shrink-0"
          title="Background Console Telemetry"
        >
          <Terminal className="w-3 h-3" />
        </button>

        {/* Calibration Trigger */}
        <button
          onClick={() => setActiveModal('calibration')}
          className="p-1.5 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 transition-colors shrink-0"
          title="Calibrate Physical Screen Click Coordinates"
        >
          <MousePointerClick className="w-3 h-3" />
        </button>

        {/* Operational Guide Trigger */}
        <button
          onClick={() => setActiveModal('guide')}
          className="p-1.5 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 transition-colors shrink-0"
          title="SpatialCraft Operational Guide"
        >
          <HelpCircle className="w-3 h-3" />
        </button>

        {/* QR Matrix Modal Trigger */}
        <button
          onClick={() => setActiveModal('qr')}
          className="p-1.5 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 transition-colors shrink-0"
          title="Mobile Ingress QR Code"
        >
          <QrCode className="w-3 h-3" />
        </button>

        {/* Capture Room Button */}
        <button
          onClick={() => setActiveModal('upload')}
          className="flex items-center gap-1 px-2 py-1 bg-zinc-100 hover:bg-white text-zinc-950 font-bold text-[10px] active:bg-zinc-300 transition-colors shrink-0"
        >
          <Camera className="w-3 h-3" />
          <span className="hidden xs:inline">CAPTURE</span>
        </button>
      </div>
    </header>
    </>
  );
};
