import React, { useState, useEffect } from 'react';
import { QrCode, X, Copy, Check } from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';

export const QrModal: React.FC = () => {
  const { activeModal, setActiveModal } = useSceneStore();
  const [copiedType, setCopiedType] = useState<string | null>(null);
  const [tunnelUrl, setTunnelUrl] = useState<string>('');

  useEffect(() => {
    fetch('/tunnel_url.json')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.tunnel_url) {
          setTunnelUrl(data.tunnel_url);
        }
      })
      .catch(() => {});
  }, []);

  if (activeModal !== 'qr') return null;

  const publicUrl = tunnelUrl || (typeof window !== 'undefined' ? window.location.origin : '');
  const localUrl = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://localhost:8000';

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopiedType(type);
    setTimeout(() => setCopiedType(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 bg-black/80 backdrop-blur-xs font-mono animate-in fade-in">
      <div className="w-full max-w-sm bg-zinc-950 border border-zinc-800 shadow-2xl flex flex-col p-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800 text-[11px]">
          <div className="flex items-center gap-2">
            <QrCode className="w-4 h-4 text-zinc-100" />
            <span className="font-bold text-zinc-100 uppercase tracking-wider">
              Mobile Ingress Matrix
            </span>
          </div>
          <button
            onClick={() => setActiveModal('none')}
            className="p-1 text-zinc-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Crisp QR Code Image (White card background for 100% optical readability) */}
        <div className="flex flex-col items-center justify-center p-4 bg-white border border-zinc-300 mx-auto w-56 h-56 mb-4">
          <img
            src="/qr.png"
            alt="Optical Connection Matrix"
            className="w-full h-full object-contain"
          />
        </div>

        {/* Direct URL Endpoints with Copy Buttons */}
        <div className="space-y-2 text-[10px]">
          {/* Public Tunnel Endpoint */}
          <div className="border border-zinc-800 bg-zinc-900/60 p-2">
            <span className="text-zinc-500 block text-[9px] uppercase font-bold">
              01. Public Endpoint (Cellular / Remote)
            </span>
            <div className="flex items-center justify-between gap-1 mt-1">
              <span className="text-zinc-200 truncate select-all">{publicUrl}</span>
              <button
                onClick={() => copyToClipboard(publicUrl, 'public')}
                className="p-1 text-zinc-400 hover:text-zinc-100 transition-colors"
                title="Copy Public Link"
              >
                {copiedType === 'public' ? (
                  <Check className="w-3.5 h-3.5 text-zinc-100" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>

          {/* Local Network Endpoint */}
          <div className="border border-zinc-800 bg-zinc-900/60 p-2">
            <span className="text-zinc-500 block text-[9px] uppercase font-bold">
              02. Local Area Endpoint (Same Wi-Fi)
            </span>
            <div className="flex items-center justify-between gap-1 mt-1">
              <span className="text-zinc-200 truncate select-all">{localUrl}</span>
              <button
                onClick={() => copyToClipboard(localUrl, 'local')}
                className="p-1 text-zinc-400 hover:text-zinc-100 transition-colors"
                title="Copy Local Link"
              >
                {copiedType === 'local' ? (
                  <Check className="w-3.5 h-3.5 text-zinc-100" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 mt-3 border-t border-zinc-800 flex justify-end">
          <button
            onClick={() => setActiveModal('none')}
            className="px-3 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 font-bold text-[11px]"
          >
            DISMISS
          </button>
        </div>
      </div>
    </div>
  );
};
