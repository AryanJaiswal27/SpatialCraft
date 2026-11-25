import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, X, Check, Loader2 } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';
import type { LLMTarget } from '../types';

export const UploadModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    targetLLM,
    setTargetLLM,
    setScene,
    setUploading,
    isUploading,
    uploadLogs,
    addUploadLog,
    refreshAvailableScenes,
  } = useSceneStore();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  if (activeModal !== 'upload') return null;

  const targets: { id: LLMTarget; name: string; host: string }[] = [
    { id: 'gemini', name: 'Physical on Gemini', host: 'gemini.google.com' },
    { id: 'chatgpt', name: 'Physical on ChatGPT', host: 'chatgpt.com' },
    { id: 'deepseek', name: 'Physical on DeepSeek', host: 'chat.deepseek.com' },
    { id: 'antigravity', name: 'Antigravity (Physical)', host: 'IDE Direct • Custom Mesh' },
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleStartProcessing = async () => {
    if (!selectedFile) return;

    setUploading(true, 'UPLOADING ARTIFACT');
    addUploadLog(`Artifact: ${selectedFile.name}`);
    addUploadLog(`Target Engine: ${targetLLM.toUpperCase()}`);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('target_llm', targetLLM);
      formData.append('auto_automate', 'true');

      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      const sceneId = data.scene_id;
      addUploadLog(`Assigned Scene ID: ${sceneId}`);

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/${sceneId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          addUploadLog(`[${payload.stage.toUpperCase()}] ${payload.message}`);

          if (payload.stage === 'done') {
            fetch(`/api/scene/${sceneId}`)
              .then((r) => r.json())
              .then((newScene) => {
                setScene(newScene);
                refreshAvailableScenes();
                setUploading(false);
                setActiveModal('none');
              });
          }
        } catch (e) {
          console.error(e);
        }
      };

      ws.onerror = () => {
        addUploadLog('[SYS] Polling mode fallback activated');
      };

      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(async () => {
        try {
          const checkRes = await fetch(`/api/scene/${sceneId}`);
          if (checkRes.ok) {
            const currentScene = await checkRes.json();
            if (currentScene.status === 'ready' && currentScene.objects?.length > 0) {
              if (intervalRef.current) clearInterval(intervalRef.current);
              setScene(currentScene);
              refreshAvailableScenes();
              setUploading(false);
              setActiveModal('none');
            } else if (currentScene.status === 'waiting_payload') {
              if (intervalRef.current) clearInterval(intervalRef.current);
              setUploading(false);
              addUploadLog(`[AUTH/PAYLOAD] ${currentScene.status_message || 'Login required. Tap PAYLOAD below.'}`);
            }
          }
        } catch (e) {
          console.error(e);
        }
      }, 3000);

    } catch (e: any) {
      addUploadLog(`[ERROR] ${e.message}`);
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 bg-black/80 backdrop-blur-xs font-mono animate-in fade-in">
      <div className="w-full max-w-md bg-zinc-950 border border-zinc-800 shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 text-[11px]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-zinc-100" />
            <h3 className="font-bold text-zinc-100 uppercase tracking-wider">
              Room Capture // Ingestion
            </h3>
          </div>
          <button
            onClick={() => setActiveModal('none')}
            disabled={isUploading}
            className="p-1 text-zinc-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto space-y-4 text-xs">
          {/* Target Engine Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">
                01. Select Physical Click Target
              </span>
              <span className="text-[9px] text-zinc-600 font-mono">
                OS Mouse & Keyboard Driver
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {targets.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTargetLLM(t.id)}
                  disabled={isUploading}
                  className={`flex flex-col justify-between p-2.5 border text-left transition-colors ${
                    targetLLM === t.id
                      ? 'border-zinc-100 bg-zinc-900 text-zinc-100 font-bold shadow-md'
                      : 'border-zinc-800 bg-zinc-950 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300'
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="text-[11px] uppercase tracking-wide">{t.name}</span>
                    {targetLLM === t.id && <Check className="w-3.5 h-3.5 text-zinc-100 shrink-0" />}
                  </div>
                  <span className="text-[9px] text-zinc-500 font-mono">{t.host}</span>
                </button>
              ))}
            </div>
            {targetLLM === 'antigravity' && (
              <div className="mt-2 p-2 border border-zinc-800 bg-zinc-900/60 text-[10px] text-zinc-300 font-mono">
                Direct IDE Mesh Mode: Physically pastes the room image &amp; instructions into Antigravity IDE chat so Antigravity identifies every object and builds custom 3D meshes with matching colors from scratch (avoiding prebuilt models).
              </div>
            )}
          </div>

          {/* Photo Selection */}
          <div>
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-2">
              02. Room Image Source
            </span>

            {previewUrl ? (
              <div className="relative border border-zinc-800 aspect-video bg-black overflow-hidden">
                <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setPreviewUrl(null);
                  }}
                  disabled={isUploading}
                  className="absolute top-2 right-2 p-1 bg-black/80 border border-zinc-700 text-white"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="flex flex-col items-center justify-center p-4 border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 text-zinc-300 transition-colors"
                >
                  <Camera className="w-5 h-5 mb-1 text-zinc-400" />
                  <span className="text-[11px] font-bold uppercase">Camera</span>
                  <span className="text-[9px] text-zinc-500">Live Device Capture</span>
                </button>

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center p-4 border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 text-zinc-300 transition-colors"
                >
                  <Upload className="w-5 h-5 mb-1 text-zinc-400" />
                  <span className="text-[11px] font-bold uppercase">Storage</span>
                  <span className="text-[9px] text-zinc-500">Local Image File</span>
                </button>

                <input
                  ref={cameraInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
            )}
          </div>

          {/* Execution Log */}
          {isUploading && (
            <div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-1">
                03. Automation Console
              </span>
              <div className="bg-black border border-zinc-800 p-2.5 text-[10px] text-zinc-300 space-y-1 max-h-32 overflow-y-auto font-mono">
                {uploadLogs.map((log, idx) => (
                  <div key={idx} className="leading-tight">
                    <span className="text-zinc-600 mr-1">#</span>
                    {log}
                  </div>
                ))}
                <div className="flex items-center gap-1.5 text-zinc-400 pt-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Processing browser driver...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-zinc-800 bg-zinc-950 flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setActiveModal('manual_paste')}
              className="text-[10px] text-zinc-500 hover:text-zinc-200 underline underline-offset-4"
            >
              Direct JSON Input
            </button>
            <button
              type="button"
              onClick={() => setActiveModal('calibration')}
              className="text-[10px] text-zinc-400 hover:text-zinc-100 font-bold uppercase underline underline-offset-4"
            >
              Calibrate Clicks
            </button>
          </div>

          <button
            type="button"
            onClick={handleStartProcessing}
            disabled={!selectedFile || isUploading}
            className={`flex items-center gap-1.5 px-4 py-2 font-mono font-bold text-[11px] transition-colors ${
              !selectedFile || isUploading
                ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
                : 'bg-zinc-100 hover:bg-white text-zinc-950'
            }`}
          >
            {isUploading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>EXECUTING...</span>
              </>
            ) : (
              <span>RECONSTRUCT 3D</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
