import React, { useState } from 'react';
import { X, Loader2, Terminal } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

export const ChatPromptDrawer: React.FC = () => {
  const { activeModal, setActiveModal, sendPromptEdit, isPrompting } = useSceneStore();
  const [promptText, setPromptText] = useState('');

  if (activeModal !== 'chat') return null;

  const presetCommands = [
    'Place a phone on table',
    'Place a laptop on desk',
    'Stick phone to table',
    'Snap art to north wall',
    'Unstick all furniture',
    'Translate sofa X -0.5m',
    'Rotate coffee table 90 deg',
    'Set wall color to #dedad3',
    'Insert floor lamp',
    'Remove selected furniture',
  ];

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!promptText.trim() || isPrompting) return;

    await sendPromptEdit(promptText);
    setPromptText('');
    setActiveModal('none');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-xs font-mono animate-in fade-in">
      <div className="w-full sm:max-w-lg bg-zinc-950 border border-zinc-800 shadow-2xl flex flex-col max-h-[85vh] pb-[env(safe-area-inset-bottom)]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 text-[11px]">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-zinc-300" />
            <h3 className="font-bold text-zinc-100 uppercase tracking-wider">
              Spatial Command Interpreter
            </h3>
          </div>
          <button
            onClick={() => setActiveModal('none')}
            className="p-1 text-zinc-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Preset commands */}
        <div className="p-4 space-y-3 overflow-y-auto">
          <div>
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-2">
              Preset Directives
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {presetCommands.map((cmd, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setPromptText(cmd)}
                  className="text-[11px] text-left px-2.5 py-1.5 border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-300 active:bg-zinc-700 transition-colors truncate"
                >
                  <span className="text-zinc-600 mr-1.5">&gt;</span>
                  {cmd}
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="pt-2">
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-1.5">
              Command Input
            </span>
            <div className="flex items-center border border-zinc-800 bg-black focus-within:border-zinc-400">
              <span className="px-3 text-zinc-500 text-xs">&gt;</span>
              <input
                type="text"
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                placeholder="Type spatial transformation command..."
                className="flex-1 bg-transparent text-xs text-zinc-100 py-2.5 pr-2 outline-none placeholder:text-zinc-600 font-mono"
                disabled={isPrompting}
                autoFocus
              />
              <button
                type="submit"
                disabled={!promptText.trim() || isPrompting}
                className={`px-4 py-2.5 text-xs font-bold font-mono transition-colors ${
                  !promptText.trim() || isPrompting
                    ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                    : 'bg-zinc-100 hover:bg-white text-zinc-950'
                }`}
              >
                {isPrompting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span>EXECUTE</span>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
