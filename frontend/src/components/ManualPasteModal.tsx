import React, { useState } from 'react';
import { FileCode2, X, Loader2, Copy, Check, ExternalLink } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

const CAD_PROMPT_TEMPLATE = `You are SpatialCraft AI, an expert 3D spatial reconstruction and interior architecture intelligence.
Your task is to analyze this room photograph and reconstruct its complete 3D digital twin with exact metric dimensions and furniture coordinates.

Analyze the room geometry, camera viewpoint, and every visible piece of furniture and interior decor.
Output ONLY a JSON block enclosed within \`\`\`json and \`\`\` with the following exact schema:

\`\`\`json
{
  "room": {
    "dimensions": { "width": 5.0, "height": 2.8, "depth": 5.0 },
    "floor": { "material": "light_oak_wood_parquet", "color": "#c4a482" },
    "walls": { "material": "matte_plaster", "color": "#f2efe9" },
    "ceiling": { "material": "matte_plaster", "color": "#fafafa" }
  },
  "objects": [
    {
      "id": "obj_sofa_1",
      "name": "Modern Grey Three-Seater Sofa",
      "category": "sofa",
      "description": "Contemporary low-profile fabric sofa with deep seat cushions and brushed metal legs",
      "position": { "x": 0.0, "y": 0.45, "z": -1.2 },
      "dimensions": { "width": 2.2, "height": 0.85, "depth": 0.95 },
      "rotation": { "yaw": 0.0 },
      "color": "#6e737b",
      "box_2d": [0.45, 0.20, 0.78, 0.80]
    }
  ]
}
\`\`\`

CRITICAL 3D COORDINATE SYSTEM RULES:
1. Ground floor is y = 0. Object position 'y' should be height / 2 so the bottom sits flush on the floor.
2. Room center on the floor is (x=0, z=0).
   - x goes from -width/2 (left wall) to +width/2 (right wall).
   - z goes from -depth/2 (far back wall) to +depth/2 (near camera).
3. 'category' must be one of: "sofa", "table", "chair", "bed", "lamp", "plant", "tv_unit", "bookshelf", "rug", "art", "decor".
4. 'box_2d' is normalized [ymin, xmin, ymax, xmax] between 0.0 and 1.0 indicating where this object appears in the photo.
5. All dimensions ('width', 'height', 'depth') must be realistic real-world meters.
6. Provide EVERY recognizable piece of furniture or decor in the room.

Respond with ONLY the JSON code block.`;

export const ManualPasteModal: React.FC = () => {
  const { activeModal, setActiveModal, scene, setScene, refreshAvailableScenes } = useSceneStore();
  const [rawText, setRawText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (activeModal !== 'manual_paste') return null;

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(CAD_PROMPT_TEMPLATE);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2500);
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = CAD_PROMPT_TEMPLATE;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2500);
    }
  };

  const handleSubmit = async () => {
    if (!rawText.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setErrorMsg('');

    try {
      const sceneId = (!scene || scene.scene_id === 'home')
        ? `scene_${Date.now().toString(16).slice(-8)}`
        : scene.scene_id;
      const res = await fetch(`/api/scene/${sceneId}/submit_raw_output`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: rawText }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to parse structured 3D payload.');
      }

      const newScene = await res.json();
      setScene(newScene);
      refreshAvailableScenes();
      setActiveModal('none');
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-xs font-mono animate-in fade-in">
      <div className="w-full max-w-lg bg-zinc-950 border border-zinc-800 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 text-[11px]">
          <div className="flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-zinc-300" />
            <h3 className="font-bold text-zinc-100 uppercase tracking-wider">
              ChatGPT // Direct Payload Ingestion
            </h3>
          </div>
          <button
            onClick={() => setActiveModal('none')}
            className="p-1 text-zinc-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4 overflow-y-auto text-xs">
          {/* Step 1 Box */}
          <div className="border border-zinc-800 bg-zinc-900/60 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-zinc-200 text-[11px] tracking-wide uppercase">
                STEP 1: Copy CAD Prompt
              </span>
              <button
                type="button"
                onClick={handleCopyPrompt}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold border transition-colors ${
                  copiedPrompt
                    ? 'border-emerald-600 bg-emerald-950/80 text-emerald-300'
                    : 'border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-zinc-100'
                }`}
              >
                {copiedPrompt ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>COPIED TO CLIPBOARD!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-zinc-300" />
                    <span>COPY PROMPT</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-[11px] text-zinc-400 leading-normal">
              Paste this prompt with your room photo into your personal{' '}
              <a
                href="https://chatgpt.com"
                target="_blank"
                rel="noreferrer"
                className="text-zinc-200 underline inline-flex items-center gap-0.5"
              >
                ChatGPT tab <ExternalLink className="w-2.5 h-2.5" />
              </a>
              .
            </p>
          </div>

          {/* Step 2 Box */}
          <div className="space-y-2">
            <label className="block font-bold text-zinc-200 text-[11px] tracking-wide uppercase">
              STEP 2: Paste ChatGPT's Output JSON
            </label>
            <textarea
              rows={8}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste raw completion or JSON from ChatGPT here..."
              className="w-full bg-black border border-zinc-800 p-3 text-[11px] font-mono text-zinc-200 outline-none focus:border-zinc-400 placeholder:text-zinc-700 resize-none"
            />
          </div>

          {errorMsg && (
            <div className="text-[11px] text-zinc-200 bg-zinc-900 p-2.5 border border-zinc-700">
              [PARSER ERROR]: {errorMsg}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-zinc-800 bg-zinc-950 flex items-center justify-end gap-2 text-xs">
          <button
            type="button"
            onClick={() => setActiveModal('none')}
            className="px-3 py-1.5 text-zinc-400 hover:text-zinc-100 font-bold"
          >
            CANCEL
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!rawText.trim() || isSubmitting}
            className={`flex items-center gap-1.5 px-4 py-2 font-mono font-bold text-[11px] transition-colors ${
              !rawText.trim() || isSubmitting
                ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                : 'bg-zinc-100 hover:bg-white text-zinc-950'
            }`}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>PARSING &amp; RECONSTRUCTING...</span>
              </>
            ) : (
              <span>INGEST &amp; RENDER 3D TWIN</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
