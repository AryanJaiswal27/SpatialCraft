import React, { useState, useEffect } from 'react';
import { MousePointerClick, X, Save, RefreshCw, Check, Monitor, Terminal, Radio, ExternalLink } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

interface TargetCoord {
  name: string;
  x: number;
  y: number;
  description: string;
}

interface PresetData {
  id: string;
  label: string;
  browser_url?: string;
  targets: Record<string, TargetCoord>;
  delays?: Record<string, number>;
  last_calibrated_at?: string | null;
}

const PRESET_TABS = [
  { id: 'gemini', label: 'Google Gemini', url: 'https://gemini.google.com' },
  { id: 'chatgpt', label: 'OpenAI ChatGPT', url: 'https://chatgpt.com' },
  { id: 'deepseek', label: 'DeepSeek Chat', url: 'https://chat.deepseek.com' },
  { id: 'antigravity', label: 'Antigravity IDE', url: 'ide://antigravity' },
];

export const CalibrationModal: React.FC = () => {
  const { activeModal, setActiveModal } = useSceneStore();
  const [config, setConfig] = useState<any>(null);
  const [selectedPreset, setSelectedPreset] = useState<string>('gemini');
  const [activePreset, setActivePreset] = useState<string>('gemini');
  const [presets, setPresets] = useState<Record<string, PresetData>>({});
  const [saving, setSaving] = useState(false);
  const [activating, setActivating] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [activatedSuccess, setActivatedSuccess] = useState(false);
  const [testingKey, setTestingKey] = useState<string | null>(null);

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/physical_clicks/config');
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
        const curActive = data.active_preset || 'gemini';
        setActivePreset(curActive);
        setSelectedPreset(curActive);
        if (data.presets) {
          setPresets(data.presets);
        }
      }
    } catch (e) {
      console.error('Failed to load physical config:', e);
    }
  };

  useEffect(() => {
    if (activeModal !== 'calibration') return;
    let cancelled = false;
    fetch('/api/physical_clicks/config')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        setConfig(data);
        const curActive = data.active_preset || 'gemini';
        setActivePreset(curActive);
        setSelectedPreset(curActive);
        if (data.presets) {
          setPresets(data.presets);
        }
      })
      .catch((e) => console.error('Failed to load physical config:', e));
    return () => {
      cancelled = true;
    };
  }, [activeModal]);

  if (activeModal !== 'calibration') return null;

  const currentPresetData = presets[selectedPreset] || {
    id: selectedPreset,
    label: selectedPreset.toUpperCase(),
    targets: {},
  };

  const currentTargets = currentPresetData.targets || {};

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

  const handleCoordChange = (key: string, field: 'x' | 'y', val: number) => {
    setPresets((prev) => {
      const existing = prev[selectedPreset] || {
        id: selectedPreset,
        label: selectedPreset,
        targets: {},
      };
      const existingTargets = existing.targets || {};
      const targetObj = existingTargets[key] || { name: key, x: 0, y: 0, description: '' };

      return {
        ...prev,
        [selectedPreset]: {
          ...existing,
          targets: {
            ...existingTargets,
            [key]: {
              ...targetObj,
              [field]: val,
            },
          },
        },
      };
    });
  };

  const handleActivatePreset = async (presetId: string) => {
    setActivating(true);
    setActivatedSuccess(false);
    try {
      const res = await fetch(`/api/physical_clicks/preset/${presetId}/activate`, {
        method: 'POST',
      });
      if (res.ok) {
        setActivePreset(presetId);
        setActivatedSuccess(true);
        setTimeout(() => setActivatedSuccess(false), 2500);
        await fetchConfig();
      }
    } catch (e) {
      console.error('Failed to activate preset:', e);
    } finally {
      setActivating(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSavedSuccess(false);
    try {
      const updatedConfig = {
        ...config,
        active_preset: activePreset,
        presets,
        targets: presets[activePreset]?.targets || currentTargets,
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
        await fetchConfig();
      }
    } catch (e) {
      console.error('Failed to save calibration:', e);
    } finally {
      setSaving(false);
    }
  };

  const targetList =
    selectedPreset === 'antigravity'
      ? [
          {
            key: 'antigravity_header',
            defaultName: '01. Antigravity Window / Top Header',
            hint: 'Top title bar or taskbar icon to bring Antigravity IDE window to front',
          },
          {
            key: 'ide_chat_box',
            defaultName: '02. Antigravity IDE Chat Input',
            hint: 'Chat composer box at bottom of Antigravity IDE (pastes room image & custom 3D mesh prompt here)',
          },
        ]
      : [
          {
            key: 'browser_tab',
            defaultName: `01. ${currentPresetData.label || 'Browser'} Tab Header`,
            hint: `Hover over your ${currentPresetData.label || 'browser'} tab or taskbar icon`,
          },
          {
            key: 'prompt_box',
            defaultName: `02. ${currentPresetData.label || 'Chat'} Prompt Input`,
            hint: `Composer input box (Ctrl+V pastes image crops and CAD prompts here)`,
          },
          {
            key: 'send_button',
            defaultName: `03. ${currentPresetData.label || 'Send'} Button`,
            hint: `Send arrow / submit button to dispatch prompts`,
          },
          {
            key: 'copy_button',
            defaultName: `04. ${currentPresetData.label || 'Copy'} Button`,
            hint: `Copy button icon at bottom of generated response to extract CAD output`,
          },
          {
            key: 'antigravity_header',
            defaultName: '05. Antigravity Window / Top Header',
            hint: 'Top title bar to bring Antigravity IDE window to front',
          },
          {
            key: 'ide_chat_box',
            defaultName: '06. Antigravity IDE Chat Input',
            hint: 'Chat composer box at bottom of Antigravity IDE',
          },
        ];

  const isCurrentActive = selectedPreset === activePreset;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-xs font-mono animate-in fade-in select-none">
      <div className="w-full max-w-xl bg-zinc-950 border border-zinc-800 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 text-[11px] shrink-0">
          <div className="flex items-center gap-2">
            <MousePointerClick className="w-4 h-4 text-zinc-100" />
            <h3 className="font-bold text-zinc-100 uppercase tracking-wider">
              Physical Click Coordinates // Multi-LLM Presets
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
          {/* Preset Selector Tabs */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[10px] text-zinc-400 font-bold uppercase tracking-wider">
              <span>Select LLM Preset</span>
              <span className="flex items-center gap-1.5 text-zinc-300">
                <span>Active Target:</span>
                <span className="text-zinc-100 font-bold bg-zinc-900 border border-zinc-700 px-1.5 py-0.5">
                  {presets[activePreset]?.label || activePreset.toUpperCase()}
                </span>
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {PRESET_TABS.map((tab) => {
                const isActive = tab.id === activePreset;
                const isSelected = tab.id === selectedPreset;

                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setSelectedPreset(tab.id)}
                    className={`p-2.5 text-left border transition-colors relative flex flex-col justify-between ${
                      isSelected
                        ? 'border-zinc-200 bg-zinc-900 text-white'
                        : 'border-zinc-800 bg-black/50 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold truncate">{tab.label}</span>
                      {isActive && (
                        <span className="text-[8px] font-bold px-1 py-0.2 bg-emerald-950 text-emerald-400 border border-emerald-800">
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <span className="text-[9px] text-zinc-500 truncate mt-1 flex items-center gap-1">
                      <span>{tab.id}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Preset Control Bar */}
          <div className="flex items-center justify-between p-2.5 border border-zinc-800 bg-zinc-900/60">
            <div className="min-w-0 pr-2">
              <div className="text-[11px] font-bold text-zinc-200 flex items-center gap-1.5">
                <span>{currentPresetData.label} Calibration</span>
                {isCurrentActive ? (
                  <span className="text-[9px] text-emerald-400 font-bold bg-emerald-950/80 border border-emerald-800/80 px-1.5 py-0.2">
                    ● ACTIVE IN DAEMON
                  </span>
                ) : (
                  <span className="text-[9px] text-zinc-400 bg-zinc-800/80 border border-zinc-700 px-1.5 py-0.2">
                    INACTIVE
                  </span>
                )}
              </div>
              <div className="text-[9px] text-zinc-400 truncate mt-0.5">
                {selectedPreset === 'antigravity'
                  ? 'Antigravity IDE Chat Composer (Direct Image + Custom 3D Mesh)'
                  : currentPresetData.browser_url || 'Custom browser window'}
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {!isCurrentActive && (
                <button
                  type="button"
                  onClick={() => handleActivatePreset(selectedPreset)}
                  disabled={activating}
                  className="px-2.5 py-1 bg-zinc-100 hover:bg-white text-zinc-950 text-[10px] font-bold flex items-center gap-1 transition-colors"
                >
                  <Radio className="w-3 h-3" />
                  <span>{activating ? 'ACTIVATING...' : 'SET AS ACTIVE'}</span>
                </button>
              )}
              {currentPresetData.browser_url?.startsWith('http') && (
                <a
                  href={currentPresetData.browser_url}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1 text-zinc-400 hover:text-white"
                  title="Open LLM in new browser tab"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>

          {/* CLI Hover Calibration Hint */}
          <div className="bg-black border border-zinc-800 p-2.5 text-[10px] text-zinc-300 flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <span className="truncate">
              To calibrate {currentPresetData.label} via cursor: run{' '}
              <strong className="text-white">calibrate_clicks.bat {selectedPreset}</strong> in project root.
            </span>
          </div>

          {/* Coordinate Target Inputs for Selected Preset */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
              <span>{currentPresetData.label} Screen Coordinates</span>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1">
                  <Monitor className="w-3 h-3 text-zinc-400" />
                  <span>{config?.screen?.width || 1920}x{config?.screen?.height || 1080}</span>
                </span>
                <button
                  type="button"
                  onClick={fetchConfig}
                  className="p-0.5 hover:text-white text-zinc-400"
                  title="Reload configuration"
                >
                  <RefreshCw className="w-3 h-3" />
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              {targetList.map((item) => {
                const target = currentTargets[item.key] || {
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
                PRESET SAVED!
              </span>
            ) : activatedSuccess ? (
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                ACTIVATED AS CURRENT TARGET!
              </span>
            ) : currentPresetData.last_calibrated_at ? (
              <span>Last calibrated: {new Date(currentPresetData.last_calibrated_at).toLocaleTimeString()}</span>
            ) : (
              <span>Uncalibrated preset template</span>
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
              <span>SAVE {currentPresetData.label?.toUpperCase() || 'PRESET'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
