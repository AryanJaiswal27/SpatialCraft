import { useEffect } from 'react';
import { SceneViewport3D } from './components/SceneViewport3D';
import { MobileHeader } from './components/MobileHeader';
import { MobileBottomControls } from './components/MobileBottomControls';
import { UploadModal } from './components/UploadModal';
import { ChatPromptDrawer } from './components/ChatPromptDrawer';
import { ManualPasteModal } from './components/ManualPasteModal';
import { QrModal } from './components/QrModal';
import { LogsModal } from './components/LogsModal';
import { CalibrationModal } from './components/CalibrationModal';
import { AntigravityModal } from './components/AntigravityModal';
import { GuideModal } from './components/GuideModal';
import { ModelCatalogDrawer } from './components/ModelCatalogDrawer';
import { useSceneStore } from './hooks/useSceneStore';
import type { SceneGraph } from './types';

// Default Spatial Matrix Geode Core (Zero dummy furniture on startup)
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

export default function App() {
  const { scene, setScene, setAvailableScenes } = useSceneStore();

  useEffect(() => {
    // Populate scene history for the room dropdown
    fetch('/api/scenes')
      .then((res) => res.json())
      .then((scenes) => {
        if (Array.isArray(scenes)) {
          setAvailableScenes(scenes);
        }
      })
      .catch((e) => console.error('Failed to load scenes list:', e));

    // Check for direct deep-link ?scene= query parameter
    const params = new URLSearchParams(window.location.search);
    const targetSceneId = params.get('scene');
    if (targetSceneId && targetSceneId !== 'home') {
      fetch(`/api/scene/${targetSceneId}`)
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error('Scene not found');
        })
        .then((data) => setScene(data))
        .catch(() => {
          if (!scene) setScene(HOME_GEODE_SCENE);
        });
    } else if (!scene) {
      setScene(HOME_GEODE_SCENE);
    }
  }, [setScene, setAvailableScenes]);

  return (
    <main className="w-full h-full relative overflow-hidden select-none bg-zinc-950 font-mono">
      <MobileHeader />
      <SceneViewport3D />
      <MobileBottomControls />
      <UploadModal />
      <ChatPromptDrawer />
      <ManualPasteModal />
      <QrModal />
      <LogsModal />
      <CalibrationModal />
      <AntigravityModal />
      <GuideModal />
      <ModelCatalogDrawer />
    </main>
  );
}
