import React, { useState } from 'react';
import {
  X,
  PackagePlus,
  Move,
  Plus,
  Armchair,
  Table,
  Archive,
  Lightbulb,
  Flower2,
  Laptop,
  Check,
} from 'lucide-react';
import { useSceneStore } from '../hooks/useSceneStore';
import { MODEL_CATALOG, type CatalogModel } from '../data/modelCatalog';
import { ModelRotatingPreview } from './ModelRotatingPreview';

type CategoryFilter = 'ALL' | 'SEATING' | 'TABLES' | 'STORAGE' | 'LIGHTING' | 'PLANTS' | 'TECH & DECOR';

export const ModelCatalogDrawer: React.FC = () => {
  const { activeModal, setActiveModal, addObject } = useSceneStore();
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>('ALL');
  const [justAddedId, setJustAddedId] = useState<string | null>(null);

  if (activeModal !== 'models') return null;

  const categories: { label: CategoryFilter; icon: React.FC<{ className?: string }> }[] = [
    { label: 'ALL', icon: PackagePlus },
    { label: 'SEATING', icon: Armchair },
    { label: 'TABLES', icon: Table },
    { label: 'STORAGE', icon: Archive },
    { label: 'LIGHTING', icon: Lightbulb },
    { label: 'PLANTS', icon: Flower2 },
    { label: 'TECH & DECOR', icon: Laptop },
  ];

  const filteredModels = MODEL_CATALOG.filter((m) => {
    if (selectedCategory === 'ALL') return true;
    if (selectedCategory === 'SEATING') return m.category === 'chair' || m.category === 'sofa';
    if (selectedCategory === 'TABLES') return m.category === 'table';
    if (selectedCategory === 'STORAGE') return m.category === 'bookshelf';
    if (selectedCategory === 'LIGHTING') return m.category === 'lamp';
    if (selectedCategory === 'PLANTS') return m.category === 'plant';
    if (selectedCategory === 'TECH & DECOR') return m.category === 'decor' || m.category === 'art';
    return true;
  });

  const handleAddClick = (model: CatalogModel) => {
    addObject(model);
    setJustAddedId(model.id);
    setTimeout(() => {
      setJustAddedId((curr) => (curr === model.id ? null : curr));
    }, 1500);
  };

  const handleDragStart = (e: React.DragEvent, model: CatalogModel) => {
    e.dataTransfer.setData('application/json', JSON.stringify(model));
    e.dataTransfer.effectAllowed = 'copy';
  };

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 flex flex-col font-mono pointer-events-auto pb-[env(safe-area-inset-bottom)]">
      {/* Semi-transparent backdrop for dismissing */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-xs -z-10"
        onClick={() => setActiveModal('none')}
      />

      <div className="bg-zinc-950/98 border-t border-zinc-800 shadow-2xl flex flex-col max-h-[82vh] sm:max-h-[68vh] transition-all">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800/80 bg-zinc-900/40">
          <div className="flex items-center gap-2 min-w-0">
            <span className="w-2 h-2 bg-zinc-200" />
            <span className="text-[11px] font-bold text-zinc-100 tracking-wider uppercase truncate">
              3D MODEL CATALOG // ASSET ASSEMBLE
            </span>
            <span className="hidden sm:inline text-[9px] text-zinc-500">
              [DRAG &amp; DROP ON SCENE • OR TAP DROP]
            </span>
          </div>

          <button
            onClick={() => setActiveModal('none')}
            className="p-1 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
            title="Close Model Drawer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Category Filter Pills (Horizontal Scrollable on Mobile) */}
        <div className="flex items-center gap-1.5 px-3 py-2 border-b border-zinc-800/60 overflow-x-auto no-scrollbar shrink-0 bg-zinc-950/80">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isActive = selectedCategory === cat.label;
            return (
              <button
                key={cat.label}
                onClick={() => setSelectedCategory(cat.label)}
                className={`flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold tracking-wider shrink-0 transition-colors border ${
                  isActive
                    ? 'bg-zinc-100 text-zinc-950 border-zinc-100'
                    : 'bg-zinc-900/90 text-zinc-400 border-zinc-800 hover:text-zinc-200 hover:border-zinc-700'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>

        {/* Model Cards Scroll Container */}
        <div className="p-3 overflow-y-auto no-scrollbar">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
            {filteredModels.map((model) => {
              const isAdded = justAddedId === model.id;
              const w = model.dimensions.width;
              const h = model.dimensions.height;
              const d = model.dimensions.depth;

              return (
                <div
                  key={model.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, model)}
                  className="group bg-zinc-900/60 border border-zinc-800 hover:border-zinc-600 transition-all p-2.5 flex flex-col justify-between gap-2 cursor-grab active:cursor-grabbing relative select-none"
                >
                  {/* Top Bar: Category badge & Color Swatch */}
                  <div className="flex items-center justify-between text-[9px]">
                    <span className="text-zinc-400 font-bold uppercase tracking-wider">
                      [{model.category.toUpperCase()}]
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-zinc-500 text-[8px]">{model.parts?.length || 1} PARTS</span>
                      <span
                        className="w-2.5 h-2.5 border border-zinc-700 shrink-0"
                        style={{ backgroundColor: model.color }}
                        title={`Color: ${model.color}`}
                      />
                    </div>
                  </div>

                  {/* Live 3D Rotating Turntable Preview */}
                  <ModelRotatingPreview
                    parts={model.parts}
                    dimensions={model.dimensions}
                    color={model.color}
                    name={model.name}
                  />

                  {/* Title & Description */}
                  <div className="space-y-1">
                    <h4 className="text-[11px] font-bold text-zinc-100 group-hover:text-white truncate">
                      {model.name}
                    </h4>
                    <p className="text-[9px] text-zinc-400 line-clamp-2 leading-relaxed">
                      {model.description}
                    </p>
                  </div>

                  {/* Dimensions Metric */}
                  <div className="text-[9px] text-zinc-500 bg-zinc-950/80 px-2 py-1 border border-zinc-800/80 flex items-center justify-between">
                    <span>BOUNDS:</span>
                    <span className="text-zinc-300 font-bold">
                      {w.toFixed(2)}x{h.toFixed(2)}x{d.toFixed(2)}m
                    </span>
                  </div>

                  {/* Action Button: Mobile Tap / Quick Add & Drag indicator */}
                  <div className="flex items-center gap-1.5 pt-1">
                    <button
                      type="button"
                      onClick={() => handleAddClick(model)}
                      className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-2 text-[10px] font-bold border transition-colors ${
                        isAdded
                          ? 'bg-zinc-200 text-zinc-950 border-zinc-200'
                          : 'bg-zinc-900 hover:bg-zinc-800 border-zinc-700 text-zinc-100 active:bg-zinc-700'
                      }`}
                    >
                      {isAdded ? (
                        <>
                          <Check className="w-3 h-3 text-zinc-950" />
                          <span>ADDED!</span>
                        </>
                      ) : (
                        <>
                          <Plus className="w-3 h-3 text-zinc-300" />
                          <span>DROP IN SCENE</span>
                        </>
                      )}
                    </button>

                    <div
                      className="hidden sm:flex items-center justify-center p-1.5 bg-zinc-900 border border-zinc-800 text-zinc-500 group-hover:text-zinc-300"
                      title="Drag and drop onto 3D scene"
                    >
                      <Move className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
