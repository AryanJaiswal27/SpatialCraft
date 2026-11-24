import React, { useState } from 'react';
import { X, BookOpen, Terminal, MousePointerClick, ShieldCheck, Layers, Move, Check } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

type GuideTab = 'quickstart' | 'capture' | 'controls' | 'cad_loop';

export const GuideModal: React.FC = () => {
  const { activeModal, setActiveModal } = useSceneStore();
  const [activeTab, setActiveTab] = useState<GuideTab>('quickstart');

  if (activeModal !== 'guide') return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/85 backdrop-blur-sm select-none font-mono">
      <div className="bg-zinc-950 border border-zinc-800 w-full max-w-2xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800 bg-zinc-900/50">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-zinc-100" />
            <h2 className="text-xs font-bold text-zinc-100 uppercase tracking-wider">
              SpatialCraft // Operational & Usage Guide
            </h2>
          </div>
          <button
            onClick={() => setActiveModal('none')}
            className="p-1 text-zinc-400 hover:text-zinc-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-zinc-800 bg-zinc-950 text-[10px] overflow-x-auto scrollbar-none">
          <button
            onClick={() => setActiveTab('quickstart')}
            className={`px-3 py-2 font-bold uppercase transition-colors shrink-0 flex items-center gap-1.5 ${
              activeTab === 'quickstart'
                ? 'bg-zinc-900 text-zinc-100 border-b-2 border-zinc-100'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Terminal className="w-3 h-3" />
            <span>01. Quick Start</span>
          </button>
          <button
            onClick={() => setActiveTab('capture')}
            className={`px-3 py-2 font-bold uppercase transition-colors shrink-0 flex items-center gap-1.5 ${
              activeTab === 'capture'
                ? 'bg-zinc-900 text-zinc-100 border-b-2 border-zinc-100'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <MousePointerClick className="w-3 h-3" />
            <span>02. Room Capture</span>
          </button>
          <button
            onClick={() => setActiveTab('controls')}
            className={`px-3 py-2 font-bold uppercase transition-colors shrink-0 flex items-center gap-1.5 ${
              activeTab === 'controls'
                ? 'bg-zinc-900 text-zinc-100 border-b-2 border-zinc-100'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Move className="w-3 h-3" />
            <span>03. 3D Controls</span>
          </button>
          <button
            onClick={() => setActiveTab('cad_loop')}
            className={`px-3 py-2 font-bold uppercase transition-colors shrink-0 flex items-center gap-1.5 ${
              activeTab === 'cad_loop'
                ? 'bg-zinc-900 text-zinc-100 border-b-2 border-zinc-100'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Layers className="w-3 h-3" />
            <span>04. CAD Loop & Export</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="p-3 sm:p-4 overflow-y-auto space-y-4 text-xs text-zinc-300 leading-relaxed font-mono">
          {/* TAB 1: QUICK START */}
          {activeTab === 'quickstart' && (
            <div className="space-y-4">
              <div className="p-2.5 bg-zinc-900/60 border border-zinc-800 text-[11px]">
                <span className="font-bold text-zinc-100 block mb-1 uppercase tracking-wide">
                  Complete Architecture Workflow
                </span>
                SpatialCraft reconstructs 3D rooms from single smartphone photos, connects over public cellular networks via Cloudflare Tunnel ingress, and drives physical desktop browser automation across Gemini, ChatGPT, and DeepSeek.
              </div>

              <div className="space-y-3">
                <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-4 h-4 rounded-full bg-zinc-800 text-zinc-200 flex items-center justify-center text-[10px] font-bold">1</span>
                    <span className="font-bold text-zinc-100 uppercase text-[11px]">Start SpatialCraft Server & Ingress</span>
                  </div>
                  <p className="text-[10px] text-zinc-400 mb-2">
                    Launches FastAPI on port 8000 and the live Cloudflare Tunnel for mobile access:
                  </p>
                  <code className="block p-1.5 bg-black border border-zinc-800 text-zinc-200 text-[10px]">
                    .\run_spatialcraft.bat
                  </code>
                </div>

                <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-4 h-4 rounded-full bg-zinc-800 text-zinc-200 flex items-center justify-center text-[10px] font-bold">2</span>
                    <span className="font-bold text-zinc-100 uppercase text-[11px]">Calibrate Screen Click Coordinates</span>
                  </div>
                  <p className="text-[10px] text-zinc-400 mb-2">
                    Open your chosen LLM tab in your browser, then run the 15-second calibrator:
                  </p>
                  <code className="block p-1.5 bg-black border border-zinc-800 text-zinc-200 text-[10px] mb-1">
                    .\calibrate_clicks.bat gemini
                  </code>
                  <span className="text-[9px] text-zinc-500 block">
                    Supported presets: <span className="text-zinc-300">gemini</span>, <span className="text-zinc-300">chatgpt</span>, <span className="text-zinc-300">deepseek</span>. Hover over targets 1 to 4 and press [SPACE].
                  </span>
                </div>

                <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-4 h-4 rounded-full bg-zinc-800 text-zinc-200 flex items-center justify-center text-[10px] font-bold">3</span>
                    <span className="font-bold text-zinc-100 uppercase text-[11px]">Start the Desktop Physical Click Daemon</span>
                  </div>
                  <p className="text-[10px] text-zinc-400 mb-2">
                    Runs in your user session to physically move the mouse and paste prompts:
                  </p>
                  <code className="block p-1.5 bg-black border border-zinc-800 text-zinc-200 text-[10px]">
                    .\run_physical_daemon.bat
                  </code>
                </div>

                <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-4 h-4 rounded-full bg-zinc-800 text-zinc-200 flex items-center justify-center text-[10px] font-bold">4</span>
                    <span className="font-bold text-zinc-100 uppercase text-[11px]">Capture Room from Mobile or Desktop</span>
                  </div>
                  <p className="text-[10px] text-zinc-400">
                    Scan the QR code from the header icon (<span className="text-zinc-200">[QR]</span>) with your smartphone, tap <span className="text-zinc-200">[CAPTURE ROOM]</span>, and select your LLM button.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ROOM CAPTURE */}
          {activeTab === 'capture' && (
            <div className="space-y-4">
              <div className="p-2.5 bg-zinc-900/60 border border-zinc-800 text-[11px]">
                <span className="font-bold text-zinc-100 block mb-1 uppercase tracking-wide">
                  Physical Click Ingestion Buttons
                </span>
                Room capture exclusively uses dedicated physical buttons driving your open browser windows without bot challenges, cookie logins, or Cloudflare blocks:
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                  <span className="font-bold text-zinc-100 uppercase text-[10px] block mb-1">
                    Physical on Gemini
                  </span>
                  <span className="text-[9px] text-zinc-500 font-mono block mb-1.5">gemini.google.com</span>
                  <p className="text-[9px] text-zinc-400 leading-normal">
                    Drives Google Gemini tab. Pastes image + CAD prompt, clicks Send, and copies the generated 3D room JSON.
                  </p>
                </div>

                <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                  <span className="font-bold text-zinc-100 uppercase text-[10px] block mb-1">
                    Physical on ChatGPT
                  </span>
                  <span className="text-[9px] text-zinc-500 font-mono block mb-1.5">chatgpt.com</span>
                  <p className="text-[9px] text-zinc-400 leading-normal">
                    Drives OpenAI ChatGPT tab. Automatically switches to calibrated ChatGPT coordinates for physical execution.
                  </p>
                </div>

                <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                  <span className="font-bold text-zinc-100 uppercase text-[10px] block mb-1">
                    Physical on DeepSeek
                  </span>
                  <span className="text-[9px] text-zinc-500 font-mono block mb-1.5">chat.deepseek.com</span>
                  <p className="text-[9px] text-zinc-400 leading-normal">
                    Drives DeepSeek Chat tab. Uses calibrated DeepSeek textarea and send buttons.
                  </p>
                </div>
              </div>

              <div className="border border-zinc-800 p-3 bg-zinc-900/30">
                <div className="flex items-center gap-1.5 mb-1.5 text-zinc-100 font-bold text-[11px] uppercase tracking-wide">
                  <ShieldCheck className="w-4 h-4 text-zinc-200" />
                  <span>5-Minute Autonomous Antigravity CAD Backup Guarantee</span>
                </div>
                <p className="text-[10px] text-zinc-400 leading-relaxed">
                  If no output is received from the browser LLM within <span className="text-zinc-100 font-bold">5 minutes (300 seconds)</span> due to network timeouts, captcha, or browser stalls:
                </p>
                <div className="mt-2 space-y-1 text-[9px] text-zinc-300">
                  <div className="flex items-start gap-1.5">
                    <Check className="w-3 h-3 text-zinc-400 shrink-0 mt-0.5" />
                    <span>Antigravity autonomously analyzes the photograph colors and room geometry.</span>
                  </div>
                  <div className="flex items-start gap-1.5">
                    <Check className="w-3 h-3 text-zinc-400 shrink-0 mt-0.5" />
                    <span>Generates the complete 3D digital twin with wall boundaries and furniture placements.</span>
                  </div>
                  <div className="flex items-start gap-1.5">
                    <Check className="w-3 h-3 text-zinc-400 shrink-0 mt-0.5" />
                    <span>Crops each object from the photo and loops through every item to construct multi-part 3D CSG meshes!</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: 3D CONTROLS */}
          {activeTab === 'controls' && (
            <div className="space-y-4">
              <div className="p-2.5 bg-zinc-900/60 border border-zinc-800 text-[11px]">
                <span className="font-bold text-zinc-100 block mb-1 uppercase tracking-wide">
                  Touch & Mouse Viewport Controls
                </span>
                SpatialCraft provides a complete precision CAD editing suite directly in your mobile browser:
              </div>

              <div className="space-y-2 text-[10px]">
                <div className="border border-zinc-800 p-2 bg-zinc-950 flex items-center justify-between">
                  <span className="font-bold text-zinc-200">Orbit Camera</span>
                  <span className="text-zinc-500">1-Finger Drag / Left-Click Drag</span>
                </div>
                <div className="border border-zinc-800 p-2 bg-zinc-950 flex items-center justify-between">
                  <span className="font-bold text-zinc-200">Zoom Camera</span>
                  <span className="text-zinc-500">Pinch In/Out / Scroll Wheel</span>
                </div>
                <div className="border border-zinc-800 p-2 bg-zinc-950 flex items-center justify-between">
                  <span className="font-bold text-zinc-200">Pan Viewport</span>
                  <span className="text-zinc-500">2-Finger Drag / Right-Click Drag</span>
                </div>
                <div className="border border-zinc-800 p-2 bg-zinc-950 flex items-center justify-between">
                  <span className="font-bold text-zinc-200">Select Furniture</span>
                  <span className="text-zinc-500">Tap Object in 3D Scene</span>
                </div>
                <div className="border border-zinc-800 p-2 bg-zinc-950 flex items-center justify-between">
                  <span className="font-bold text-zinc-200">Drag Furniture</span>
                  <span className="text-zinc-500">Touch & Drag along Floor Plane</span>
                </div>
              </div>

              <div className="border border-zinc-800 p-3 bg-zinc-950">
                <span className="font-bold text-zinc-100 uppercase text-[10px] block mb-1.5">
                  Hierarchical Parent-Child Sticking
                </span>
                <p className="text-[10px] text-zinc-400 mb-2 leading-relaxed">
                  When selecting tabletop items (laptops, phones, desk lamps, mugs):
                </p>
                <div className="space-y-1.5 text-[9px] text-zinc-300">
                  <p>
                    <span className="text-zinc-100 font-bold">[STICK TO TABLE]</span>: Snaps the item flush onto the top surface of the parent desk/table. Moving or rotating the desk automatically orbits and translates the child object synchronously!
                  </p>
                  <p>
                    <span className="text-zinc-100 font-bold">[SNAP WALL]</span>: Snaps paintings, clocks, and TV units flush to the nearest boundary wall.
                  </p>
                  <p>
                    <span className="text-zinc-100 font-bold">[UNSTICK]</span>: Detaches the object back to independent floor motion.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: CAD LOOP & EXPORT */}
          {activeTab === 'cad_loop' && (
            <div className="space-y-4">
              <div className="p-2.5 bg-zinc-900/60 border border-zinc-800 text-[11px]">
                <span className="font-bold text-zinc-100 block mb-1 uppercase tracking-wide">
                  Antigravity CAD Object Refinement Loop
                </span>
                Antigravity prioritizes and steps through every furniture piece one-by-one to build millimeter-accurate 3D constructive solid geometry (CSG) meshes:
              </div>

              <div className="border border-zinc-800 p-2.5 bg-zinc-950 space-y-1.5 text-[10px]">
                <div className="flex items-center gap-1.5 text-zinc-200 font-bold uppercase text-[10px]">
                  <span>Priority Sequence</span>
                </div>
                <p className="text-[9px] text-zinc-400">
                  1. Structural Anchors (Desks, Tables, Sofas, Beds) <br />
                  2. Ergonomic Seating & Storage (Executive Chairs, Credenzas, Bookshelves) <br />
                  3. Tabletop Tech (Laptops, Phones, Monitors, Task Lamps) <br />
                  4. Floor & Wall Decor (Area Rugs, Framed Art, Ceramic Planters)
                </p>
              </div>

              <div className="border border-zinc-800 p-2.5 bg-zinc-950">
                <span className="font-bold text-zinc-100 uppercase text-[10px] block mb-1">
                  Exporting Your Digital Twin
                </span>
                <p className="text-[10px] text-zinc-400 mb-2">
                  Tap <span className="text-zinc-200 font-bold">[EXPORT]</span> in the bottom dock:
                </p>
                <div className="space-y-1 text-[9px] text-zinc-300">
                  <p>
                    • <span className="text-zinc-100 font-bold">Download .GLB</span>: Standard binary glTF 2.0 with all dynamic parts, PBR materials, and lighting. Imports directly into Blender, Unity, Unreal Engine, WebXR, or Apple Vision Pro.
                  </p>
                  <p>
                    • <span className="text-zinc-100 font-bold">Download .JSON</span>: Complete Pydantic Scene Graph hierarchy with exact coordinates, yaw rotations, bounding boxes, and attachment IDs.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-3 py-2 border-t border-zinc-800 bg-zinc-900/40 text-[10px]">
          <span className="text-zinc-500 font-mono">SPATIALCRAFT // CAD STUDIO v1.0</span>
          <button
            onClick={() => setActiveModal('none')}
            className="px-3 py-1 bg-zinc-100 hover:bg-white text-zinc-950 font-bold text-[10px] uppercase transition-colors"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
