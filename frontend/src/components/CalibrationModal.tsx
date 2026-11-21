import React, { useState, useEffect } from 'react';
import { MousePointerClick, X, Save, RefreshCw, Check, Monitor, Terminal } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

interface TargetCoord {
  name: string;
  x: number;
  y: number;
  description: string;
}

export const CalibrationModal: React.FC = () => {
  const { activeModal, setActiveModal } = useSceneStore();
  const [config, setConfig] = useState<any>(null);
  const [targets, setTargets] = useState<Record<string, TargetCoord>>({});
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [testingKey, setTestingKey] = useState<string | null>(null);

  const handleTestTarget = async (key: string, target: TargetCoord) => {
    setTestingKey(key);
    try {
      await fetch('/api/physical_clicks/test_target', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: key, coords: { x: target.x, y: target.y } }),
      });
    } catch (e) {
      console.error('Failed to trigger hover test:', e);
    } finally {
      setTimeout(() => setTestingKey(null), 1500);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/physical_clicks/config');
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
        if (data.targets) {
          setTargets(data.targets);
        }
      }
    } catch (e) {
      console.error('Failed to load physical config:', e);
    }
  };

  useEffect(() => {
    if (activeModal === 'calibration') {
      fetchConfig();
    }
  }, [activeModal]);

  if (activeModal !== 'calibration') return null;

  const handleCoordChange = (key: string, field: 'x' | 'y', val: number) => {
    setTargets((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: val,
      },
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSavedSuccess(false);
    try {
      const updatedConfig = {
        ...config,
        targets,
        last_calibrated_at: new Date().toISOString(),
      };
      const res = await fetch('/api/physical_clicks/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedConfig),
      });
      if (res.ok) {
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2500);
      }
    } catch (e) {
      console.error('Failed to save calibration:', e);
    } finally {
      setSaving(false);
    }
  };

  const targetList = [
    { key: 'browser_tab', defaultName: '01. Browser Tab Header', hint: 'Chrome tab header to bring window to focus' },
    { key: 'prompt_box', defaultName: '02. Prompt Input Box', hint: 'Composer textarea (Images & prompts are pasted here via Ctrl+V)' },
    { key: 'send_button', defaultName: '03. Send / Submit Button', hint: 'Send arrow or submit button' },
    { key: 'copy_button', defaultName: '04. Copy Response Button', hint: 'Copy Markdown icon at bottom of response' },
    { key: 'ide_chat_box', defaultName: '05. Antigravity IDE Chat Input', hint: 'Input box at bottom of Antigravity IDE (pastes LLM response here)' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-xs font-mono animate-in fade-in select-none">
      <div className="w-full max-w-lg bg-zinc-950 border border-zinc-800 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 text-[11px] shrink-0">
          <div className="flex items-center gap-2">
            <MousePointerClick className="w-4 h-4 text-zinc-100" />
            <h3 className="font-bold text-zinc-100 uppercase tracking-wider">
              Physical Click Coordinates // Calibration
            </h3>
          </div>
          <button
            onClick={() => setActiveModal('none')}
            className="p-1 text-zinc-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 overflow-y-auto text-xs font-mono">
          {/* Quick Info Box */}
          <div className="border border-zinc-800 bg-zinc-900/60 p-3 space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-bold text-zinc-200 uppercase tracking-wide flex items-center gap-1.5">
                <Monitor className="w-3.5 h-3.5 text-zinc-400" />
                Target Monitor: {config?.screen?.width || 1920}x{config?.screen?.height || 1080}
              </span>
              <button
                onClick={fetchConfig}
                className="text-[10px] text-zinc-400 hover:text-white flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>RELOAD</span>
              </button>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed">
              Coordinates correspond to physical screen pixels on your desktop. Antigravity moves the
              physical cursor, pastes prompts and captures responses directly in your open browser window.
            </p>
            <div className="bg-black border border-zinc-800 p-2 text-[10px] text-zinc-300 flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
              <span>
                To auto-record by hovering cursor: run <strong className="text-white">calibrate_antigravity.bat</strong> in project root.
              </span>
            </div>
          </div>

          {/* Coordinate Target Inputs */}
          <div className="space-y-2">
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">
              Calibrated Coordinate Matrix
            </span>

            <div className="space-y-1.5">
              {targetList.map((item) => {
                const target = targets[item.key] || {
                  name: item.defaultName,
                  x: 0,
                  y: 0,
                  description: item.hint,
                };
                return (
                  <div
                    key={item.key}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-2 border border-zinc-800/80 bg-black/60 gap-2"
                  >
                    <div className="min-w-0">
                      <div className="text-[11px] font-bold text-zinc-200 truncate">
                        {target.name || item.defaultName}
                      </div>
                      <div className="text-[9px] text-zinc-500 truncate">
                        {item.hint}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 px-2 py-1">
                        <span className="text-[10px] text-zinc-500">X:</span>
                        <input
                          type="number"
                          value={target.x || 0}
                          onChange={(e) =>
                            handleCoordChange(item.key, 'x', parseInt(e.target.value) || 0)
                          }
                          className="w-16 bg-transparent text-zinc-100 text-[11px] font-mono outline-none text-right"
                        />
                      </div>
                      <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 px-2 py-1">
                        <span className="text-[10px] text-zinc-500">Y:</span>
                        <input
                          type="number"
                          value={target.y || 0}
                          onChange={(e) =>
                            handleCoordChange(item.key, 'y', parseInt(e.target.value) || 0)
                          }
                          className="w-16 bg-transparent text-zinc-100 text-[11px] font-mono outline-none text-right"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => handleTestTarget(item.key, target)}
                        className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 text-[9px] font-bold transition-colors"
                        title="Move mouse cursor to this spot on your screen"
                      >
                        {testingKey === item.key ? 'HOVERING...' : 'TEST'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-zinc-800 bg-zinc-950 flex items-center justify-between text-xs shrink-0">
          <div className="text-[10px] text-zinc-500">
            {savedSuccess ? (
              <span className="text-zinc-200 font-bold flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-zinc-100" />
                COORDINATES SAVED!
              </span>
            ) : config?.last_calibrated_at ? (
              <span>Last calibrated: {new Date(config.last_calibrated_at).toLocaleTimeString()}</span>
            ) : (
              <span>Using default calibration values</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveModal('none')}
              className="px-3 py-1.5 text-zinc-400 hover:text-zinc-100 font-bold text-[11px]"
            >
              DISMISS
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 font-mono font-bold text-[11px] transition-colors"
            >
              <Save className="w-3.5 h-3.5" />
              <span>SAVE CALIBRATION</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
