import React, { useState, useEffect } from 'react';
import { Terminal, X, RefreshCw } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

export const LogsModal: React.FC = () => {
  const { activeModal, setActiveModal } = useSceneStore();
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs?limit=100');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.logs)) {
          setLogs(data.logs);
        }
      }
    } catch (e) {
      console.error('Failed to fetch logs:', e);
    }
  };

  useEffect(() => {
    if (activeModal === 'logs') {
      fetchLogs();
      const interval = setInterval(() => {
        if (autoRefresh) fetchLogs();
      }, 2500);
      return () => clearInterval(interval);
    }
  }, [activeModal, autoRefresh]);

  if (activeModal !== 'logs') return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/80 backdrop-blur-xs font-mono animate-in fade-in">
      <div className="w-full max-w-2xl bg-zinc-950 border border-zinc-800 shadow-2xl flex flex-col h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2.5 border-b border-zinc-800 text-[11px] shrink-0 gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Terminal className="w-4 h-4 text-zinc-100 shrink-0" />
            <span className="font-bold text-zinc-100 uppercase tracking-wider truncate">
              Telemetry Console
            </span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={() => {
                setLoading(true);
                fetchLogs().finally(() => setLoading(false));
              }}
              className="p-1 text-zinc-400 hover:text-white"
              title="Refresh"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setActiveModal('none')}
              className="p-1 text-zinc-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Live Terminal Log Stream */}
        <div className="flex-1 p-3 bg-black overflow-y-auto font-mono text-[10px] leading-relaxed space-y-1 text-zinc-300 select-text">
          {logs.length === 0 ? (
            <div className="text-zinc-600 italic py-4 text-center">
              Awaiting background pipeline events...
            </div>
          ) : (
            logs.map((log, idx) => {
              let styling = 'text-zinc-400';
              if (log.includes('[ERROR]') || log.includes('failed') || log.includes('Error')) {
                styling = 'text-zinc-100 font-bold bg-zinc-900/90 pl-1 border-l-2 border-zinc-100';
              } else if (log.includes('[PIPELINE') || log.includes('[STATUS]')) {
                styling = 'text-zinc-200 font-semibold';
              } else if (log.includes('[Gemini') || log.includes('[ChatGPT') || log.includes('[Claude')) {
                styling = 'text-zinc-300';
              } else if (log.includes('[AUTH') || log.includes('SECURITY')) {
                styling = 'text-zinc-100 font-bold underline underline-offset-2';
              }
              return (
                <div key={idx} className={`${styling} break-all leading-snug`}>
                  {log}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-3 py-2 border-t border-zinc-800 bg-zinc-950 flex items-center justify-between text-[10px] text-zinc-500 shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-zinc-100 animate-pulse" />
            <span>Telemetry Active ({logs.length} events)</span>
          </div>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-2 py-1 text-[9px] border transition-colors ${
              autoRefresh
                ? 'border-zinc-500 text-zinc-100 bg-zinc-900'
                : 'border-zinc-800 text-zinc-600'
            }`}
          >
            {autoRefresh ? 'AUTO-REFRESH: ON' : 'AUTO-REFRESH: OFF'}
          </button>
        </div>
      </div>
    </div>
  );
};
