import React, { useState, useEffect } from 'react';
import { X, Sparkles, Copy, Check, Play, RefreshCw, ChevronRight } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

interface PlanStep {
  step: number;
  total_steps: number;
  object_id: string;
  object_name: string;
  category: string;
  crop_url?: string;
  antigravity_prompt: string;
}

export const AntigravityModal: React.FC = () => {
  const { activeModal, setActiveModal, scene } = useSceneStore();
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedStep, setSelectedStep] = useState<PlanStep | null>(null);
  const [isRunningLoop, setIsRunningLoop] = useState(false);

  const isOpen = activeModal === 'antigravity';

  const fetchPlan = async () => {
    if (!scene?.scene_id || scene.scene_id === 'home') return;
    setIsLoading(true);
    try {
      const res = await fetch(`/api/scene/${scene.scene_id}/antigravity_plan`);
      if (res.ok) {
        const data = await res.json();
        setPlan(data.plan || []);
        if (data.plan?.length > 0 && !selectedStep) {
          setSelectedStep(data.plan[0]);
        }
      }
    } catch (e) {
      console.error('Failed to fetch Antigravity plan:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !scene?.scene_id || scene.scene_id === 'home') return;
    let cancelled = false;
    fetch(`/api/scene/${scene.scene_id}/antigravity_plan`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        const steps = data.plan || [];
        setPlan(steps);
        setSelectedStep((prev) => prev || (steps.length > 0 ? steps[0] : null));
      })
      .catch((e) => console.error('Failed to fetch Antigravity plan:', e));
    return () => {
      cancelled = true;
    };
  }, [isOpen, scene?.scene_id]);

  if (!isOpen) return null;

  const handleCopyPrompt = (step: PlanStep) => {
    navigator.clipboard.writeText(step.antigravity_prompt);
    setCopiedId(step.object_id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleTriggerRefine = async (step?: PlanStep) => {
    if (!scene?.scene_id) return;
    setIsRunningLoop(true);
    try {
      const payload = step ? { object_id: step.object_id } : { max_items: plan.length };
      await fetch(`/api/scene/${scene.scene_id}/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (e) {
      console.error('Failed to trigger refinement:', e);
    } finally {
      setTimeout(() => setIsRunningLoop(false), 2500);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md">
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-zinc-950 border border-zinc-800 text-zinc-100 shadow-2xl font-mono">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-900/60">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-zinc-300" />
            <div>
              <h2 className="text-xs uppercase tracking-widest font-bold text-zinc-100">
                ANTIGRAVITY CAD INTELLIGENCE LOOP
              </h2>
              <p className="text-[10px] text-zinc-400">
                Sequential object-by-object prompt engineering and multi-pass refinement
              </p>
            </div>
          </div>
          <button
            onClick={() => setActiveModal('none')}
            className="p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action Bar */}
        <div className="p-3 bg-zinc-900/40 border-b border-zinc-800 flex items-center justify-between gap-2 flex-wrap">
          <div className="text-[10px] text-zinc-400">
            OBJECTS IDENTIFIED:{' '}
            <span className="text-zinc-100 font-bold">{plan.length} ITEMS</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchPlan}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-2.5 py-1 text-[10px] bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
              <span>RELOAD PLAN</span>
            </button>
            <button
              onClick={() => handleTriggerRefine()}
              disabled={isRunningLoop || plan.length === 0}
              className="flex items-center gap-1.5 px-3 py-1 text-[10px] bg-zinc-100 text-zinc-950 font-bold hover:bg-white active:bg-zinc-300 transition-colors"
            >
              <Play className="w-3 h-3 fill-zinc-950" />
              <span>{isRunningLoop ? 'EXECUTING LOOP...' : 'RUN FULL ANTIGRAVITY LOOP'}</span>
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-12 divide-y md:divide-y-0 md:divide-x divide-zinc-800">
          {/* Left Column: Object Hierarchy List */}
          <div className="md:col-span-5 overflow-y-auto max-h-[40vh] md:max-h-none p-2 space-y-1.5 bg-zinc-950">
            {plan.length === 0 ? (
              <div className="p-6 text-center text-zinc-500 text-[11px]">
                {isLoading ? 'Generating Antigravity CAD Plan...' : 'No objects detected in scene.'}
              </div>
            ) : (
              plan.map((step) => {
                const isSelected = selectedStep?.object_id === step.object_id;
                return (
                  <div
                    key={step.object_id}
                    onClick={() => setSelectedStep(step)}
                    className={`p-2.5 border text-left cursor-pointer transition-colors flex items-center justify-between gap-2 ${
                      isSelected
                        ? 'bg-zinc-900 border-zinc-600 text-zinc-100'
                        : 'bg-zinc-950/70 border-zinc-800/80 hover:bg-zinc-900/50 text-zinc-400'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      {step.crop_url ? (
                        <img
                          src={step.crop_url}
                          alt={step.object_name}
                          className="w-10 h-10 object-cover border border-zinc-800 shrink-0 bg-black"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-zinc-900 border border-zinc-800 flex items-center justify-center text-[9px] text-zinc-500 shrink-0">
                          N/A
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[9px] text-zinc-500 font-bold">
                            #{String(step.step).padStart(2, '0')}
                          </span>
                          <span className="text-[9px] px-1 py-0.2 bg-zinc-800 text-zinc-300 uppercase">
                            {step.category}
                          </span>
                        </div>
                        <div className="text-[11px] font-bold text-zinc-200 truncate">
                          {step.object_name}
                        </div>
                      </div>
                    </div>
                    <ChevronRight
                      className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-zinc-200' : 'text-zinc-600'}`}
                    />
                  </div>
                );
              })
            )}
          </div>

          {/* Right Column: Antigravity Prompt Inspector */}
          <div className="md:col-span-7 flex flex-col p-4 bg-zinc-900/20 overflow-y-auto">
            {selectedStep ? (
              <div className="space-y-3 flex-1 flex flex-col">
                <div className="flex items-start justify-between gap-2 border-b border-zinc-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] px-1.5 py-0.5 bg-zinc-800 text-zinc-300 uppercase font-bold">
                        PASS #{selectedStep.step} OF {selectedStep.total_steps}
                      </span>
                      <span className="text-[10px] text-zinc-500">ID: {selectedStep.object_id}</span>
                    </div>
                    <h3 className="text-sm font-bold text-zinc-100 mt-1">
                      {selectedStep.object_name}
                    </h3>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => handleCopyPrompt(selectedStep)}
                      className="flex items-center gap-1 px-2 py-1 text-[10px] bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-zinc-200 transition-colors"
                      title="Copy Antigravity CAD Prompt"
                    >
                      {copiedId === selectedStep.object_id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">COPIED</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>COPY PROMPT</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleTriggerRefine(selectedStep)}
                      disabled={isRunningLoop}
                      className="flex items-center gap-1 px-2.5 py-1 text-[10px] bg-zinc-100 text-zinc-950 font-bold hover:bg-white transition-colors"
                      title="Refine this object via desktop daemon"
                    >
                      <Play className="w-2.5 h-2.5 fill-zinc-950" />
                      <span>REFINE</span>
                    </button>
                  </div>
                </div>

                {/* Prompt Preview Textarea */}
                <div className="flex-1 flex flex-col">
                  <div className="text-[9px] uppercase tracking-wider text-zinc-500 mb-1">
                    ANTIGRAVITY GENERATED CAD PROMPT
                  </div>
                  <pre className="flex-1 p-3 bg-zinc-950 border border-zinc-800 text-[10px] leading-relaxed text-zinc-300 font-mono whitespace-pre-wrap overflow-y-auto max-h-[46vh]">
                    {selectedStep.antigravity_prompt}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-zinc-500 text-[11px]">
                Select an object on the left to inspect its Antigravity CAD prompt.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
